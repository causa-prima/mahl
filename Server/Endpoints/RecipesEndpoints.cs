using System.Collections.Immutable;
using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Middleware;
using mahl.Server.Types;
using Microsoft.EntityFrameworkCore;
using Npgsql;
using OneOf;
using static mahl.Server.Endpoints.ValidationProblems;
using static mahl.Server.OneOfExtensions;

// Die zerlegten Zeilen in Zeilenreihenfolge, je Zeile die zerlegte Zeile oder ihre Meldung.
using ParsedIngredientLines = System.Collections.Immutable.ImmutableArray<OneOf.OneOf<
    mahl.Server.Endpoints.ParsedIngredientLine, mahl.Server.Endpoints.FieldError>>;

// Die gefundenen aktiven Zutaten je Name aus den Zeilen – Schlüssel ist der Name genau so, wie die Zeile ihn
// nennt (Ordinal): die Zuordnung Name -> Zutat trifft die Datenbank, .NET faltet nichts (ADR-S135-2, Addendum S148).
using IngredientsByName = System.Collections.Generic.IReadOnlyDictionary<string, mahl.Server.Endpoints.StoredIngredient>;

// Eine gefundene Zutat zusammen mit dem Namen, unter dem die Zeile sie nennt (für die Meldungen).
using NamedIngredient = (string Name, mahl.Server.Endpoints.StoredIngredient Ingredient);

// Die validierte Nutzlast des Anlegens – Titel, aufgelöste Zutatenzeilen, Schritte; noch ohne Identität.
using RecipeValues = (
    mahl.Server.Domain.RecipeTitle Title,
    mahl.Server.Types.NonEmptyImmutableArray<mahl.Server.Endpoints.ResolvedIngredientLine> Lines,
    mahl.Server.Types.NonEmptyImmutableArray<mahl.Server.Domain.StepInstruction> Steps);

namespace mahl.Server.Endpoints;

// Zwischenstände der Zeilenauflösung an der Grenze – ohne eigene Invarianten (die halten die Domänentypen). Als
// file-Typen statt Tupel-Aliase, weil Aliase einander nicht referenzieren können und die Tupel sonst in jedem
// Alias, der sie enthält, erneut ausgeschrieben stünden.

// Eine zerlegte, noch nicht gegen den Zutatenbestand aufgelöste Zutatenzeile (ADR-S135-2): die normalisierte
// Zeile (für das Zitat der Meldung), die Menge und der Text nach der Menge – ohne Menge die ganze Zeile.
file readonly record struct ParsedIngredientLine(string Line, Quantity Quantity, string Remainder);

// Eine aktive Zutat, wie die Datenbank sie zu einem Namen aus einer Zeile findet: Id, gespeicherter Name,
// Basiseinheit.
file readonly record struct StoredIngredient(Guid Id, string Name, string BaseUnit);

// Eine fehlerfrei aufgelöste Zutatenzeile: die Zutat und die Menge.
file readonly record struct ResolvedIngredientLine(StoredIngredient Ingredient, Quantity Quantity);

internal static class RecipesEndpoints
{
    internal static void MapRecipesEndpoints(this WebApplication app)
    {
        var group = app.MapGroup($"{ApiRoutes.Prefix}/recipes");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact (ADR-S136-1)
        group.WithTags("Recipes");

        // ADR-S142-1: Sortierung in der DB mit expliziter ICU-Collation – die Default-Collation sortiert auf
        // postgres:18-alpine nach Bytes. Zugleich die deterministische Reihenfolge für den Collection-ETag (ADR-S084-1).
        group.MapGet(
            "",
            async (MahlDbContext db) =>
                Results.Ok(
                    await db.Recipes
                        .OrderBy(r => EF.Functions.Collate(r.Title, Collations.German))
                        .Select(r => new RecipeSummaryDto(r.Id, r.Title))
                        .ToListAsync()));

        // Handler-Logik ausgelagert wie IngredientsEndpoints.CreateIngredient – diese Methode bleibt
        // eine Routentabelle.
        group.MapPost("", RecipeMappings.CreateRecipe);

        // ADR-S142-2: {id:guid} – eine Kennung, die keine GUID ist, beantwortet die Route-Constraint mit 404.
        group.MapGet("/{id:guid}", RecipeMappings.GetRecipe);
    }
}

file static class RecipeMappings
{
    // ADR-S030-1: hier – und nur hier – entsteht die Identität des Rezepts (RecipeId.New() unten), weil hier
    // die Zeile entsteht.
    // Die Zeilen werden rein zerlegt, die Namen daraus in EINER Abfrage nachgeschlagen, dann rein aufgelöst und
    // mit Titel und Schritten gesammelt (ADR-S135-2). Die Abfrage läuft auch bei ungültigem Titel – nur so stehen
    // die Zeilenmeldungen neben der Titelmeldung (ADR-S135-3).
    internal static async Task<IResult> CreateRecipe(CreateRecipeDto dto, MahlDbContext db, HttpContext httpContext)
    {
        ParsedIngredientLines lines = [.. NormalizedNonEmptyLines(dto.Ingredients).Select(ParseLine)];
        var found = await FindActiveIngredientsAsync(NamesIn(lines), db);
        return await dto.ToValues(lines, found).Match(
            values => SaveRecipe(values, db, httpContext),
            errors => Task.FromResult(ValidationProblemFor(errors)));
    }

    // ADR-S135-3: alle Feldprüfungen laufen gesammelt (ADR-S119-2) – Titel und Zutatenfeld, dann die
    // Schritte. Die Reihenfolge der Keys im Body ist unerheblich (er ist feld-keyed, ADR-S090-1); die Meldungen
    // eines Keys stehen in Zeilenreihenfolge (ADR-S135-2).
    private static OneOf<RecipeValues, IReadOnlyList<FieldError>> ToValues(
        this CreateRecipeDto dto, ParsedIngredientLines lines, IngredientsByName found) =>
        CollectMany(
            CollectMany(ToTitle(dto.Title), ToIngredientLines(lines, found), (title, resolved) => (title, resolved)),
            ToSteps(dto.Steps),
            (head, steps) => (head.title, head.resolved, steps));

    private static OneOf<RecipeTitle, IReadOnlyList<FieldError>> ToTitle(string? input) =>
        RecipeTitle.Create(input)
            .MapError<RecipeTitle, RecipeTitleError, IReadOnlyList<FieldError>>(error => [DescribeTitle(error)]);

    // ADR-S135-2: leere Zeilen und Zeilen aus Leerraum werden übergangen; „mindestens eine Zutat" gilt nur,
    // wenn keine nicht leere Zeile da ist – fehlerhafte Zeilen erreichen die Prüfung nicht, Bind schließt nach
    // CollectAll kurz. Null (explizit gesendet, ADR-S144-2) ist wie leer.
    private static OneOf<NonEmptyImmutableArray<ResolvedIngredientLine>, IReadOnlyList<FieldError>> ToIngredientLines(
        ParsedIngredientLines lines, IngredientsByName found) =>
        CollectAll(ResolveLines(lines, found))
            .Bind<ImmutableArray<ResolvedIngredientLine>, NonEmptyImmutableArray<ResolvedIngredientLine>, IReadOnlyList<FieldError>>(
                resolved => NonEmptyImmutableArray<ResolvedIngredientLine>.Create(resolved)
                    .MapError<NonEmptyImmutableArray<ResolvedIngredientLine>, ListViolation, IReadOnlyList<FieldError>>(
                        _ => [IngredientsMissing]));

    // ADR-S135-2 Punkt 5 / Addendum S148: Zutat doppelt ist die letzte Prüfung einer Zeile und gilt nur gegenüber
    // einer früheren fehlerfreien Zeile – deshalb in Zeilenreihenfolge gefaltet, im Speicher über die Zeilen dieses
    // einen Rezepts. Der Zustand der Faltung: die Zutaten der früheren fehlerfreien Zeilen und die bisherigen Ergebnisse.
    private static ImmutableArray<OneOf<ResolvedIngredientLine, FieldError>> ResolveLines(
        ParsedIngredientLines lines, IngredientsByName found) =>
        lines.Aggregate(
            (Earlier: ImmutableHashSet<Guid>.Empty, Results: ImmutableArray<OneOf<ResolvedIngredientLine, FieldError>>.Empty),
            (state, line) => Advance(state, line, found)).Results;

    // Ein Schritt der Faltung: die Zeile auflösen, ihr Ergebnis anhängen, eine fehlerfreie Zeile merkt ihre Zutat.
    private static (ImmutableHashSet<Guid> Earlier, ImmutableArray<OneOf<ResolvedIngredientLine, FieldError>> Results) Advance(
        (ImmutableHashSet<Guid> Earlier, ImmutableArray<OneOf<ResolvedIngredientLine, FieldError>> Results) state,
        OneOf<ParsedIngredientLine, FieldError> line,
        IngredientsByName found)
    {
        var result = line.Bind(parsed => ResolveIngredient(parsed, found)
            .Bind<NamedIngredient, ResolvedIngredientLine, FieldError>(named => ResolveDuplicate(state.Earlier, parsed, named)));
        return (result.Match(resolved => state.Earlier.Add(resolved.Ingredient.Id), _ => state.Earlier), state.Results.Add(result));
    }

    private static OneOf<ResolvedIngredientLine, FieldError> ResolveDuplicate(
        ImmutableHashSet<Guid> earlierIngredients, ParsedIngredientLine parsed, NamedIngredient named) =>
        earlierIngredients.Contains(named.Ingredient.Id)
            ? LineError(parsed.Line, $"Zutat '{named.Name}' steht bereits in einer früheren Zeile.")
            : new ResolvedIngredientLine(named.Ingredient, parsed.Quantity);

    // ADR-S135-2 Punkt 2/3: mit Menge kann der Rest Einheit und Zutat sein, ohne Menge ist er die Zutat.
    private static OneOf<NamedIngredient, FieldError> ResolveIngredient(ParsedIngredientLine line, IngredientsByName found) =>
        line.Quantity.Match(
            _ => ResolveWithQuantity(line, found),
            () => ResolveName(line.Line, line.Remainder, found));

    // ADR-S135-2 Punkt 2, Prüfreihenfolge Addendum S148: Ist der ganze Rest eine aktive Zutat, fehlt die Einheit.
    // Sonst ist bei mehreren Wörtern das erste die Einheit, ein einzelnes Wort ist die (nicht gefundene) Zutat.
    private static OneOf<NamedIngredient, FieldError> ResolveWithQuantity(ParsedIngredientLine line, IngredientsByName found) =>
        found.TryGetValue(line.Remainder, out var withoutUnit)
            ? LineError(line.Line, $"Einheit fehlt (für '{line.Remainder}': '{withoutUnit.BaseUnit}').")
            : ResolveUnitAndName(line, found);

    private static OneOf<NamedIngredient, FieldError> ResolveUnitAndName(ParsedIngredientLine line, IngredientsByName found) =>
        SplitUnit(line.Remainder) is [var unit, var name]
            ? ResolveName(line.Line, name, found).Bind(named => CheckUnit(line.Line, unit, named))
            : NotFound(line.Line, line.Remainder);

    private static OneOf<NamedIngredient, FieldError> ResolveName(string line, string name, IngredientsByName found) =>
        found.TryGetValue(name, out var ingredient)
            ? (name, ingredient)
            : NotFound(line, name);

    // ADR-S135-2, Addendum S148: Einheiten ohne Unterschied der Groß-/Kleinschreibung, im Speicher – an ihnen hängt
    // keine Eindeutigkeit.
    private static OneOf<NamedIngredient, FieldError> CheckUnit(string line, string unit, NamedIngredient named) =>
        string.Equals(unit, named.Ingredient.BaseUnit, StringComparison.OrdinalIgnoreCase)
            ? named
            : LineError(line, $"Einheit '{unit}' passt nicht zu '{named.Name}' (möglich: '{named.Ingredient.BaseUnit}').");

    private static FieldError NotFound(string line, string name) =>
        LineError(line, $"Zutat '{name}' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt.");

    // ADR-S051-2, Addendum S135: jede Zeilenmeldung zitiert die normalisierte Zeile in „…“ (U+201E, U+201C).
    private static FieldError LineError(string line, string message) => new(IngredientsField, $"„{line}“: {message}");

    // Erstes Wort (die Einheit) und Rest (die Zutat) – ein Wort allein bleibt ungeteilt.
    private static string[] SplitUnit(string rest) => rest.Split(WordSeparator, 2);

    // Die Namen, unter denen eine Zeile eine Zutat nennen kann: der ganze Rest und – bei mehreren Wörtern – der
    // Rest ohne die Einheit; eine schon fehlerhafte Zeile nennt keine. Ordinal ohne Dubletten: jeder Name ist ein
    // Schlüssel des Ergebnisses.
    private static string[] NamesIn(ParsedIngredientLines lines) =>
    [
        .. lines.SelectMany(line => line.Match(NamesInLine, _ => Enumerable.Empty<string>())).Distinct(StringComparer.Ordinal),
    ];

    private static IEnumerable<string> NamesInLine(ParsedIngredientLine line) =>
        SplitUnit(line.Remainder) is [_, var name] ? [line.Remainder, name] : [line.Remainder];

    // ADR-S135-2, Addendum S148: Namen vergleicht die DB mit LOWER auf BEIDEN Seiten – dieselbe Funktion wie der
    // Unique-Index auf LOWER("Name") (ADR-S105-2). Der Name aus der Zeile ist dabei ein Element der Parameter-
    // Collection, kein freistehender Parameter. Am generierten SQL geprüft (kein Test trennt es): EF übersetzt
    // c.ToLower() nach SQL lower() und wertet es nicht in .NET aus –
    // `… FROM unnest(@names) AS n(value) WHERE lower(n.value) = lower(i."Name")`. Die DB liefert die Paare
    // (Name, Zutat); der Unique-Index lässt je Name höchstens eine Zutat zu. Soft-gelöschte Zutaten gelten als
    // nicht gefunden (ADR-S135-2 Punkt 4).
    private static async Task<IngredientsByName> FindActiveIngredientsAsync(string[] names, MahlDbContext db)
    {
#pragma warning disable CA1304, CA1311, CA1862, MA0011 // ToLower() ist SQL-übersetzt (lower()), kein CLR-Aufruf – s. Kommentar oben
        var rows = await db.Ingredients
            .Where(i => i.DeletedAt == null)
            .SelectMany(
                i => names.Where(name => name.ToLower() == i.Name.ToLower()),
                (i, name) => new { Name = name, i.Id, StoredName = i.Name, i.BaseUnit })
            .ToListAsync(Cancellation.None);
#pragma warning restore CA1304, CA1311, CA1862, MA0011
        return rows.ToDictionary(row => row.Name, row => new StoredIngredient(row.Id, row.StoredName, row.BaseUnit), StringComparer.Ordinal);
    }

    private const char LineSeparator = '\n';

    // Trennt die Wörter einer normalisierten Zeile – nach ADR-S135-1 steht dort nur noch je ein ASCII-Leerzeichen.
    private const char WordSeparator = ' ';

    // ADR-S135-2 / ADR-S135-1: jede Zeile wird normalisiert; Null und normalisiert leere Zeilen ergeben keine Zeile.
    private static IEnumerable<string> NormalizedNonEmptyLines(string? text) =>
        (text ?? string.Empty).Split(LineSeparator)
            .SelectMany(line => NonEmptyNormalizedString.Create(line)
                .Match<IEnumerable<string>>(normalized => [normalized.Value], _ => []));

    // ADR-S144-1: die Meldung zu einer Anweisung keyt auf den Index in der gesendeten Liste, die zur
    // Liste als Ganzes auf `steps`.
    private static OneOf<NonEmptyImmutableArray<StepInstruction>, IReadOnlyList<FieldError>> ToSteps(IReadOnlyList<StepDto>? steps) =>
        CollectAll((steps ?? []).Select((step, index) => StepInstruction.Create(step.Instruction)
                .MapError<StepInstruction, StepInstructionError, FieldError>(error => DescribeStep(error, index))))
            .Bind<ImmutableArray<StepInstruction>, NonEmptyImmutableArray<StepInstruction>, IReadOnlyList<FieldError>>(
                instructions => NonEmptyImmutableArray<StepInstruction>.Create(instructions)
                    .MapError<NonEmptyImmutableArray<StepInstruction>, ListViolation, IReadOnlyList<FieldError>>(
                        _ => [StepsMissing]));

    // ADR-S051-2 / ADR-S090-1: ein Fehlerfall -> ein (Request-JSON-Property, fester deutscher Text), benannt an
    // der Grenze. ListViolation kennt nur „leer" und bildet damit auf genau diese eine Meldung je Liste ab.
    // Als Property statt static readonly Feld: Stryker schaltet Mutanten zur Laufzeit um, ein Feld-Initialisierer
    // liefe nur einmal je Prozess und sähe den aktiven Mutanten nicht.
    private static FieldError IngredientsMissing => new(IngredientsField, "Rezept muss mindestens eine Zutat haben.");

    // Request-JSON-Property des Zutatenfelds: Key der Listen- und der Zeilenmeldungen (ADR-S090-1, ADR-S135-2).
    private const string IngredientsField = "ingredients";

    // Request-JSON-Property des Titels: Key der Feld- und der Eindeutigkeitsmeldung (ADR-S135-3).
    private const string TitleField = "title";

    private static FieldError StepsMissing => new("steps", "Rezept muss mindestens einen Schritt haben.");

    // Der Domänentyp bleibt feldagnostisch (ADR-S120-1). Coverage-Ausschluss je ganze Methode wie bei
    // IngredientMappings.DescribeName: der Enum-Default-Arm ist unerreichbar.
    [ExcludeFromCoverageGate("structurally unreachable sum-type/enum default arm (ADR-S040-1)")]
    private static FieldError DescribeTitle(RecipeTitleError error) => error switch
    {
        RecipeTitleError.Empty => new FieldError(TitleField, "Titel darf nicht leer sein."),
        RecipeTitleError.TooLong => new FieldError(TitleField, "Titel darf maximal 100 Zeichen lang sein."),
        _ => SumType.Unreachable<FieldError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
    };

    [ExcludeFromCoverageGate("structurally unreachable sum-type/enum default arm (ADR-S040-1)")]
    private static FieldError DescribeStep(StepInstructionError error, int index) => error switch
    {
        StepInstructionError.Empty => new FieldError($"steps[{index}].instruction", "Schritt-Anweisung darf nicht leer sein."),
        StepInstructionError.TooLong => new FieldError($"steps[{index}].instruction", "Schritt-Anweisung darf maximal 1000 Zeichen lang sein."),
        _ => SumType.Unreachable<FieldError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
    };

    private static async Task<IResult> SaveRecipe(RecipeValues values, MahlDbContext db, HttpContext httpContext)
    {
        var recipe = Recipe.Create(
            RecipeId.New(),
            values.Title,
            values.Lines.Map(line => RecipeIngredient.Create(IngredientId.Create(line.Ingredient.Id), line.Quantity)),
            values.Steps);

        return (await InsertAsync(recipe, db)).Match<IResult>(
            recipeRow =>
            {
                // ADR-S106-1/ADR-S000-12: der xmin der neu angelegten Rezeptzeile geht als ETag mit dem 201 heraus.
                httpContext.Response.Headers.ETag = XminETag.Format(db.ReadXmin(recipeRow));
                // Der Body nennt je Zeile den gespeicherten Namen und die Basiseinheit der aufgelösten Zutat (ADR-S135-2).
                return Results.Created($"{ApiRoutes.Prefix}/recipes/{recipe.Id.Value}", recipe.ToDto(values.Lines.Items));
            },
            titleTaken => ValidationProblemFor([titleTaken]));
    }

    // ADR-S105-2 / ADR-S135-3: die Titel-Eindeutigkeit prüft allein der Unique-Index (LOWER(title)) beim
    // Insert – also erst, wenn alle übrigen Prüfungen bestanden sind. Zitiert wird der normalisierte Titel.
    private static async Task<OneOf<RecipeDbType, FieldError>> InsertAsync(Recipe recipe, MahlDbContext db)
    {
        var recipeRow = recipe.ToDbType();
        db.Recipes.Add(recipeRow);
        db.RecipeIngredients.AddRange(recipe.ToRecipeIngredientDbTypes());
        db.Steps.AddRange(recipe.ToStepDbTypes());
        try
        {
            await db.SaveChangesAsync(Cancellation.None);
            return recipeRow;
        }
        catch (DbUpdateException ex) when (ex.InnerException is PostgresException { SqlState: PostgresErrorCodes.UniqueViolation, ConstraintName: UniqueIndexNames.RecipeTitle })
        {
            return new FieldError(TitleField, $"Ein Rezept mit dem Titel '{recipe.Title.Value}' existiert bereits.");
        }
    }

    // ADR-S142-2: dasselbe Rezept-DTO wie der 201 beim Anlegen, dazu der xmin der Rezeptzeile als ETag.
    // Die Middleware (ADR-S084-1) lässt den gesetzten ETag stehen und beantwortet If-None-Match damit.
    // Ohne Validierung der Zeilen (korrupte Daten: TD-S141-3). Der ETag deckt Zeilen, Schritte und
    // Zutatendaten nicht ab, und die Abfragen laufen ohne gemeinsamen Snapshot (TD-S142-2).
    internal static async Task<IResult> GetRecipe(Guid id, MahlDbContext db, HttpContext httpContext)
    {
        var recipe = await db.Recipes.SingleOrDefaultAsync(r => r.Id == id, Cancellation.None);
        if (recipe is null)
            return NotFoundProblem();

        var ingredients = await LoadIngredientsAsync(id, db);
        var steps = await LoadStepsAsync(id, db);

        httpContext.Response.Headers.ETag = XminETag.Format(db.ReadXmin(recipe));
        return Results.Ok(new RecipeDto(recipe.Id, recipe.Title, ingredients, steps));
    }

    // ADR-S135-2: Zeilenreihenfolge = Position.
    private static async Task<IReadOnlyList<RecipeIngredientDto>> LoadIngredientsAsync(Guid recipeId, MahlDbContext db)
    {
        var rows = await db.RecipeIngredients
            .Where(ri => ri.RecipeId == recipeId)
            .OrderBy(ri => ri.Position)
            .Join(db.Ingredients, ri => ri.IngredientId, i => i.Id, (ri, i) => new { i.Name, ri.Quantity, i.BaseUnit })
            .ToListAsync(Cancellation.None);
        return [.. rows.Select(row => ToIngredientDto(row.Name, row.Quantity, row.BaseUnit))];
    }

    // ADR-S027-1: Schritt-Reihenfolge = StepNumber.
    private static async Task<IReadOnlyList<StepDto>> LoadStepsAsync(Guid recipeId, MahlDbContext db) =>
        await db.Steps
            .Where(s => s.RecipeId == recipeId)
            .OrderBy(s => s.StepNumber)
            .Select(s => new StepDto(s.Instruction))
            .ToListAsync(Cancellation.None);

    // Einzige Abbildung der Zutatenzeile auf das DTO (Lesen und Anlegen): mit Menge ist die Einheit die
    // Basiseinheit der Zutat; ohne Menge sind Menge und Einheit null (ADR-S135-2, ADR-S020-1).
    private static RecipeIngredientDto ToIngredientDto(string name, decimal? quantity, string baseUnit) =>
        new(name, quantity, quantity is null ? null : baseUnit);

    // ADR-S054-6-Muster wie IngredientMappings.NotFoundProblem: fixe deutsche Meldung + errorCode.
    private static IResult NotFoundProblem() =>
        Results.Problem(
            detail: "Rezept wurde nicht gefunden.",
            statusCode: StatusCodes.Status404NotFound,
            extensions: new Dictionary<string, object?>(StringComparer.Ordinal) { ["errorCode"] = "RECIPE_NOT_FOUND" });

    // ADR-S135-2: beginnt die Zeile mit einer Ziffer, ist das erste Wort die Menge; sonst ist die ganze Zeile
    // die Zutat, ohne Menge (ADR-S020-1). Eine ungültige Menge wird zur Meldung, die die Zeile zitiert.
    private static OneOf<ParsedIngredientLine, FieldError> ParseLine(string line) =>
        char.IsAsciiDigit(line[0])
            ? ParseLineWithQuantity(line, line.Split(WordSeparator, 2))
            : new ParsedIngredientLine(line, Quantity.Unspecified, line);

    // ADR-S135-2, Addendum S148: steht nach der Menge kein Wort mehr, fehlt die Zutat – geprüft erst nach der Menge.
    private static OneOf<ParsedIngredientLine, FieldError> ParseLineWithQuantity(string line, string[] words) =>
        QuantityAmount.Create(words[0])
            .MapError<QuantityAmount, QuantityError, FieldError>(error => LineError(line, DescribeQuantity(error)))
            .Bind<QuantityAmount, ParsedIngredientLine, FieldError>(amount => words is [_, var rest]
                ? new ParsedIngredientLine(line, Quantity.Specified(amount), rest)
                : LineError(line, "Zutat fehlt."));

    [ExcludeFromCoverageGate("structurally unreachable sum-type/enum default arm (ADR-S040-1)")]
    private static string DescribeQuantity(QuantityError error) => error switch
    {
        QuantityError.NotANumber => "Menge muss eine Zahl sein (z. B. 1,5).",
        QuantityError.NotPositive => "Menge muss größer als 0 sein.",
        QuantityError.TooManyDecimals => "Menge darf maximal 3 Nachkommastellen haben.",
        QuantityError.TooLarge => "Menge darf maximal 9999,999 sein.",
        _ => SumType.Unreachable<string>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
    };

    private static RecipeDbType ToDbType(this Recipe recipe) =>
        new() { Id = recipe.Id.Value, Title = recipe.Title.Value };

    // ADR-S135-2: Position = Zeilenreihenfolge, 1-basiert. ADR-S020-1: ohne Menge NULL.
    private static IEnumerable<RecipeIngredientDbType> ToRecipeIngredientDbTypes(this Recipe recipe) =>
        recipe.Ingredients.Items.Select((ingredient, index) => new RecipeIngredientDbType
        {
            RecipeId = recipe.Id.Value,
            Position = index + 1,
            IngredientId = ingredient.Ingredient.Value,
            Quantity = ingredient.Quantity.Match<decimal?>(amount => amount, () => null),
        });

    // ADR-S027-1: StepNumber = Index + 1 der Listenposition, nur in der DB-Entität.
    private static IEnumerable<StepDbType> ToStepDbTypes(this Recipe recipe) =>
        recipe.Steps.Items.Select((step, index) => new StepDbType
        {
            RecipeId = recipe.Id.Value, StepNumber = index + 1, Instruction = step.Value,
        });

    // Reihenfolge und Menge kommen aus dem Rezept, Name und Basiseinheit je IngredientId aus den aufgelösten Zeilen
    // (Recipe.Ingredients entsteht aus genau diesen Zeilen, SaveRecipe).
    private static RecipeDto ToDto(this Recipe recipe, ImmutableArray<ResolvedIngredientLine> lines)
    {
        var ingredientsById = lines.ToDictionary(line => line.Ingredient.Id, line => line.Ingredient);
        return new(
            recipe.Id.Value,
            recipe.Title.Value,
            [.. recipe.Ingredients.Items.Select(ingredient =>
            {
                var stored = ingredientsById[ingredient.Ingredient.Value];
                return ToIngredientDto(stored.Name, ingredient.Quantity.Match<decimal?>(amount => amount, () => null), stored.BaseUnit);
            })],
            [.. recipe.Steps.Items.Select(step => new StepDto(step.Value))]);
    }
}

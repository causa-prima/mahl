using System.Collections.Immutable;
using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Middleware;
using mahl.Server.Types;
using Microsoft.EntityFrameworkCore;
using OneOf;
using static mahl.Server.Endpoints.ValidationProblems;
using static mahl.Server.OneOfExtensions;

// Eine zerlegte Zutatenzeile (ADR-S135-2): der Name, unter dem die Zutat nachgeschlagen wird, und die
// Menge. Tupel-Alias statt eigenem Typ aus demselben Grund wie IngredientValues in IngredientsEndpoints:
// keine Invariante, nur Zwischenstand an der Grenze.
using ParsedIngredientLine = (string Name, mahl.Server.Domain.Quantity Quantity);

// Die validierte Nutzlast des Anlegens – Titel, zerlegte Zutatenzeilen, Schritte; noch ohne Identität
// und ohne Zutat-Ids (die kennt erst die DB). Tupel-Alias aus demselben Grund wie ParsedIngredientLine.
// (Aliase können einander nicht referenzieren, daher ausgeschrieben.)
using RecipeValues = (
    mahl.Server.Domain.RecipeTitle Title,
    mahl.Server.Types.NonEmptyImmutableArray<(string Name, mahl.Server.Domain.Quantity Quantity)> Lines,
    mahl.Server.Types.NonEmptyImmutableArray<mahl.Server.Domain.StepInstruction> Steps);

namespace mahl.Server.Endpoints;

internal static class RecipesEndpoints
{
    internal static void MapRecipesEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/recipes");
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
    // Validiert sind bisher die Pflichtangaben (Titel, Zutatenfeld, Schritte), Längen und die Menge jeder Zeile;
    // die übrigen Fehler-Szenarien der Zeilen (Zutat nicht gefunden, Einheit falsch, leerer Name, doppelte
    // Zutat) kommen später. Bis dahin ist eine solche Zeile unbestimmt.
    internal static async Task<IResult> CreateRecipe(CreateRecipeDto dto, MahlDbContext db, HttpContext httpContext) =>
        await dto.ToValues().Match(
            values => SaveRecipe(values, db, httpContext),
            errors => Task.FromResult(ValidationProblemFor(errors)));

    // ADR-S135-3: alle Feldprüfungen laufen gesammelt (ADR-S119-2) – Titel und Zutatenfeld, dann die
    // Schritte; die Fehlerreihenfolge im Body ist unerheblich (er ist feld-keyed, ADR-S090-1).
    private static OneOf<RecipeValues, IReadOnlyList<FieldError>> ToValues(this CreateRecipeDto dto) =>
        CollectMany(
            CollectMany(ToTitle(dto.Title), ToIngredientLines(dto.Ingredients), (title, lines) => (title, lines)),
            ToSteps(dto.Steps),
            (head, steps) => (head.title, head.lines, steps));

    private static OneOf<RecipeTitle, IReadOnlyList<FieldError>> ToTitle(string? input) =>
        RecipeTitle.Create(input)
            .MapError<RecipeTitle, RecipeTitleError, IReadOnlyList<FieldError>>(error => [DescribeTitle(error)]);

    // ADR-S135-2: leere Zeilen und Zeilen aus Leerraum werden übergangen; „mindestens eine Zutat" gilt nur,
    // wenn keine nicht leere Zeile da ist – fehlerhafte Zeilen erreichen die Prüfung nicht, Bind schließt nach
    // CollectAll kurz. Null (explizit gesendet, ADR-S144-2) ist wie leer.
    private static OneOf<NonEmptyImmutableArray<ParsedIngredientLine>, IReadOnlyList<FieldError>> ToIngredientLines(string? text) =>
        CollectAll(NormalizedNonEmptyLines(text).Select(ParseLine))
            .Bind<ImmutableArray<ParsedIngredientLine>, NonEmptyImmutableArray<ParsedIngredientLine>, IReadOnlyList<FieldError>>(
                lines => NonEmptyImmutableArray<ParsedIngredientLine>.Create(lines)
                    .MapError<NonEmptyImmutableArray<ParsedIngredientLine>, ListViolation, IReadOnlyList<FieldError>>(
                        _ => [IngredientsMissing]));

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
    private static FieldError StepsMissing => new("steps", "Rezept muss mindestens einen Schritt haben.");

    // Der Domänentyp bleibt feldagnostisch (ADR-S120-1). Coverage-Ausschluss je ganze Methode wie bei
    // IngredientMappings.DescribeName: der Enum-Default-Arm ist unerreichbar.
    [ExcludeFromCoverageGate("structurally unreachable sum-type/enum default arm (ADR-S040-1)")]
    private static FieldError DescribeTitle(RecipeTitleError error) => error switch
    {
        RecipeTitleError.Empty => new FieldError("title", "Titel darf nicht leer sein."),
        RecipeTitleError.TooLong => new FieldError("title", "Titel darf maximal 100 Zeichen lang sein."),
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
        // Bewusst ohne RequestAborted: Das Backend reicht Abbruch nirgends durch (Sonar S8949 verlangt die explizite Wahl).
        var ingredients = await db.Ingredients.ToListAsync(CancellationToken.None);
        var ingredientsById = ingredients.ToDictionary(i => i.Id);
        var recipe = Recipe.Create(
            RecipeId.New(),
            values.Title,
            values.Lines.Map(line => ToRecipeIngredient(line, name => IngredientIdByName(ingredients, name))),
            values.Steps);

        var recipeRow = recipe.ToDbType();
        db.Recipes.Add(recipeRow);
        db.RecipeIngredients.AddRange(recipe.ToRecipeIngredientDbTypes());
        db.Steps.AddRange(recipe.ToStepDbTypes());
        await db.SaveChangesAsync(CancellationToken.None);

        // ADR-S106-1/ADR-S000-12: der xmin der neu angelegten Rezeptzeile geht als ETag mit dem 201 heraus.
        var xmin = db.ReadXmin(recipeRow);
        httpContext.Response.Headers.ETag = XminETag.Format(xmin);
        return Results.Created($"/api/recipes/{recipe.Id.Value}", recipe.ToDto(id => ingredientsById[id.Value]));
    }

    // ADR-S142-2: dasselbe Rezept-DTO wie der 201 beim Anlegen, dazu der xmin der Rezeptzeile als ETag.
    // Die Middleware (ADR-S084-1) lässt den gesetzten ETag stehen und beantwortet If-None-Match damit.
    // Ohne Validierung der Zeilen (korrupte Daten: TD-S141-3). Der ETag deckt Zeilen, Schritte und
    // Zutatendaten nicht ab, und die Abfragen laufen ohne gemeinsamen Snapshot (TD-S142-2).
    internal static async Task<IResult> GetRecipe(Guid id, MahlDbContext db, HttpContext httpContext)
    {
        // Bewusst ohne RequestAborted: Das Backend reicht Abbruch nirgends durch (Sonar S8949 verlangt die explizite Wahl).
        var recipe = await db.Recipes.SingleOrDefaultAsync(r => r.Id == id, CancellationToken.None);
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
            .ToListAsync(CancellationToken.None);
        return [.. rows.Select(row => ToIngredientDto(row.Name, row.Quantity, row.BaseUnit))];
    }

    // ADR-S027-1: Schritt-Reihenfolge = StepNumber.
    private static async Task<IReadOnlyList<StepDto>> LoadStepsAsync(Guid recipeId, MahlDbContext db) =>
        await db.Steps
            .Where(s => s.RecipeId == recipeId)
            .OrderBy(s => s.StepNumber)
            .Select(s => new StepDto(s.Instruction))
            .ToListAsync(CancellationToken.None);

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

    // ADR-S135-2: Namen werden ohne Unterschied der Groß-/Kleinschreibung verglichen. Bewusst kein Dictionary
    // nach Name: Die DB-Eindeutigkeit gilt unter LOWER(name), und OrdinalIgnoreCase faltet anders – „µg" (Mikro-
    // Zeichen) und „μg" (griechisches My) oder „ς" und „σ" sind darunter gleich, unter LOWER verschieden. Ein
    // Dictionary risse dann jedes Anlegen mit. Nicht abgesichert: Gibt es beide, nimmt First still eine davon
    // (TD-S148-1). Ein unbekannter Name endet in 500 (TD-S144-1).
    // Stryker disable once Linq : First vs. FirstOrDefault both end in 500 until unknown names get a message (Einzelfall, vom User freigegeben S148)
    private static Guid IngredientIdByName(IReadOnlyList<IngredientDbType> ingredients, string name) =>
        ingredients.First(i => string.Equals(i.Name, name, StringComparison.OrdinalIgnoreCase)).Id;

    // Der Lookup Name -> Zutat-Id kommt als Funktion herein: die Zerlegung kennt keine DB.
    private static RecipeIngredient ToRecipeIngredient(ParsedIngredientLine line, Func<string, Guid> ingredientIdByName) =>
        RecipeIngredient.Create(IngredientId.Create(ingredientIdByName(line.Name)), line.Quantity);

    // ADR-S135-2: beginnt die Zeile mit einer Ziffer, ist sie „Menge Einheit Zutat"; sonst ist die ganze Zeile
    // die Zutat, ohne Menge (ADR-S020-1). Eine ungültige Menge wird zur Meldung, die die Zeile zitiert. Die
    // Einheit wird noch nicht gelesen – sie ist die Basiseinheit der Zutat; ihre Prüfung kommt mit dem Szenario
    // „Einheit falsch".
    private static OneOf<ParsedIngredientLine, FieldError> ParseLine(string line) =>
        char.IsAsciiDigit(line[0])
            ? ParseLineWithQuantity(line, line.Split(WordSeparator))
            : (line, Quantity.Unspecified);

    private static OneOf<ParsedIngredientLine, FieldError> ParseLineWithQuantity(string line, string[] words) =>
        QuantityAmount.Create(words[0])
            .MapError<QuantityAmount, QuantityError, FieldError>(error => DescribeQuantity(error, line))
            // Wort 2 ist die Einheit, noch ungelesen (s. ParseLine); der Rest ist der – möglicherweise mehrwortige – Name.
            .Map<QuantityAmount, ParsedIngredientLine, FieldError>(
                amount => (string.Join(WordSeparator, words.Skip(2)), Quantity.Specified(amount)));

    // ADR-S051-2, Addendum S135: die Meldung zitiert die normalisierte Zeile in „…“ (U+201E, U+201C).
    [ExcludeFromCoverageGate("structurally unreachable sum-type/enum default arm (ADR-S040-1)")]
    private static FieldError DescribeQuantity(QuantityError error, string line) => new(IngredientsField, $"„{line}“: " + error switch
    {
        QuantityError.NotANumber => "Menge muss eine Zahl sein (z. B. 1,5).",
        QuantityError.NotPositive => "Menge muss größer als 0 sein.",
        QuantityError.TooManyDecimals => "Menge darf maximal 3 Nachkommastellen haben.",
        QuantityError.TooLarge => "Menge darf maximal 9999,999 sein.",
        _ => SumType.Unreachable<string>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
    });

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

    private static RecipeDto ToDto(this Recipe recipe, Func<IngredientId, IngredientDbType> ingredientRow) =>
        new(
            recipe.Id.Value,
            recipe.Title.Value,
            [.. recipe.Ingredients.Items.Select(ingredient => ingredient.ToDto(ingredientRow(ingredient.Ingredient)))],
            [.. recipe.Steps.Items.Select(step => new StepDto(step.Value))]);

    private static RecipeIngredientDto ToDto(this RecipeIngredient ingredient, IngredientDbType row) =>
        ToIngredientDto(row.Name, ingredient.Quantity.Match<decimal?>(amount => amount, () => null), row.BaseUnit);
}

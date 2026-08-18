using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Middleware;
using mahl.Server.Types;
using Microsoft.EntityFrameworkCore;
using Npgsql;
using OneOf;
using static mahl.Server.OneOfExtensions;

// Die validierte Nutzlast eines Ingredient-Schreibzugriffs – Name und Einheit, keine Identität.
// Ein Tupel-Alias statt eines eigenen Typs: der Typ hätte keine Invariante zu wahren (die halten
// IngredientName und Unit), bräuchte aber nach §3 einen Ktor-Guard samt Suppression. Der Alias
// hält die ROP-Typargumente unten lesbar, ohne diesen Preis.
using IngredientValues = (mahl.Server.Domain.IngredientName Name, mahl.Server.Domain.Unit BaseUnit);

namespace mahl.Server.Endpoints;

internal static class IngredientsEndpoints
{
    internal static void MapIngredientsEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/ingredients");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact
        group.WithTags("Ingredients");

        group.MapGet(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            // ADR-S000-6: soft-deleted Zeilen werden ausgeblendet.
            // ADR-S084-1: deterministische Sortierung (OrderBy(Name)) ist Voraussetzung für einen
            // stabilen Collection-Content-Hash-ETag (die Middleware hasht den serialisierten Body).
            async (MahlDbContext db) =>
                Results.Ok(await db.Ingredients
                    .Where(i => i.DeletedAt == null)
                    .OrderBy(i => i.Name)
                    // ADR-S108-1: per-Zeile xmin-ETag im Body – If-Match-Quelle für ein DELETE aus der Liste.
                    .Select(i => new IngredientDto(i.Id, i.Name, i.BaseUnit, XminETag.Format(EF.Property<uint>(i, "xmin"))))
                    .ToListAsync()));

        group.MapPost(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            // Handler-Logik ausgelagert (IngredientMappings.CreateIngredient) statt inline lambda – hält
            // die Cognitive Complexity von MapIngredientsEndpoints niedrig und diese Methode eine
            // Routentabelle (docs/guidelines/coding-guideline-general.md); analog RestoreIngredient.
            IngredientMappings.CreateIngredient);

        group.MapDelete(
            "/{id:guid}",
            async (Guid id, HttpRequest request, MahlDbContext db) =>
            {
                // ADR-S000-5/ADR-S051-5: Not-Found dominiert VOR dem If-Match-Check – eine bereits
                // soft-deleted oder nie existente Zeile liefert immer 404, auch mit fehlendem/stale If-Match.
                var ingredient = await db.Ingredients.FirstOrDefaultAsync(i => i.Id == id && i.DeletedAt == null);
                if (ingredient is null)
                    return IngredientMappings.NotFoundProblem();

                // ADR-S058-1: mutierender Single-Resource-Endpoint verlangt If-Match.
                var ifMatch = request.Headers.IfMatch;
                if (ifMatch.Count == 0)
                    return Results.StatusCode(StatusCodes.Status428PreconditionRequired);

                // ADR-S106-2: 428/400/412-Dreiteilung – ein If-Match, der zwar vorhanden, aber nicht zu
                // einem xmin parsebar ist (non-hex/Overflow/leer/Wildcard/Liste), liefert 400 statt einer
                // unbehandelten FormatException/OverflowException (die vorher als 500 durchschlug).
                if (!XminETag.TryParse(ifMatch.ToString(), out var xmin))
                    return IngredientMappings.InvalidIfMatchProblem();

                // ADR-S058-3: xmin als Concurrency-Token setzen – EF Core prüft ihn beim SaveChangesAsync
                // gegen den aktuellen DB-Wert und wirft DbUpdateConcurrencyException bei Mismatch.
                db.Entry(ingredient).Property("xmin").OriginalValue = xmin;
                ingredient.DeletedAt = DateTimeOffset.UtcNow;
                try
                {
                    await db.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    return Results.StatusCode(StatusCodes.Status412PreconditionFailed);
                }
                return Results.NoContent();
            });

        group.MapPost(
            "/{id:guid}/restore",
            // ADR-S111-1: Pflicht-Body, ohne If-Match (Single-User-App-Ausnahme, ADR-S058-1 unverändert).
            // Handler-Logik ausgelagert (IngredientMappings.RestoreIngredient) statt inline lambda – hält
            // die Cognitive Complexity von MapIngredientsEndpoints niedrig (docs/guidelines/coding-guideline-general.md).
            IngredientMappings.RestoreIngredient);
    }
}

// ADR-S120-1: der akkumulierte Fehlertyp IST das Antwortformat (ADR-S090-1: Feld-Key + Meldung),
// keine Zwischenstufe. Reiner Transport-Record an der API-Grenze – kein Domänentyp, deshalb ohne
// Factory und ohne Guards: er hat keine Invariante, die er durchsetzen müsste.
// `file`-scoped wie der Mapping-Layer: der zweite Endpoint mit Feldvalidierung zieht ihn hoch, bis
// dahin gäbe es für einen geteilten Typ keinen Aufrufer.
file readonly record struct FieldError(string Key, string Message);

file static class IngredientMappings
{
    // Collect-all validation of the independent required fields (ADR-S090-1): name and unit are
    // validated independently and ALL errors collected, so both-fields-empty reports both field
    // errors at once. Collect ist der Applicative-Kombinator dafür (ADR-S119-2) – Bind schlösse
    // beim ersten Fehler kurz. Die Feldregeln (Länge, Leere) stehen in IngredientName/Unit, nicht
    // mehr hier (ADR-S119-1/ADR-S120-1).
    // Ergebnis ist die validierte Nutzlast OHNE Identität: die vergibt allein der anlegende Pfad
    // (ADR-S030-1), und der Restore-Pfad identifiziert die Zeile über den Routenparameter. So kann
    // kein Ingredient ohne brauchbare Id entstehen.
    internal static OneOf<IngredientValues, IReadOnlyList<FieldError>> ToValues(this IngredientValuesDto dto) =>
        Collect(
            IngredientName.Create(dto.Name).MapError<IngredientName, IngredientNameError, FieldError>(DescribeName),
            Unit.Create(dto.BaseUnit).MapError<Unit, UnitError, FieldError>(DescribeBaseUnit),
            (name, unit) => (Name: name, BaseUnit: unit));

    // ADR-S105-2: Eindeutigkeit ist ein DB-Constraint (funktionaler LOWER(name)-Unique-Index,
    // ADR-S051-3/ADR-S004-1 Addendum S105) – kein App-Layer-Check-then-Insert (TOCTOU-Race). Der
    // schreibende Endpoint fängt die Unique-Violation (Postgres 23505).
    // ADR-S030-1: hier – und nur hier – entsteht die Identität, weil hier die Zeile entsteht.
    internal static async Task<IResult> CreateIngredient(IngredientValuesDto dto, MahlDbContext db, HttpContext httpContext) =>
        await dto.ToValues()
            .MapError<IngredientValues, IReadOnlyList<FieldError>, IResult>(ValidationProblemFor)
            .Map(values => Ingredient.Create(IngredientId.New(), values.Name, values.BaseUnit))
            .BindAsync<Ingredient, IngredientDto, IResult>(async ingredient =>
            {
                var dbType = ingredient.ToDbType();
                db.Ingredients.Add(dbType);
                try
                {
                    await db.SaveChangesAsync();
                }
                catch (DbUpdateException ex) when (ex.InnerException is PostgresException { SqlState: PostgresErrorCodes.UniqueViolation, ConstraintName: "IX_Ingredients_Name_Lower" })
                {
                    return await SoftDeletedOrDuplicateConflict(dbType, ingredient, db);
                }
                // ADR-S058-3: der ETag der neu angelegten Zeile geht mit dem 201 heraus, damit ein
                // Client ihn als If-Match auf ein späteres DELETE/PUT/PATCH mitschicken kann.
                // ADR-S108-1: derselbe xmin füllt zusätzlich das DTO-Feld etag – einmal gelesen,
                // für Header UND Body verwendet (kein doppelter xmin-Read).
                var xmin = (uint) db.Entry(dbType).Property("xmin").CurrentValue!;
                httpContext.Response.Headers.ETag = XminETag.Format(xmin);
                return ingredient.ToDto(xmin);
            })
            .MatchAsync(
                created => Results.Created($"/api/ingredients/{created.Id}", created),
                error => error);

    // ADR-S090-1: field-keyed 422 body { "errors": { "<jsonPropertyName>": ["<msg>"] } } – multiple field
    // errors group into one dictionary so all messages appear simultaneously.
    internal static IResult ValidationProblemFor(IReadOnlyList<FieldError> errors) =>
        Results.ValidationProblem(
            errors.GroupBy(e => e.Key, e => e.Message, StringComparer.Ordinal)
                .ToDictionary(g => g.Key, g => g.ToArray(), StringComparer.Ordinal),
            statusCode: StatusCodes.Status422UnprocessableEntity);

    // ADR-S051-2 / ADR-S090-1: ein Fehlerfall des Konzepts -> ein (Request-JSON-Property, fester
    // deutscher Text). Die Zuordnung liegt hier an der API-Grenze, die das Request-Format kennt –
    // der Domänentyp bleibt feldagnostisch (ADR-S120-1, Regel 5). Je Verwendungsstelle eine eigene
    // Zuordnung: die Rezept-Einheit bekommt später ihre eigene, der Typ `Unit` bleibt einer.
    private static FieldError DescribeName(IngredientNameError error) => error switch
    {
        IngredientNameError.Empty => new FieldError("name", "Name darf nicht leer sein."),
        IngredientNameError.TooLong => new FieldError("name", "Name darf maximal 30 Zeichen lang sein."),
        _ => SumType.Unreachable<FieldError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
    };

    private static FieldError DescribeBaseUnit(UnitError error) => error switch
    {
        UnitError.Empty => new FieldError("baseUnit", "Einheit darf nicht leer sein."),
        UnitError.TooLong => new FieldError("baseUnit", "Einheit darf maximal 20 Zeichen lang sein."),
        _ => SumType.Unreachable<FieldError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
    };

    // ADR-S004-1 (Addendum S105): aktives Duplikat, case-insensitiv (ADR-S051-3). Anders als die
    // Feldregeln entsteht dieser Fehler erst NACH der abgelehnten Insert-Operation (ADR-S111-2),
    // also bereits an der Grenze – er wird direkt zum FieldError. Die Meldung braucht den getrimmten
    // EINGEGEBENEN Namen, nicht den gespeicherten.
    private static FieldError DuplicateName(string enteredName) =>
        new("name", $"Eine Zutat mit dem Namen '{enteredName}' existiert bereits.");

    internal static IngredientDbType ToDbType(this Ingredient domain) =>
        new() { Id = domain.Id.Value, Name = domain.Name.Value, BaseUnit = domain.BaseUnit.Value };

    internal static IngredientDto ToDto(this Ingredient domain, uint xmin) =>
        new(domain.Id.Value, domain.Name.Value, domain.BaseUnit.Value, XminETag.Format(xmin));

    // ADR-S108-1: derselbe Zeilen-DTO, hier direkt aus der DB-Zeile gebaut (Restore-Pfade lesen den
    // Stand einer schon existierenden Zeile, nicht eines frisch validierten Domain-Objekts). Bewusste
    // Abweichung vom kanonischen Read-Pfad DbType -> ToDomain() -> DTO: der ToDomain()-Roundtrip würde
    // hier einen ungeübten DB-Inkonsistenz-Fehlerzweig einführen, den kein Szenario fordert.
    // Gleiche Abweichung auf dem GET-Pfad, dort als Schuld erfasst (TD-S083-5).
    private static IngredientDto ToDto(this IngredientDbType row, uint xmin) =>
        new(row.Id, row.Name, row.BaseUnit, XminETag.Format(xmin));

    // ADR-S111-2: Lookup NACH der abgelehnten Insert-Operation (kein Vorab-Check, ADR-S105-2) –
    // entscheidet nur noch, welche Fehlerantwort rausgeht: 409 (soft-deleted) oder 422 (aktives
    // Duplikat). Das nicht persistierte Entity hängt sonst als Added im ChangeTracker und würde den
    // Lookup verfälschen -> Detach. AsNoTracking: die gelesene Zeile wird nicht mutiert.
    internal static async Task<OneOf<IngredientDto, IResult>> SoftDeletedOrDuplicateConflict(
        IngredientDbType failedInsert, Ingredient ingredient, MahlDbContext db)
    {
        db.Entry(failedInsert).State = EntityState.Detached;
        // Linke Seite (i.Name.ToLower()) läuft NICHT als CLR-Code – EF Core übersetzt den Ausdruck nach
        // SQL LOWER(), identisch zum funktionalen Unique-Index (ADR-S105-2/ADR-S051-3). Die rechte Seite
        // hat keinen Bezug zum Query-Root -> EF Core extrahiert sie als Parameter und wertet sie CLR-
        // seitig aus, deshalb ToLowerInvariant() statt ToLower(): unter einer Locale mit Sonderregeln
        // (z.B. tr-TR, punktloses ı) läge ein kulturabhängig ausgewerteter Parameter sonst neben dem
        // SQL-LOWER() der DB-Collation, der Lookup fände nichts. CA1308 (empfiehlt generell
        // ToUpperInvariant() statt ToLowerInvariant()) greift hier nicht: die Groß-/Kleinschreibung muss
        // exakt zur linken, SQL-übersetzten LOWER()-Seite passen – ToUpperInvariant() bräche den Vergleich.
        // CA1862 bleibt auf beiden Seiten berechtigt: der von CA1862 empfohlene Ersatz
        // (string.Equals(..., StringComparison.X)) ist hier nicht anwendbar, weil die linke Seite als SQL
        // LOWER()-Prädikat übersetzt wird – ein StringComparison-Overload übersetzt Npgsql nicht in eine
        // äquivalente SQL-Klausel.
#pragma warning disable CA1862
        var conflicting = await db.Ingredients
            .AsNoTracking()
#pragma warning disable CA1304, CA1308, CA1311, MA0011 // linke Seite (i.Name.ToLower()) ist SQL-übersetzt, rechte muss LOWER() spiegeln – s. Kommentar oben
            .Where(i => i.Name.ToLower() == ingredient.Name.Value.ToLowerInvariant())
#pragma warning restore CA1304, CA1308, CA1311, MA0011
            .FirstOrDefaultAsync();
#pragma warning restore CA1862

        var duplicateProblem = OneOf<IngredientDto, IResult>.FromT1(
            ValidationProblemFor([DuplicateName(ingredient.Name.Value)]));

        if (conflicting is null)
            return duplicateProblem;

        return conflicting.DeletedAt is not null
            ? OneOf<IngredientDto, IResult>.FromT1(SoftDeletedConflict(conflicting.Id))
            : duplicateProblem;
    }

    // ADR-S111-1: Pflicht-Body, validiert über denselben Pfad wie POST (ToValues()) – die sync
    // Validierungskette läuft VOR dem DB-Lookup, ein invalider Body liefert also 422 auch für eine
    // nicht existente id. Kein Widerspruch zu ADR-S000-5s Not-Found-Dominanz: die dortige Abwägung
    // betrifft Not-Found vs. Precondition (If-Match, ein 412 würde fälschlich Ressourcen-Existenz
    // suggerieren) – ein 422 redet über den Request-Body, nicht über die Ressource. Query ohne
    // DeletedAt-Filter: Restore muss sowohl aktive als auch soft-deleted Zeilen finden.
    // Restore braucht nur die Werte, keine Entity: beide Zweige identifizieren die Zeile über den
    // `id`-Routenparameter (`row.Id`) und schreiben Name/Einheit auf die gefundene Zeile.
    internal static async Task<IResult> RestoreIngredient(Guid id, IngredientValuesDto dto, MahlDbContext db) =>
        await dto.ToValues()
            .MapError<IngredientValues, IReadOnlyList<FieldError>, IResult>(ValidationProblemFor)
            .BindAsync<IngredientValues, IngredientDto, IResult>(async requested =>
            {
                var row = await db.Ingredients.FirstOrDefaultAsync(i => i.Id == id);
                if (row is null)
                    return OneOf<IngredientDto, IResult>.FromT1(NotFoundProblem());

                return row.DeletedAt is null
                    ? await RestoreActiveRow(row, requested, db)
                    : await RestoreSoftDeletedRow(row, requested, db);
            })
            .MatchAsync(restored => Results.Ok(restored), error => error);

    // ADR-S111-1: aktive Zeile – exakt-ordinaler Wertevergleich entscheidet Idempotenz (200, kein
    // Schreibvorgang) vs. Konflikt (409, fremde Werte bleiben unangetastet). Der case-insensitive
    // Duplikat-Check (ADR-S051-3) beantwortet "ist das dieselbe Zutat", hier zählt nur "sind die
    // WERTE identisch" – deshalb Ordinal, nicht die case-insensitive Namensgleichheit.
    private static Task<OneOf<IngredientDto, IResult>> RestoreActiveRow(IngredientDbType row, IngredientValues requested, MahlDbContext db)
    {
        var xmin = (uint) db.Entry(row).Property("xmin").CurrentValue!;
        var isUnchanged = string.Equals(row.Name, requested.Name.Value, StringComparison.Ordinal)
            && string.Equals(row.BaseUnit, requested.BaseUnit.Value, StringComparison.Ordinal);

        OneOf<IngredientDto, IResult> result = isUnchanged
            ? row.ToDto(xmin)
            : OneOf<IngredientDto, IResult>.FromT1(AlreadyActiveConflict(row.ToDto(xmin)));
        return Task.FromResult(result);
    }

    // ADR-S111-1/ADR-S051-4: soft-deleted Zeile – Name/Einheit werden UNBEDINGT aus dem Request
    // übernommen, unabhängig vom vorherigen Stand. Restore ist seit run-11 ein allgemeiner
    // Schreib-Endpoint (kein bloßes DeletedAt-Clear mehr) und braucht deshalb dieselbe
    // Exception-Behandlung wie jeder andere Schreibpfad (Review run-11: RestoreSoftDeletedRow war der
    // einzige Schreibpfad ohne sie, TD-S106-1 – kein globaler Exception-Handler im Projekt).
    private static async Task<OneOf<IngredientDto, IResult>> RestoreSoftDeletedRow(IngredientDbType row, IngredientValues requested, MahlDbContext db)
    {
        row.Name = requested.Name.Value;
        row.BaseUnit = requested.BaseUnit.Value;
        row.DeletedAt = null;
        try
        {
            await db.SaveChangesAsync();
        }
        // ADR-S111-1 Parallelfall (Addendum, s. dort): zwei überlappende Restores derselben
        // soft-deleted Zeile – der Verlierer sah beim Lesen eine gelöschte, beim Schreiben (Gewinner
        // hat committed) eine bereits aktive Zeile. ReloadAsync holt den committeten Gewinner-Stand
        // (Name/Einheit/xmin/DeletedAt=null); die Entscheidung 200-idempotent-vs-409-Konflikt
        // delegiert an RestoreActiveRow, statt sie hier zu duplizieren – sonst bekäme der HÄUFIGSTE
        // reale Auslöser (Doppelklick auf "Rückgängig", identische Werte) fälschlich einen Konflikt
        // gemeldet, obwohl ADR-S111-1 dafür 200 verlangt (Zielzustand bereits erreicht).
        // Nicht deterministisch über HTTP testbar: der Restore nimmt kein If-Match (anders als DELETE,
        // wo ein bewusst stale If-Match-Wert die 412-Kollision ohne echten Race reproduziert) – das
        // lesende SELECT und das schreibende UPDATE liegen beide innerhalb DIESES einen Requests, ohne
        // einen von außen erreichbaren Injektionspunkt dazwischen. Ein echter Task.WhenAll-Race wäre
        // interleaving-abhängig und damit flaky. Begründete Suppression statt Test, analog ADR-S041-9
        // (Defensive Guards ohne Test, mit begründeter Unterdrückung) – dieselbe Kategorie: strukturell
        // erreichbarer, aber von außen nicht kontrollierbarer Zweig.
        // Stryker disable once Block,Statement : DbUpdateConcurrencyException-Zweig nicht deterministisch über HTTP auslösbar (kein If-Match am Restore, Race liegt innerhalb eines einzelnen Requests)
        catch (DbUpdateConcurrencyException)
        {
            await db.Entry(row).ReloadAsync();
            return await RestoreActiveRow(row, requested, db);
        }
        catch (DbUpdateException ex) when (ex.InnerException is PostgresException { SqlState: PostgresErrorCodes.UniqueViolation, ConstraintName: "IX_Ingredients_Name_Lower" })
        {
            // Restore ist seit run-11 ein allgemeiner Schreib-Endpoint auf der eindeutigkeitsbeschränkten
            // Name-Spalte (ADR-S105-2/ADR-S111-2) – ein Request-Name, der mit einer ANDEREN Zeile
            // kollidiert, verletzt den Index genauso wie beim POST. Über die aktuelle UI nicht
            // erreichbar (der Client sendet nur LOWER-gleiche Namen), über die API sehr wohl -> derselbe
            // 422-Pfad wie POST (ADR-S090-1/ADR-S051-2).
            return OneOf<IngredientDto, IResult>.FromT1(
                ValidationProblemFor([DuplicateName(requested.Name.Value)]));
        }
        var xmin = (uint) db.Entry(row).Property("xmin").CurrentValue!;
        return row.ToDto(xmin);
    }

    // ADR-S051-5/ADR-S054-6: fixe deutsche Meldung + maschinenlesbarer errorCode für den DELETE-404-Fall
    // (nicht vorhanden ODER bereits soft-deleted, ADR-S000-5).
    internal static IResult NotFoundProblem() =>
        Results.Problem(
            detail: "Zutat wurde nicht gefunden.",
            statusCode: StatusCodes.Status404NotFound,
            extensions: new Dictionary<string, object?>(StringComparer.Ordinal) { ["errorCode"] = "INGREDIENT_NOT_FOUND" });

    // ADR-S106-2/ADR-S054-6: fixe deutsche Meldung + maschinenlesbarer errorCode für einen
    // vorhandenen, aber nicht zu einem xmin parsebaren If-Match-Header (428/400/412-Dreiteilung).
    internal static IResult InvalidIfMatchProblem() =>
        Results.Problem(
            detail: "Der If-Match-Header ist ungültig.",
            statusCode: StatusCodes.Status400BadRequest,
            extensions: new Dictionary<string, object?>(StringComparer.Ordinal) { ["errorCode"] = "INVALID_IF_MATCH" });

    // ADR-S004-1/ADR-S111-2: 409-Body für POST, wenn der Namenskonflikt gegen eine soft-deleted Zeile
    // geht – der Client orchestriert daraufhin automatisch den Restore mit den eigenen Eingaben.
    private static IResult SoftDeletedConflict(Guid id) =>
        Results.Conflict(new { code = "ingredient_soft_deleted", id });

    // ADR-S111-1/ADR-S111-3: 409-Body für den Restore, wenn die Zeile bereits aktiv ist, aber mit
    // abweichenden Werten – der gespeicherte Stand geht mit, damit der Client ihn benennen kann.
    private static IResult AlreadyActiveConflict(IngredientDto ingredient) =>
        Results.Conflict(new { code = "ingredient_already_active", ingredient });
}

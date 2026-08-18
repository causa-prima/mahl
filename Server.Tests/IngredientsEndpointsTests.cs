using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace mahl.Server.Tests;

[Collection(PostgresCollectionDefinition.Name)]
public class IngredientsEndpointsTests(PostgresContainerFixture postgres) : EndpointsTestsBase(postgres)
{
#pragma warning disable CA1812 // instantiated by JSON deserializer via reflection
    private sealed record IngredientResponse(Guid Id, string Name, string BaseUnit);
    // ADR-S108-1: eigener, NICHT-blinder Response-Record fürs neue etag-Feld. IngredientResponse bleibt
    // unverändert – eine Erweiterung würde bestehende BeEquivalentTo-Assertions zwingen, einen xmin-Wert
    // vorherzusagen, den sie nicht kennen können.
    private sealed record IngredientWithEtagResponse(Guid Id, string Name, string BaseUnit, string Etag);
    private sealed record CreateIngredientRequest(string Name, string BaseUnit);
    private sealed record ValidationErrorResponse(Dictionary<string, string[]> Errors);
    private sealed record ProblemDetailsResponse(string? Detail, string? ErrorCode);
    // ADR-S004-1/ADR-S111-2: 409-Body von POST bei soft-deleted-Namenskonflikt.
    private sealed record SoftDeletedConflictResponse(string Code, Guid Id);
    // ADR-S111-1: 409-Body vom Restore, wenn die Zeile bereits aktiv ist, aber mit abweichenden Werten.
    private sealed record AlreadyActiveConflictResponse(string Code, IngredientWithEtagResponse Ingredient);
#pragma warning restore CA1812

    // Helper: sendet DELETE mit optionalem If-Match-Header. HttpClient.DeleteAsync kennt keine
    // Custom-Header-Overload -> HttpRequestMessage nötig, wie im bestehenden ETag-Test-Muster
    // (ETagMiddlewareTests) für If-None-Match.
    private async Task<HttpResponseMessage> DeleteIngredientAsync(Guid id, string? ifMatch)
    {
        using var request = new HttpRequestMessage(HttpMethod.Delete, $"/api/ingredients/{id}");
        if (ifMatch is not null)
            request.Headers.TryAddWithoutValidation("If-Match", ifMatch);
        return await Client.SendAsync(request, TestContext.Current.CancellationToken);
    }

    // Helper: legt eine Zutat via POST an und liefert sie zusammen mit ihrem echten xmin-ETag
    // zurück – das POST+Deserialize+ETag-Auslesen-Setup wiederholt sich über mehrere DELETE-Tests.
    private async Task<(IngredientResponse Ingredient, string ETag)> CreateIngredientAsync(string name, string unit)
    {
        var createRequest = new CreateIngredientRequest(Name: name, BaseUnit: unit);
        var createResponse = await Client.PostAsJsonAsync("/api/ingredients", createRequest, TestContext.Current.CancellationToken);
        var created = await createResponse.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        return (created!, createResponse.Headers.ETag!.Tag);
    }

    // Helper: pinnt den Soft-Delete-Erfolgszustand (full-state DB assertion, DeletedAt aus dem
    // Equivalenzvergleich ausgeschlossen weil sein exakter Zeitstempel nicht Teil des erwarteten
    // Zustands ist – stattdessen separat auf "gesetzt" geprüft). Dupliziert sich über mehrere Tests.
    private async Task AssertSoftDeletedAsync(IngredientDbType expected)
    {
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo([expected], o => o.Excluding(x => x.DeletedAt));
        persisted[0].DeletedAt.Should().NotBeNull();
    }

    // ADR-S111-1 (überholt ADR-S108-2): Restore verlangt ab run-11 einen Pflicht-Body { name,
    // baseUnit } – ohne If-Match (Single-User-App-Ausnahme von ADR-S058-1 bleibt unverändert gültig).
    private async Task<HttpResponseMessage> RestoreIngredientAsync(Guid id, string name, string baseUnit) =>
        await Client.PostAsJsonAsync(
            $"/api/ingredients/{id}/restore",
            new CreateIngredientRequest(Name: name, BaseUnit: baseUnit),
            TestContext.Current.CancellationToken);

    [Fact]
    public async Task US904_HappyPath_GetIngredients_EmptyDb_Returns200WithEmptyList()
    {
        var response = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse[]>(TestContext.Current.CancellationToken);
        body.Should().BeEmpty();
    }

    [Fact]
    public async Task US904_HappyPath_CreateIngredient_ValidData_Returns201WithBodyAndLocation()
    {
        // Given: name and unit for a new ingredient
        var request = new CreateIngredientRequest(Name: "Tomaten", BaseUnit: "Stück");

        // When: ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created with the created ingredient as body (ADR-S068-1)
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Tomaten");
        body.BaseUnit.Should().Be("Stück");

        // Then: Location header points to the new resource (ADR-S068-1)
        response.Headers.Location.Should().Be($"/api/ingredients/{body.Id}");

        // Then: the ingredient is persisted (full-state DB assertion) with the server-generated id
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = "Tomaten", BaseUnit = "Stück" }]);
    }

    [Fact]
    public async Task US904_HappyPath_GetIngredients_AfterCreate_ReturnsCreatedIngredient()
    {
        // Given: an ingredient was created
        var request = new CreateIngredientRequest(Name: "Tomaten", BaseUnit: "Stück");
        var createResponse = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);
        var created = await createResponse.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        created.Should().NotBeNull();

        // When: the ingredient list is requested
        var response = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);

        // Then: the list contains exactly the created ingredient with name and unit
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse[]>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Should().BeEquivalentTo(
            [new IngredientResponse(Id: created.Id, Name: "Tomaten", BaseUnit: "Stück")]);
    }

    // @US-904-happy-path (run-7 „Liste"): mehrere Zutaten erscheinen alphabetisch sortiert. Insertion-
    // Order ("Zwiebel", "Apfel", "Mehl") weicht bewusst von der erwarteten alphabetischen Reihenfolge ab –
    // sonst wäre der OrderBy-Mutant nicht Stryker-killbar (ein reines Insertion-Order-Passthrough würde
    // den Test zufällig auch bestehen). ADR-S084-1: deterministische Sortierung ist zugleich Voraussetzung
    // für den stabilen Collection-Content-Hash-ETag.
    [Fact]
    public async Task US904_HappyPath_GetIngredients_MultipleIngredients_ReturnsAlphabeticallySortedByName()
    {
        // Given: three ingredients created in non-alphabetical order
        await CreateIngredientAsync("Zwiebel", "Stück");
        await CreateIngredientAsync("Apfel", "Stück");
        await CreateIngredientAsync("Mehl", "g");

        // When: the ingredient list is requested
        var response = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);

        // Then: 200 OK with the ingredients ordered alphabetically by name, not insertion order
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse[]>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Select(i => i.Name).Should().Equal("Apfel", "Mehl", "Zwiebel");
    }

    // @US-904-edge-case (run-7 „Liste"): eine soft-deleted Zutat erscheint nicht in der Zutaten-Liste
    // (ADR-S000-6). Der soft-deleted Zustand wird direkt in der DB hergestellt (statt über POST+DELETE),
    // um den GET-Test von der Korrektheit des DELETE-Endpoints zu isolieren.
    [Fact]
    public async Task US904_EdgeCase_GetIngredients_SoftDeletedIngredient_ExcludedFromResponse()
    {
        // Given: one active ingredient and one soft-deleted ingredient (DeletedAt set directly in the DB)
        var (active, _) = await CreateIngredientAsync("Petersilie", "Bund");
        Db.Ingredients.Add(new IngredientDbType
        {
            Id = Guid.CreateVersion7(), Name = "Basilikum", BaseUnit = "Stück", DeletedAt = DateTimeOffset.UtcNow,
        });
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When: the ingredient list is requested
        var response = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);

        // Then: 200 OK with only the active ingredient – the soft-deleted row is filtered out
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse[]>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo([new IngredientResponse(Id: active.Id, Name: "Petersilie", BaseUnit: "Bund")]);
    }

    // @US-904-edge-case: Führende und nachfolgende Leerzeichen werden beim Speichern entfernt.
    // Pinnt die Trim-KORREKTHEIT (ADR-S051-1: vor der Validierung trimmen, den getrimmten Wert speichern)
    // am Backend-Grenzwert. Auf E2E-Ebene ist die exakte Whitespace-Entfernung nur mühsam (Regex gegen den
    // Roh-DOM-Text) beobachtbar; die byte-genaue Prüfung von Response-Body UND DB-State gehört hierher
    // (ADR-S041-5-Addendum). Nur leading/trailing – inneres Whitespace ist nicht Teil des Szenarios.
    [Fact]
    public async Task US904_EdgeCase_CreateIngredient_WhitespacePaddedInput_TrimsAndPersistsTrimmedValue()
    {
        // Given: name and unit padded with leading and trailing whitespace
        var request = new CreateIngredientRequest(Name: "  Oregano  ", BaseUnit: "  g  ");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created and the response body carries the TRIMMED values (no surrounding whitespace)
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Oregano");
        body.BaseUnit.Should().Be("g");

        // Then: the persisted row stores the trimmed values (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = "Oregano", BaseUnit = "g" }]);
    }

    // Same invariant ("Pflichtfeld leer oder nur Whitespace -> 422 feld-keyed"), nur Input variiert
    // -> ein parametrisierter Test (docs/process/tdd-process.md "Parametrisierte Tests").
    // ADR-S051-1: Strings werden vor der Validierung getrimmt -> "   " ist nach Trimming leer.
    [Theory]
    [InlineData("", "g", "name", "Name darf nicht leer sein.")]
    [InlineData("   ", "g", "name", "Name darf nicht leer sein.")]
    [InlineData("Salz", "", "baseUnit", "Einheit darf nicht leer sein.")]
    [InlineData("Salz", "   ", "baseUnit", "Einheit darf nicht leer sein.")]
    public async Task US904_Error_CreateIngredient_InvalidInput_Returns422WithFieldKeyedError(
        string name, string unit, string expectedKey, string expectedMessage)
    {
        // Given: a request whose required field is empty or whitespace-only
        var request = new CreateIngredientRequest(Name: name, BaseUnit: unit);

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 422 Unprocessable Entity (ADR-S090-1: status must be 422, not 400)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        // Then: field-keyed error body maps the offending field to its message (ADR-S090-1, ADR-S051-2)
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            [expectedKey] = [expectedMessage],
        });

        // Then: nothing is persisted – the ingredient list stays unchanged (empty)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }

    // @US-904-error: Server-seitige Max-Length-Validierung (ADR-S051-3: name max. 30 Zeichen, nach
    // Trimming gemessen). Eigener Test statt weiterer [InlineData] der Empty-Theory oben – andere
    // fachliche Invariante (zu lang statt leer), eigener erwarteter Text (ADR-S051-2).
    [Fact]
    public async Task US904_Error_CreateIngredient_NameExceeds30Chars_Returns422WithNameTooLongError()
    {
        // Given: a name of 31 characters (exceeds the 30-character limit, ADR-S051-3)
        var request = new CreateIngredientRequest(Name: new string('A', 31), BaseUnit: "g");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 422 Unprocessable Entity (ADR-S090-1)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        // Then: field-keyed error body carries the fixed max-length message (ADR-S090-1, ADR-S051-2)
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["name"] = ["Name darf maximal 30 Zeichen lang sein."],
        });

        // Then: nothing is persisted – the ingredient list stays unchanged (empty)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }

    // @US-904-edge-case: die Grenze liegt bei > 30, NICHT >= 30 – exakt 30 Zeichen ist gültig (ADR-S051-3).
    [Fact]
    public async Task US904_EdgeCase_CreateIngredient_NameExactly30Chars_Returns201()
    {
        // Given: a name of exactly 30 characters (at the limit, still valid per ADR-S051-3)
        var name = new string('A', 30);
        var request = new CreateIngredientRequest(Name: name, BaseUnit: "g");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created – the boundary value is accepted
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be(name);
        body.BaseUnit.Should().Be("g");

        // Then: the ingredient is persisted (full-state DB assertion) with the server-generated id
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = name, BaseUnit = "g" }]);
    }

    // @US-904-edge-case: die Längengrenze misst den GETRIMMTEN Wert (ADR-S051-3 "nach Trimming gemessen"),
    // nicht den rohen Input. Erst die Kombination beider Achsen unterscheidet die zwei Implementierungen:
    // 30 Zeichen mit Padding sind roh 34, eine Messung VOR dem Trimmen antwortete hier mit 422 statt 201.
    // Die benachbarten Tests decken je nur eine Achse ab – WhitespacePaddedInput trimmt kurze Werte,
    // NameExactly30Chars prüft den Grenzwert ohne Padding.
    [Fact]
    public async Task US904_EdgeCase_CreateIngredient_PaddedNameAt30CharLimit_Returns201AndPersistsTrimmedValue()
    {
        // Given: a name of exactly 30 characters, padded to 34 raw characters
        var name = new string('A', 30);
        var request = new CreateIngredientRequest(Name: $"  {name}  ", BaseUnit: "g");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created – the limit applies to the trimmed value, which is still at the boundary
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be(name);
        body.BaseUnit.Should().Be("g");

        // Then: the persisted row stores the trimmed 30-character value (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = name, BaseUnit = "g" }]);
    }

    // @US-904-error: Server-seitige Max-Length-Validierung (ADR-S051-3: baseUnit max. 20 Zeichen, nach
    // Trimming gemessen). Eigener Test statt weiterer [InlineData] der Empty-Theory oben – andere
    // fachliche Invariante (zu lang statt leer), eigener erwarteter Text (ADR-S051-2).
    [Fact]
    public async Task US904_Error_CreateIngredient_UnitExceeds20Chars_Returns422WithUnitTooLongError()
    {
        // Given: a unit of 21 characters (exceeds the 20-character limit, ADR-S051-3)
        var request = new CreateIngredientRequest(Name: "Salz", BaseUnit: new string('A', 21));

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 422 Unprocessable Entity (ADR-S090-1)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        // Then: field-keyed error body carries the fixed max-length message (ADR-S090-1, ADR-S051-2)
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["baseUnit"] = ["Einheit darf maximal 20 Zeichen lang sein."],
        });

        // Then: nothing is persisted – the ingredient list stays unchanged (empty)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }

    // @US-904-edge-case: die Grenze liegt bei > 20, NICHT >= 20 – exakt 20 Zeichen ist gültig (ADR-S051-3).
    [Fact]
    public async Task US904_EdgeCase_CreateIngredient_UnitExactly20Chars_Returns201()
    {
        // Given: a unit of exactly 20 characters (at the limit, still valid per ADR-S051-3)
        var unit = new string('A', 20);
        var request = new CreateIngredientRequest(Name: "Salz", BaseUnit: unit);

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created – the boundary value is accepted
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Salz");
        body.BaseUnit.Should().Be(unit);

        // Then: the ingredient is persisted (full-state DB assertion) with the server-generated id
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = "Salz", BaseUnit = unit }]);
    }

    // @US-904-edge-case: Einheiten-Gegenstück zum Namens-Fall oben – dieselbe Invariante (Grenze misst den
    // getrimmten Wert, ADR-S051-3) auf der zweiten Feld-Achse, weil jedes Feld seinen eigenen Marker-Typ
    // für den Grenzwert trägt. 20 Zeichen mit Padding sind roh 24.
    [Fact]
    public async Task US904_EdgeCase_CreateIngredient_PaddedUnitAt20CharLimit_Returns201AndPersistsTrimmedValue()
    {
        // Given: a unit of exactly 20 characters, padded to 24 raw characters
        var unit = new string('A', 20);
        var request = new CreateIngredientRequest(Name: "Salz", BaseUnit: $"  {unit}  ");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created – the limit applies to the trimmed value, which is still at the boundary
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Salz");
        body.BaseUnit.Should().Be(unit);

        // Then: the persisted row stores the trimmed 20-character value (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = "Salz", BaseUnit = unit }]);
    }

    // @US-904-error: Drei Gherkin-Szenarien testen dieselbe fachliche Invariante (Eindeutigkeit case-insensitiv,
    // ADR-S051-3; Meldung field-keyed 422 mit dem getrimmten EINGEGEBENEN Namen, ADR-S090-1/ADR-S004-1) mit nur
    // variierendem Input/Setup -> ein parametrisierter Test (docs/process/tdd-process.md "Parametrisierte Tests"):
    // "Zutat mit bereits vorhandenem Namen anlegen schlägt fehl" (exakte Schreibweise) |
    // "Zutat mit vorhandenem Namen in abweichender Schreibweise anlegen schlägt fehl" (case-insensitiv) |
    // "Fehlermeldung bei Duplikat zeigt getrimmten Namen" (Trailing-Space).
    [Theory]
    [InlineData("Zucker", "g", "Zucker", "kg", "Zucker")]
    [InlineData("Öl", "ml", "öl", "l", "öl")] // Umlaut statt ASCII: Case-Insensitivität (ADR-S051-3) + nagelt das umlaut-faltende Locale fest (ADR-S105-1: en_US.utf8, nicht C)
    [InlineData("Tomaten", "Stück", "tomaten ", "g", "tomaten")] // Trailing-Space in requestName ist beabsichtigt (Trim-Szenario; deckt ASCII-Faltung ab)
    public async Task US904_Error_CreateIngredient_DuplicateName_Returns422WithNameDuplicateError(
        string existingName, string existingUnit, string requestName, string requestUnit, string expectedNameInMessage)
    {
        // Given: an ingredient with the existing name already exists
        var existing = new IngredientDbType { Id = Guid.CreateVersion7(), Name = existingName, BaseUnit = existingUnit };
        Db.Ingredients.Add(existing);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When: another ingredient with a duplicate (possibly differently cased/padded) name is created
        var request = new CreateIngredientRequest(Name: requestName, BaseUnit: requestUnit);
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 422 Unprocessable Entity (ADR-S090-1, ADR-S004-1 Addendum S105 – aktives Duplikat ist field-keyed)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        // Then: field-keyed error body names the ENTERED (trimmed) name, not the stored one (ADR-S004-1)
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["name"] = [$"Eine Zutat mit dem Namen '{expectedNameInMessage}' existiert bereits."],
        });

        // Then: the ingredient list stays unchanged – only the pre-existing ingredient remains
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo([existing]);
    }

    // Eigener Test (nicht weitere InlineData der Single-Field-Theory): die Invariante ist hier der
    // collect-all-Merge – BEIDE unabhängigen Pflichtfelder werden validiert und ihre Fehler GLEICHZEITIG
    // gemeldet (ADR-S000-1 collect-all, gültig laut ADR-S090-1). Die Single-Field-Theory pinnt nur je EINEN Key.
    [Fact]
    public async Task US904_Error_CreateIngredient_BothFieldsEmpty_Returns422WithBothFieldKeyedErrors()
    {
        // Given: a request whose name AND unit are both empty
        var request = new CreateIngredientRequest(Name: "", BaseUnit: "");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 422 Unprocessable Entity (ADR-S090-1)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        // Then: field-keyed error body carries BOTH fields with their messages simultaneously (ADR-S090-1, ADR-S051-2)
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["name"] = ["Name darf nicht leer sein."],
            ["baseUnit"] = ["Einheit darf nicht leer sein."],
        });

        // Then: nothing is persisted – the ingredient list stays unchanged (empty)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }

    // ADR-S058-3: erste Single-Resource-xmin-ETag-Umsetzung – POST liefert den ETag der neu angelegten
    // Zeile, damit ein Client ihn als If-Match für ein nachfolgendes DELETE (Optimistic Concurrency,
    // ADR-S058-1) mitschicken kann. Nicht durch ein Gherkin-Szenario getrieben (wie der Collection-ETag,
    // s. ETagMiddlewareTests) – daher ohne US904-Präfix.
    [Fact]
    public async Task CreateIngredient_ValidData_Returns201WithXminETagHeader()
    {
        // Given: name and unit for a new ingredient
        var request = new CreateIngredientRequest(Name: "Zimt", BaseUnit: "g");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created with a quoted, non-empty ETag header (ADR-S058-3: xmin, hex-encoded)
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        response.Headers.ETag.Should().NotBeNull();
        response.Headers.ETag!.Tag.Should().StartWith("\"").And.EndWith("\"");
        response.Headers.ETag.Tag.Trim('"').Should().NotBeEmpty();
    }

    // @US-904-edge-case: "Bereits gelöschte Zutat erneut löschen schlägt fehl" – das Given des Szenarios
    // ("...existiert und gelöscht wurde") erzwingt, dass das ERSTE Löschen korrekt gelingt. Pinnt damit
    // die eigentliche Soft-Delete-Erfolgsmechanik des Endpoints: 204 und die Zeile bleibt physisch
    // bestehen mit gesetztem DeletedAt (ADR-S000-6 Soft-Delete) – kein eigenständiges EdgeCase-Verhalten
    // dieses Tests selbst.
    [Fact]
    public async Task US904_EdgeCase_DeleteIngredient_ActiveIngredientWithValidIfMatch_Returns204AndSoftDeletesRow()
    {
        // Given: an ingredient created via POST (real xmin ETag from the response)
        var (created, etag) = await CreateIngredientAsync("Pfeffer", "g");

        // When: the ingredient is deleted with the matching If-Match
        var response = await DeleteIngredientAsync(created.Id, etag);

        // Then: 204 No Content (ADR-S000-5)
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // Then: the row is soft-deleted – physically retained, DeletedAt set (ADR-S000-6)
        await AssertSoftDeletedAsync(new IngredientDbType { Id = created.Id, Name = "Pfeffer", BaseUnit = "g" });
    }

    // @US-904-edge-case: "Bereits gelöschte Zutat erneut löschen schlägt fehl". Sendet bewusst dasselbe
    // (jetzt STALE) If-Match wie beim ersten Löschen mit, um die Not-Found-VOR-If-Match-Reihenfolge zu
    // pinnen (ADR-S000-5: 404, nicht 412).
    [Fact]
    public async Task US904_EdgeCase_DeleteIngredient_AlreadyDeleted_Returns404WithNotFoundDetail()
    {
        // Given: "Pfeffer" (g) existiert und wurde bereits gelöscht (erstes DELETE gelingt, 204)
        var (created, etag) = await CreateIngredientAsync("Pfeffer", "g");
        var firstDelete = await DeleteIngredientAsync(created.Id, etag);
        firstDelete.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // When: der Lösch-Befehl für "Pfeffer" wird erneut abgesendet (gleicher, nun stale ETag)
        var response = await DeleteIngredientAsync(created.Id, etag);

        // Then: 404 mit der fixen deutschen Fehlermeldung und maschinenlesbarem errorCode (ADR-S051-5, ADR-S054-6)
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        var body = await response.Content.ReadFromJsonAsync<ProblemDetailsResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Detail.Should().Be("Zutat wurde nicht gefunden.");
        body.ErrorCode.Should().Be("INGREDIENT_NOT_FOUND");

        // Then: die Zeile bleibt unverändert soft-deleted – keine weitere Mutation (full-state DB assertion)
        await AssertSoftDeletedAsync(new IngredientDbType { Id = created.Id, Name = "Pfeffer", BaseUnit = "g" });
    }

    // ADR-S058-1: mutierende Single-Resource-Endpoints verlangen If-Match. Nicht durch das Gherkin-Szenario
    // getrieben (wie der Collection-ETag) – daher ohne US904-Präfix, geprüft ausschließlich hier
    // (Server.Tests), nicht im äußeren E2E.
    [Fact]
    public async Task DeleteIngredient_ActiveIngredientMissingIfMatch_Returns428PreconditionRequired()
    {
        // Given: eine aktive Zutat
        var (created, _) = await CreateIngredientAsync("Salz", "g");

        // When: DELETE ohne If-Match-Header
        var response = await DeleteIngredientAsync(created.Id, ifMatch: null);

        // Then: 428 Precondition Required
        response.StatusCode.Should().Be(HttpStatusCode.PreconditionRequired);

        // Then: nichts wird soft-deleted (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo([new IngredientDbType { Id = created.Id, Name = "Salz", BaseUnit = "g" }]);
    }

    // ADR-S058-1/ADR-S058-3: stale If-Match auf eine aktive Zeile -> 412 (EF Core prüft xmin beim
    // SaveChanges). Nicht durch das Gherkin-Szenario getrieben – daher ohne US904-Präfix.
    [Fact]
    public async Task DeleteIngredient_ActiveIngredientStaleIfMatch_Returns412PreconditionFailed()
    {
        // Given: eine aktive Zutat (echter ETag aus dem POST)
        var (created, _) = await CreateIngredientAsync("Muskat", "g");

        // When: DELETE mit einem wohlgeformten, aber nicht passenden (stale) If-Match
        var response = await DeleteIngredientAsync(created.Id, ifMatch: "\"deadbeef\"");

        // Then: 412 Precondition Failed
        response.StatusCode.Should().Be(HttpStatusCode.PreconditionFailed);

        // Then: nichts wird soft-deleted (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo([new IngredientDbType { Id = created.Id, Name = "Muskat", BaseUnit = "g" }]);
    }

    // Ein If-Match-Wert, der wie ein ETag AUSSIEHT, aber nicht zu einem xmin geparst werden kann
    // (non-hex/Overflow/leer/Wildcard), würde sonst eine unbehandelte FormatException/OverflowException
    // -> 500 (Stack-Trace-Leak-Risiko) auslösen. Dreiteilung: 428 = fehlt, 400 = nicht-parsebar (dieser
    // Test), 412 = wohlgeformt-aber-stale (Test oben). `*`/Weak-ETags/Multi-Value-Listen werden bewusst
    // NICHT unterstützt (YAGNI, konsistent zum Nichtsupport in ETagMiddleware).
    [Theory]
    [InlineData("zzzzzzzz")] // non-hex
    [InlineData("\"1ffffffff\"")] // 9 Hex-Ziffern -> Overflow für uint
    [InlineData("\"\"")] // quoted-leer (ein echt leerer Header-Wert erreicht den Server transport-bedingt gar nicht -> 428, s. Kommentar oben)
    [InlineData("*")] // Wildcard
    public async Task DeleteIngredient_ActiveIngredientMalformedIfMatch_Returns400BadRequest(string malformedIfMatch)
    {
        // Given: eine aktive Zutat
        var (created, _) = await CreateIngredientAsync("Kardamom", "g");

        // When: DELETE mit einem nicht-parsebaren If-Match
        var response = await DeleteIngredientAsync(created.Id, malformedIfMatch);

        // Then: 400 Bad Request (nicht 500 – die Ausnahme wird VOR dem EF-Concurrency-Pfad abgefangen)
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        var body = await response.Content.ReadFromJsonAsync<ProblemDetailsResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Detail.Should().Be("Der If-Match-Header ist ungültig.");
        body.ErrorCode.Should().Be("INVALID_IF_MATCH");

        // Then: nichts wird soft-deleted (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo([new IngredientDbType { Id = created.Id, Name = "Kardamom", BaseUnit = "g" }]);
    }

    // Pinnt die 404-Dominanz aus dem ADR-S000-5-Addendum GEGEN den If-Match-Check, auch wenn dieser
    // einen anderen Fehlerstatus (400 malformed / 428 fehlend) liefern würde – eine bereits soft-deleted
    // Zeile liefert IMMER 404, unabhängig vom If-Match-Zustand. Der bestehende "AlreadyDeleted"-Test
    // deckt das nur für ein WOHLGEFORMTES (stale) If-Match ab; ohne diesen Test bliebe eine versehentliche
    // Vertauschung der Check-Reihenfolge (If-Match VOR Existenz-Check) unentdeckt grün. Stryker kann diese
    // Ordering-Invariante strukturell nicht fangen (Statement-Reorder ist kein Mutant) – daher hier als
    // expliziter Regressions-Test, ohne US-Tag (Protokoll-/Invarianten-Test).
    [Theory]
    [InlineData("zzzzzzzz")] // malformed If-Match auf soft-deleted Zeile -> 404, nicht 400
    [InlineData(null)] // fehlendes If-Match auf soft-deleted Zeile -> 404, nicht 428
    public async Task DeleteIngredient_AlreadySoftDeletedWithMalformedOrMissingIfMatch_Returns404NotBadRequestOrPreconditionRequired(
        string? ifMatch)
    {
        // Given: "Wacholder" existiert und wurde bereits gelöscht (erstes DELETE gelingt, 204)
        var (created, etag) = await CreateIngredientAsync("Wacholder", "g");
        var firstDelete = await DeleteIngredientAsync(created.Id, etag);
        firstDelete.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // When: der Lösch-Befehl wird erneut abgesendet, mit einem malformed bzw. fehlenden If-Match
        var response = await DeleteIngredientAsync(created.Id, ifMatch);

        // Then: 404 dominiert – nicht 400 (malformed) und nicht 428 (fehlend)
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        var body = await response.Content.ReadFromJsonAsync<ProblemDetailsResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Detail.Should().Be("Zutat wurde nicht gefunden.");
        body.ErrorCode.Should().Be("INGREDIENT_NOT_FOUND");

        // Then: die Zeile bleibt unverändert soft-deleted – keine weitere Mutation (full-state DB assertion)
        await AssertSoftDeletedAsync(new IngredientDbType { Id = created.Id, Name = "Wacholder", BaseUnit = "g" });
    }

    // ADR-S108-1: GET /api/ingredients liefert je Zeile den xmin-ETag im Body (etag-Feld) – die
    // If-Match-Quelle für ein DELETE einer aus der Liste geladenen Zutat. Kategorie-1-Protokolltest
    // (ADR-S106-3) ohne treibendes Gherkin-Szenario, daher ohne US-Tag. Der etag-Wert wird gegen den
    // ECHTEN ETag-Header derselben Zeile verglichen (nicht nur "nicht leer") – beide stammen aus
    // demselben xmin und müssen identisch sein.
    [Fact]
    public async Task GetIngredients_ActiveIngredient_ReturnsRowEtagMatchingItsOwnPostETagHeader()
    {
        // Given: an ingredient created via POST (its real xmin ETag from the response header)
        var (created, etag) = await CreateIngredientAsync("Kreuzkümmel", "g");

        // When: the ingredient list is requested
        var response = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);

        // Then: the row's etag field equals the POST's ETag header for the same row (same xmin)
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientWithEtagResponse[]>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo(
            [new IngredientWithEtagResponse(Id: created.Id, Name: "Kreuzkümmel", BaseUnit: "g", Etag: etag)]);
    }

    // ADR-S108-1: POST /api/ingredients (201) teilt sich das IngredientDto mit GET – das etag-Feld des
    // Response-Bodys wird aus demselben xmin gefüllt, das ohnehin schon für den ETag-Response-Header
    // (ADR-S106-1) gelesen wird. Kategorie-1-Protokolltest (ADR-S106-3), kein US-Tag.
    [Fact]
    public async Task CreateIngredient_ValidData_Returns201BodyWithEtagFieldMatchingETagHeader()
    {
        // Given: name and unit for a new ingredient
        var request = new CreateIngredientRequest(Name: "Ingwer", BaseUnit: "g");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: the body's etag field equals the response's own ETag header (same xmin, read once)
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientWithEtagResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Etag.Should().Be(response.Headers.ETag!.Tag);
    }

    // @US-904-happy-path (Szenario 2 "Löschen rückgängig machen via Toast"): pinnt das Backend-
    // Verhalten hinter "Then sehe ich 'Mehl' in der Zutaten-Liste mit Einheit 'g'" – Restore setzt
    // DeletedAt = null. Szenario-getrieben, daher US-Tag (nicht Kategorie-1 nach ADR-S106-3 – das wäre
    // nur reine Protokoll-/Infrastruktur-Mechanik ohne Domänen-Verhalten). ADR-S111-1 (überholt
    // ADR-S108-2): Restore-Body ist ab run-11 Pflicht und Erfolgs-Status 200 statt 204 – der Undo-Aufruf
    // schickt Name/Einheit der gelöschten Zeile unverändert mit (fachlich ein No-op, ein Codepfad).
    [Fact]
    public async Task US904_HappyPath_RestoreIngredient_SoftDeletedIngredient_Returns200AndClearsDeletedAt()
    {
        // Given: "Rosmarin" exists and was already deleted (first DELETE succeeds, 204)
        var (created, etag) = await CreateIngredientAsync("Rosmarin", "g");
        var deleteResponse = await DeleteIngredientAsync(created.Id, etag);
        deleteResponse.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // When: the soft-deleted ingredient is restored with its own (unchanged) name/unit
        var response = await RestoreIngredientAsync(created.Id, "Rosmarin", "g");

        // Then: 200 OK with the restored ingredient (ADR-S111-1)
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Rosmarin");
        body.BaseUnit.Should().Be("g");

        // Then: the row is active again – DeletedAt cleared, name/unit unchanged (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = created.Id, Name = "Rosmarin", BaseUnit = "g" }]);
    }

    // ADR-S108-2/ADR-S111-1: eine nie existente id liefert 404 mit demselben Body wie DELETE
    // (NotFoundProblem, ADR-S051-5/ADR-S054-6). Kategorie-1-Protokolltest (ADR-S106-3), kein US-Tag.
    // Body ist valide (422 läuft VOR 404, s. Kommentar am Endpoint) – sonst würde dieser Test
    // fälschlich den 422-Pfad statt den 404-Pfad treffen.
    [Fact]
    public async Task RestoreIngredient_NonExistentId_Returns404WithNotFoundDetail()
    {
        // Given: an id that was never created
        var nonExistentId = Guid.CreateVersion7();

        // When: restoring that id with a valid body
        var response = await RestoreIngredientAsync(nonExistentId, name: "Irrelevant", baseUnit: "g");

        // Then: 404 with the fixed German detail and machine-readable errorCode
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        var body = await response.Content.ReadFromJsonAsync<ProblemDetailsResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Detail.Should().Be("Zutat wurde nicht gefunden.");
        body.ErrorCode.Should().Be("INGREDIENT_NOT_FOUND");

        // Then: nothing was written – the 404 path is read-only, the ingredient list stays empty
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }

    // Kategorie-1-Protokolltest (ADR-S106-3): kein treibendes Gherkin-Szenario – der Validierungs-Zweig
    // im Restore ist strukturell erzwungen (sonst umginge der Restore die Invariante aus ADR-S051-3,
    // ADR-S111-1). Ein Fall genügt (die Validierungslogik selbst ist über die POST-Tests abgedeckt).
    [Fact]
    public async Task RestoreIngredient_InvalidBody_Returns422WithFieldKeyedError()
    {
        // Given: an active ingredient (any existing row – the invalid body must be rejected first)
        var (created, _) = await CreateIngredientAsync("Kurkuma", "g");

        // When: restoring with an empty name
        var response = await RestoreIngredientAsync(created.Id, name: "", baseUnit: "g");

        // Then: 422 Unprocessable Entity, field-keyed (ADR-S090-1, same ToDomain() path as POST)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["name"] = ["Name darf nicht leer sein."],
        });

        // Then: the row is unchanged (full-state DB assertion) – validation runs before the DB write
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = created.Id, Name = "Kurkuma", BaseUnit = "g" }]);
    }

    // Kategorie-1-Protokolltest (ADR-S106-3): kein treibendes Gherkin-Szenario – Restore ist seit
    // run-11 ein allgemeiner Schreib-Endpoint auf der eindeutigkeitsbeschränkten Name-Spalte
    // (ADR-S105-2/ADR-S111-2). Ein Request-Name, der mit einer ANDEREN aktiven Zeile kollidiert,
    // verletzt den Index genauso wie beim POST – über die aktuelle UI nicht erreichbar (der Client
    // sendet nur LOWER-gleiche Namen), über die API sehr wohl. Derselbe 422-Pfad wie POST
    // (ADR-S090-1/ADR-S051-2), damit die Invariante aus ADR-S051-3 für BEIDE Schreibpfade gilt.
    [Fact]
    public async Task RestoreIngredient_SoftDeletedRowNameCollidesWithActiveRow_Returns422WithNameDuplicateError()
    {
        // Given: an active ingredient "Mehl" and a soft-deleted ingredient "Zucker"
        var (mehl, _) = await CreateIngredientAsync("Mehl", "g");
        var (zucker, zuckerEtag) = await CreateIngredientAsync("Zucker", "g");
        var deleteResponse = await DeleteIngredientAsync(zucker.Id, zuckerEtag);
        deleteResponse.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // When: restoring "Zucker" with a name colliding with the active "Mehl"
        var response = await RestoreIngredientAsync(zucker.Id, name: "Mehl", baseUnit: "g");

        // Then: 422 Unprocessable Entity, field-keyed with the same duplicate-name message as POST
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["name"] = ["Eine Zutat mit dem Namen 'Mehl' existiert bereits."],
        });

        // Then: nothing was overwritten – both rows keep their original state (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [
                new IngredientDbType { Id = mehl.Id, Name = "Mehl", BaseUnit = "g" },
                new IngredientDbType { Id = zucker.Id, Name = "Zucker", BaseUnit = "g" },
            ],
            o => o.Excluding(x => x.DeletedAt)); // Zucker bleibt soft-deleted – exakter Zeitstempel nicht Teil des Szenarios
        persisted.Single(i => i.Id == zucker.Id).DeletedAt.Should().NotBeNull();
    }

    // @US-904-edge-case: "Gelöschte Zutat mit gleichem Namen anlegen reaktiviert diese" (Szenario 1,
    // exakte Schreibweise) + "Reaktivierung übernimmt neuen Namen bei abweichender Schreibweise"
    // (Szenario 3, case-insensitiver Lookup) – gleiche Setup-/Assert-Struktur, nur die Schreibweise
    // variiert (docs/process/tdd-process.md "Parametrisierte Tests"). ADR-S004-1/ADR-S111-2: POST
    // unterscheidet den Namenskonflikt gegen eine soft-deleted Zeile (409, strukturiert) von einer
    // aktiven Zeile (422, field-keyed, s. bestehende DuplicateName-Theory).
    [Theory]
    [InlineData("Butter", "Butter")]
    [InlineData("mehl", "Mehl")]
    public async Task US904_EdgeCase_CreateIngredient_SoftDeletedDuplicateName_Returns409WithSoftDeletedConflictBody(
        string existingName, string requestName)
    {
        // Given: a soft-deleted ingredient with the existing (possibly differently cased) name
        var deleted = new IngredientDbType
        {
            Id = Guid.CreateVersion7(), Name = existingName, BaseUnit = "g", DeletedAt = DateTimeOffset.UtcNow,
        };
        Db.Ingredients.Add(deleted);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When: an ingredient with the (possibly differently cased) duplicate name is created
        var request = new CreateIngredientRequest(Name: requestName, BaseUnit: "kg");
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 409 Conflict with the soft-deleted row's id (ADR-S004-1)
        response.StatusCode.Should().Be(HttpStatusCode.Conflict);
        var body = await response.Content.ReadFromJsonAsync<SoftDeletedConflictResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Code.Should().Be("ingredient_soft_deleted");
        body.Id.Should().Be(deleted.Id);

        // Then: nothing was written – the soft-deleted row is unchanged (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo([deleted]);
    }

    // @US-904-edge-case: "Gelöschte Zutat mit gleichem Namen anlegen reaktiviert diese" (Szenario 1) +
    // "Reaktivierung übernimmt neue Einheit" (Szenario 2) + "...abweichender Schreibweise" (Szenario 3)
    // – dieselbe Invariante (Restore übernimmt Name+Einheit UNBEDINGT aus dem Request, ADR-S051-4/
    // ADR-S111-1), nur Setup/Erwartung variieren -> ein parametrisierter Test.
    [Theory]
    [InlineData("Butter", "g", "Butter", "g")]
    [InlineData("Butter", "Würfel", "Butter", "g")]
    [InlineData("mehl", "g", "Mehl", "g")]
    public async Task US904_EdgeCase_RestoreIngredient_SoftDeletedRow_Returns200AndAppliesRequestValues(
        string storedName, string storedUnit, string requestName, string requestUnit)
    {
        // Given: a soft-deleted ingredient with the stored name/unit
        var deleted = new IngredientDbType
        {
            Id = Guid.CreateVersion7(), Name = storedName, BaseUnit = storedUnit, DeletedAt = DateTimeOffset.UtcNow,
        };
        Db.Ingredients.Add(deleted);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        // The restore request runs against a DIFFERENT (request-scoped) DbContext instance – clear the
        // test context's tracker so the later full-state read below reflects the DB, not the stale
        // in-memory "deleted" instance that EF's identity resolution would otherwise return unchanged.
        Db.ChangeTracker.Clear();

        // When: the ingredient is restored with the request name/unit
        var response = await RestoreIngredientAsync(deleted.Id, requestName, requestUnit);

        // Then: 200 OK with the request values (ADR-S111-1)
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be(requestName);
        body.BaseUnit.Should().Be(requestUnit);

        // Then: the row is active again with the request values (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = deleted.Id, Name = requestName, BaseUnit = requestUnit }]);
    }

    // @US-904-edge-case: "Reaktivierung gelingt auch wenn Zutat parallel mit denselben Daten
    // wiederhergestellt wurde" (Szenario 4) – der Server-seitige Teil: ein Restore auf eine bereits
    // AKTIVE Zeile mit exakt identischen Werten ist idempotent (200, kein Schreibvorgang), weil es
    // nichts zu schützen gibt (ADR-S111-1). Das E2E erreicht diese Konstellation nur über ein
    // künstliches Zeitfenster (Route-Interception) – hier direkt: aktive Zeile seeden, Restore mit
    // identischen Werten aufrufen.
    [Fact]
    public async Task US904_EdgeCase_RestoreIngredient_ActiveRowWithIdenticalValues_Returns200()
    {
        // Given: an active ingredient
        var (created, _) = await CreateIngredientAsync("Koriander", "Bund");

        // When: the ingredient is restored with EXACTLY the same name/unit
        var response = await RestoreIngredientAsync(created.Id, "Koriander", "Bund");

        // Then: 200 OK, no conflict – the target state was already reached
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Koriander");
        body.BaseUnit.Should().Be("Bund");

        // Then: the row remains unchanged and active (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = created.Id, Name = "Koriander", BaseUnit = "Bund" }]);
    }

    // @US-904-error: "Reaktivierung meldet Konflikt wenn die Zutat parallel mit anderen Daten
    // wiederhergestellt wurde" (Szenario 5) – ein Restore auf eine bereits AKTIVE Zeile mit
    // ABWEICHENDEN Werten überschreibt nicht fremde Werte, sondern meldet 409 mit dem gespeicherten
    // Stand (ADR-S111-1/ADR-S111-3 – der Anzeigetext selbst ist Frontend-Sache).
    [Fact]
    public async Task US904_Error_RestoreIngredient_ActiveRowWithDifferentValues_Returns409WithAlreadyActiveConflictBody()
    {
        // Given: an active ingredient (its real xmin ETag from creation)
        var (created, etag) = await CreateIngredientAsync("Koriander", "Töpfchen");

        // When: the ingredient is restored with a DIFFERENT unit ("Bund" vs. stored "Töpfchen")
        var response = await RestoreIngredientAsync(created.Id, "Koriander", "Bund");

        // Then: 409 Conflict with the SAVED (not the requested) values (ADR-S111-1)
        response.StatusCode.Should().Be(HttpStatusCode.Conflict);
        var body = await response.Content.ReadFromJsonAsync<AlreadyActiveConflictResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Code.Should().Be("ingredient_already_active");
        body.Ingredient.Id.Should().Be(created.Id);
        body.Ingredient.Name.Should().Be("Koriander");
        body.Ingredient.BaseUnit.Should().Be("Töpfchen");
        // The 409 path writes nothing -> xmin is unchanged, so the etag must equal the creation-time one
        // exactly (not just "look like" an etag – a hardcoded well-formed string must not survive).
        body.Ingredient.Etag.Should().Be(etag);

        // Then: nothing was overwritten – the saved values stay unchanged (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = created.Id, Name = "Koriander", BaseUnit = "Töpfchen" }]);
    }

    // ADR-S108-1: IngredientDto.etag ist ausdrücklich die If-Match-Quelle für ein nachfolgendes DELETE.
    // Kein bisheriger Test pinnt, dass der Restore-200-Body einen FRISCHEN, brauchbaren ETag liefert –
    // der Endpoint liest xmin nach SaveChangesAsync und verlässt sich darauf, dass EF/Npgsql die
    // store-generierte Shadow-Property nachlädt. Hält das nicht mehr, liefert der Restore einen
    // veralteten ETag und ein Client bekäme beim folgenden DELETE unbemerkt ein 412. Kategorie-1-
    // Protokolltest (ADR-S106-3): kein treibendes Gherkin-Szenario.
    [Fact]
    public async Task RestoreIngredient_SoftDeletedRow_Returns200WithFreshEtagUsableForSubsequentDelete()
    {
        // Given: a soft-deleted ingredient
        var (created, etag) = await CreateIngredientAsync("Liebstöckel", "Bund");
        var deleteResponse = await DeleteIngredientAsync(created.Id, etag);
        deleteResponse.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // When: the ingredient is restored
        var restoreResponse = await RestoreIngredientAsync(created.Id, "Liebstöckel", "Bund");
        restoreResponse.StatusCode.Should().Be(HttpStatusCode.OK);
        var restored = await restoreResponse.Content.ReadFromJsonAsync<IngredientWithEtagResponse>(TestContext.Current.CancellationToken);
        restored.Should().NotBeNull();

        // When: the ingredient is deleted again using the ETag FROM THE RESTORE RESPONSE BODY
        var response = await DeleteIngredientAsync(created.Id, restored.Etag);

        // Then: 204 No Content – the restore's etag is a valid If-Match for the row's current state
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // Then: the row is soft-deleted again (full-state DB assertion)
        await AssertSoftDeletedAsync(new IngredientDbType { Id = created.Id, Name = "Liebstöckel", BaseUnit = "Bund" });
    }
}

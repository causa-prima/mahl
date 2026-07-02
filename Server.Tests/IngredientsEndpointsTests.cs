using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace mahl.Server.Tests;

public class IngredientsEndpointsTests : EndpointsTestsBase
{
#pragma warning disable CA1812 // instantiated by JSON deserializer via reflection
    private sealed record IngredientResponse(Guid Id, string Name, string DefaultUnit);
    private sealed record CreateIngredientRequest(string Name, string DefaultUnit);
    private sealed record ValidationErrorResponse(Dictionary<string, string[]> Errors);
#pragma warning restore CA1812

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
        var request = new CreateIngredientRequest(Name: "Tomaten", DefaultUnit: "Stück");

        // When: ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created with the created ingredient as body (ADR-S068-1)
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Tomaten");
        body.DefaultUnit.Should().Be("Stück");

        // Then: Location header points to the new resource (ADR-S068-1)
        response.Headers.Location.Should().Be($"/api/ingredients/{body.Id}");

        // Then: the ingredient is persisted (full-state DB assertion) with the server-generated id
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = "Tomaten", DefaultUnit = "Stück" }]);
    }

    [Fact]
    public async Task US904_HappyPath_GetIngredients_AfterCreate_ReturnsCreatedIngredient()
    {
        // Given: an ingredient was created
        var request = new CreateIngredientRequest(Name: "Tomaten", DefaultUnit: "Stück");
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
            [new IngredientResponse(Id: created.Id, Name: "Tomaten", DefaultUnit: "Stück")]);
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
        var request = new CreateIngredientRequest(Name: "  Oregano  ", DefaultUnit: "  g  ");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 201 Created and the response body carries the TRIMMED values (no surrounding whitespace)
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Name.Should().Be("Oregano");
        body.DefaultUnit.Should().Be("g");

        // Then: the persisted row stores the trimmed values (full-state DB assertion)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEquivalentTo(
            [new IngredientDbType { Id = body.Id, Name = "Oregano", DefaultUnit = "g" }]);
    }

    // Same invariant ("Pflichtfeld leer oder nur Whitespace -> 422 feld-keyed"), nur Input variiert
    // -> ein parametrisierter Test (docs/process/tdd-process.md "Parametrisierte Tests").
    // ADR-S051-1: Strings werden vor der Validierung getrimmt -> "   " ist nach Trimming leer.
    [Theory]
    [InlineData("", "g", "name", "Name darf nicht leer sein.")]
    [InlineData("   ", "g", "name", "Name darf nicht leer sein.")]
    [InlineData("Salz", "", "defaultUnit", "Einheit darf nicht leer sein.")]
    [InlineData("Salz", "   ", "defaultUnit", "Einheit darf nicht leer sein.")]
    public async Task US904_Error_CreateIngredient_InvalidInput_Returns422WithFieldKeyedError(
        string name, string unit, string expectedKey, string expectedMessage)
    {
        // Given: a request whose required field is empty or whitespace-only
        var request = new CreateIngredientRequest(Name: name, DefaultUnit: unit);

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

    // Eigener Test (nicht weitere InlineData der Single-Field-Theory): die Invariante ist hier der
    // collect-all-Merge – BEIDE unabhängigen Pflichtfelder werden validiert und ihre Fehler GLEICHZEITIG
    // gemeldet (ADR-S000-1 collect-all, gültig laut ADR-S090-1). Die Single-Field-Theory pinnt nur je EINEN Key.
    [Fact]
    public async Task US904_Error_CreateIngredient_BothFieldsEmpty_Returns422WithBothFieldKeyedErrors()
    {
        // Given: a request whose name AND unit are both empty
        var request = new CreateIngredientRequest(Name: "", DefaultUnit: "");

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
            ["defaultUnit"] = ["Einheit darf nicht leer sein."],
        });

        // Then: nothing is persisted – the ingredient list stays unchanged (empty)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }
}

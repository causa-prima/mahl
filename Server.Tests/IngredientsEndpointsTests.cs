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

    [Fact]
    public async Task US904_Error_CreateIngredient_EmptyName_Returns422WithFieldKeyedError()
    {
        // Given: a request with an empty name and a valid unit
        var request = new CreateIngredientRequest(Name: "", DefaultUnit: "g");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 422 Unprocessable Entity (ADR-S090-1: status must be 422, not 400)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        // Then: field-keyed error body maps the "name" field to its message (ADR-S090-1, ADR-S051-2)
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["name"] = ["Name darf nicht leer sein."],
        });

        // Then: nothing is persisted – the ingredient list stays unchanged (empty)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }

    [Fact]
    public async Task US904_Error_CreateIngredient_EmptyUnit_Returns422WithFieldKeyedError()
    {
        // Given: a request with a valid name and an empty unit
        var request = new CreateIngredientRequest(Name: "Salz", DefaultUnit: "");

        // When: the ingredient is created
        var response = await Client.PostAsJsonAsync("/api/ingredients", request, TestContext.Current.CancellationToken);

        // Then: 422 Unprocessable Entity (ADR-S090-1: status must be 422, not 400)
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        // Then: field-keyed error body maps the "defaultUnit" field to its message (ADR-S090-1, ADR-S051-2)
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["defaultUnit"] = ["Einheit darf nicht leer sein."],
        });

        // Then: nothing is persisted – the ingredient list stays unchanged (empty)
        var persisted = await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken);
        persisted.Should().BeEmpty();
    }
}

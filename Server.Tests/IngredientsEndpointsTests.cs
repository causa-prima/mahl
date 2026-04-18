using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Server.Tests.Helpers;
using Xunit;

namespace mahl.Server.Tests;

public class IngredientsEndpointsTests : EndpointsTestsBase
{
#pragma warning disable CA1812 // instantiated by JSON deserializer via reflection
    private sealed record IngredientResponse(Guid Id, string Name, string DefaultUnit, bool AlwaysInStock);
#pragma warning restore CA1812

    [Fact]
    public async Task US904_HappyPath_GetIngredients_EmptyDb_Returns200WithEmptyList()
    {
        var response = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse[]>(TestContext.Current.CancellationToken);
        body.Should().BeEmpty();
    }
}

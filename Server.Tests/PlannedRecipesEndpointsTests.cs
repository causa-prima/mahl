using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Server.Tests.Helpers;
using Xunit;

namespace mahl.Server.Tests;

[Collection(PostgresCollectionDefinition.Name)]
public class PlannedRecipesEndpointsTests(PostgresContainerFixture postgres) : EndpointsTestsBase(postgres)
{
    // Szenario: Ohne Vormerkungen zeigt die Vorgemerkt-Seite einen Hinweis
    [Fact]
    public async Task US803_HappyPath_GetPlannedRecipes_NonePlannedButRecipeExists_Returns200WithEmptyList()
    {
        // Given: das Rezept "Pfannkuchen" existiert, kein Rezept ist vorgemerkt
        Db.Recipes.Add(ARecipe("Pfannkuchen"));
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When
        var response = await Client.GetAsync("/api/planned-recipes", TestContext.Current.CancellationToken);

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<object[]>(TestContext.Current.CancellationToken);
        body.Should().BeEmpty();
    }
}

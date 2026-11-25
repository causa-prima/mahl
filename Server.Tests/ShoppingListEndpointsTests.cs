using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using Xunit;

namespace mahl.Server.Tests;

[Collection(PostgresCollectionDefinition.Name)]
public class ShoppingListEndpointsTests(PostgresContainerFixture postgres) : EndpointsTestsBase(postgres)
{
    // Szenario: Eine noch nie gefüllte Einkaufsliste zeigt einen Hinweis
    [Fact]
    public async Task US201_HappyPath_GetShoppingList_NeverFilled_Returns200WithEmptyList()
    {
        // Given: das Rezept "Pfannkuchen" ist vorgemerkt, die Einkaufsliste ist leer (noch nie gefüllt)
        var pancake = ARecipe("Pfannkuchen");
        Db.Recipes.Add(pancake);
        Db.PlannedRecipes.Add(new PlannedRecipeDbType { RecipeId = pancake.Id });
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When
        var response = await Client.GetAsync("/api/shopping-list", TestContext.Current.CancellationToken);

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<object[]>(TestContext.Current.CancellationToken);
        body.Should().BeEmpty();
    }
}

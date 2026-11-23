using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using Microsoft.EntityFrameworkCore;
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

    // Szenario: Ein Rezept vormerken
    // Beispiel: alle
    [Fact]
    public async Task US803_HappyPath_PutPlannedRecipe_RecipeExists_Returns204AndPlansOnlyThatRecipe()
    {
        // Given: die Rezepte "Kartoffelsuppe" und "Pfannkuchen" existieren, kein Rezept ist vorgemerkt
        var soup = ARecipe("Kartoffelsuppe");
        var pancake = ARecipe("Pfannkuchen");
        Db.Recipes.AddRange(soup, pancake);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When
        var response = await Client.PutAsync($"/api/planned-recipes/{pancake.Id}", content: null, TestContext.Current.CancellationToken);

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        (await ReadPlannedRecipesAsync())
            .Should().BeEquivalentTo([new PlannedRecipeDbType { RecipeId = pancake.Id }]);
        var body = await Client.GetFromJsonAsync<RecipeSummaryResponse[]>("/api/planned-recipes", TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo([new RecipeSummaryResponse(Id: pancake.Id, Title: "Pfannkuchen")]);
    }

    // Szenario: Ein inzwischen anderswo vorgemerktes Rezept vormerken
    [Fact]
    public async Task US803_EdgeCase_PutPlannedRecipe_AlreadyPlanned_Returns204AndStaysPlannedOnce()
    {
        // Given: das Rezept "Pfannkuchen" existiert und ist (auf einem anderen Gerät) schon vorgemerkt
        var pancake = ARecipe("Pfannkuchen");
        Db.Recipes.Add(pancake);
        Db.PlannedRecipes.Add(new PlannedRecipeDbType { RecipeId = pancake.Id });
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When
        var response = await Client.PutAsync($"/api/planned-recipes/{pancake.Id}", content: null, TestContext.Current.CancellationToken);

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        (await ReadPlannedRecipesAsync())
            .Should().BeEquivalentTo([new PlannedRecipeDbType { RecipeId = pancake.Id }]);
    }

    // Szenario: Die Vorgemerkt-Seite zeigt nur die vorgemerkten Rezepte, alphabetisch
    [Fact]
    public async Task US803_HappyPath_GetPlannedRecipes_SeveralPlanned_ReturnsOnlyPlannedAlphabetically()
    {
        // Given: vier Rezepte in dieser Anlage-Reihenfolge
        var pancake = ARecipe("Pfannkuchen");
        var spaghetti = ARecipe("Spaghetti Bolognese");
        var lentils = ARecipe("Linsensalat");
        var soup = ARecipe("Kartoffelsuppe");
        // je ein Save, damit die Insert-Reihenfolge feststeht und ein unsortierter Endpoint sie sichtbar durchreicht
        foreach (var recipe in new[] { pancake, spaghetti, lentils, soup })
        {
            Db.Recipes.Add(recipe);
            await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        }
        // And: Spaghetti, Kartoffelsuppe und Pfannkuchen in dieser Reihenfolge vorgemerkt
        foreach (var recipe in new[] { spaghetti, soup, pancake })
        {
            var put = await Client.PutAsync($"/api/planned-recipes/{recipe.Id}", content: null, TestContext.Current.CancellationToken);
            put.StatusCode.Should().Be(HttpStatusCode.NoContent);
        }

        // When
        var body = await Client.GetFromJsonAsync<RecipeSummaryResponse[]>("/api/planned-recipes", TestContext.Current.CancellationToken);

        // Then
        body.Should().BeEquivalentTo(
            [
                new RecipeSummaryResponse(Id: soup.Id, Title: "Kartoffelsuppe"),
                new RecipeSummaryResponse(Id: pancake.Id, Title: "Pfannkuchen"),
                new RecipeSummaryResponse(Id: spaghetti.Id, Title: "Spaghetti Bolognese"),
            ],
            o => o.WithStrictOrdering());
    }

    private async Task<List<PlannedRecipeDbType>> ReadPlannedRecipesAsync() =>
        await Db.PlannedRecipes.AsNoTracking().ToListAsync(TestContext.Current.CancellationToken);
}

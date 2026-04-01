namespace mahl.Server.Tests;

using FluentAssertions;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Dtos;
using System.Net;
using System.Net.Http.Json;

[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[Parallelizable(ParallelScope.All)]
[TestFixture]
public class WeeklyPoolEndpointsTests : EndpointsTestsBase
{
    [Test]
    public async Task GetAll_EmptyPool_Returns200WithEmptyList()
    {
        var response = await Client.GetAsync("/api/weekly-pool");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var items = await response.Content.ReadFromJsonAsync<List<WeeklyPoolEntryDto>>();
        items.Should().BeEmpty();
    }

    // POST /api/weekly-pool

    [Test]
    public async Task Post_ValidRecipeId_Returns201AndPersists()
    {
        SeedRecipes([ARecipe("Tomatensalat")]);
        var recipeId = GetAllRecipesFromDb()[0].Id;

        var beforePost = DateTimeOffset.UtcNow;
        var response = await Client.PostAsJsonAsync("/api/weekly-pool", new AddToPoolDto(RecipeId: recipeId));

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<WeeklyPoolEntryDto>();
        var entry = GetAllPoolEntriesFromDb()[0];
        response.Headers.Location!.ToString().Should().Be($"/api/weekly-pool/{entry.Id}");
        body.Should().BeEquivalentTo(new WeeklyPoolEntryDto(Id: entry.Id, RecipeId: recipeId, RecipeTitle: "", AddedAt: entry.AddedAt));
        GetAllPoolEntriesFromDb().Should().BeEquivalentTo(
            [new WeeklyPoolEntryDbType { Id = body!.Id, RecipeId = recipeId }],
            o => o.Excluding(x => x.AddedAt).Excluding(x => x.Recipe));
        entry.AddedAt.Should().BeCloseTo(beforePost, TimeSpan.FromSeconds(1));
    }

    [Test]
    public async Task Post_NonExistingRecipeId_Returns422()
    {
        var stateBeforeAction = GetAllPoolEntriesFromDb();

        var response = await Client.PostAsJsonAsync("/api/weekly-pool", new AddToPoolDto(RecipeId: Guid.NewGuid()));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        var body = await response.Content.ReadFromJsonAsync<string>();
        body.Should().Be("Rezept nicht gefunden.");
        GetAllPoolEntriesFromDb().Should().BeEquivalentTo(stateBeforeAction);
    }

    [Test]
    public async Task Post_SoftDeletedRecipeId_Returns422()
    {
        SeedRecipes([ARecipe(deletedAt: DateTimeOffset.UtcNow)]);
        var recipeId = GetAllRecipesFromDb()[0].Id;
        var stateBeforeAction = GetAllPoolEntriesFromDb();

        var response = await Client.PostAsJsonAsync("/api/weekly-pool", new AddToPoolDto(RecipeId: recipeId));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        var body = await response.Content.ReadFromJsonAsync<string>();
        body.Should().Be("Rezept nicht gefunden.");
        GetAllPoolEntriesFromDb().Should().BeEquivalentTo(stateBeforeAction);
    }

    [Test]
    public async Task Post_DuplicateRecipeId_Returns409()
    {
        SeedRecipes([ARecipe("Tomatensalat")]);
        var recipeId = GetAllRecipesFromDb()[0].Id;
        SeedPool([new WeeklyPoolEntryDbType { RecipeId = recipeId }]);
        var stateBeforeAction = GetAllPoolEntriesFromDb();

        var response = await Client.PostAsJsonAsync("/api/weekly-pool", new AddToPoolDto(RecipeId: recipeId));

        response.StatusCode.Should().Be(HttpStatusCode.Conflict);
        var body = await response.Content.ReadFromJsonAsync<string>();
        body.Should().Be("Rezept ist bereits im Wochenplan.");
        GetAllPoolEntriesFromDb().Should().BeEquivalentTo(stateBeforeAction);
    }

    // DELETE /api/weekly-pool/recipes/{recipeId}

    [Test]
    public async Task Delete_ExistingRecipeId_Returns204AndRemovesEntry()
    {
        SeedRecipes([ARecipe("Salat"), ARecipe("Suppe")]);
        var recipes = GetAllRecipesFromDb();
        SeedPool([
            new WeeklyPoolEntryDbType { RecipeId = recipes[0].Id },
            new WeeklyPoolEntryDbType { RecipeId = recipes[1].Id },
        ]);
        var entryForRecipe1 = GetAllPoolEntriesFromDb().Single(e => e.RecipeId == recipes[1].Id);

        var response = await Client.DeleteAsync($"/api/weekly-pool/recipes/{recipes[0].Id}");

        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        GetAllPoolEntriesFromDb().Should().BeEquivalentTo(
            [new WeeklyPoolEntryDbType { Id = entryForRecipe1.Id, RecipeId = recipes[1].Id, AddedAt = entryForRecipe1.AddedAt }],
            o => o.Excluding(x => x.Recipe));
    }

    [Test]
    public async Task GetAll_ReturnsExistingEntries()
    {
        var recipe = ARecipe("Tomatensalat");
        SeedRecipes([recipe]);
        var recipeId = GetAllRecipesFromDb()[0].Id;
        SeedPool([new WeeklyPoolEntryDbType { RecipeId = recipeId }]);

        var items = await Client.GetFromJsonAsync<List<WeeklyPoolEntryDto>>("/api/weekly-pool");

        var entry = GetAllPoolEntriesFromDb()[0];
        items!.Should().BeEquivalentTo(
            [new WeeklyPoolEntryDto(Id: entry.Id, RecipeId: recipeId, RecipeTitle: "Tomatensalat", AddedAt: entry.AddedAt)]);
    }
}

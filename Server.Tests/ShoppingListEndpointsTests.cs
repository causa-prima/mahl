namespace mahl.Server.Tests;

using FluentAssertions;
using mahl.Server.Dtos;
using System.Net;
using System.Net.Http.Json;

[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[Parallelizable(ParallelScope.All)]
[TestFixture]
public class ShoppingListEndpointsTests : EndpointsTestsBase
{
    // POST /api/shopping-list/generate

    [Test]
    public async Task Generate_WithPoolEntries_Returns200WithItems()
    {
        var tomato = AnIngredient("Tomate", "Stück");
        var recipe = ARecipe("Tomatensalat", ingredients: [ARecipeIngredient(tomato, 3, "Stück")]);
        SeedRecipes([recipe]);
        var recipeId = GetAllRecipesFromDb()[0].Id;
        SeedPool([new Server.Data.DatabaseTypes.WeeklyPoolEntryDbType { RecipeId = recipeId }]);

        var response = await Client.PostAsync("/api/shopping-list/generate", null);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var result = await response.Content.ReadFromJsonAsync<ShoppingListResponseDto>();
        var item = GetAllShoppingItemsFromDb()[0];
        var tomatoId = GetAllIngredientsFromDb().Single(i => string.Equals(i.Name, "Tomate", StringComparison.Ordinal)).Id;
        result.Should().BeEquivalentTo(new ShoppingListResponseDto(
            OpenItems: [new ShoppingListItemDto(Id: item.Id, IngredientId: tomatoId, IngredientName: "Tomate", Quantity: 3m, Unit: "Stück", BoughtAt: null)],
            BoughtItems: []));
    }

    // PUT /api/shopping-list/items/{id}/check

    [Test]
    public async Task Check_ExistingItem_Returns204AndSetsBoughtAt()
    {
        SeedRecipes([ARecipe()]);
        var recipeId = GetAllRecipesFromDb()[0].Id;
        SeedPool([new Server.Data.DatabaseTypes.WeeklyPoolEntryDbType { RecipeId = recipeId }]);
        await Client.PostAsync("/api/shopping-list/generate", null);
        var stateBeforeAction = GetAllShoppingItemsFromDb();
        var itemId = stateBeforeAction[0].Id;
        var beforeCheck = DateTimeOffset.UtcNow;

        var response = await Client.PutAsync($"/api/shopping-list/items/{itemId}/check", null);

        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        var inDb = GetAllShoppingItemsFromDb();
        inDb.Should().BeEquivalentTo(stateBeforeAction, options => options.Excluding(x => x.BoughtAt));
        inDb[0].BoughtAt!.Value.Should().BeCloseTo(beforeCheck, TimeSpan.FromSeconds(1));
    }

    [Test]
    public async Task Check_NonExistingItem_Returns404()
    {
        var response = await Client.PutAsync($"/api/shopping-list/items/{Guid.NewGuid()}/check", null);

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    // PUT /api/shopping-list/items/{id}/uncheck

    [Test]
    public async Task Uncheck_NonExistingItem_Returns404()
    {
        var response = await Client.PutAsync($"/api/shopping-list/items/{Guid.NewGuid()}/uncheck", null);

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Test]
    public async Task Uncheck_CheckedItem_Returns204AndClearsBoughtAt()
    {
        SeedRecipes([ARecipe()]);
        var recipeId = GetAllRecipesFromDb()[0].Id;
        SeedPool([new Server.Data.DatabaseTypes.WeeklyPoolEntryDbType { RecipeId = recipeId }]);
        await Client.PostAsync("/api/shopping-list/generate", null);
        var itemId = GetAllShoppingItemsFromDb()[0].Id;
        await Client.PutAsync($"/api/shopping-list/items/{itemId}/check", null);
        var stateBeforeAction = GetAllShoppingItemsFromDb();

        var response = await Client.PutAsync($"/api/shopping-list/items/{itemId}/uncheck", null);

        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        var inDb = GetAllShoppingItemsFromDb();
        inDb.Should().BeEquivalentTo(stateBeforeAction, options => options.Excluding(x => x.BoughtAt));
        inDb[0].BoughtAt.Should().BeNull();
    }

    // GET /api/shopping-list

    [Test]
    public async Task Get_ReturnsOpenAndBoughtItemsSeparately()
    {
        SeedRecipes([
            ARecipe("Salat", ingredients: [ARecipeIngredient(AnIngredient("Tomate", "Stück"), 2, "Stück")]),
            ARecipe("Suppe", ingredients: [ARecipeIngredient(AnIngredient("Karotte", "Stück"), 3, "Stück")])
        ]);
        var recipes = GetAllRecipesFromDb();
        SeedPool([
            new Server.Data.DatabaseTypes.WeeklyPoolEntryDbType { RecipeId = recipes[0].Id },
            new Server.Data.DatabaseTypes.WeeklyPoolEntryDbType { RecipeId = recipes[1].Id }
        ]);
        await Client.PostAsync("/api/shopping-list/generate", null);
        var items = GetAllShoppingItemsFromDb();
        var tomatoItemId = items.Single(i => string.Equals(i.Unit, "Stück", StringComparison.Ordinal) && i.Quantity == 2).Id;
        await Client.PutAsync($"/api/shopping-list/items/{tomatoItemId}/check", null);

        var result = await Client.GetFromJsonAsync<ShoppingListResponseDto>("/api/shopping-list");

        var dbIngredients = GetAllIngredientsFromDb();
        var tomatoIngredientId = dbIngredients.Single(i => string.Equals(i.Name, "Tomate", StringComparison.Ordinal)).Id;
        var karotteIngredientId = dbIngredients.Single(i => string.Equals(i.Name, "Karotte", StringComparison.Ordinal)).Id;
        var dbItems = GetAllShoppingItemsFromDb();
        var tomatoItem = dbItems.Single(i => i.IngredientId == tomatoIngredientId);
        var karotteItem = dbItems.Single(i => i.IngredientId == karotteIngredientId);
        result.Should().BeEquivalentTo(new ShoppingListResponseDto(
            OpenItems: [new ShoppingListItemDto(Id: karotteItem.Id, IngredientId: karotteIngredientId, IngredientName: "Karotte", Quantity: 3m, Unit: "Stück", BoughtAt: null)],
            BoughtItems: [new ShoppingListItemDto(Id: tomatoItem.Id, IngredientId: tomatoIngredientId, IngredientName: "Tomate", Quantity: 2m, Unit: "Stück", BoughtAt: tomatoItem.BoughtAt)]));
    }

    [Test]
    public async Task Get_EmptyList_Returns200WithEmptyLists()
    {
        var response = await Client.GetAsync("/api/shopping-list");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var result = await response.Content.ReadFromJsonAsync<ShoppingListResponseDto>();
        result.Should().BeEquivalentTo(new ShoppingListResponseDto(OpenItems: [], BoughtItems: []));
    }

    [Test]
    public async Task Generate_EmptyPool_Returns200WithEmptyList()
    {
        var response = await Client.PostAsync("/api/shopping-list/generate", null);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var result = await response.Content.ReadFromJsonAsync<ShoppingListResponseDto>();
        result.Should().BeEquivalentTo(new ShoppingListResponseDto(OpenItems: [], BoughtItems: []));
    }

    [Test]
    public async Task Generate_WithExistingItems_ReplacesAllItems()
    {
        SeedIngredients([AnIngredient("Altbestand", "Stück")]);
        var oldIngredientId = GetAllIngredientsFromDb().Single(i => string.Equals(i.Name, "Altbestand", StringComparison.Ordinal)).Id;
        SeedShoppingListItems([new Server.Data.DatabaseTypes.ShoppingListItemDbType { IngredientId = oldIngredientId, Quantity = 5m, Unit = "Stück" }]);

        SeedRecipes([ARecipe("Salat", ingredients: [ARecipeIngredient(AnIngredient("Tomate", "Stück"), 2, "Stück")])]);
        var recipeId = GetAllRecipesFromDb()[0].Id;
        SeedPool([new Server.Data.DatabaseTypes.WeeklyPoolEntryDbType { RecipeId = recipeId }]);

        var beforeGenerate = DateTimeOffset.UtcNow;
        await Client.PostAsync("/api/shopping-list/generate", null);

        var tomatoIngredientId = GetAllIngredientsFromDb().Single(i => string.Equals(i.Name, "Tomate", StringComparison.Ordinal)).Id;
        var items = GetAllShoppingItemsFromDb();
        items.Should().BeEquivalentTo(
            [new Server.Data.DatabaseTypes.ShoppingListItemDbType { IngredientId = tomatoIngredientId, Quantity = 2m, Unit = "Stück", BoughtAt = null }],
            o => o.Excluding(x => x.Id).Excluding(x => x.GeneratedAt).Excluding(x => x.Ingredient));
        items[0].GeneratedAt.Should().BeCloseTo(beforeGenerate, TimeSpan.FromSeconds(1));
    }
}

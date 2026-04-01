namespace mahl.Server.Tests;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Dtos;
using mahl.Server.Tests.Helpers;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;
using Serilog.Events;
using System.Collections.Concurrent;

[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[Parallelizable(ParallelScope.All)]
[TestFixture]
public class EndpointsTestsBase : IAsyncDisposable
{
    protected HttpClient Client { get; }
    private readonly TestWebApplicationFactory _factory;
    private readonly string _testId;

    public EndpointsTestsBase()
    {
        _testId = Guid.NewGuid().ToString();
        ParallelTestLogStore.Logs[_testId] = new ConcurrentBag<LogEvent>();
        _factory = new TestWebApplicationFactory(_testId);
        Client = _factory.CreateClient();
    }

    protected static CreateRecipeDto ACreateRecipeDto(
        Guid ingredientId,
        string title = "Tomatensalat",
        Uri? sourceUrl = null,
        IReadOnlyList<CreateRecipeIngredientDto>? ingredients = null,
        IReadOnlyList<CreateStepDto>? steps = null) =>
        new(title, sourceUrl,
            ingredients ?? [new CreateRecipeIngredientDto(ingredientId, 200, "g")],
            steps ?? [new CreateStepDto("Tomaten schneiden."), new CreateStepDto("Würzen.")]);

    protected static RecipeIngredientDbType ARecipeIngredient(
        IngredientDbType ingredient,
        decimal? quantity = 200,
        string? unit = "g") =>
        new() { Ingredient = ingredient, Quantity = quantity, Unit = unit };

    protected static RecipeDbType ARecipe(
        string title = "Tomatensalat",
        string? sourceUrl = null,
        IReadOnlyList<RecipeIngredientDbType>? ingredients = null,
        IReadOnlyList<StepDbType>? steps = null,
        DateTimeOffset? deletedAt = null)
    {
        var defaultIngredient = AnIngredient("Tomate", "Stück");
        return new()
        {
            Title = title,
            SourceUrl = sourceUrl,
            Ingredients = ingredients?.ToList() ?? [ARecipeIngredient(defaultIngredient)],
            Steps = steps?.ToList() ?? [new StepDbType { StepNumber = 1, Instruction = "Tomaten schneiden." }],
            DeletedAt = deletedAt
        };
    }

    protected static IngredientDbType AnIngredient(
        string name = "Butter",
        string unit = "g",
        bool alwaysInStock = false,
        DateTimeOffset? deletedAt = null) =>
        new() { Name = name, DefaultUnit = unit, AlwaysInStock = alwaysInStock, DeletedAt = deletedAt };

    protected void SeedRecipes(IEnumerable<RecipeDbType> recipes)
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        db.Recipes.AddRange(recipes);
        db.SaveChanges();
    }

    protected IReadOnlyList<RecipeDbType> GetAllRecipesFromDb()
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        return db.Recipes.ToList();
    }

    protected void SeedPool(IEnumerable<WeeklyPoolEntryDbType> entries)
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        db.WeeklyPoolEntries.AddRange(entries);
        db.SaveChanges();
    }

    protected IReadOnlyList<WeeklyPoolEntryDbType> GetAllPoolEntriesFromDb()
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        return db.WeeklyPoolEntries.ToList();
    }

    protected void SeedShoppingListItems(IEnumerable<ShoppingListItemDbType> items)
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        db.ShoppingListItems.AddRange(items);
        db.SaveChanges();
    }

    protected IReadOnlyList<ShoppingListItemDbType> GetAllShoppingItemsFromDb()
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        return db.ShoppingListItems.ToList();
    }

    protected void SeedIngredients(IEnumerable<IngredientDbType> ingredients)
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        db.Ingredients.AddRange(ingredients);
        db.SaveChanges();
    }

    protected IReadOnlyList<IngredientDbType> GetAllIngredientsFromDb()
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        return db.Ingredients.ToList();
    }

    protected IReadOnlyList<StepDbType> GetAllStepsFromDb()
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        return db.Steps.ToList();
    }

    protected IReadOnlyList<RecipeIngredientDbType> GetAllRecipeIngredientsFromDb()
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        return db.RecipeIngredients.ToList();
    }

    public async ValueTask DisposeAsync()
    {
        using var scope = _factory.Services.CreateScope();
        var dbContext = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        await dbContext.Database.EnsureDeletedAsync();
        Client.Dispose();
        await _factory.DisposeAsync();
        ParallelTestLogStore.Logs.TryRemove(_testId, out _);
        GC.SuppressFinalize(this);
    }
}

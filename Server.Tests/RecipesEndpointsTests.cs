namespace mahl.Server.Tests;

using FluentAssertions;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Dtos;
using Microsoft.AspNetCore.Mvc;
using System.Net;
using System.Net.Http.Json;

[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[Parallelizable(ParallelScope.All)]
[TestFixture]
public class RecipesEndpointsTests : EndpointsTestsBase
{
    [Test]
    public async Task GetAll_EmptyDb_Returns200WithEmptyList()
    {
        var response = await Client.GetAsync("/api/recipes");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var items = await response.Content.ReadFromJsonAsync<List<RecipeSummaryDto>>();
        items.Should().BeEmpty();
    }

    [Test]
    public async Task GetAll_ReturnsSortedByTitle()
    {
        SeedRecipes([
            ARecipe("Zwiebelsalat"),
            ARecipe("Apfelkuchen"),
            ARecipe("Müsli"),
        ]);

        var items = await Client.GetFromJsonAsync<List<RecipeSummaryDto>>("/api/recipes");

        items!.Select(r => r.Title).Should().Equal("Apfelkuchen", "Müsli", "Zwiebelsalat");
    }

    // GET /api/recipes/{id}

    [Test]
    public async Task GetById_UnknownId_Returns404()
    {
        var response = await Client.GetAsync($"/api/recipes/{Guid.NewGuid()}");
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Test]
    public async Task GetById_SoftDeletedRecipe_Returns404()
    {
        SeedRecipes([ARecipe(deletedAt: DateTimeOffset.UtcNow)]);
        var id = GetAllRecipesFromDb()[0].Id;

        var response = await Client.GetAsync($"/api/recipes/{id}");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Test]
    public async Task GetById_ExistingId_Returns200WithCorrectData()
    {
        var ingredient = AnIngredient("Tomate", "Stück");
        SeedRecipes([ARecipe("Tomatensalat", ingredients: [ARecipeIngredient(ingredient, 3, "Stück")])]);
        var id = GetAllRecipesFromDb()[0].Id;

        var dto = await Client.GetFromJsonAsync<RecipeDto>($"/api/recipes/{id}");

        var ingredientId = GetAllIngredientsFromDb().Single(i => string.Equals(i.Name, "Tomate", StringComparison.Ordinal)).Id;
        var riId = GetAllRecipeIngredientsFromDb()[0].Id;
        var stepId = GetAllStepsFromDb()[0].Id;
        dto.Should().BeEquivalentTo(
            new RecipeDto(Id: id, Title: "Tomatensalat", SourceUrl: null,
                Ingredients: [new RecipeIngredientDto(Id: riId, IngredientId: ingredientId, IngredientName: "Tomate", Quantity: 3m, Unit: "Stück")],
                Steps: [new StepDto(Id: stepId, Instruction: "Tomaten schneiden.")]),
            options => options.WithStrictOrdering());
    }

    [Test]
    public async Task GetById_Returns200WithStepsOrderedByStepNumber()
    {
        SeedRecipes([ARecipe(steps: [
            new StepDbType { StepNumber = 2, Instruction = "Würzen." },
            new StepDbType { StepNumber = 1, Instruction = "Schneiden." },
        ])]);
        var id = GetAllRecipesFromDb()[0].Id;

        var dto = await Client.GetFromJsonAsync<RecipeDto>($"/api/recipes/{id}");

        dto!.Steps.Select(s => s.Instruction).Should().Equal("Schneiden.", "Würzen.");
    }

    // DELETE /api/recipes/{id}

    [Test]
    public async Task Delete_ExistingId_Returns204AndSoftDeletes()
    {
        SeedRecipes([ARecipe("Salat")]);
        var stateBeforeAction = GetAllRecipesFromDb();

        var response = await Client.DeleteAsync($"/api/recipes/{stateBeforeAction[0].Id}");

        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        var inDb = GetAllRecipesFromDb();
        inDb.Should().BeEquivalentTo(stateBeforeAction, options => options.Excluding(r => r.DeletedAt));
        inDb[0].DeletedAt.Should().NotBeNull();
    }

    // POST /api/recipes

    [Test]
    public async Task Post_RelativeSourceUrl_Returns422()
    {
        SeedIngredients([AnIngredient()]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.PostAsJsonAsync("/api/recipes",
            ACreateRecipeDto(ingredientId, sourceUrl: new Uri("/relative/path", UriKind.Relative)));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Post_EmptyTitle_Returns422()
    {
        SeedIngredients([AnIngredient()]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.PostAsJsonAsync("/api/recipes", ACreateRecipeDto(ingredientId, title: "  "));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Post_EmptySteps_Returns422()
    {
        SeedIngredients([AnIngredient()]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.PostAsJsonAsync("/api/recipes", ACreateRecipeDto(ingredientId, steps: []));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Post_UnknownIngredientId_Returns422()
    {
        var response = await Client.PostAsJsonAsync("/api/recipes", ACreateRecipeDto(Guid.NewGuid()));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        var body = await response.Content.ReadFromJsonAsync<string>();
        body.Should().Be("Eine oder mehrere Zutaten wurden nicht gefunden.");
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Post_NullQuantity_PersistsNullUnit()
    {
        SeedIngredients([AnIngredient("Tomate", "Stück")]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;
        var dto = new CreateRecipeDto(Title: "Salat", SourceUrl: null,
            Ingredients: [new CreateRecipeIngredientDto(IngredientId: ingredientId, Quantity: null, Unit: null)],
            Steps: [new CreateStepDto(Instruction: "Zubereiten.")]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var created = await response.Content.ReadFromJsonAsync<RecipeDto>();
        created!.Ingredients[0].Quantity.Should().BeNull();
        created.Ingredients[0].Unit.Should().BeNull();
    }

    [Test]
    public async Task Post_SoftDeletedIngredientId_Returns422()
    {
        SeedIngredients([AnIngredient(deletedAt: DateTimeOffset.UtcNow)]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.PostAsJsonAsync("/api/recipes", ACreateRecipeDto(ingredientId));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Post_ValidRecipe_Returns201WithCorrectResponseBody()
    {
        SeedIngredients([AnIngredient("Tomate", "Stück")]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;
        var dto = new CreateRecipeDto(Title: "Tomatensalat", SourceUrl: new Uri("https://example.com"),
            Ingredients: [new CreateRecipeIngredientDto(IngredientId: ingredientId, Quantity: 3, Unit: "Stück")],
            Steps: [new CreateStepDto(Instruction: "Tomaten schneiden."), new CreateStepDto(Instruction: "Würzen.")]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var created = await response.Content.ReadFromJsonAsync<RecipeDto>();
        var inDb = GetAllRecipesFromDb();
        var ingredientsInDb = GetAllRecipeIngredientsFromDb();
        var stepsInDb = GetAllStepsFromDb().OrderBy(s => s.StepNumber).ToList();
        created.Should().BeEquivalentTo(
            new RecipeDto(
                Id: inDb[0].Id,
                Title: "Tomatensalat",
                SourceUrl: new Uri("https://example.com"),
                Ingredients: [new RecipeIngredientDto(Id: ingredientsInDb[0].Id, IngredientId: ingredientId, IngredientName: "Tomate", Quantity: 3m, Unit: "Stück")],
                Steps: [new StepDto(Id: stepsInDb[0].Id, Instruction: "Tomaten schneiden."), new StepDto(Id: stepsInDb[1].Id, Instruction: "Würzen.")]
            ),
            options => options.WithStrictOrdering());
    }

    [Test]
    public async Task Post_ValidRecipe_PersistsCorrectDataToDb()
    {
        SeedIngredients([AnIngredient("Tomate", "Stück")]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;
        var dto = new CreateRecipeDto(Title: "Tomatensalat", SourceUrl: new Uri("https://example.com"),
            Ingredients: [new CreateRecipeIngredientDto(IngredientId: ingredientId, Quantity: 3, Unit: "Stück")],
            Steps: [new CreateStepDto(Instruction: "Tomaten schneiden."), new CreateStepDto(Instruction: "Würzen.")]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        var created = await response.Content.ReadFromJsonAsync<RecipeDto>();
        var inDb = GetAllRecipesFromDb();
        var ingredientsInDb = GetAllRecipeIngredientsFromDb();
        var stepsInDb = GetAllStepsFromDb().OrderBy(s => s.StepNumber).ToList();
        inDb.Should().BeEquivalentTo(
            [new RecipeDbType
            {
                Id = created!.Id,
                Title = "Tomatensalat",
                SourceUrl = "https://example.com",
                SourceImagePath = null,
                DeletedAt = null
            }],
            options => options.Excluding(x => x.Ingredients).Excluding(x => x.Steps));
        ingredientsInDb.Should().BeEquivalentTo(
            [new RecipeIngredientDbType
            {
                Id = created.Ingredients[0].Id,
                RecipeId = inDb[0].Id,
                IngredientId = ingredientId,
                Quantity = 3m,
                Unit = "Stück"
            }],
            options => options.Excluding(x => x.Recipe).Excluding(x => x.Ingredient));
        stepsInDb.Should().BeEquivalentTo(
            [
                new StepDbType { Id = created.Steps[0].Id, RecipeId = inDb[0].Id, StepNumber = 1, Instruction = "Tomaten schneiden." },
                new StepDbType { Id = created.Steps[1].Id, RecipeId = inDb[0].Id, StepNumber = 2, Instruction = "Würzen." },
            ],
            options => options.Excluding(x => x.Recipe).WithStrictOrdering());
    }

    [Test]
    public async Task Post_ValidRecipe_Returns201WithCorrectLocationHeader()
    {
        SeedIngredients([AnIngredient("Tomate", "Stück")]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.PostAsJsonAsync("/api/recipes", ACreateRecipeDto(ingredientId));

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var id = GetAllRecipesFromDb()[0].Id;
        response.Headers.Location.Should().NotBeNull();
        response.Headers.Location!.ToString().Should().Be($"/api/recipes/{id}");
    }

    [Test]
    public async Task Post_EmptyIngredients_Returns422()
    {
        var dto = new CreateRecipeDto(Title: "Tomatensalat", SourceUrl: null, Ingredients: [], Steps: [new CreateStepDto(Instruction: "Schritt 1.")]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [TestCase(0)]
    [TestCase(-1)]
    public async Task Post_NonPositiveQuantity_Returns422(decimal quantity)
    {
        SeedIngredients([AnIngredient()]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;
        var dto = ACreateRecipeDto(ingredientId,
            ingredients: [new CreateRecipeIngredientDto(IngredientId: ingredientId, Quantity: quantity, Unit: "g")]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Post_QuantityWithoutUnit_Returns422()
    {
        SeedIngredients([AnIngredient()]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;
        var dto = ACreateRecipeDto(ingredientId,
            ingredients: [new CreateRecipeIngredientDto(IngredientId: ingredientId, Quantity: 100m, Unit: null)]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [TestCase("")]
    [TestCase("   ")]
    public async Task Post_EmptyUnit_Returns422(string emptyUnit)
    {
        SeedIngredients([AnIngredient()]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;
        var dto = ACreateRecipeDto(ingredientId,
            ingredients: [new CreateRecipeIngredientDto(IngredientId: ingredientId, Quantity: 100, Unit: emptyUnit)]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [TestCase("")]
    [TestCase("   ")]
    public async Task Post_EmptyInstruction_Returns422(string emptyInstruction)
    {
        SeedIngredients([AnIngredient()]);
        var ingredientId = GetAllIngredientsFromDb()[0].Id;
        var dto = ACreateRecipeDto(ingredientId,
            steps: [new CreateStepDto(Instruction: emptyInstruction)]);

        var response = await Client.PostAsJsonAsync("/api/recipes", dto);

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        GetAllRecipesFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Delete_AlreadySoftDeleted_Returns404()
    {
        SeedRecipes([ARecipe(deletedAt: DateTimeOffset.UtcNow)]);
        var id = GetAllRecipesFromDb()[0].Id;

        var response = await Client.DeleteAsync($"/api/recipes/{id}");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Test]
    public async Task Delete_NonExistingId_Returns404()
    {
        var response = await Client.DeleteAsync($"/api/recipes/{Guid.NewGuid()}");
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Test]
    public async Task GetById_RecipeWithInvalidStoredUrl_Returns500WithProblemDetails()
    {
        SeedRecipes([ARecipe(sourceUrl: "not-a-valid-url")]);
        var id = GetAllRecipesFromDb()[0].Id;

        var response = await Client.GetAsync($"/api/recipes/{id}");

        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
        response.Content.Headers.ContentType!.MediaType.Should().Be("application/problem+json");
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Detail.Should().Be($"DB inconsistency in Recipe #{id}: Ungültige URL 'not-a-valid-url'.");
    }

    [Test]
    public async Task GetById_CorruptRecipe_Returns500WithProblemDetails()
    {
        SeedRecipes([new RecipeDbType
        {
            Title = "",
            Ingredients = [ARecipeIngredient(AnIngredient())],
            Steps = [new StepDbType { StepNumber = 1, Instruction = "Schritt." }]
        }]);
        var id = GetAllRecipesFromDb()[0].Id;

        var response = await Client.GetAsync($"/api/recipes/{id}");

        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
        response.Content.Headers.ContentType!.MediaType.Should().Be("application/problem+json");
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Detail.Should().Be($"DB inconsistency in Recipe #{id}: Titel darf nicht leer sein.");
    }

    [Test]
    public async Task GetAll_ExcludesSoftDeletedRecipes()
    {
        SeedRecipes([
            ARecipe("Aktiv"),
            ARecipe("Gelöscht", deletedAt: DateTimeOffset.UtcNow),
        ]);

        var items = await Client.GetFromJsonAsync<List<RecipeSummaryDto>>("/api/recipes");

        var aktiv = GetAllRecipesFromDb().Single(r => string.Equals(r.Title, "Aktiv", StringComparison.Ordinal));
        items!.Should().BeEquivalentTo(
            [new RecipeSummaryDto(Id: aktiv.Id, Title: "Aktiv", SourceUrl: null)]);
    }

    [Test]
    public async Task GetAll_RecipeSummaryIncludesSourceUrl()
    {
        SeedRecipes([ARecipe("Salat", sourceUrl: "https://example.com")]);

        var items = await Client.GetFromJsonAsync<List<RecipeSummaryDto>>("/api/recipes");

        items!.Single().SourceUrl.Should().Be(new Uri("https://example.com"));
    }

    [Test]
    public async Task GetAll_RecipeWithInvalidStoredUrl_Returns500WithProblemDetails()
    {
        SeedRecipes([ARecipe("Salat", sourceUrl: "not-a-valid-url")]);

        var response = await Client.GetAsync("/api/recipes");

        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
        response.Content.Headers.ContentType!.MediaType.Should().Be("application/problem+json");
        var id = GetAllRecipesFromDb()[0].Id;
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Detail.Should().Be($"DB inconsistency in Recipe #{id}: Ungültige URL 'not-a-valid-url'.");
    }
}

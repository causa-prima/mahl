namespace mahl.Server.Tests.Domain;

using FluentAssertions;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Tests.Helpers;
using NUnit.Framework;
using OneOf;
using OneOf.Types;

[TestFixture]
public class RecipeTests
{
    // RecipeIngredient.Create

    [Test]
    public void RecipeIngredient_Id_DefaultInstance_Throws()
    {
        var recipeIngredient = default(RecipeIngredient);

        Action act = () => { var _ = recipeIngredient.Id; };

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Uninitialized");
    }

    [Test]
    public void RecipeIngredient_ParameterlessConstructor_Throws()
    {
        Action act = () => new RecipeIngredient();

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Valid instances can only be created with Create.");
    }

    [Test]
    public void RecipeIngredient_Create_ValidArgs_ReturnsRecipeIngredient()
    {
        var id = Guid.NewGuid();
        var ingredientId = Guid.NewGuid();
        var result = RecipeIngredient.Create(id, ingredientId, "Tomate", "Stück", 200, "g");

        result.Value.Should().BeOfType<RecipeIngredient>().Which.Satisfy(i =>
        {
            i.Id.Should().Be(id);
            i.Ingredient.Id.Should().Be(ingredientId);
            ((string)i.Ingredient.Name).Should().Be("Tomate");
            ((string)i.Ingredient.DefaultUnit).Should().Be("Stück");
            i.Quantity.Match((v, _) => (decimal?)v, () => null).Should().Be(200m);
            i.Quantity.Match((_, u) => (string?)u, () => null).Should().Be("g");
        });
    }

    [TestCase("")]
    [TestCase(null)]
    public void RecipeIngredient_Create_QuantityWithMissingUnit_ReturnsError(string? unit)
    {
        var result = RecipeIngredient.Create(Guid.NewGuid(), Guid.NewGuid(), "Tomate", "Stück", 100, unit);

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Einheit darf nicht leer sein.");
    }

    [Test]
    public void RecipeIngredient_Create_NullQuantity_ReturnsUnspecified()
    {
        var result = RecipeIngredient.Create(Guid.NewGuid(), Guid.NewGuid(), "Tomate", "Stück", null, null);

        var isUnspecified = result.Value.Should().BeOfType<RecipeIngredient>()
            .Which.Quantity.Match((_, _) => false, () => true);
        isUnspecified.Should().BeTrue();
    }

    // RecipeStep.Create

    [Test]
    public void RecipeStep_ParameterlessConstructor_Throws()
    {
        Action act = () => new RecipeStep();

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Valid instances can only be created with Create.");
    }

    [Test]
    public void RecipeStep_Id_DefaultInstance_Throws()
    {
        var step = default(RecipeStep);

        Action act = () => { var _ = step.Id; };

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Uninitialized");
    }

    [Test]
    public void RecipeStep_Create_ValidInstruction_ReturnsRecipeStep()
    {
        var id = Guid.NewGuid();
        var result = RecipeStep.Create(id, "Tomaten schneiden.");

        result.Value.Should().BeOfType<RecipeStep>().Which.Satisfy(s =>
        {
            s.Id.Should().Be(id);
            ((string)s.Instruction).Should().Be("Tomaten schneiden.");
        });
    }

    [Test]
    public void RecipeStep_Create_EmptyInstruction_ReturnsError()
    {
        var result = RecipeStep.Create(Guid.NewGuid(), "");

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Schritt-Anweisung darf nicht leer sein.");
    }

    // Recipe

    [Test]
    public void Recipe_ParameterlessConstructor_Throws()
    {
        Action act = () => new Recipe();

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Valid instances can only be created with Create.");
    }

    // Recipe.Create

    [Test]
    public void Recipe_Id_DefaultInstance_Throws()
    {
        var recipe = default(Recipe);

        Action act = () => { var _ = recipe.Id; };

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Uninitialized");
    }

    [Test]
    public void Recipe_Create_SetsIdFromParameter()
    {
        var id = Guid.NewGuid();

        var result = Recipe.Create(
            id,
            "Tomatensalat",
            null,
            new List<(Guid, Guid, string, string, decimal?, string?)> { (Guid.NewGuid(), DefaultIngredientId, "Tomate", "Stück", 200, "g") }.AsReadOnly(),
            new List<(Guid, string)> { (Guid.NewGuid(), "Tomaten schneiden.") }.AsReadOnly());

        result.Value.Should().BeOfType<Recipe>().Which.Id.Should().Be(id);
    }

    [Test]
    public void Recipe_Create_RelativeSourceUrl_ReturnsError()
    {
        var result = CreateRecipe(ValidDto(sourceUrl: new Uri("/relative/path", UriKind.Relative)));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Quell-URL muss eine absolute URI sein.");
    }

    [TestCase("https://example.com")]
    [TestCase(null)]
    public void Recipe_Create_Source_ReflectsSourceUrl(string? sourceUrlString)
    {
        var sourceUrl = sourceUrlString is not null ? new Uri(sourceUrlString) : (Uri?)null;
        var result = CreateRecipe(ValidDto(sourceUrl: sourceUrl));

        result.Value.Should().BeOfType<Recipe>().Which
            .Source.Match(onUrl: url => (string?)url.OriginalString, onNone: () => null)
            .Should().Be(sourceUrlString);
    }

    [Test]
    public void Recipe_Create_ValidDto_ReturnsRecipe()
    {
        var result = CreateRecipe(ValidDto());

        result.Value.Should().BeOfType<Recipe>().Which.Satisfy(r =>
        {
            ((string)r.Title).Should().Be("Tomatensalat");
            r.Ingredients.Value.Should().BeEquivalentTo(
                [RecipeIngredient.Create(Guid.NewGuid(), DefaultIngredientId, "Tomate", "Stück", 200, "g").AsT0],
                opts => opts.Excluding(x => x.Id));
            r.Steps.Value.Should().BeEquivalentTo(
                [RecipeStep.Create(Guid.NewGuid(), "Tomaten schneiden.").AsT0],
                opts => opts.Excluding(x => x.Id));
        });
    }

    [Test]
    public void Recipe_Create_EmptyTitle_ReturnsError()
    {
        var result = CreateRecipe(ValidDto(title: ""));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Titel darf nicht leer sein.");
    }

    [Test]
    public void Recipe_Create_EmptyIngredientsList_ReturnsError()
    {
        var result = CreateRecipe(ValidDto(ingredients: []));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Rezept muss mindestens eine Zutat haben.");
    }

    [Test]
    public void Recipe_Create_EmptyStepsList_ReturnsError()
    {
        var result = CreateRecipe(ValidDto(steps: []));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Rezept muss mindestens einen Schritt haben.");
    }

    [TestCase(1)]
    [TestCase(2)]
    public void Recipe_Create_IngredientWithEmptyUnit_ReturnsError(int ingredientCount)
    {
        var ingredients = Enumerable.Range(0, ingredientCount - 1)
            .Select(_ => new CreateRecipeIngredientDto(IngredientId: Guid.NewGuid(), Quantity: 200, Unit: "g"))
            .Append(new CreateRecipeIngredientDto(IngredientId: Guid.NewGuid(), Quantity: 100, Unit: ""))
            .ToList();

        var result = CreateRecipe(ValidDto(ingredients: ingredients));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Einheit darf nicht leer sein.");
    }

    [TestCase(1)]
    [TestCase(2)]
    public void Recipe_Create_StepWithEmptyInstruction_ReturnsError(int stepCount)
    {
        var steps = Enumerable.Range(0, stepCount - 1)
            .Select(_ => new CreateStepDto(Instruction: "Tomaten schneiden."))
            .Append(new CreateStepDto(Instruction: ""))
            .ToList();

        var result = CreateRecipe(ValidDto(steps: steps));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Schritt-Anweisung darf nicht leer sein.");
    }

    [Test]
    public void Recipe_Create_TitleValidationTakesPrecedenceOverEmptyIngredients()
    {
        var result = CreateRecipe(ValidDto(title: "", ingredients: []));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Titel darf nicht leer sein.");
    }

    private static readonly Guid DefaultIngredientId = Guid.NewGuid();

    private static OneOf<Recipe, Error<string>> CreateRecipe(CreateRecipeDto dto) =>
        Recipe.Create(
            Guid.NewGuid(),
            dto.Title,
            dto.SourceUrl,
            dto.Ingredients.Select(i => (Guid.NewGuid(), i.IngredientId, "Tomate", "Stück", i.Quantity, i.Unit)).ToList().AsReadOnly(),
            dto.Steps.Select(s => (Guid.NewGuid(), s.Instruction)).ToList().AsReadOnly());

    private static CreateRecipeDto ValidDto(
        string title = "Tomatensalat",
        Uri? sourceUrl = null,
        List<CreateRecipeIngredientDto>? ingredients = null,
        List<CreateStepDto>? steps = null) =>
        new(Title: title, SourceUrl: sourceUrl,
            Ingredients: ingredients ?? [new CreateRecipeIngredientDto(IngredientId: DefaultIngredientId, Quantity: 200, Unit: "g")],
            Steps: steps ?? [new CreateStepDto(Instruction: "Tomaten schneiden.")]);

}

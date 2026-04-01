namespace mahl.Server.Domain;

using mahl.Server.Types;
using OneOf;
using OneOf.Types;

public readonly record struct RecipeIngredient
{
    private readonly Guid _id;
    private readonly Ingredient _ingredient;
    private readonly Quantity _quantity;

#pragma warning disable S4581 // == default is intentional: checks for default-initialized (unset) Guid value
    public Guid Id => _id == default ? throw new InvalidOperationException("Uninitialized") : _id;
#pragma warning restore S4581
    public Ingredient Ingredient => _ingredient;
    public Quantity Quantity => _quantity;

    // Must be public, as record structs cannot have private parameterless constructors
    public RecipeIngredient()
        => throw new InvalidOperationException($"Valid instances can only be created with {nameof(Create)}.");

    private RecipeIngredient(Guid id, Ingredient ingredient, Quantity quantity)
    {
        _id = id;
        _ingredient = ingredient;
        _quantity = quantity;
    }

    public static OneOf<RecipeIngredient, Error<string>> Create(
        Guid id, Guid ingredientId, string ingredientName, string defaultUnit, decimal? quantity, string? unit) =>
        Ingredient.Create(ingredientId, ingredientName, defaultUnit)
            .Bind(ingredient => quantity is null
                ? new RecipeIngredient(id, ingredient, Quantity.Unspecified())
                : NonEmptyTrimmedString.Create(unit ?? string.Empty)
                    .MapError(_ => new Error<string>("Einheit darf nicht leer sein."))
                    .Bind(u => Quantity.Create(quantity.Value, u))
                    .Match<OneOf<RecipeIngredient, Error<string>>>(
                        q => new RecipeIngredient(id, ingredient, q),
                        e => e));
}

public readonly record struct RecipeStep
{
    private readonly Guid _id;
    private readonly NonEmptyTrimmedString _instruction;

#pragma warning disable S4581 // == default is intentional: checks for default-initialized (unset) Guid value
    public Guid Id => _id == default ? throw new InvalidOperationException("Uninitialized") : _id;
#pragma warning restore S4581
    public NonEmptyTrimmedString Instruction => _instruction;

    // Must be public, as record structs cannot have private parameterless constructors
    public RecipeStep()
        => throw new InvalidOperationException($"Valid instances can only be created with {nameof(Create)}.");

    private RecipeStep(Guid id, NonEmptyTrimmedString instruction)
    {
        _id = id;
        _instruction = instruction;
    }

    public static OneOf<RecipeStep, Error<string>> Create(Guid id, string instruction) =>
        NonEmptyTrimmedString.Create(instruction)
            .MapError(_ => new Error<string>("Schritt-Anweisung darf nicht leer sein."))
            .Map(i => new RecipeStep(id, i));
}

public readonly record struct Recipe
{
    private readonly Guid _id;
    private readonly NonEmptyTrimmedString _title;
    private readonly RecipeSource _source;
    private readonly NonEmptyList<RecipeIngredient> _ingredients;
    private readonly NonEmptyList<RecipeStep> _steps;

#pragma warning disable S4581 // == default is intentional: checks for default-initialized (unset) Guid value
    public Guid Id => _id == default ? throw new InvalidOperationException("Uninitialized") : _id;
#pragma warning restore S4581
    public NonEmptyTrimmedString Title => _title;
    public RecipeSource Source => _source;
    public NonEmptyList<RecipeIngredient> Ingredients => _ingredients;
    public NonEmptyList<RecipeStep> Steps => _steps;

    // Must be public, as record structs cannot have private parameterless constructors
    public Recipe()
        => throw new InvalidOperationException($"Valid instances can only be created with {nameof(Create)}.");

    private Recipe(
        Guid id,
        NonEmptyTrimmedString title,
        RecipeSource source,
        NonEmptyList<RecipeIngredient> ingredients,
        NonEmptyList<RecipeStep> steps)
    {
        _id = id;
        _title = title;
        _source = source;
        _ingredients = ingredients;
        _steps = steps;
    }

    public static OneOf<Recipe, Error<string>> Create(
        Guid id,
        string title,
        Uri? sourceUrl,
        IReadOnlyList<(Guid Id, Guid IngredientId, string IngredientName, string DefaultUnit, decimal? Quantity, string? Unit)> ingredients,
        IReadOnlyList<(Guid Id, string Instruction)> steps) =>
        NonEmptyTrimmedString.Create(title)
            .MapError(_ => new Error<string>("Titel darf nicht leer sein."))
            .Bind(t => ingredients.Count > 0
                ? (OneOf<NonEmptyTrimmedString, Error<string>>) t
                : new Error<string>("Rezept muss mindestens eine Zutat haben."))
            .Bind(t => steps.Count > 0
                ? (OneOf<NonEmptyTrimmedString, Error<string>>) t
                : new Error<string>("Rezept muss mindestens einen Schritt haben."))
            .Bind(t => sourceUrl is { IsAbsoluteUri: false }
                ? new Error<string>("Quell-URL muss eine absolute URI sein.")
                : (OneOf<NonEmptyTrimmedString, Error<string>>) t)
            .Bind(t => ingredients
                .Select(i => RecipeIngredient.Create(i.Id, i.IngredientId, i.IngredientName, i.DefaultUnit, i.Quantity, i.Unit))
                .Sequence()
                .Bind(ingrs => steps
                    .Select(s => RecipeStep.Create(s.Id, s.Instruction))
                    .Sequence()
                    .Map(stps =>
                    {
                        var source = sourceUrl is { } url
                            ? RecipeSource.FromUrl(url)
                            : RecipeSource.None;
                        return new Recipe(id, t, source,
                            NonEmptyList<RecipeIngredient>.Create(ingrs).ValueOrThrowUnreachable(),
                            NonEmptyList<RecipeStep>.Create(stps).ValueOrThrowUnreachable());
                    })));
}

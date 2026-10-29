using mahl.Server.Types;

namespace mahl.Server.Domain;

// Domain-Entity (docs/reference/glossary.md, "Rezept"): nimmt ausschließlich Domänentypen und
// vertraut ihnen. Die Reihenfolge der Listen ist fachlich: Zutaten in Zeilenreihenfolge
// (ADR-S135-2), Schritte in Listenreihenfolge – die Schrittnummer ist keine Eigenschaft des
// Rezepts, sie entsteht erst beim Speichern (ADR-S027-1).
// „Mindestens eine Zutat / ein Schritt" (ADR-S135-2, ADR-S135-3) steckt im Typ der Listen
// (NonEmptyImmutableArray): ein Rezept ohne Zutat oder Schritt ist nicht darstellbar.
internal readonly record struct Recipe
{
    private readonly RecipeId _id;
    private readonly RecipeTitle _title;
    private readonly NonEmptyImmutableArray<RecipeIngredient> _ingredients;
    private readonly NonEmptyImmutableArray<StepInstruction> _steps;

    public RecipeId Id => _id;
    public RecipeTitle Title => _title;
    public NonEmptyImmutableArray<RecipeIngredient> Ingredients => _ingredients;
    public NonEmptyImmutableArray<StepInstruction> Steps => _steps;

    // Parameterless ctor must be public (record struct limitation) – catches new Recipe():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public Recipe() => throw new InvalidOperationException("Uninitialized");

    private Recipe(
        RecipeId id,
        RecipeTitle title,
        NonEmptyImmutableArray<RecipeIngredient> ingredients,
        NonEmptyImmutableArray<StepInstruction> steps)
    {
        _id = id;
        _title = title;
        _ingredients = ingredients;
        _steps = steps;
    }

    // Kein OneOf: alle Teile kommen schon als geprüfte Domänentypen an; die Fehler der Teile sammelt die API-Grenze
    // (RecipesEndpoints.ToValues, ADR-S119-2) – ein OneOf hier käme erst danach zum Zug und schlösse kurz.
    // „Jede Zutat höchstens einmal" kommt mit ihrem Szenario.
    public static Recipe Create(
        RecipeId id,
        RecipeTitle title,
        NonEmptyImmutableArray<RecipeIngredient> ingredients,
        NonEmptyImmutableArray<StepInstruction> steps) =>
        new(id, title, ingredients, steps);
}

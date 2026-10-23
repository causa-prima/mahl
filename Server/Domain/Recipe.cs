using System.Collections.Immutable;
using mahl.Server.Types;

namespace mahl.Server.Domain;

// Domain-Entity (docs/reference/glossary.md, "Rezept"): nimmt ausschließlich Domänentypen und
// vertraut ihnen. Die Reihenfolge der Listen ist fachlich: Zutaten in Zeilenreihenfolge
// (ADR-S135-2), Schritte in Listenreihenfolge – die Schrittnummer ist keine Eigenschaft des
// Rezepts, sie entsteht erst beim Speichern (ADR-S027-1).
// ImmutableArray statt ImmutableList: als Struct hat es keinen null-Zustand; ein default(ImmutableArray)
// wirft erst bei Length bzw. Enumeration, nicht schon beim Feldzugriff.
internal readonly record struct Recipe
{
    private readonly RecipeId _id;
    private readonly RecipeTitle _title;
    private readonly ImmutableArray<RecipeIngredient> _ingredients;
    private readonly ImmutableArray<StepInstruction> _steps;

    // Id und Title sind Domänentypen, deren default beim Zugriff wirft. Die Arrays nicht: Create nimmt auch
    // ein default-Array an. Ein Guard kommt mit den Entity-Invarianten (mindestens ein Schritt).
    public RecipeId Id => _id;
    public RecipeTitle Title => _title;
    public ImmutableArray<RecipeIngredient> Ingredients => _ingredients;
    public ImmutableArray<StepInstruction> Steps => _steps;

    // Parameterless ctor must be public (record struct limitation) – catches new Recipe():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public Recipe() => throw new InvalidOperationException("Uninitialized");

    private Recipe(
        RecipeId id, RecipeTitle title, ImmutableArray<RecipeIngredient> ingredients, ImmutableArray<StepInstruction> steps)
    {
        _id = id;
        _title = title;
        _ingredients = ingredients;
        _steps = steps;
    }

    // Kein OneOf: Entity-Invarianten (mindestens ein Schritt, jede Zutat höchstens einmal) kommen mit
    // den Szenarien, die sie prüfen.
    public static Recipe Create(
        RecipeId id, RecipeTitle title, ImmutableArray<RecipeIngredient> ingredients, ImmutableArray<StepInstruction> steps) =>
        new(id, title, ingredients, steps);
}

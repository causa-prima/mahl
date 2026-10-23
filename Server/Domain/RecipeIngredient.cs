using mahl.Server.Types;

namespace mahl.Server.Domain;

// Domain-Entity (docs/reference/glossary.md, "Rezept-Zutat"): die Verwendung einer Zutat in einem
// Rezept – Verweis auf die Zutat plus Menge (ADR-S020-1).
internal readonly record struct RecipeIngredient
{
    private readonly IngredientId _ingredient;
    private readonly Quantity _quantity;

    public IngredientId Ingredient => _ingredient; // wirft transitiv – der Guard sitzt in Uuid7
    // Stryker disable once NullCoalescing,String : default(T) guard unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("default(T) guard unreachable via normal construction (ADR-S041-9)")]
    public Quantity Quantity => _quantity ?? throw new InvalidOperationException("Uninitialized");

    // Parameterless ctor must be public (record struct limitation) – catches new RecipeIngredient():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public RecipeIngredient() => throw new InvalidOperationException("Uninitialized");

    private RecipeIngredient(IngredientId ingredient, Quantity quantity)
    {
        _ingredient = ingredient;
        _quantity = quantity;
    }

    public static RecipeIngredient Create(IngredientId ingredient, Quantity quantity) => new(ingredient, quantity);
}

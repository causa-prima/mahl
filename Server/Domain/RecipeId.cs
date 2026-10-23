using mahl.Server.Types;

namespace mahl.Server.Domain;

// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): die Identität
// eines Rezepts. Kapselt den Constraint-Typ Uuid7 wie IngredientId – und ist gegen diese nicht
// austauschbar.
internal readonly record struct RecipeId
{
    private readonly Uuid7 _value;
    public Guid Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new RecipeId():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public RecipeId() => throw new InvalidOperationException("Uninitialized");

    private RecipeId(Uuid7 value) => _value = value;

    // ADR-S030-1: UUIDv7, serverseitig vergeben.
    public static RecipeId New() => new(Uuid7.New());
}

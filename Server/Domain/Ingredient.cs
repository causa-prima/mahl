using mahl.Server.Types;

namespace mahl.Server.Domain;

internal readonly record struct Ingredient
{
    private readonly Guid _id;
    private readonly NonEmptyTrimmedString _name;
    private readonly NonEmptyTrimmedString _defaultUnit;

    // Guid has no meaningful default – guard against default(Ingredient).Id (ADR-S041-9; ternary adds Conditional mutant):
    // Stryker disable once Equality,String,Conditional : default(T) guard unreachable via normal construction (ADR-S041-9)
    public Guid Id => _id == Guid.Empty ? throw new InvalidOperationException("Uninitialized") : _id;
    // NonEmptyTrimmedString throws transitively on access – no extra guard needed:
    public NonEmptyTrimmedString Name => _name;
    public NonEmptyTrimmedString DefaultUnit => _defaultUnit;

    // Parameterless ctor must be public (record struct limitation) – catches new Ingredient():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public Ingredient() => throw new InvalidOperationException("Uninitialized");

    private Ingredient(Guid id, NonEmptyTrimmedString name, NonEmptyTrimmedString defaultUnit)
    {
        _id = id;
        _name = name;
        _defaultUnit = defaultUnit;
    }

    public static Ingredient Create(Guid id, NonEmptyTrimmedString name, NonEmptyTrimmedString defaultUnit) =>
        new(id, name, defaultUnit);
}

using System.Collections.Immutable;
using OneOf;

namespace mahl.Server.Types;

// Constraint-Typ (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): Liste mit mindestens
// einem Element. Ein Domänentyp, der „mindestens eins" fordert, nimmt diesen Typ statt einer ImmutableArray –
// eine leere Liste ist dann nicht darstellbar.
internal readonly record struct NonEmptyImmutableArray<T>
{
    private readonly ImmutableArray<T> _items;
    // default(T) guard – _items.IsDefault only for default(NonEmptyImmutableArray<T>), unreachable via normal construction (ADR-S041-9):
    // Stryker disable once Conditional,String : default(T) guard unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("default(T) guard unreachable via normal construction (ADR-S041-9)")]
    public ImmutableArray<T> Items => _items.IsDefault ? throw new InvalidOperationException("Uninitialized") : _items;

    // Parameterless ctor must be public (record struct limitation) – catches new NonEmptyImmutableArray<T>():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public NonEmptyImmutableArray() => throw new InvalidOperationException("Uninitialized");

    private NonEmptyImmutableArray(ImmutableArray<T> items) => _items = items;

    public static OneOf<NonEmptyImmutableArray<T>, ListViolation> Create(ImmutableArray<T> input) =>
        input.IsDefaultOrEmpty
            ? ListViolation.Empty
            : new NonEmptyImmutableArray<T>(input);

    // Abbilden erhält die Länge – das Ergebnis ist ohne erneute Prüfung wieder nicht leer.
    public NonEmptyImmutableArray<TOut> Map<TOut>(Func<T, TOut> map) =>
        new([.. Items.Select(map)]);
}

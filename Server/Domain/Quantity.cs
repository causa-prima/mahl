using mahl.Server.Types;

namespace mahl.Server.Domain;

// ADR-S020-1: die Menge einer Rezept-Zutat – angegeben oder nicht ("nach Geschmack"). Sum-Type statt
// decimal? (Make Illegal States Unrepresentable), Variante A nach ADR-S018-1.
// Ohne Einheit: mit Menge ist sie die Basiseinheit der Zutat (ADR-S135-2), ohne Menge
// Unspecified – sie gehört der Zutat, nicht der Menge. Der Wert ist vorerst ein rohes decimal: die
// Mengenregeln (> 0, höchstens 3 Nachkommastellen, höchstens 9999,999) kommen mit den Szenarien, die
// sie prüfen, und mit ihnen der Constraint-Typ.
internal abstract record Quantity
{
    private Quantity() { }

    private sealed record SpecifiedCase(decimal Amount) : Quantity;
    private sealed record UnspecifiedCase : Quantity;

    public static Quantity Specified(decimal amount) => new SpecifiedCase(amount);
    public static Quantity Unspecified { get; } = new UnspecifiedCase();

    // Wert-Träger-Sum-Type: Match ist public, der Mapping-Layer braucht ihn (ADR-S018-1).
    [ExcludeFromCoverageGate("structurally unreachable sum-type default arm (ADR-S040-1)")]
    public T Match<T>(Func<decimal, T> onSpecified, Func<T> onUnspecified) => this switch
    {
        SpecifiedCase specified => onSpecified(specified.Amount),
        UnspecifiedCase => onUnspecified(),
        _ => SumType.Unreachable<T>(), // ADR-S040-1: private ctor verhindert externe Subtypen
    };
}

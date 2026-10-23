using mahl.Server.Types;

namespace mahl.Server.Domain;

// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): die Anweisung
// eines Schritts (docs/reference/glossary.md, "Schritt"). Noch regellos – die Feldregeln aus
// ADR-S135-3 (Pflicht, Länge) samt OneOf-Fehlerkanal kommen mit den Szenarien, die sie prüfen.
internal readonly record struct StepInstruction
{
    private readonly string _value;
    // Stryker disable once NullCoalescing,String : default(T) guard unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("default(T) guard unreachable via normal construction (ADR-S041-9)")]
    public string Value => _value ?? throw new InvalidOperationException("Uninitialized");

    // Parameterless ctor must be public (record struct limitation) – catches new StepInstruction():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public StepInstruction() => throw new InvalidOperationException("Uninitialized");

    private StepInstruction(string value) => _value = value;

    public static StepInstruction Create(string value) => new(value);
}

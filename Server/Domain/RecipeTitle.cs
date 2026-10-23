using mahl.Server.Types;

namespace mahl.Server.Domain;

// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): der Titel eines
// Rezepts. Noch regellos – die Feldregeln aus ADR-S135-3 (Pflicht, Länge) samt OneOf-Fehlerkanal
// kommen mit den Szenarien, die sie prüfen; bis dahin wäre jede Regel ein ungeübter Fehlerzweig.
internal readonly record struct RecipeTitle
{
    private readonly string _value;
    // Stryker disable once NullCoalescing,String : default(T) guard unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("default(T) guard unreachable via normal construction (ADR-S041-9)")]
    public string Value => _value ?? throw new InvalidOperationException("Uninitialized");

    // Parameterless ctor must be public (record struct limitation) – catches new RecipeTitle():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public RecipeTitle() => throw new InvalidOperationException("Uninitialized");

    private RecipeTitle(string value) => _value = value;

    // ADR-S135-3: gespeichert in eingegebener Schreibweise.
    public static RecipeTitle Create(string value) => new(value);
}

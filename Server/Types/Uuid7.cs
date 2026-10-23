namespace mahl.Server.Types;

// Constraint-Typ für einen serverseitig vergebenen Primärschlüssel (ADR-S030-1). Er löst den
// Guid.Empty-In-band-Sentinel ab: "uninitialisiert" ist kein Wert dieses Typs mehr, sondern ein
// default(T)-Guard (docs/guidelines/coding-guideline-csharp.md#CGC-regel-abwesenheit –
// Abwesenheit gehört out-of-band, das
// leistet IngredientId).
//
// Zwei Quellen: New() vergibt die Identität im Schreibpfad (Guid.CreateVersion7()), Create(Guid)
// übernimmt eine bereits gespeicherte aus der DB (Lesepfad, z.B. die Zutat einer Rezeptzeile).
// Create(Guid) prüft bewusst NICHT, ob die Guid gültig ist (nicht default, Version 7): ein solches
// Prädikat brächte einen Fehlerzweig (DB-Inkonsistenz -> 500) mit, den noch kein Szenario ausübt.
// Er entsteht mit dem DB-Inkonsistenz-Szenario; bis dahin vertraut der Lesepfad der DB.
internal readonly record struct Uuid7
{
    private readonly Guid _value;

    // Guid has no meaningful default – guard against default(Uuid7).Value (ADR-S041-9; ternary adds Conditional mutant).
    // ADR-S035-1: `== default` statt `== Guid.Empty` – "strukturell uninitialisiert" statt eines
    // Guid-Wertes; S4581 ist genau dafür freigegeben.
#pragma warning disable S4581
    // Stryker disable once Equality,String,Conditional : default(T) guard unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("default(T) guard unreachable via normal construction (ADR-S041-9)")]
    public Guid Value => _value == default ? throw new InvalidOperationException("Uninitialized") : _value;
#pragma warning restore S4581

    // Parameterless ctor must be public (record struct limitation) – catches new Uuid7():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public Uuid7() => throw new InvalidOperationException("Uninitialized");

    private Uuid7(Guid value) => _value = value;

    // ADR-S030-1: UUIDv7, serverseitig vergeben.
    public static Uuid7 New() => new(Guid.CreateVersion7());

    // Lesepfad: nicht validierend, s. Kommentar am Typ.
    public static Uuid7 Create(Guid stored) => new(stored);
}

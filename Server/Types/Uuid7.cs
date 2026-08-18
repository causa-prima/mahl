namespace mahl.Server.Types;

// Constraint-Typ für einen serverseitig vergebenen Primärschlüssel (ADR-S030-1). Er löst den
// Guid.Empty-In-band-Sentinel ab: "uninitialisiert" ist kein Wert dieses Typs mehr, sondern ein
// default(T)-Guard (coding-guideline-csharp.md §2 Regel 4 – Abwesenheit gehört out-of-band, das
// leistet IngredientId).
//
// Bewusst ohne validierendes Create(Guid) -> OneOf: die einzige Guid-Quelle im Schreibpfad ist
// Guid.CreateVersion7(), ein UUIDv7-Prädikat hätte hier also einen unerreichbaren Fehlerzweig.
// Sein Aufrufer ist der Lesepfad aus der DB, der einen eigenen Fehlerzweig (DB-Inkonsistenz)
// einführt – der entsteht mit dem DB-Inkonsistenz-Szenario.
internal readonly record struct Uuid7
{
    private readonly Guid _value;

    // Guid has no meaningful default – guard against default(Uuid7).Value (ADR-S041-9; ternary adds Conditional mutant).
    // ADR-S035-1: `== default` statt `== Guid.Empty` – "strukturell uninitialisiert" statt eines
    // Guid-Wertes; S4581 ist genau dafür freigegeben.
#pragma warning disable S4581
    // Stryker disable once Equality,String,Conditional : default(T) guard unreachable via normal construction (ADR-S041-9)
    public Guid Value => _value == default ? throw new InvalidOperationException("Uninitialized") : _value;
#pragma warning restore S4581

    // Parameterless ctor must be public (record struct limitation) – catches new Uuid7():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public Uuid7() => throw new InvalidOperationException("Uninitialized");

    private Uuid7(Guid value) => _value = value;

    // ADR-S030-1: UUIDv7, serverseitig vergeben.
    public static Uuid7 New() => new(Guid.CreateVersion7());
}

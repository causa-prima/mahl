using mahl.Server.Types;

namespace mahl.Server.Domain;

// Domänentyp (coding-guideline-csharp.md §2 Ebene 2): die Identität einer Zutat. Er kapselt den
// Constraint-Typ Uuid7, damit dieser nicht in Signaturen steht (Regel 1) und eine IngredientId nicht
// gegen eine künftige RecipeId austauschbar ist.
//
// Nur der anlegende Schreibpfad erzeugt eine Identität (ADR-S030-1: serverseitig vergeben). Wo keine
// existiert – der Restore-Pfad validiert einen Body, identifiziert die Zeile aber über den
// Routenparameter –, wird auch keine gebraucht: dort läuft die validierte Nutzlast ohne Id, statt
// eine Abwesenheit im Typ darzustellen (§2 Regel 4 – Abwesenheit gehört out-of-band; hier ist
// out-of-band schlicht "nicht Teil des Wertes").
internal readonly record struct IngredientId
{
    private readonly Uuid7 _value;
    public Guid Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new IngredientId():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public IngredientId() => throw new InvalidOperationException("Uninitialized");

    private IngredientId(Uuid7 value) => _value = value;

    // ADR-S030-1: UUIDv7, serverseitig vergeben.
    public static IngredientId New() => new(Uuid7.New());
}

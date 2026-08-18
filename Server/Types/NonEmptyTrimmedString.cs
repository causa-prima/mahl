using OneOf;

namespace mahl.Server.Types;

// Constraint-Typ (coding-guideline-csharp.md §2 Ebene 1): getrimmt und nicht leer.
// Trimmen und Nicht-Leer liegen bewusst in EINEM Träger statt in zwei komponierbaren: Ein Träger,
// der nur normalisiert, müsste im Null-Fall einen Wert liefern ("" aus null), und der ist von ""
// aus "" nicht unterscheidbar – der Zweig wäre über HTTP nicht mehr beobachtbar. Hier gibt er einen
// FEHLER zurück, und dessen Wegfall ist es (ein leerer Name käme sonst als 201 durch).
// Es gibt zudem keinen Aufrufer für "getrimmt, darf leer sein"; kommt einer (optionales Feld),
// ist die Aufspaltung ein additiver Schritt.
internal readonly record struct NonEmptyTrimmedString : IStringConstraint<NonEmptyTrimmedString>
{
    private readonly string _value;
    // default(T) guard – _value is null only for default(NonEmptyTrimmedString), unreachable via normal construction (ADR-S041-9):
    // Stryker disable once NullCoalescing,String : default(T) guard unreachable via normal construction (ADR-S041-9)
    public string Value => _value ?? throw new InvalidOperationException("Uninitialized");

    // Parameterless ctor must be public (record struct limitation) – catches new NonEmptyTrimmedString():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public NonEmptyTrimmedString() => throw new InvalidOperationException("Uninitialized");

    private NonEmptyTrimmedString(string value) => _value = value;

    // ADR-S051-1: trim before validation, store the trimmed value.
    // Der Träger meldet einen Verstoß, keinen Meldungstext: er ist feldagnostisch und kennt weder
    // Feldnamen noch Request-Format (Regel 5, ADR-S051-2).
    // `string?`: ein fehlendes oder explizit null gesetztes JSON-Property kommt hier als null an
    // (System.Text.Json erzwingt die NRT-Annotationen des DTOs nicht) und ist wie leer zu behandeln.
    public static OneOf<NonEmptyTrimmedString, StringViolation> Create(string? input)
    {
        var trimmed = input?.Trim();
        if (string.IsNullOrEmpty(trimmed))
            return StringViolation.Empty;

        return new NonEmptyTrimmedString(trimmed);
    }
}

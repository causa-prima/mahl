using System.Text;
using OneOf;

namespace mahl.Server.Types;

// Constraint-Typ (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession):
// normalisiert (ADR-S135-1; umfasst das Trimmen aus ADR-S051-1) und nicht leer.
// Normalisieren und Nicht-Leer liegen bewusst in EINEM Träger statt in zwei komponierbaren: Ein Träger,
// der nur normalisiert, müsste im Null-Fall einen Wert liefern ("" aus null), und der ist von ""
// aus "" nicht unterscheidbar – der Zweig wäre über HTTP nicht mehr beobachtbar. Hier gibt er einen
// FEHLER zurück, und dessen Wegfall ist es (ein leerer Name käme sonst als 201 durch).
// Es gibt zudem keinen Aufrufer für "getrimmt, darf leer sein"; kommt einer (optionales Feld),
// ist die Aufspaltung ein additiver Schritt.
internal readonly record struct NonEmptyNormalizedString : IStringConstraint<NonEmptyNormalizedString>
{
    private readonly string _value;
    // default(T) guard – _value is null only for default(NonEmptyNormalizedString), unreachable via normal construction (ADR-S041-9):
    // Stryker disable once NullCoalescing,String : default(T) guard unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("default(T) guard unreachable via normal construction (ADR-S041-9)")]
    public string Value => _value ?? throw new InvalidOperationException("Uninitialized");

    // Parameterless ctor must be public (record struct limitation) – catches new NonEmptyNormalizedString():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public NonEmptyNormalizedString() => throw new InvalidOperationException("Uninitialized");

    private NonEmptyNormalizedString(string value) => _value = value;

    // ADR-S051-1 / ADR-S135-1: normalize before validation, store the normalized value.
    // Der Träger meldet einen Verstoß, keinen Meldungstext: er ist feldagnostisch und kennt weder
    // Feldnamen noch Request-Format (Meldungen an die Grenze, ADR-S051-2).
    // `string?`: ein fehlendes oder explizit null gesetztes JSON-Property kommt hier als null an
    // (System.Text.Json erzwingt die NRT-Annotationen des DTOs nicht) und ist wie leer zu behandeln.
    public static OneOf<NonEmptyNormalizedString, StringViolation> Create(string? input)
    {
        var normalized = Normalize(input ?? string.Empty);
        if (normalized.Length == 0)
            return StringViolation.Empty;

        return new NonEmptyNormalizedString(normalized);
    }

    // ADR-S135-1: unsichtbare Zeichen entfernen, jede Leerraum-Folge zu einem Leerzeichen falten (trimmt zugleich
    // Anfang und Ende über Split(RemoveEmptyEntries)), danach NFC.
    // Die Leerraum-Prüfung steht bewusst VOR NFC: NFC kanonisiert U+2000 zu U+2002 und U+2001 zu U+2003;
    // Leerraum zuerst zu ' ' zu falten macht die Prüfung unabhängig von dieser Abbildung. Für alle anderen
    // Codepunkte ändert NFC die Zugehörigkeit zu White_Space und zu den unsichtbaren Zeichen nicht.
    private static string Normalize(string text)
    {
        var visible = new string(text.Where(c => !IsInvisible(c)).ToArray());
        var spaced = new string(visible.Select(c => IsWhiteSpace(c) ? ' ' : c).ToArray());
        return string.Join(' ', spaced.Split(' ', StringSplitOptions.RemoveEmptyEntries)).Normalize(NormalizationForm.FormC);
    }

    // Leerzeichen ohne Breite, weiches Trennzeichen, Wortverbinder, Byte-Order-Mark (ADR-S135-1).
    private static bool IsInvisible(char c) => (int)c is 0x200B or 0x00AD or 0x2060 or 0xFEFF;

    // Unicode-Eigenschaft White_Space (PropList.txt) – bewusst NICHT char.IsWhiteSpace, das zusätzlich
    // U+001C–U+001F kennt. Client/src/domain/text.ts (isBlank) entscheidet über dieselbe Menge.
    private static bool IsWhiteSpace(char c) =>
        (int)c is (>= 0x0009 and <= 0x000D) or 0x0020 or 0x0085 or 0x00A0 or 0x1680
            or (>= 0x2000 and <= 0x200A) or 0x2028 or 0x2029 or 0x202F or 0x205F or 0x3000;
}

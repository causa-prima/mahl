using mahl.Server.Types;
using OneOf;

namespace mahl.Server.Domain;

// ADR-S120-1: der Fehlertyp gehört zum Konzept "Einheit", nicht zum Feld und nicht zur Entität –
// er trägt deshalb über alle Verwendungsstellen (Zutat, Rezept, Einkaufsliste). Der Feldbezug und
// der deutsche Text entstehen je Verwendungsstelle an der API-Grenze (ADR-S051-2, Regel 5).
// MA0048: File name must match type name – der Fehlertyp ist per ADR-S120-1 an das Konzept gebunden:
//         er ist der Fehlerkanal von Unit.Create, außerhalb dieses Typs bedeutungslos und ändert
//         sich ausschließlich mit ihm. Beim absehbaren Wechsel `Unit`: string -> Enum wandern beide
//         gemeinsam – getrennte Dateien suggerierten eine Unabhängigkeit, die es nicht gibt.
#pragma warning disable MA0048
internal enum UnitError { Empty, TooLong }
#pragma warning restore MA0048

// Domänentyp (coding-guideline-csharp.md §2 Ebene 2, Regel 2): die Einheit einer Zutat
// (docs/reference/glossary.md, "Basiseinheit"; UI-Label "Einheit"). GETEILT, nicht IngredientUnit –
// Rezept- und Einkaufslisten-Einheit sind dasselbe Konzept, und mehrere Typen dafür verteilten
// seine Regeln auf mehrere Änderungsorte.
internal readonly record struct Unit
{
    // ADR-S051-3: max. 20 Zeichen, nach Trimming gemessen – die Grenze ist Teil des Typs.
    private readonly Bounded<NonEmptyTrimmedString, Max20> _value;
    public string Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new Unit():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public Unit() => throw new InvalidOperationException("Uninitialized");

    private Unit(Bounded<NonEmptyTrimmedString, Max20> value) => _value = value;

    public static OneOf<Unit, UnitError> Create(string? input) =>
        Bounded<NonEmptyTrimmedString, Max20>.Create(input)
            .MapError<Bounded<NonEmptyTrimmedString, Max20>, StringViolation, UnitError>(v => v switch
            {
                StringViolation.Empty => UnitError.Empty,
                StringViolation.TooLong => UnitError.TooLong,
                _ => SumType.Unreachable<UnitError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
            })
            .Map(v => new Unit(v));
}

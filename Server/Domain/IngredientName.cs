using mahl.Server.Types;
using OneOf;

namespace mahl.Server.Domain;

// ADR-S120-1: ein Validierungs-Fehlertyp je Domänentyp. Die Fälle sind die Fehlerfälle des
// Fachkonzepts "Zutatenname" – nicht die des Constraint-Typs und nicht die eines Feldes. Der Typ
// trägt weder Feldnamen (den kennt die Grenze statisch) noch Meldungstext (ADR-S051-2, Regel 5).
// MA0048: File name must match type name – der Fehlertyp ist per ADR-S120-1 an das Konzept gebunden,
//         nicht ans Feld und nicht an die Entität: er ist der Fehlerkanal von IngredientName.Create,
//         außerhalb dieses Typs bedeutungslos und ändert sich ausschließlich mit ihm. Eine eigene
//         Datei suggerierte eine Unabhängigkeit, die es nicht gibt.
#pragma warning disable MA0048
internal enum IngredientNameError { Empty, TooLong }
#pragma warning restore MA0048

// Domänentyp (coding-guideline-csharp.md §2 Ebene 2): der Hauptname einer Zutat
// (docs/reference/glossary.md, "Zutat"). Er baut sich aus Constraint-Typen; die Grenze steht als
// Marker im Feldtyp, nicht als const in Create() (ADR-S119-1).
internal readonly record struct IngredientName
{
    // ADR-S051-3: max. 30 Zeichen, nach Trimming gemessen – die Grenze ist Teil des Typs.
    private readonly Bounded<NonEmptyTrimmedString, Max30> _value;
    public string Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new IngredientName():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public IngredientName() => throw new InvalidOperationException("Uninitialized");

    private IngredientName(Bounded<NonEmptyTrimmedString, Max30> value) => _value = value;

    // Regel 5: der Typ liefert die Fehlerfälle SEINES Konzepts – der Constraint-Typ und sein
    // StringViolation bleiben Implementierungsdetail (Regel 1, ADR-S120-1).
    public static OneOf<IngredientName, IngredientNameError> Create(string? input) =>
        Bounded<NonEmptyTrimmedString, Max30>.Create(input)
            .MapError<Bounded<NonEmptyTrimmedString, Max30>, StringViolation, IngredientNameError>(v => v switch
            {
                StringViolation.Empty => IngredientNameError.Empty,
                StringViolation.TooLong => IngredientNameError.TooLong,
                _ => SumType.Unreachable<IngredientNameError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
            })
            .Map(v => new IngredientName(v));
}

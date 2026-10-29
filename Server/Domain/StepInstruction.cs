using mahl.Server.Types;
using OneOf;

namespace mahl.Server.Domain;

// ADR-S120-1: ein Validierungs-Fehlertyp je Domänentyp, feldagnostisch (Feldbezug und Meldungstext
// entstehen an der API-Grenze, ADR-S051-2).
// MA0048: File name must match type name – der Fehlertyp ist der Fehlerkanal von StepInstruction.Create,
//         außerhalb dieses Typs bedeutungslos und ändert sich ausschließlich mit ihm.
#pragma warning disable MA0048
internal enum StepInstructionError { Empty }
#pragma warning restore MA0048

// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): die Anweisung
// eines Schritts (docs/reference/glossary.md, "Schritt"). Die Längengrenze (ADR-S135-3) kommt mit dem
// Szenario, das sie prüft.
internal readonly record struct StepInstruction
{
    private readonly NonEmptyTrimmedString _value;
    public string Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new StepInstruction():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public StepInstruction() => throw new InvalidOperationException("Uninitialized");

    private StepInstruction(NonEmptyTrimmedString value) => _value = value;

    // ADR-S051-1: getrimmt gespeichert.
    public static OneOf<StepInstruction, StepInstructionError> Create(string? input) =>
        NonEmptyTrimmedString.Create(input)
            .MapError<NonEmptyTrimmedString, StringViolation, StepInstructionError>(v => v switch
            {
                StringViolation.Empty => StepInstructionError.Empty,
                _ => SumType.Unreachable<StepInstructionError>(), // ADR-S040-1: bis zur Längengrenze nur Empty möglich
            })
            .Map(v => new StepInstruction(v));
}

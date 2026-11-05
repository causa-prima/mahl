using mahl.Server.Types;
using OneOf;

namespace mahl.Server.Domain;

// ADR-S120-1: ein Validierungs-Fehlertyp je Domänentyp, feldagnostisch (Feldbezug und Meldungstext
// entstehen an der API-Grenze, ADR-S051-2).
// MA0048: File name must match type name – der Fehlertyp ist der Fehlerkanal von StepInstruction.Create,
//         außerhalb dieses Typs bedeutungslos und ändert sich ausschließlich mit ihm.
#pragma warning disable MA0048
internal enum StepInstructionError { Empty, TooLong }
#pragma warning restore MA0048

// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): die Anweisung
// eines Schritts (docs/reference/glossary.md, "Schritt"). Höchstens 1000 Zeichen am normalisierten Wert
// (ADR-S135-3, ADR-S119-1).
internal readonly record struct StepInstruction
{
    private readonly Bounded<NonEmptyNormalizedString, Max1000> _value;
    public string Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new StepInstruction():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public StepInstruction() => throw new InvalidOperationException("Uninitialized");

    private StepInstruction(Bounded<NonEmptyNormalizedString, Max1000> value) => _value = value;

    // ADR-S135-1: normalisiert gespeichert.
    public static OneOf<StepInstruction, StepInstructionError> Create(string? input) =>
        Bounded<NonEmptyNormalizedString, Max1000>.Create(input)
            .MapError<Bounded<NonEmptyNormalizedString, Max1000>, StringViolation, StepInstructionError>(v => v switch
            {
                StringViolation.Empty => StepInstructionError.Empty,
                StringViolation.TooLong => StepInstructionError.TooLong,
                _ => SumType.Unreachable<StepInstructionError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
            })
            .Map(v => new StepInstruction(v));
}

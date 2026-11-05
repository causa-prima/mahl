using mahl.Server.Types;
using OneOf;

namespace mahl.Server.Domain;

// ADR-S120-1: ein Validierungs-Fehlertyp je Domänentyp, feldagnostisch (Feldbezug und Meldungstext
// entstehen an der API-Grenze, ADR-S051-2).
// MA0048: File name must match type name – der Fehlertyp ist der Fehlerkanal von RecipeTitle.Create,
//         außerhalb dieses Typs bedeutungslos und ändert sich ausschließlich mit ihm.
#pragma warning disable MA0048
internal enum RecipeTitleError { Empty, TooLong }
#pragma warning restore MA0048

// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): der Titel eines
// Rezepts. Höchstens 100 Zeichen am normalisierten Wert (ADR-S135-3, ADR-S119-1).
internal readonly record struct RecipeTitle
{
    private readonly Bounded<NonEmptyNormalizedString, Max100> _value;
    public string Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new RecipeTitle():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public RecipeTitle() => throw new InvalidOperationException("Uninitialized");

    private RecipeTitle(Bounded<NonEmptyNormalizedString, Max100> value) => _value = value;

    // ADR-S135-1: normalisiert gespeichert, ADR-S135-3: sonst in eingegebener Schreibweise.
    public static OneOf<RecipeTitle, RecipeTitleError> Create(string? input) =>
        Bounded<NonEmptyNormalizedString, Max100>.Create(input)
            .MapError<Bounded<NonEmptyNormalizedString, Max100>, StringViolation, RecipeTitleError>(v => v switch
            {
                StringViolation.Empty => RecipeTitleError.Empty,
                StringViolation.TooLong => RecipeTitleError.TooLong,
                _ => SumType.Unreachable<RecipeTitleError>(), // ADR-S040-1: enum-Default-Arm, strukturell unerreichbar
            })
            .Map(v => new RecipeTitle(v));
}

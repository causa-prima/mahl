using mahl.Server.Types;
using OneOf;

namespace mahl.Server.Domain;

// ADR-S120-1: ein Validierungs-Fehlertyp je Domänentyp, feldagnostisch (Feldbezug und Meldungstext
// entstehen an der API-Grenze, ADR-S051-2).
// MA0048: File name must match type name – der Fehlertyp ist der Fehlerkanal von RecipeTitle.Create,
//         außerhalb dieses Typs bedeutungslos und ändert sich ausschließlich mit ihm.
#pragma warning disable MA0048
internal enum RecipeTitleError { Empty }
#pragma warning restore MA0048

// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-primitive-obsession): der Titel eines
// Rezepts. Die Längengrenze (ADR-S135-3) kommt mit dem Szenario, das sie prüft.
internal readonly record struct RecipeTitle
{
    private readonly NonEmptyTrimmedString _value;
    public string Value => _value.Value; // wirft transitiv – der Guard sitzt im Constraint-Typ

    // Parameterless ctor must be public (record struct limitation) – catches new RecipeTitle():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public RecipeTitle() => throw new InvalidOperationException("Uninitialized");

    private RecipeTitle(NonEmptyTrimmedString value) => _value = value;

    // ADR-S051-1: getrimmt gespeichert, ADR-S135-3: sonst in eingegebener Schreibweise.
    public static OneOf<RecipeTitle, RecipeTitleError> Create(string? input) =>
        NonEmptyTrimmedString.Create(input)
            .MapError<NonEmptyTrimmedString, StringViolation, RecipeTitleError>(v => v switch
            {
                StringViolation.Empty => RecipeTitleError.Empty,
                _ => SumType.Unreachable<RecipeTitleError>(), // ADR-S040-1: bis zur Längengrenze nur Empty möglich
            })
            .Map(v => new RecipeTitle(v));
}

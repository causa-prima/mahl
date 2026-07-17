using mahl.Server.Types;

namespace mahl.Server.Domain;

// Field-bearing validation error as a sum-type (ADR-S018-1 Variante A): identifies which Ingredient field
// failed validation, so the API boundary can key the field-keyed 422 body (ADR-S090-1) on the right field.
// Private nested subtypes, with Match<T> as the sole consumer entry point (ADR-S018-1). Payloadless cases –
// the field-to-key/text mapping lives at the boundary (ADR-S051-2), so the cases carry no data.
internal abstract record IngredientValidationError
{
    private IngredientValidationError() { } // prevents external subtypes (strongest encapsulation)

    private sealed record NameEmptyCase : IngredientValidationError;
    // ADR-S051-3: name max. 30 Zeichen, nach Trimming gemessen.
    private sealed record NameTooLongCase : IngredientValidationError;
    private sealed record UnitEmptyCase : IngredientValidationError;
    // ADR-S051-3: defaultUnit max. 20 Zeichen, nach Trimming gemessen.
    private sealed record UnitTooLongCase : IngredientValidationError;

    public static IngredientValidationError NameEmpty { get; } = new NameEmptyCase();
    public static IngredientValidationError NameTooLong { get; } = new NameTooLongCase();
    public static IngredientValidationError UnitEmpty { get; } = new UnitEmptyCase();
    public static IngredientValidationError UnitTooLong { get; } = new UnitTooLongCase();

    [System.Diagnostics.CodeAnalysis.ExcludeFromCodeCoverage] // ADR-S040-1: structurally unreachable _-arm
    public T Match<T>(Func<T> onNameEmpty, Func<T> onNameTooLong, Func<T> onUnitEmpty, Func<T> onUnitTooLong) => this switch
    {
        NameEmptyCase => onNameEmpty(),
        NameTooLongCase => onNameTooLong(),
        UnitEmptyCase => onUnitEmpty(),
        UnitTooLongCase => onUnitTooLong(),
        _ => SumType.Unreachable<T>(), // ADR-S040-1: private subtypes make this arm unreachable
    };
}

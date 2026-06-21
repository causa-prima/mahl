using OneOf;
using OneOf.Types;

namespace mahl.Server.Types;

internal readonly record struct NonEmptyTrimmedString
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
    // Payloadless Error (OneOf.Types.Error): field-specific messages belong at the API boundary
    // that knows the field (ADR-S051-2), not in this field-agnostic primitive.
    public static OneOf<NonEmptyTrimmedString, Error> Create(string input)
    {
        var trimmed = input?.Trim();
        if (string.IsNullOrEmpty(trimmed))
            return new Error();

        return new NonEmptyTrimmedString(trimmed);
    }

    public static implicit operator string(NonEmptyTrimmedString name) => name.Value;
}

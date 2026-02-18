namespace mahl.Shared.Types;

using OneOf;
using OneOf.Types;

public readonly record struct NonEmptyTrimmedString
{
    private readonly TrimmedString _value;

    public TrimmedString Value
        => _value.Length == 0
        ? throw new InvalidOperationException($"Cannot access an uninitialized {nameof(NonEmptyTrimmedString)}.")
        : _value;

    public int Length => Value.Length;

    // Must be public, as record structs cannot have private parameterless constructors
    public NonEmptyTrimmedString()
        => throw new InvalidOperationException($"Valid instances can only be created with {nameof(Create)}.");

    private NonEmptyTrimmedString(TrimmedString value)
    {
        _value = value;
    }

    public static OneOf<Success<NonEmptyTrimmedString>, Error<string>> Create(string value)
    {
        var trimmed = (TrimmedString)value;
        return Validate(trimmed).Match<OneOf<Success<NonEmptyTrimmedString>, Error<string>>>(
            success => new Success<NonEmptyTrimmedString>(new NonEmptyTrimmedString(trimmed)),
            error => error
            );
    }

    private static OneOf<Success, Error<string>> Validate(TrimmedString value) =>
        value.Length == 0
        ? new Error<string>("Value cannot be null, empty or white space.")
        : new Success();

    // Override ToString to trigger exception when used on an uninitialized instance
    public override string ToString() => Value;

    public static implicit operator string(NonEmptyTrimmedString instance) => instance.Value;
    public static implicit operator TrimmedString(NonEmptyTrimmedString instance) => instance.Value;
}

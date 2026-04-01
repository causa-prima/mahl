namespace mahl.Server.Domain;

using mahl.Server.Types;
using OneOf;
using OneOf.Types;
using System.Diagnostics.CodeAnalysis;

public abstract record Quantity
{
    private Quantity() { }

    private sealed record UnspecifiedCase : Quantity;
    private sealed record SpecifiedCase(decimal Value, NonEmptyTrimmedString Unit) : Quantity;

    public static Quantity Unspecified() => new UnspecifiedCase();

    public static OneOf<Quantity, Error<string>> Create(decimal value, NonEmptyTrimmedString unit) =>
        value <= 0
            ? new Error<string>("Menge muss größer als 0 sein.")
            : new SpecifiedCase(value, unit);

    [ExcludeFromCodeCoverage] // _ arm is structurally unreachable; private ctor prevents external subtypes
#pragma warning disable S3060 // Sum-Type dispatch: type test in switch is unavoidable with private-ctor subtypes
    public T Match<T>(Func<decimal, NonEmptyTrimmedString, T> onSpecified, Func<T> onUnspecified) => this switch
    {
        SpecifiedCase s => onSpecified(s.Value, s.Unit),
        UnspecifiedCase => onUnspecified(),
        _               => SumType.Unreachable<T>()
    };
#pragma warning restore S3060 // Sum-Type dispatch
}

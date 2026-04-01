namespace mahl.Server.Types;

using OneOf;
using OneOf.Types;

public readonly struct NonEmptyList<T> : IEquatable<NonEmptyList<T>>
{
    private readonly IReadOnlyList<T>? _items;

    public IReadOnlyList<T> Value
        => _items is null || _items.Count == 0
            ? throw new InvalidOperationException($"Cannot access an uninitialized {nameof(NonEmptyList<T>)}.")
            : _items;

    // No explicit parameterless constructor: default(NonEmptyList<T>) leaves _items null,
    // which the null-guard in Value catches. Same defensive pattern as NonEmptyTrimmedString.
    private NonEmptyList(IReadOnlyList<T> items) => _items = items;

    public static OneOf<NonEmptyList<T>, Error<string>> Create(IReadOnlyList<T> items)
    {
        if (items.Count == 0)
            return new Error<string>("List must not be empty.");
        return new NonEmptyList<T>(items);
    }

    // Delegates to SequenceEqual so that NonEmptyList<T> behaves like the list it wraps.
    public bool Equals(NonEmptyList<T> other) => Value.SequenceEqual(other.Value);
    public override bool Equals(object? obj) => obj is NonEmptyList<T> other && Equals(other);
    public override int GetHashCode()
    {
        var hash = new HashCode();
        foreach (var item in Value)
            hash.Add(item);
        return hash.ToHashCode();
    }

    public static bool operator ==(NonEmptyList<T> left, NonEmptyList<T> right) => left.Equals(right);
    public static bool operator !=(NonEmptyList<T> left, NonEmptyList<T> right) => !left.Equals(right);
}

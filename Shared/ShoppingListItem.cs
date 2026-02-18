namespace mahl.Shared;

using mahl.Shared.Types;
using OneOf;
using OneOf.Types;

public record ShoppingListItem
{
    private static OneOf<ShoppingListItem, Error<string>> TryCreate(SyncItemId id, NonEmptyTrimmedString title, TrimmedString description, OneOf<DateTimeOffset, Unknown> boughtAt)
    {
        if (title.Length > Constants.ShoppingListTitleMaxLength) return new Error<string>($"{nameof(Title)} must not be longer than {Constants.ShoppingListTitleMaxLength} characters.");
        if (description.Length > Constants.ShoppingListDescriptionMaxLength) return new Error<string>($"{nameof(Description)} must not be longer than {Constants.ShoppingListDescriptionMaxLength} characters.");
        if (boughtAt.IsT0 && boughtAt.AsT0 > DateTimeOffset.Now) return new Error<string>($"{nameof(BoughtAt)} must not be a future date.");

        return new ShoppingListItem(id, title, description, boughtAt);
    }

    // This constructor must only be called after validating all the passed properties with Validate!
    private ShoppingListItem(SyncItemId id, NonEmptyTrimmedString title, TrimmedString description, OneOf<DateTimeOffset, Unknown> boughtAt) =>
        (Id, Title, Description, BoughtAt) = (id, title, description, boughtAt);

    public static OneOf<ShoppingListItem, Error<string>> FromPrimitiveTypes(int? id, string title, string description, DateTimeOffset? boughtAt)
        => NonEmptyTrimmedString.Create(title).Match(
            success => TryCreate(id,
                                 success.Value,
                                 (TrimmedString)description,
                                 boughtAt.HasValue ? boughtAt.Value : new Unknown()),
            error => error
            );
    public static OneOf<ShoppingListItem, Error<string>> Unbought(SyncItemId id, NonEmptyTrimmedString title, TrimmedString description) => TryCreate(id, title, description, new Unknown());
    public static OneOf<ShoppingListItem, Error<string>> Unbought(SyncItemId id, string title, string description) => FromPrimitiveTypes(id, title, description, (DateTimeOffset?)null);
    public static OneOf<ShoppingListItem, Error<string>> New(NonEmptyTrimmedString title, TrimmedString description) => TryCreate(SyncItemId.Unknown, title, description, new Unknown());
    public static OneOf<ShoppingListItem, Error<string>> New(string title, string description) => FromPrimitiveTypes(SyncItemId.Unknown, title, description, (DateTimeOffset?)null);

    public SyncItemId Id { get; init; }

    public NonEmptyTrimmedString Title { get; init; }

    public TrimmedString Description { get; init; }

    public OneOf<DateTimeOffset, Unknown> BoughtAt { get; init; }

    public bool WasBought => BoughtAt.Match(_ => true, _ => false);

    public bool WasSynced => Id.Match(_ => true, _ => false);

    /// <summary>
    /// Determines whether this item should be regarded as the same as <paramref name="other"/>.
    /// Two items are regarded as the same if they have the same title,
    /// or if both have a known id and the ids are equal.
    /// </summary>
    public bool IsRegardedAsSameAs(ShoppingListItem? other)
    {
        if (other is null)
            return false;
        if (this.Title == other.Title)
            return true;
        // If the titles are not the same, we need to check whether one of the items
        // was already persisted and has the same Id as the other item.
        return this.Id.Match(
            id => other.Id.Match(
                otherid => id == otherid,
                _ => false),
            _ => false);
    }

    public static explicit operator ShoppingListItem(OneOf<ShoppingListItem, Error<string>> instance) => instance.Match(item => item, error => throw new InvalidCastException($"The underlying value was an instance of {typeof(Error<string>).Name}, not an instance of {typeof(ShoppingListItem).Name}"));
}
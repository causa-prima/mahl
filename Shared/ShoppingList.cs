namespace mahl.Shared;

using OneOf;
using OneOf.Types;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;

public abstract record ShoppingListType
{
    public abstract IImmutableSet<ShoppingListItem> Items { get; }

    public static explicit operator ShoppingListType(OneOf<ShoppingListType, Error<string>> instance)
        => instance.Match(list => list, error => throw new InvalidCastException($"The underlying value was an instance of {typeof(Error<string>).Name}, not an instance of {typeof(ShoppingListType).Name}"));
}

internal sealed record EmptyShoppingListType : ShoppingListType
{
    public override IImmutableSet<ShoppingListItem> Items => ImmutableHashSet<ShoppingListItem>.Empty;
}

internal sealed record PopulatedShoppingListType(IEnumerable<ShoppingListItem> items) : ShoppingListType
{
    public override IImmutableSet<ShoppingListItem> Items => items.ToImmutableHashSet();
}

public static class ShoppingList
{
    public static readonly ShoppingListType Empty = new EmptyShoppingListType();

    public static OneOf<ShoppingListType, Error<string>> Create(IEnumerable<ShoppingListItem> items)
        => items.Any() switch
        {
            false => Empty,
            true => items.Aggregate((OneOf<ShoppingListType, Error<string>>)new EmptyShoppingListType(),
                                    (acc, item) => acc.Bind(acc => acc.Add(item)))
        };

    public static OneOf<ShoppingListType, Error<string>> Add(this ShoppingListType shoppingList, ShoppingListItem item)
        => shoppingList.Contains(item) switch
        {
            false => new PopulatedShoppingListType(shoppingList.Items.Add(item)),
            true => new Error<string>($"Item with id {item.Id} already in list.")
        };

    public static OneOf<ShoppingListType, Error<string>> Update(this ShoppingListType shoppingList, ShoppingListItem item)
        => shoppingList.Items.Where(i => i.IsRegardedAsSameAs(item)).ToList() switch
        {
            []
                => new Error<string>($"Item with id {item.Id} not in list."),
            [var foundItem]
                => ValidateUpdateRules(foundItem, item).Bind<Success, ShoppingListType, Error<string>>(
                    success => new PopulatedShoppingListType(shoppingList.Items.Where(i => !i.IsRegardedAsSameAs(item)).Union([item]))),
            _ => throw new InvalidOperationException("Shopping list invariant violated: multiple equivalent items found."),
        };

    private static OneOf<Success, Error<string>> ValidateUpdateRules(ShoppingListItem existing, ShoppingListItem updated)
    => (existing, updated) switch
    {
        var (e, u) when e.Id != u.Id
            => new Error<string>("The id of an item must not be changed."),
        var (e, u) when e.Title != u.Title
            => new Error<string>("The title of an item must not be changed."),
        _ => new Success()
    };

    public static bool Contains(this ShoppingListType shoppingList, ShoppingListItem item)
        => shoppingList.Items.Where(i => i.IsRegardedAsSameAs(item)).Any();

    public static IEnumerable<T> Select<T>(this ShoppingListType shoppingList, Func<ShoppingListItem, T> func)
        => shoppingList.Items.Select(func);

    public static async Task ApplyAsync(this ShoppingListType shoppingList, Func<IEnumerable<ShoppingListItem>, Task> asyncAction)
        => await asyncAction(shoppingList.Items);

    public static IEnumerable<ShoppingListItem> GetBoughtItems(this ShoppingListType shoppingList)
        => shoppingList.Items.Where(i => i.WasBought);

    public static IEnumerable<ShoppingListItem> GetUnboughtItems(this ShoppingListType shoppingList)
        => shoppingList.Items.Where(i => !i.WasBought);

    public static bool Any(this ShoppingListType shoppingList) =>
        shoppingList.Items.Any();

}


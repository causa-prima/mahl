namespace mahl.Shared.Dtos;
using OneOf;
using OneOf.Types;
using System.Collections.Immutable;
using System.Linq;

public class ShoppingListDto
{
    public IImmutableList<ShoppingListItemDto> Items { get; set; } = ImmutableList<ShoppingListItemDto>.Empty;
}

public static partial class Mappings
{
    public static OneOf<ShoppingListType, Error<string>> MapToDomain(this ShoppingListDto list) =>
        list.Items.Aggregate(
            (OneOf<ShoppingListType, Error<string>>)ShoppingList.Empty,
            (acc, dtoItem) => acc.Bind(
                shoppingList => dtoItem.MapToDomain().Bind(
                    domainItem => shoppingList.Add(domainItem)
                    )
                )
            );

    public static ShoppingListDto MapToDto(this ShoppingListType item) =>
        new ShoppingListDto
        {
            Items = item.Items.Select(MapToDto).ToImmutableList(),
        };
}

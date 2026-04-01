namespace mahl.Server.Dtos;

public record ShoppingListResponseDto(IReadOnlyList<ShoppingListItemDto> OpenItems, IReadOnlyList<ShoppingListItemDto> BoughtItems);

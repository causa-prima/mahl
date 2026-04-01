namespace mahl.Server.Dtos;

/// <param name="Quantity">Menge des Eintrags. NULL bedeutet "Menge nicht angegeben" (entspricht semantisch 1).</param>
/// <param name="Unit">Einheit. NULL wenn Quantity NULL ist.</param>
public record ShoppingListItemDto(Guid Id, Guid IngredientId, string IngredientName, decimal? Quantity, string? Unit, DateTimeOffset? BoughtAt);

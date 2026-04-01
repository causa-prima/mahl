namespace mahl.Server.Dtos;

/// <param name="Quantity">Menge der Zutat. NULL bedeutet "nach Geschmack" (keine definierte Menge).</param>
/// <param name="Unit">Einheit. NULL wenn Quantity NULL ist.</param>
public record RecipeIngredientDto(Guid Id, Guid IngredientId, string IngredientName, decimal? Quantity, string? Unit);

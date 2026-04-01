namespace mahl.Server.Dtos;

/// <param name="Quantity">Menge der Zutat. NULL bedeutet "nach Geschmack" (keine definierte Menge). Wenn angegeben, muss der Wert größer als 0 sein.</param>
/// <param name="Unit">Einheit. Pflicht wenn Quantity angegeben; NULL wenn Quantity NULL ist.</param>
public record CreateRecipeIngredientDto(Guid IngredientId, decimal? Quantity, string? Unit);

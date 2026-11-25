namespace mahl.Server.Dtos;

// Ein Eintrag der Einkaufsliste (GET /api/shopping-list), im Glossar „Shopping List Item“. Quantity und Unit sind
// beide null, wenn die Zutat in allen Rezepten ohne Menge steht (ADR-S020-1).
internal sealed record ShoppingListItemDto(string Name, decimal? Quantity, string? Unit);

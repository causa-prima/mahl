namespace mahl.Server.Dtos;

// Name und Unit sind die gespeicherten Werte der Zutat (Unit = Basiseinheit, ADR-S135-2).
// ADR-S020-1: Quantity und Unit sind beide null (ohne Menge) oder beide gesetzt – null nur hier an
// der Grenze, im Domain-Typ ist es der Sum-Type Quantity.
internal sealed record RecipeIngredientDto(string Name, decimal? Quantity, string? Unit);

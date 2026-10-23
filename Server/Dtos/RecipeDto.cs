namespace mahl.Server.Dtos;

// ADR-S068-1: der POST-201-Body trägt das ganze Rezept. Zutaten in Zeilenreihenfolge, Schritte in
// Listenreihenfolge.
internal sealed record RecipeDto(Guid Id, string Title, IReadOnlyList<RecipeIngredientDto> Ingredients, IReadOnlyList<StepDto> Steps);

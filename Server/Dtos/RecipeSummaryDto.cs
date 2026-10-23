namespace mahl.Server.Dtos;

// Ein Eintrag der Rezept-Liste (GET /api/recipes).
internal sealed record RecipeSummaryDto(Guid Id, string Title);

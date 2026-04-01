namespace mahl.Server.Dtos;

public record WeeklyPoolEntryDto(Guid Id, Guid RecipeId, string RecipeTitle, DateTimeOffset AddedAt);

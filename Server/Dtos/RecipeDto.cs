namespace mahl.Server.Dtos;

public record RecipeDto(
    Guid Id,
    string Title,
    Uri? SourceUrl,
    IReadOnlyList<RecipeIngredientDto> Ingredients,
    IReadOnlyList<StepDto> Steps);

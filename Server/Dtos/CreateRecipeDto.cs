namespace mahl.Server.Dtos;

public record CreateRecipeDto(string Title, Uri? SourceUrl, IReadOnlyList<CreateRecipeIngredientDto> Ingredients, IReadOnlyList<CreateStepDto> Steps);

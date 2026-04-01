namespace mahl.Server.Dtos;

public record IngredientDto(Guid Id, string Name, string DefaultUnit, bool AlwaysInStock);

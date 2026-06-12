namespace mahl.Server.Dtos;

#pragma warning disable CA1812 // instantiated by ASP.NET Core model binding via reflection
internal sealed record CreateIngredientDto(string Name, string DefaultUnit);
#pragma warning restore CA1812

using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Types;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;

namespace mahl.Server.Endpoints;

internal static class IngredientsEndpoints
{
    internal static void MapIngredientsEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/ingredients");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact
        group.WithTags("Ingredients");

        group.MapGet(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (MahlDbContext db) =>
            {
                var ingredients = await db.Ingredients
                    .Select(i => new IngredientDto(i.Id, i.Name, i.DefaultUnit))
                    .ToListAsync();
                return Results.Ok(ingredients);
            });

        group.MapPost(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (CreateIngredientDto dto, MahlDbContext db) =>
                await dto.ToDomain()
                    .MapError<Ingredient, Error<string>, IResult>(e => Results.UnprocessableEntity(e.Value))
                    .BindAsync<Ingredient, IngredientDto, IResult>(async ingredient =>
                    {
                        db.Ingredients.Add(ingredient.ToDbType());
                        await db.SaveChangesAsync();
                        return ingredient.ToDto();
                    })
                    .MatchAsync(
                        created => Results.Created($"/api/ingredients/{created.Id}", created),
                        error => error));
    }
}

file static class IngredientMappings
{
    public static OneOf<Ingredient, Error<string>> ToDomain(this CreateIngredientDto dto) =>
        NonEmptyTrimmedString.Create(dto.Name)
            .Bind(name => NonEmptyTrimmedString.Create(dto.DefaultUnit)
                // ADR-S030-1: server-side UUIDv7 primary key.
                .Map(unit => Ingredient.Create(Guid.CreateVersion7(), name, unit)));

    public static IngredientDbType ToDbType(this Ingredient domain) =>
        new() { Id = domain.Id, Name = domain.Name.Value, DefaultUnit = domain.DefaultUnit.Value };

    public static IngredientDto ToDto(this Ingredient domain) =>
        new(domain.Id, domain.Name.Value, domain.DefaultUnit.Value);
}

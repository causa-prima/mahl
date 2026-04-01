namespace mahl.Server.Endpoints;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;

public static class IngredientsEndpoints
{
    public static void MapIngredientsEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/ingredients");
        // Stryker disable once String,Statement : Tag name has no routing or behavioral impact
        group.WithTags("Ingredients");

        group.MapGet(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (MahlDbContext db) =>
        {
            var dbIngredients = await db.Ingredients
                .Where(i => i.DeletedAt == null)
                .OrderBy(i => i.Name)
                .ToListAsync();

            IResult? firstError = null;
            var dtos = new List<IngredientDto>(dbIngredients.Count);
            foreach (var i in dbIngredients)
                i.ToDomain().Switch(
                    domain => dtos.Add(domain.ToDto(i.Id, i.AlwaysInStock)),
                    e => firstError ??= Results.Problem(e.Value, statusCode: StatusCodes.Status500InternalServerError));

            return firstError ?? Results.Ok(dtos);
        });

        group.MapGet("/{id:guid}", async (Guid id, MahlDbContext db) =>
        {
            var ingredient = await db.Ingredients
                .Where(i => i.Id == id && i.DeletedAt == null)
                .FirstOrDefaultAsync();
            if (ingredient is null) return Results.NotFound();
            return ingredient.ToDomain().Match(
                domain => Results.Ok(domain.ToDto(ingredient.Id, ingredient.AlwaysInStock)),
                e => Results.Problem(e.Value, statusCode: StatusCodes.Status500InternalServerError));
        });

        // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
        group.MapPost("/", async (CreateIngredientDto dto, MahlDbContext db) =>
            await Ingredient.Create(Guid.CreateVersion7(), dto.Name, dto.DefaultUnit)
                .MapError<Ingredient, Error<string>, IResult>(e => Results.UnprocessableEntity(e.Value))
                .BindAsync<Ingredient, (IngredientDbType entity, Ingredient domain), IResult>(async ingredient =>
                {
                    var softDeleted = await db.Ingredients
                        .FirstOrDefaultAsync(i => i.Name == ingredient.Name.Value && i.DeletedAt != null);
                    if (softDeleted != null)
                        return OneOf<(IngredientDbType entity, Ingredient domain), IResult>.FromT1(
                            Results.Conflict(new SoftDeletedConflictDto("ingredient_soft_deleted", softDeleted.Id)));

                    var exists = await db.Ingredients
                        .AnyAsync(i => i.Name == ingredient.Name.Value && i.DeletedAt == null);
                    if (exists)
                        return OneOf<(IngredientDbType entity, Ingredient domain), IResult>.FromT1(
                            Results.Conflict($"Eine Zutat mit dem Namen '{ingredient.Name}' existiert bereits."));

                    var entity = new IngredientDbType
                    {
                        Id = ingredient.Id,
                        Name = ingredient.Name.Value,
                        DefaultUnit = ingredient.DefaultUnit.Value
                    };
                    db.Ingredients.Add(entity);
                    await db.SaveChangesAsync();
                    return (entity, ingredient);
                })
                .MatchAsync(
                    result => Results.Created($"/api/ingredients/{result.entity.Id}",
                        result.domain.ToDto(result.entity.Id, result.entity.AlwaysInStock)),
                    error => error));

        group.MapPost("/{id:guid}/restore", async (Guid id, MahlDbContext db) =>
        {
            var ingredient = await db.Ingredients.FindAsync(id);
            if (ingredient is null) return Results.NotFound();
            if (ingredient.DeletedAt == null) return Results.Conflict("Zutat ist bereits aktiv.");
            ingredient.DeletedAt = null;
            await db.SaveChangesAsync();
            return ingredient.ToDomain().Match(
                domain => Results.Ok(domain.ToDto(ingredient.Id, ingredient.AlwaysInStock)),
                e => Results.Problem(e.Value, statusCode: StatusCodes.Status500InternalServerError));
        });

        group.MapDelete("/{id:guid}", async (Guid id, MahlDbContext db) =>
        {
            var ingredient = await db.Ingredients.FindAsync(id);
            if (ingredient is null || ingredient.DeletedAt != null) return Results.NotFound();
            ingredient.DeletedAt = DateTimeOffset.UtcNow;
            await db.SaveChangesAsync();
            return Results.NoContent();
        });
    }
}

file static class IngredientMappings
{
    public static OneOf<Ingredient, Error<string>> ToDomain(this IngredientDbType db) =>
        Ingredient.Create(db.Id, db.Name, db.DefaultUnit)
            .MapError(e => new Error<string>($"DB inconsistency in Ingredient #{db.Id}: {e.Value}"));

    public static IngredientDto ToDto(this Ingredient domain, Guid id, bool alwaysInStock) =>
        new(id, domain.Name.Value, domain.DefaultUnit.Value, alwaysInStock);
}

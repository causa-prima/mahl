namespace mahl.Server.Endpoints;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;

public static class RecipesEndpoints
{
    public static void MapRecipesEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/recipes");
        // Stryker disable once String,Statement : Tag name has no routing or behavioral impact
        group.WithTags("Recipes");

        group.MapGet(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (MahlDbContext db) =>
        {
            var recipes = await db.Recipes
                .Where(r => r.DeletedAt == null)
                .OrderBy(r => r.Title)
                .ToListAsync();
            return recipes
                .Select(r => r.ToSummaryDtoOrError())
                .Sequence()
                .Match<IResult>(
                    dtos => Results.Ok(dtos.ToList()),
                    e => Results.Problem(e.Value, statusCode: StatusCodes.Status500InternalServerError));
        });

        group.MapPost(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (CreateRecipeDto dto, MahlDbContext db) =>
            {
                var ingredientIds = dto.Ingredients.Select(i => i.IngredientId).ToList();
                var foundIngredients = await db.Ingredients
                    .Where(i => ingredientIds.Contains(i.Id) && i.DeletedAt == null)
                    .ToListAsync();
                if (foundIngredients.Count != ingredientIds.Count)
                    return Results.UnprocessableEntity("Eine oder mehrere Zutaten wurden nicht gefunden.");

                var ingredientLookup = foundIngredients.ToDictionary(i => i.Id);
                return await Recipe.Create(
                        Guid.CreateVersion7(),
                        dto.Title,
                        dto.SourceUrl,
                        dto.Ingredients.Select(i => (Guid.CreateVersion7(), i.IngredientId, ingredientLookup[i.IngredientId].Name, ingredientLookup[i.IngredientId].DefaultUnit, i.Quantity, i.Unit)).ToList().AsReadOnly(),
                        dto.Steps.Select(s => (Guid.CreateVersion7(), s.Instruction)).ToList().AsReadOnly())
                    .MapError<Recipe, Error<string>, IResult>(e => Results.UnprocessableEntity(e.Value))
                    .BindAsync(async domain =>
                    {
                        var recipe = new RecipeDbType
                        {
                            Id = domain.Id,
                            Title = domain.Title.Value,
                            SourceUrl = (string?)domain.Source,
                            Ingredients = domain.Ingredients.Value.Select((i, idx) => new RecipeIngredientDbType
                            {
                                Id = i.Id,
                                Ingredient = ingredientLookup[i.Ingredient.Id],
                                Quantity = i.Quantity.Match((v, _) => (decimal?)v, () => null),
                                Unit = i.Quantity.Match((_, u) => (string?)u, () => null)
                            }).ToList(),
                            Steps = domain.Steps.Value.Select((s, idx) => new StepDbType
                            {
                                Id = s.Id,
                                StepNumber = idx + 1,
                                Instruction = s.Instruction.Value
                            }).ToList()
                        };
                        db.Recipes.Add(recipe);
                        await db.SaveChangesAsync();
                        return (OneOf<Recipe, IResult>) domain;
                    })
                    .MatchAsync(
                        domain => Results.Created($"/api/recipes/{domain.Id}", domain.ToDto()),
                        error => error);
            });

        group.MapDelete("/{id:guid}", async (Guid id, MahlDbContext db) =>
        {
            var recipe = await db.Recipes.FindAsync(id);
            if (recipe is null || recipe.DeletedAt != null) return Results.NotFound();
            recipe.DeletedAt = DateTimeOffset.UtcNow;
            await db.SaveChangesAsync();
            return Results.NoContent();
        });

        group.MapGet("/{id:guid}", async (Guid id, MahlDbContext db) =>
        {
            var recipe = await db.Recipes
                .Where(r => r.Id == id && r.DeletedAt == null)
                .Include(r => r.Ingredients).ThenInclude(i => i.Ingredient)
                .Include(r => r.Steps)
                .FirstOrDefaultAsync();
            if (recipe is null) return Results.NotFound();
            return recipe.ToDomain().Match(
                domain => Results.Ok(domain.ToDto()),
                e => Results.Problem(e.Value, statusCode: StatusCodes.Status500InternalServerError));
        });
    }
}

file static class RecipeMappings
{
    public static OneOf<Recipe, Error<string>> ToDomain(this RecipeDbType db)
    {
        Uri? sourceUri = null;
        if (db.SourceUrl is not null && !Uri.TryCreate(db.SourceUrl, UriKind.Absolute, out sourceUri))
            return new Error<string>($"DB inconsistency in Recipe #{db.Id}: Ungültige URL '{db.SourceUrl}'.");
        return Recipe.Create(
                db.Id,
                db.Title,
                sourceUri,
                db.Ingredients.Select(i => (i.Id, i.IngredientId, i.Ingredient.Name, i.Ingredient.DefaultUnit, i.Quantity, i.Unit)).ToList().AsReadOnly(),
                db.Steps.OrderBy(s => s.StepNumber).Select(s => (s.Id, s.Instruction)).ToList().AsReadOnly())
            .MapError(e => new Error<string>($"DB inconsistency in Recipe #{db.Id}: {e.Value}"));
    }

    public static RecipeDto ToDto(this Recipe domain) =>
        new(
            domain.Id, domain.Title.Value,
            domain.Source.Match(url => (Uri?)url, () => null),
            domain.Ingredients.Value.Select(i => new RecipeIngredientDto(
                i.Id, i.Ingredient.Id, i.Ingredient.Name,
                i.Quantity.Match((v, _) => (decimal?)v, () => null),
                i.Quantity.Match((_, u) => (string?)u, () => null))).ToList(),
            domain.Steps.Value.Select(s => new StepDto(s.Id, s.Instruction.Value)).ToList());

    public static OneOf<RecipeSummaryDto, Error<string>> ToSummaryDtoOrError(this RecipeDbType r)
    {
        Uri? sourceUri = null;
        if (r.SourceUrl is not null && !Uri.TryCreate(r.SourceUrl, UriKind.Absolute, out sourceUri))
            return new Error<string>($"DB inconsistency in Recipe #{r.Id}: Ungültige URL '{r.SourceUrl}'.");
        return new RecipeSummaryDto(r.Id, r.Title, sourceUri);
    }
}

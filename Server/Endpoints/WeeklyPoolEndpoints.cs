namespace mahl.Server.Endpoints;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Dtos;
using Microsoft.EntityFrameworkCore;

public static class WeeklyPoolEndpoints
{
    public static void MapWeeklyPoolEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/weekly-pool");
        // Stryker disable once String,Statement : Tag name has no routing or behavioral impact
        group.WithTags("WeeklyPool");

        group.MapGet(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (MahlDbContext db) =>
        {
            var entries = await db.WeeklyPoolEntries
                .Select(e => new WeeklyPoolEntryDto(e.Id, e.RecipeId, e.Recipe.Title, e.AddedAt))
                .ToListAsync();
            return Results.Ok(entries);
        });

        group.MapPost(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (AddToPoolDto dto, MahlDbContext db) =>
        {
            var recipeExists = await db.Recipes.AnyAsync(r => r.Id == dto.RecipeId && r.DeletedAt == null);
            if (!recipeExists) return Results.UnprocessableEntity("Rezept nicht gefunden.");
            var alreadyInPool = await db.WeeklyPoolEntries.AnyAsync(e => e.RecipeId == dto.RecipeId);
            if (alreadyInPool) return Results.Conflict("Rezept ist bereits im Wochenplan.");
            var entry = new WeeklyPoolEntryDbType { RecipeId = dto.RecipeId };
            db.WeeklyPoolEntries.Add(entry);
            await db.SaveChangesAsync();
            return Results.Created($"/api/weekly-pool/{entry.Id}",
                new WeeklyPoolEntryDto(entry.Id, entry.RecipeId, "", entry.AddedAt));
        });

        group.MapDelete("/recipes/{recipeId:guid}", async (Guid recipeId, MahlDbContext db) =>
        {
            var entries = await db.WeeklyPoolEntries.Where(e => e.RecipeId == recipeId).ToListAsync();
            db.WeeklyPoolEntries.RemoveRange(entries);
            await db.SaveChangesAsync();
            return Results.NoContent();
        });
    }
}

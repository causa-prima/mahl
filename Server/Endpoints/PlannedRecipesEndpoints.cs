using mahl.Infrastructure;
using mahl.Server.Dtos;
using Microsoft.EntityFrameworkCore;

namespace mahl.Server.Endpoints;

internal static class PlannedRecipesEndpoints
{
    internal static void MapPlannedRecipesEndpoints(this WebApplication app)
    {
        var group = app.MapGroup($"{ApiRoutes.Prefix}/planned-recipes");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact (ADR-S136-1)
        group.WithTags("PlannedRecipes");

        // ADR-S153-1: GET listet die vorgemerkten Rezepte. Die Sortierung folgt mit der Vorgemerkt-Seite.
        group.MapGet(
            "",
            async (MahlDbContext db, CancellationToken ct) =>
                Results.Ok(await db.PlannedRecipes
                    .Join(db.Recipes, p => p.RecipeId, r => r.Id, (_, r) => new RecipeSummaryDto(r.Id, r.Title))
                    .ToListAsync(ct)));

        // ADR-S153-1: Vormerken setzt einen Zielzustand und ist idempotent – ein schon vorgemerktes Rezept
        // antwortet wie beim ersten Mal 204. ADR-S105-2: Kein Check-then-Insert; die Datenbank entscheidet
        // (ON CONFLICT DO NOTHING auf dem Primärschlüssel).
        group.MapPut(
            "{recipeId:guid}",
            async (Guid recipeId, MahlDbContext db, CancellationToken ct) =>
            {
                await db.PlanRecipeAsync(recipeId, ct);
                return Results.NoContent();
            });
    }
}

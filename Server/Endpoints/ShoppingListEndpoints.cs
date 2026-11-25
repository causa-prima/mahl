using mahl.Infrastructure;
using mahl.Server.Dtos;
using Microsoft.EntityFrameworkCore;

namespace mahl.Server.Endpoints;

internal static class ShoppingListEndpoints
{
    internal static void MapShoppingListEndpoints(this WebApplication app)
    {
        var group = app.MapGroup($"{ApiRoutes.Prefix}/shopping-list");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact (ADR-S136-1)
        group.WithTags("ShoppingList");

        // ADR-S154-3: Name und Einheit kommen aus der Zutat, sortiert wie die Zutaten-Liste (ADR-S142-1).
        // ADR-S020-1: ohne Menge sind Menge und Einheit beide null.
        group.MapGet(
            "",
            async (MahlDbContext db, CancellationToken ct) =>
                Results.Ok(await db.Ingredients
                    .OrderedByName()
                    .Join(
                        db.ShoppingListItems,
                        ingredient => ingredient.Id,
                        item => item.IngredientId,
                        (ingredient, item) => new ShoppingListItemDto(
                            ingredient.Name, item.Quantity, item.Quantity == null ? null : ingredient.BaseUnit))
                    .ToListAsync(ct)));

        // ADR-S154-2/-3: Übernehmen liest die Vormerkungen auf dem Server und ersetzt die Liste; 204 ohne Body.
        group.MapPost(
            "generate",
            async (MahlDbContext db, CancellationToken ct) =>
            {
                await db.ReplaceShoppingListFromPlannedRecipesAsync(ct);
                return Results.NoContent();
            });
    }
}

namespace mahl.Server.Endpoints;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Dtos;
using Microsoft.EntityFrameworkCore;

public static class ShoppingListEndpoints
{
    public static void MapShoppingListEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/shopping-list");
        // Stryker disable once String,Statement : Tag name has no routing or behavioral impact
        group.WithTags("ShoppingList");

        group.MapGet(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (MahlDbContext db) =>
        {
            var items = await db.ShoppingListItems
                .Select(i => new ShoppingListItemDto(
                    i.Id, i.IngredientId, i.Ingredient.Name, i.Quantity, i.Unit, i.BoughtAt))
                .ToListAsync();

            var openItems = items.Where(i => i.BoughtAt == null).ToList();
            var boughtItems = items.Where(i => i.BoughtAt != null).ToList();
            return Results.Ok(new ShoppingListResponseDto(openItems, boughtItems));
        });

        group.MapPost("/generate", async (MahlDbContext db) =>
        {
            var recipeIngredients = await db.WeeklyPoolEntries
                .SelectMany(e => e.Recipe.Ingredients)
                .Select(i => new { i.Ingredient.Id, i.Ingredient.Name, i.Quantity, i.Unit })
                .ToListAsync();

            var existing = await db.ShoppingListItems.ToListAsync();
            db.ShoppingListItems.RemoveRange(existing);

            var newItems = recipeIngredients
                .Select(i => new ShoppingListItemDbType
                {
                    IngredientId = i.Id,
                    Quantity = i.Quantity,
                    Unit = i.Unit
                })
                .ToList();

            db.ShoppingListItems.AddRange(newItems);
            await db.SaveChangesAsync();

            var items = newItems.Zip(recipeIngredients, (item, src) => new ShoppingListItemDto(
                item.Id, item.IngredientId, src.Name, item.Quantity, item.Unit, item.BoughtAt)).ToList();

            return Results.Ok(new ShoppingListResponseDto(items, []));
        });

        group.MapPut("/items/{id:guid}/check", async (Guid id, MahlDbContext db) =>
        {
            var item = await db.ShoppingListItems.FindAsync(id);
            if (item is null) return Results.NotFound();
            item.BoughtAt = DateTimeOffset.UtcNow;
            await db.SaveChangesAsync();
            return Results.NoContent();
        });

        group.MapPut("/items/{id:guid}/uncheck", async (Guid id, MahlDbContext db) =>
        {
            var item = await db.ShoppingListItems.FindAsync(id);
            if (item is null) return Results.NotFound();
            item.BoughtAt = null;
            await db.SaveChangesAsync();
            return Results.NoContent();
        });
    }
}

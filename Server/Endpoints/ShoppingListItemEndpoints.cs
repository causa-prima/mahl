namespace mahl.Server.Endpoints;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Shared;
using mahl.Shared.Dtos;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;

public static class ShoppingListItemEndpoints
{
    public static void MapShoppingListItemEndpoints(this IEndpointRouteBuilder routes)
    {
        // POST: Add a new ShoppingListItem, returnin an error if it already (should) exists
        routes.MapPost(RouteBases.ShoppingListItem, async (ShoppingListItemDto itemToCreate, MariaDbContext dbContext, HttpContext context, ILogger<Program> logger) =>
              await itemToCreate.MapToDomain().Match(
                async domainItem => await (await AddItem(domainItem, dbContext)).Match(
                    async dbItem => await dbItem.MapToDomain().Match(
                        async item =>
                        {
                            await dbContext.SaveChangesAsync();
                            return Results.Ok(item.MapToDto());
                        },
                        // Stryker disable all: This error should never happen, as we just created the item from valid data
                        error =>
                        {
                            logger.LogMappingError(typeof(ShoppingListItem), dbItem, error.Value);
                            return Task.FromResult(Helpers.CreateProblemWithTraceId(context));
                        }
                        // Stryker restore all
                        ),
                    error => Task.FromResult(Results.UnprocessableEntity(error.Value))
                    ),
                domainMappingError => Task.FromResult(Results.UnprocessableEntity(domainMappingError.Value))
             )
        );

        // PUT: Update an existing ShoppingListItem, returning an error if the item does not exist or the update is not valid
        routes.MapPut(RouteBases.ShoppingListItem, async (ShoppingListItemDto itemToUpdate, MariaDbContext dbContext, HttpContext context, ILogger<Program> logger) =>
            await itemToUpdate.MapToDomain().Match(
                async domainItem => await (await UpdateItem(domainItem, dbContext)).Match(
                    async dbItem => await dbItem.MapToDomain().Match(
                        async item =>
                        {
                            await dbContext.SaveChangesAsync();
                            return Results.Ok(item.MapToDto());
                        },
                        // Stryker disable all: This error should never happen, as we just updated the item from valid data
                        error =>
                        {
                            logger.LogMappingError(typeof(ShoppingListItem), dbItem, error.Value);
                            return Task.FromResult(Helpers.CreateProblemWithTraceId(context));
                        }
                        // Stryker restore all
                        ),
                    notFound => Task.FromResult(Results.NotFound()),
                    error => Task.FromResult(Results.UnprocessableEntity(error.Value))
                    ),
                domainMappingError => Task.FromResult(Results.UnprocessableEntity(domainMappingError.Value))
             )
        );
    }

    private static async Task<OneOf<ShoppingListItemDBType, NotFound, Error<string>>>
        UpdateItem(ShoppingListItem itemToUpdate, MariaDbContext dbContext)
        =>
            (await itemToUpdate.Id.Match(
                async id => await dbContext.ShoppingListItems.FindAsync(id) switch
                            {
                                null => new NotFound(),
                                var foundItem when foundItem.Title != itemToUpdate.Title => new Error<string>(
                                     $"There already was an item with the ID {foundItem.Id} with a different title,"
                                    + " but an items title must not change.\n"
                                    + $"\tTitle of item to update: {itemToUpdate.Title}\n"
                                    + $"\tTitle of item in database: {foundItem.Title}"),
                                var foundItem => foundItem.Update(itemToUpdate)
                            },
                _ => Task.FromResult<OneOf<ShoppingListItemDBType, NotFound, Error<string>>>(
                    new Error<string>("The Id of the item is empty,"
                        + " thus the item can not have been added to the database yet."))
                )
            );

    private static async Task<OneOf<ShoppingListItemDBType, Error<string>>>
        AddItem(ShoppingListItem item, MariaDbContext dbContext)
        => await item.Id.Match(
            id => Task.FromResult<OneOf<ShoppingListItemDBType, Error<string>>>(
                new Error<string>("The Id of the item is not empty, thus the item must already have been added to the database.")),
            async _ => await dbContext.ShoppingListItems
                            .Where(i => i.Title == item.Title)
                            .Select(i => i.Id)
                            .ToListAsync() switch
                        {
                            [] => item.AddToDbContext(dbContext),
                            var list => new Error<string>(
                                "Item(s) with same title found when trying to add item, but the tile must be unique. "
                                + "Ids of these Items:\n\t"
                                + string.Join("\n\t", list))
                        });


    private static ShoppingListItemDBType AddToDbContext(this ShoppingListItem item, MariaDbContext dbContext)
    {
        var dbItem = item.MapToDBType();
        dbContext.ShoppingListItems.Add(dbItem);
        return dbItem;
    }

    private static ShoppingListItemDBType Update(this ShoppingListItemDBType item, ShoppingListItem updatedItem)
    {
        item.Description = updatedItem.Description;
        item.BoughtAt = updatedItem.BoughtAt.Match(
            dt => dt,
            _ => (DateTimeOffset?)null
            );

        return item;
    }
}
namespace mahl.Server.Endpoints;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Shared;
using mahl.Shared.Dtos;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;

public static class ShoppingListEndpoints
{
    public static void MapShoppingListEndpoints(this IEndpointRouteBuilder routes)
    {
        // GET: Retrieve all ShoppingListItems
        routes.MapGet(RouteBases.ShoppingList, async (MariaDbContext dbContext, HttpContext context, ILogger<Program> logger) =>
        (await dbContext.ShoppingListItems
                        .Where(i => i.BoughtAt == null)
                        .ToListAsync())
                        .Aggregate((OneOf<ShoppingListType, Error<(ShoppingListItemDBType DBItem, string ErrorString)>>)ShoppingList.Empty,
                            (acc, dbItem) => acc.Bind(
                                list => dbItem.MapToDomain().Match(
                                    item => list.Add(item)
                                                .MapError(
                                                    addingError => new Error<(ShoppingListItemDBType, string)>((dbItem, addingError.Value))),
                                    domainMappingError => new Error<(ShoppingListItemDBType DBItem, string ErrorString)>((dbItem, domainMappingError.Value)))))
                        .Match(
                            list => Results.Ok(list.MapToDto()),
                            error =>
                            {
                                logger.LogMappingError(typeof(ShoppingList), error);
                                return Helpers.CreateProblemWithTraceId(context);
                            })
         );

        // PUT: Bulk update using a collection of ShoppingListItems
        //routes.MapPut(RouteBases.ShoppingList, async (ShoppingListDto listToUpdate, MariaDbContext dbContext) =>
        //{
        //    var (storedItems, failedItems, errorItems) =
        //            await listToUpdate.Items
        //                .Aggregate(
        //                    Task.FromResult((
        //                        storedItems: Enumerable.Empty<ShoppingListItemDBType>(),
        //                        failedItems: Enumerable.Empty<ShoppingListItem>(),
        //                        errorItems: Enumerable.Empty<(ShoppingListItem, string)>()
        //                    )),
        //                    async (accTask, item) =>
        //                    {
        //                        var acc = await accTask;
        //                        var result = await UpdateItem(item, dbContext);
        //                        return result.Match(
        //                            storedItem => (acc.storedItems.Append(storedItem), acc.failedItems, acc.errorItems),
        //                            notFound => (acc.storedItems, acc.failedItems.Append(item), acc.errorItems),
        //                            error => (acc.storedItems, acc.failedItems, acc.errorItems.Append((item, error.Value))));
        //                    });

        //    await dbContext.SaveChangesAsync();

        //    return Results.Ok(new BulkUpdateResult(storedItems, failedItems, errorItems));
        //});
    }
}
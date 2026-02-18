namespace mahl.Server.Endpoints;

using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Shared;
using mahl.Shared.Dtos;
using mahl.Shared.Types;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;
using System.Collections.Immutable;

public static class SuggestionsEndpoints
{
    public static void MapSuggestionEndpoints(this IEndpointRouteBuilder routes)
    {
        // GET: Get suggestions for ShoppingListItems based on a given text
        routes.MapGet($"{RouteBases.Suggestions}", async (string query, MariaDbContext dbContext, HttpContext context, ILogger<Program> logger) =>

            await NonEmptyTrimmedString.Create(query).Match(
                async success => await GetSuggestions(success.Value, dbContext, context, logger),
                error => Task.FromResult(Results.UnprocessableEntity($"Parameter {nameof(query)} was not valid: {error.Value}"))
             )
         );

        static async Task<IResult> GetSuggestions(NonEmptyTrimmedString query, MariaDbContext dbContext, HttpContext context, ILogger<Program> logger)
        {
            var searchResults = await GetPrioritizedDbItems(query, dbContext);

            return MapDbItemsToDomain(searchResults)
                .Match(
                    list => Results.Ok(list.Select(item => item.MapToDto())),
                    error =>
                    {
                        logger.LogMappingError(typeof(ShoppingListItem), error);
                        return Helpers.CreateProblemWithTraceId(context);
                    });

            static async Task<ImmutableList<ShoppingListItemDBType>> GetPrioritizedDbItems(NonEmptyTrimmedString query, MariaDbContext dbContext)
            {
                var searchResults = await dbContext.ShoppingListItems
                    .Where(i => i.Title.StartsWith(query, StringComparison.InvariantCultureIgnoreCase))
                    .Take(Constants.NumberOfSearchSuggestions)
                    .ToListAsync();

                var suggestionsLeft = Constants.NumberOfSearchSuggestions - searchResults.Count;
                if (suggestionsLeft > 0)
                {
                    var additionalSugestions = await dbContext.ShoppingListItems
                        .Where(i => !i.Title.StartsWith(query, StringComparison.InvariantCultureIgnoreCase)
                                    && i.Title.Contains(query, StringComparison.InvariantCultureIgnoreCase))
                        .Take(suggestionsLeft)
                        .ToListAsync();
                    searchResults.AddRange(additionalSugestions);
                }

                return ImmutableList.CreateRange(searchResults);
            }

            static OneOf<ImmutableList<ShoppingListItem>, Error<(ShoppingListItemDBType DBItem, string ErrorString)>>
                MapDbItemsToDomain(IEnumerable<ShoppingListItemDBType> dbItems)
                => dbItems.Aggregate((OneOf<ImmutableList<ShoppingListItem>, Error<(ShoppingListItemDBType DBItem, string ErrorString)>>)ImmutableList.Create<ShoppingListItem>(),
                                     (acc, dbItem) => acc.Bind(
                                         list => dbItem.MapToDomain().Match<OneOf<ImmutableList<ShoppingListItem>, Error<(ShoppingListItemDBType DBItem, string ErrorString)>>>(
                                             item => list.Add(item),
                                             domainMappingError => new Error<(ShoppingListItemDBType DBItem, string ErrorString)>((dbItem, domainMappingError.Value)))));
        }
        ;
    }
}
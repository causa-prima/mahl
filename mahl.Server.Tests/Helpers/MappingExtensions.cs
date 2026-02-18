namespace mahl.Server.Tests.Helpers;

using mahl.Server.Data.DatabaseTypes;
using mahl.Shared.Dtos;

internal static class MappingExtensions
{
    internal static ShoppingListItemDto MapToDto(this ShoppingListItemDBType dbType)
    {
        return new ShoppingListItemDto
        {
            Id = dbType.Id,
            Title = dbType.Title,
            Description = dbType.Description,
            BoughtAt = dbType.BoughtAt,
        };
    }
}

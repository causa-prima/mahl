namespace mahl.Shared.Dtos;

using OneOf;
using OneOf.Types;
using System;
using System.ComponentModel.DataAnnotations;

public record ShoppingListItemDto
{
    public int? Id { get; set; }

    [Required]
    [StringLength(Constants.ShoppingListTitleMaxLength, MinimumLength = 2)]
    public string Title { get; set; } = string.Empty;

    [StringLength(Constants.ShoppingListDescriptionMaxLength)]
    public string Description { get; set; } = string.Empty;

    public DateTimeOffset? BoughtAt { get; set; }
}

public static partial class Mappings
{
    public static OneOf<ShoppingListItem, Error<string>> MapToDomain(this ShoppingListItemDto item) =>
        ShoppingListItem.FromPrimitiveTypes(item.Id, item.Title, item.Description, item.BoughtAt);

    public static ShoppingListItemDto MapToDto(this ShoppingListItem item) =>
        new ShoppingListItemDto
        {
            Id = item.Id,
            Title = item.Title,
            Description = item.Description,
            BoughtAt = item.BoughtAt.Match(
                dt => dt,
                _ => (DateTimeOffset?)null
                )
        };
}
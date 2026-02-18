namespace mahl.Server.Data.DatabaseTypes;

using mahl.Shared;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Index(nameof(Title), nameof(Description), IsUnique = true), Table($"{nameof(ShoppingListItem)}")]
public class ShoppingListItemDBType
{
    [Key]
    public int Id { get; set; }

    [Required]
    [StringLength(Constants.ShoppingListTitleMaxLength, MinimumLength = 2)]
    public string Title { get; set; } = string.Empty;

    [StringLength(Constants.ShoppingListDescriptionMaxLength)]
    public string Description { get; set; } = string.Empty;

    public DateTimeOffset? BoughtAt { get; set; }
}

public static partial class Mappings
{
    public static OneOf<ShoppingListItem, Error<string>> MapToDomain(this ShoppingListItemDBType item) =>
        ShoppingListItem.FromPrimitiveTypes(item.Id, item.Title, item.Description, item.BoughtAt);

    public static ShoppingListItemDBType MapToDBType(this ShoppingListItem item) =>
        new ShoppingListItemDBType
        {
            Id = item.Id.Match(
                id => id,
                _ => default
                ),
            Title = item.Title,
            Description = item.Description,
            BoughtAt = item.BoughtAt.Match(
                dt => dt,
                _ => (DateTimeOffset?)null
                )
        };
}
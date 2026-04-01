namespace mahl.Server.Data.DatabaseTypes;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("ShoppingListItems")]
public class ShoppingListItemDbType
{
    [Key]
    public Guid Id { get; set; } = Guid.CreateVersion7();

    public Guid IngredientId { get; set; }
    public IngredientDbType Ingredient { get; set; } = null!;

    [Column(TypeName = "decimal(10,3)")]
    public decimal? Quantity { get; set; }

    /// <summary>Einheit. NULL wenn Quantity NULL ist.</summary>
    [MaxLength(50)]
    public string? Unit { get; set; }

    public DateTimeOffset? BoughtAt { get; set; }

    public DateTimeOffset GeneratedAt { get; set; } = DateTimeOffset.UtcNow;
}

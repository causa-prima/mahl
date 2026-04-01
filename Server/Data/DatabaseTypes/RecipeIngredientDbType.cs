namespace mahl.Server.Data.DatabaseTypes;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("RecipeIngredients")]
public class RecipeIngredientDbType
{
    [Key]
    public Guid Id { get; set; } = Guid.CreateVersion7();

    public Guid RecipeId { get; set; }
    public RecipeDbType Recipe { get; set; } = null!;

    public Guid IngredientId { get; set; }
    public IngredientDbType Ingredient { get; set; } = null!;

    /// <summary>Menge der Zutat. NULL bedeutet "nach Geschmack".</summary>
    [Column(TypeName = "decimal(10,3)")]
    public decimal? Quantity { get; set; }

    /// <summary>Einheit der Zutat. NULL wenn Quantity NULL ist.</summary>
    [MaxLength(50)]
    public string? Unit { get; set; }
}

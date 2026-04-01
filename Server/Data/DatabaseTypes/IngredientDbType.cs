namespace mahl.Server.Data.DatabaseTypes;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("Ingredients")]
public class IngredientDbType
{
    [Key]
    public Guid Id { get; set; } = Guid.CreateVersion7();

    [Required]
    [MaxLength(200)]
    public string Name { get; set; } = string.Empty;

    [Required]
    [MaxLength(50)]
    public string DefaultUnit { get; set; } = string.Empty;

    public bool AlwaysInStock { get; set; }

    public DateTimeOffset? DeletedAt { get; set; }
}

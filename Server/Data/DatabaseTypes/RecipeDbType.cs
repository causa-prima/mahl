namespace mahl.Server.Data.DatabaseTypes;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("Recipes")]
public class RecipeDbType
{
    [Key]
    public Guid Id { get; set; } = Guid.CreateVersion7();

    [Required]
    [MaxLength(300)]
    public string Title { get; set; } = string.Empty;

    [MaxLength(2000)]
    public string? SourceUrl { get; set; }

    [MaxLength(500)]
    public string? SourceImagePath { get; set; }

    public DateTimeOffset? DeletedAt { get; set; }

    public List<RecipeIngredientDbType> Ingredients { get; set; } = new();
    public List<StepDbType> Steps { get; set; } = new();
}

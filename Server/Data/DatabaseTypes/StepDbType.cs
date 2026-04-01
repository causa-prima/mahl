namespace mahl.Server.Data.DatabaseTypes;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("Steps")]
public class StepDbType
{
    [Key]
    public Guid Id { get; set; } = Guid.CreateVersion7();

    public Guid RecipeId { get; set; }
    public RecipeDbType Recipe { get; set; } = null!;

    public int StepNumber { get; set; }

    [Required]
    [MaxLength(4000)]
    public string Instruction { get; set; } = string.Empty;
}

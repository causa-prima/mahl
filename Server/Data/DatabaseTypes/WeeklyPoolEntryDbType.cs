namespace mahl.Server.Data.DatabaseTypes;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("WeeklyPoolEntries")]
public class WeeklyPoolEntryDbType
{
    [Key]
    public Guid Id { get; set; } = Guid.CreateVersion7();

    public Guid RecipeId { get; set; }
    public RecipeDbType Recipe { get; set; } = null!;

    public DateTimeOffset AddedAt { get; set; } = DateTimeOffset.UtcNow;
}

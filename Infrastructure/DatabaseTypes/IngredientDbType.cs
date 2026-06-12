namespace mahl.Infrastructure.DatabaseTypes;

public class IngredientDbType
{
    public Guid Id { get; set; }
    public string Name { get; set; } = null!;
    public string DefaultUnit { get; set; } = null!;
}

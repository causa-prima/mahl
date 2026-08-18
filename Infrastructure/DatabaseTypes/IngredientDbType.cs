namespace mahl.Infrastructure.DatabaseTypes;

public class IngredientDbType
{
    public Guid Id { get; set; }
    public string Name { get; set; } = null!;
    public string BaseUnit { get; set; } = null!;
    // ADR-S000-6: Soft-Delete via nullable Timestamp statt IsDeleted-Bool. null = aktiv.
    public DateTimeOffset? DeletedAt { get; set; }
}

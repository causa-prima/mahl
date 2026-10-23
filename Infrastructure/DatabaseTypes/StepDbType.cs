namespace mahl.Infrastructure.DatabaseTypes;

public class StepDbType
{
    public Guid RecipeId { get; set; }
    // ADR-S027-1: vom Server aus der Listenposition vergeben (Index + 1), nur hier und zur Sortierung.
    public int StepNumber { get; set; }
    public string Instruction { get; set; } = null!;
}

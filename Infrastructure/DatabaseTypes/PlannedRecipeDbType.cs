namespace mahl.Infrastructure.DatabaseTypes;

// ADR-S153-1: Eine Vormerkung ist reine Mengenzugehörigkeit – die Rezept-ID ist Primär- und Fremdschlüssel.
public class PlannedRecipeDbType
{
    public Guid RecipeId { get; set; }
}

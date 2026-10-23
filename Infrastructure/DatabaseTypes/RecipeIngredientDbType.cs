namespace mahl.Infrastructure.DatabaseTypes;

// Eine Rezept-Zutat: Position im Rezept (1-basiert, Zeilenreihenfolge des Zutatenfelds, ADR-S135-2)
// plus Verweis auf die Zutat. Keine Einheit-Spalte: mit Menge ist sie die Basiseinheit der Zutat
// (ADR-S135-2), ohne Menge Unspecified (ADR-S020-1).
public class RecipeIngredientDbType
{
    public Guid RecipeId { get; set; }
    public int Position { get; set; }
    public Guid IngredientId { get; set; }
    // ADR-S020-1: NULL = Unspecified (ohne Menge).
    public decimal? Quantity { get; set; }
}

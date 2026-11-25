namespace mahl.Infrastructure.DatabaseTypes;

// ADR-S154-3: Ein Eintrag je Zutat – die Zutat-Id ist Primär- und Fremdschlüssel. Name und Einheit kommen beim
// Lesen aus der Zutat.
public class ShoppingListItemDbType
{
    public Guid IngredientId { get; set; }
    // ADR-S154-2: Gesamtmenge in der Basiseinheit, numeric(8,3); NULL = ohne Menge (ADR-S020-1).
    public decimal? Quantity { get; set; }
}

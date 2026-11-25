using Microsoft.EntityFrameworkCore;

namespace mahl.Infrastructure;

// ADR-S154-3: Übernehmen ersetzt die Einkaufsliste in einer Transaktion. Tabellen- und Spaltennamen sind Literale im
// SQL-Text (wie in PlannedRecipeExtensions); eine Umbenennung im Modell fällt erst im Integrationstest auf.
public static class ShoppingListExtensions
{
    // Gesamtmenge je Zutat exakt dezimal (numeric): SUM überspringt „ohne Menge" (NULL) und liefert NULL, wenn alle
    // Vorkommen ohne Menge sind (ADR-S020-1, ADR-S154-2). Gleichzeitiges Übernehmen sichert der Primärschlüssel ab;
    // kein Anwendungszweig dafür (ADR-S105-2).
    public static async Task ReplaceShoppingListFromPlannedRecipesAsync(this MahlDbContext db, CancellationToken ct)
    {
        ArgumentNullException.ThrowIfNull(db);
        var transaction = await db.Database.BeginTransactionAsync(ct).ConfigureAwait(false);
        await using (transaction.ConfigureAwait(false))
        {
            await db.ShoppingListItems.ExecuteDeleteAsync(ct).ConfigureAwait(false);
            await db.Database.ExecuteSqlRawAsync(
                """
                INSERT INTO "ShoppingListItems" ("IngredientId", "Quantity")
                SELECT ri."IngredientId", SUM(ri."Quantity")
                FROM "PlannedRecipes" p
                JOIN "RecipeIngredients" ri ON ri."RecipeId" = p."RecipeId"
                GROUP BY ri."IngredientId"
                """,
                ct).ConfigureAwait(false);
            await transaction.CommitAsync(ct).ConfigureAwait(false);
        }
    }
}

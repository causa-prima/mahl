using Microsoft.EntityFrameworkCore;

namespace mahl.Infrastructure;

// ADR-S153-1 / ADR-S105-2: Der Postgres-spezifische Upsert (ON CONFLICT) steht in Infrastructure, nicht im Endpoint.
// Tabellen- und Spaltenname sind Literale im SQL-Text und nicht an das Modell gebunden: Eine Interpolation machte sie
// zu Parametern, die Postgres als Bezeichner nicht annimmt. Eine Umbenennung im Modell fällt erst im Integrationstest auf.
public static class PlannedRecipeExtensions
{
    // Idempotent: ein schon vorgemerktes Rezept bleibt unverändert, kein Check-then-Insert. Die ID ist ein
    // Parameter, kein Teil des SQL-Texts.
    public static async Task PlanRecipeAsync(this MahlDbContext db, Guid recipeId, CancellationToken ct)
    {
        ArgumentNullException.ThrowIfNull(db);
        await db.Database.ExecuteSqlInterpolatedAsync(
            $"""INSERT INTO "PlannedRecipes" ("RecipeId") VALUES ({recipeId}) ON CONFLICT ("RecipeId") DO NOTHING""",
            ct).ConfigureAwait(false);
    }

    // Idempotent (ADR-S000-5): ein nicht vorgemerktes Rezept löscht nichts. Ein einzelnes Statement, kein Check-then-Delete.
    public static async Task UnplanRecipeAsync(this MahlDbContext db, Guid recipeId, CancellationToken ct)
    {
        ArgumentNullException.ThrowIfNull(db);
        await db.PlannedRecipes
            .Where(p => p.RecipeId == recipeId)
            .ExecuteDeleteAsync(ct).ConfigureAwait(false);
    }
}

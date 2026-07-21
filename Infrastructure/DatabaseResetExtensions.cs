using Microsoft.EntityFrameworkCore;

namespace mahl.Infrastructure;

// Geteilter Reset-Helper für per-Test-DB-Isolation (E2E: ADR-S084-4 Addendum; Server.Tests: ADR-S105-1).
// Public in Infrastructure (nicht Server-internal), damit Server.Tests ihn ohne InternalsVisibleTo
// nutzen kann (ADR-S041-3: Domain-/Server-Internals sind für Tests nicht zugänglich). Tabellennamen
// generisch aus dem EF-Modell abgeleitet -> kein Pflegeaufwand bei neuen Entitäten.
public static class DatabaseResetExtensions
{
    public static async Task TruncateAllTablesAsync(this MahlDbContext db)
    {
        ArgumentNullException.ThrowIfNull(db);

        var tables = db.Model.GetEntityTypes()
            .Select(t => (Schema: t.GetSchema(), Name: t.GetTableName()))
            .Where(t => t.Name is not null)
            .Distinct()
            .Select(t => t.Schema is null ? $"\"{t.Name}\"" : $"\"{t.Schema}\".\"{t.Name}\"");
        var truncate = $"TRUNCATE TABLE {string.Join(", ", tables)} RESTART IDENTITY CASCADE";
        // EF1002: Tabellennamen stammen aus dem EF-Modell (Compile-Zeit-Schema), nicht aus Nutzereingaben
        // -> keine Injection-Fläche; Identifier sind in SQL ohnehin nicht parametrisierbar.
#pragma warning disable EF1002 // Table identifiers come from the trusted EF model, not user input
        await db.Database.ExecuteSqlRawAsync(truncate).ConfigureAwait(false);
#pragma warning restore EF1002
    }
}

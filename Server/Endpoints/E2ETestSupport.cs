using mahl.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace mahl.Server.Endpoints;

// E2E-Test-Support: AUSSCHLIESSLICH in der E2E-Umgebung aktiviert (Guard in Program.cs) – existiert in
// dev/prod nicht. Gibt der E2E-Suite per-Test-Isolation gegen eine echte Postgres (mahl_e2e). Motivation,
// Strategie (eigene DB, TRUNCATE statt DROP, generische Ableitung) und Abgrenzung zu EF-InMemory:
// ADR-S084-4 Addendum (docs/history/adr.md).
//
// Bewusst als EIGENE Methode (nicht inline in Program.<Main>$): die relationalen APIs (MigrateAsync,
// ExecuteSqlRawAsync) liegen im Microsoft.EntityFrameworkCore.Relational-Assembly. Direkt in Main müsste
// der Test-Host (WebApplicationFactory, InMemory) dieses Assembly schon beim JIT von Main auflösen – auch
// wenn der E2E-Branch nie läuft – und mit FileNotFoundException scheitern. Als Methode JITtet der Body
// erst beim tatsächlichen E2E-Aufruf.
internal static class E2ETestSupport
{
    internal static async Task UseE2ETestSupportAsync(this WebApplication app)
    {
        // Schema pro Lauf provisionieren (legt mahl_e2e bei Bedarf an).
        using (var scope = app.Services.CreateScope())
        {
            await scope.ServiceProvider.GetRequiredService<MahlDbContext>().Database.MigrateAsync();
        }

        // Leert vor jedem Test ALLE Tabellen (Playwright beforeEach) -> leere DB je Test. Tabellennamen
        // generisch aus dem EF-Modell, daher kein Pflegeaufwand bei neuen Entitäten. Begründung TRUNCATE
        // statt DROP / RESTART IDENTITY / CASCADE: ADR-S084-4 Addendum. Prämisse: mind. eine gemappte
        // Entität (sonst leeres TRUNCATE-Statement) – für diese App strukturell immer erfüllt.
        app.MapPost("/api/test/reset", async (MahlDbContext db) =>
        {
            var tables = db.Model.GetEntityTypes()
                .Select(t => (Schema: t.GetSchema(), Name: t.GetTableName()))
                .Where(t => t.Name is not null)
                .Distinct()
                .Select(t => t.Schema is null ? $"\"{t.Name}\"" : $"\"{t.Schema}\".\"{t.Name}\"");
            var truncate = $"TRUNCATE TABLE {string.Join(", ", tables)} RESTART IDENTITY CASCADE";
            // EF1002: Tabellennamen stammen aus dem EF-Modell (Compile-Zeit-Schema), nicht aus Nutzereingaben
            // -> keine Injection-Fläche; Identifier sind in SQL ohnehin nicht parametrisierbar.
#pragma warning disable EF1002 // Table identifiers come from the trusted EF model, not user input
            await db.Database.ExecuteSqlRawAsync(truncate);
#pragma warning restore EF1002
            return Results.NoContent();
        });
    }
}

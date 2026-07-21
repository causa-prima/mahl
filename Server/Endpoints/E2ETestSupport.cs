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
        // Schema pro Lauf NEU provisionieren (ADR-S105-1/-2: InitialCreate wurde um den funktionalen
        // LOWER(name)-Unique-Index ergänzt; MigrateAsync würde eine bereits angewandte, geänderte
        // Migration NICHT erneut ausführen). EnsureDeletedAsync vor MigrateAsync erzwingt einen frischen
        // Schema-Stand pro Lauf. Nur für die dedizierte E2E-DB (mahl_e2e) vertretbar, niemand sonst nutzt sie.
        using (var scope = app.Services.CreateScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();
            await db.Database.EnsureDeletedAsync();
            await db.Database.MigrateAsync();
        }

        // Leert vor jedem Test ALLE Tabellen (Playwright beforeEach) -> leere DB je Test. Begründung
        // TRUNCATE statt DROP / RESTART IDENTITY / CASCADE: ADR-S084-4 Addendum. Reset-Logik geteilt mit
        // Server.Tests (ADR-S105-1): Infrastructure.DatabaseResetExtensions.
        app.MapPost("/api/test/reset", async (MahlDbContext db) =>
        {
            await db.TruncateAllTablesAsync();
            return Results.NoContent();
        });
    }
}

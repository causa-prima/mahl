using mahl.Infrastructure;
using Microsoft.EntityFrameworkCore;
using Testcontainers.PostgreSql;
using Xunit;

namespace mahl.Server.Tests.Helpers;

// ADR-S105-1: ein geteilter Postgres-Testcontainer für die gesamte Server.Tests-Assembly (Speed) statt
// ein Container je Testklasse/-methode. Schema wird EINMALIG via MigrateAsync provisioniert (dieselben
// Migrations wie E2E/Prod, inkl. dem funktionalen LOWER(name)-Unique-Index, ADR-S105-2) – jeder einzelne
// Test resettet danach nur seine eigenen Daten (EndpointsTestsBase.InitializeAsync).
public sealed class PostgresContainerFixture : IAsyncLifetime
{
    // Image literal (wechselt praktisch nie) – muss mit docker-compose.yml übereinstimmen.
    // Init-Config (Locale/Encoding) dagegen aus der Single Source config/postgres.env (CM-S105-1),
    // damit sie nicht von der Deployment-DB divergieren kann (LL-S105-1).
    private readonly PostgreSqlContainer _container = new PostgreSqlBuilder("postgres:15-alpine")
        .WithEnvironment("POSTGRES_INITDB_ARGS", PostgresTestConfig.InitdbArgs)
        .Build();

    internal string ConnectionString => _container.GetConnectionString();

    public async ValueTask InitializeAsync()
    {
        await _container.StartAsync();

        var options = new DbContextOptionsBuilder<MahlDbContext>().UseNpgsql(ConnectionString).Options;
        await using var db = new MahlDbContext(options);
        await db.Database.MigrateAsync();
    }

    public async ValueTask DisposeAsync() => await _container.DisposeAsync();
}

using mahl.Infrastructure;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace mahl.Server.Tests.Helpers;

// ADR-S105-1: Schema lebt im geteilten Postgres-Testcontainer (PostgresContainerFixture, einmalig
// via MigrateAsync provisioniert) – hier wird pro Test nur noch der Datenbestand zurückgesetzt
// (TruncateAllTablesAsync), nicht das Schema selbst neu angelegt/gelöscht.
public class EndpointsTestsBase : IAsyncLifetime
{
    private readonly PostgresContainerFixture _postgres;
    private TestWebApplicationFactory _factory = null!;
    private IServiceScope _scope = null!;
    private HttpClient _client = null!;
    private MahlDbContext _db = null!;

    protected HttpClient Client => _client;
    protected MahlDbContext Db => _db;

    protected EndpointsTestsBase(PostgresContainerFixture postgres)
    {
        _postgres = postgres;
    }

    public async ValueTask InitializeAsync()
    {
        _factory = new TestWebApplicationFactory(_postgres.ConnectionString);
        _client = _factory.CreateClient();
        _scope = _factory.Services.CreateScope();
        _db = _scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        await _db.TruncateAllTablesAsync();
    }

    public async ValueTask DisposeAsync()
    {
        await _db.DisposeAsync();
        _scope.Dispose();
        _client.Dispose();
        await _factory.DisposeAsync();
        GC.SuppressFinalize(this);
    }
}

using mahl.Infrastructure;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace mahl.Server.Tests.Helpers;

// ADR-S105-1: Das Schema stellt PostgresContainerFixture je Testlauf bereit (ADR-S137-2) – hier wird pro
// Test nur der Datenbestand zurückgesetzt (TruncateAllTablesAsync), nicht das Schema.
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

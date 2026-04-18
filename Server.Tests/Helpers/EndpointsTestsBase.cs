using mahl.Infrastructure;
using Microsoft.Extensions.DependencyInjection;

namespace mahl.Server.Tests.Helpers;

public class EndpointsTestsBase : IDisposable
{
    private readonly TestWebApplicationFactory _factory;
    private readonly IServiceScope _scope;
    private readonly HttpClient _client;
    private readonly MahlDbContext _db;

    protected HttpClient Client => _client;
    protected MahlDbContext Db => _db;

    protected EndpointsTestsBase()
    {
        _factory = new TestWebApplicationFactory();
        _client = _factory.CreateClient();
        _scope = _factory.Services.CreateScope();
        _db = _scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        _db.Database.EnsureCreated();
    }

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            _db.Database.EnsureDeleted();
            _db.Dispose();
            _scope.Dispose();
            _client.Dispose();
            _factory.Dispose();
        }
    }
}

using mahl.Infrastructure;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using Microsoft.Extensions.DependencyInjection;

namespace mahl.Server.Tests.Helpers;

internal sealed class TestWebApplicationFactory : WebApplicationFactory<Program>
{
    // ADR-S000-11: InMemoryDatabaseRoot + per-instance GUID name guarantee a shared store
    // view between the request DbContext and the test DbContext (needed for POST->GET +
    // full-state DB assertions). Guid.NewGuid() in the options lambda is fragile and was rejected.
    private readonly InMemoryDatabaseRoot _dbRoot = new();
    private readonly string _dbName = Guid.NewGuid().ToString();

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<MahlDbContext>));
            if (descriptor is not null)
                services.Remove(descriptor);

            // UseInternalServiceProvider isolates EF Core's internal services per factory,
            // preventing the "two providers registered" conflict with Npgsql.
            var inMemoryServiceProvider = new ServiceCollection()
                .AddEntityFrameworkInMemoryDatabase()
                .BuildServiceProvider();

            services.AddDbContext<MahlDbContext>(options =>
                options.UseInMemoryDatabase(_dbName, _dbRoot)
                       .UseInternalServiceProvider(inMemoryServiceProvider));
        });
    }
}

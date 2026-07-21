using mahl.Infrastructure;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace mahl.Server.Tests.Helpers;

// ADR-S105-1: verbindet den Test-Host mit dem geteilten Postgres-Testcontainer statt EF-InMemory.
internal sealed class TestWebApplicationFactory(string connectionString) : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<MahlDbContext>));
            if (descriptor is not null)
                services.Remove(descriptor);

            services.AddDbContext<MahlDbContext>(options => options.UseNpgsql(connectionString));
        });
    }
}

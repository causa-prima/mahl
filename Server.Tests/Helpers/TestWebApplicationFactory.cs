using mahl.Infrastructure;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace mahl.Server.Tests.Helpers;

internal sealed class TestWebApplicationFactory : WebApplicationFactory<Program>
{
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
                options.UseInMemoryDatabase(Guid.NewGuid().ToString())
                       .UseInternalServiceProvider(inMemoryServiceProvider));
        });
    }
}

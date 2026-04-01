namespace mahl.Server.Tests.Helpers;

using mahl.Server.Data;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Serilog;

public class TestWebApplicationFactory : WebApplicationFactory<Program>
{
    private readonly string _testId;

    public TestWebApplicationFactory(string testId)
    {
        _testId = testId;
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureLogging(loggingBuilder =>
        {
            loggingBuilder.ClearProviders();

            var serilogLogger = new LoggerConfiguration()
                .MinimumLevel.Verbose()
                .Enrich.FromLogContext()
                .WriteTo.Sink(new TestIdSink(_testId))
                .CreateLogger();

            loggingBuilder.AddSerilog(serilogLogger, dispose: true);
        });

        builder.ConfigureServices(services =>
        {
            var descriptorsToRemove = services
                .Where(d => d.ServiceType == typeof(DbContextOptions<MahlDbContext>)
                         || d.ServiceType == typeof(IDbContextOptionsConfiguration<MahlDbContext>))
                .ToList();
            foreach (var descriptor in descriptorsToRemove)
                services.Remove(descriptor);

            var dbName = $"TestDb-{TestContext.CurrentContext.Test.Name}-{_testId}";
            services.AddDbContext<MahlDbContext>(options =>
                options.UseInMemoryDatabase(dbName)
                       .ConfigureWarnings(w => w.Ignore(Microsoft.EntityFrameworkCore.Diagnostics.InMemoryEventId.TransactionIgnoredWarning)));
        });
    }
}

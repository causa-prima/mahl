namespace mahl.Server.Tests.Helpers;

using mahl.Server.Data;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
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
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<MariaDbContext>));
            if (descriptor != null)
                services.Remove(descriptor);

            var dbName = $"TestDb-{TestContext.CurrentContext.Test.Name}-{_testId}";
            services.AddDbContext<MariaDbContext>(options =>
                options.UseInMemoryDatabase(dbName));

            var sp = services.BuildServiceProvider();
            using var scope = sp.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<MariaDbContext>();
            db.Database.EnsureCreated();
        });
    }
}
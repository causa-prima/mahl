using mahl.Infrastructure;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.FileProviders;

namespace mahl.Server.Tests.Helpers;

// ADR-S105-1: verbindet den Test-Host mit der Postgres-Datenbank des Testlaufs (ADR-S137-2) statt EF-InMemory.
// ADR-S150-2: Server/wwwroot ist Build-Output und nicht eingecheckt – der Test-Host bekommt deshalb ein
// eigenes Web-Root mit einer Test-index.html und einem Asset, statt sich auf einen vorhandenen Client-Build zu verlassen.
internal sealed class TestWebApplicationFactory(string connectionString) : WebApplicationFactory<Program>
{
    public const string IndexHtml = "<!doctype html><html><body>test-index-marker</body></html>";
    public const string AssetJs = "console.log('test-asset-marker');";
    public const string AssetPath = "/assets/x.js";

    private readonly string _webRoot = Directory.CreateTempSubdirectory("mahl-webroot-").FullName;

    private void CreateWebRoot()
    {
        var assetFile = Path.Combine(_webRoot, AssetPath.TrimStart('/'));
        Directory.CreateDirectory(Path.GetDirectoryName(assetFile)!);
        File.WriteAllText(Path.Combine(_webRoot, "index.html"), IndexHtml);
        File.WriteAllText(assetFile, AssetJs);
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        CreateWebRoot();
        builder.UseWebRoot(_webRoot);

        builder.ConfigureServices((context, services) =>
        {
            // UseWebRoot setzt nur WebRootPath, nicht den WebRootFileProvider der Umgebung – der zeigte sonst
            // weiter auf das echte Server/wwwroot und der Fallback lieferte dessen index.html.
            context.HostingEnvironment.WebRootFileProvider = new PhysicalFileProvider(_webRoot);

            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<MahlDbContext>));
            if (descriptor is not null)
                services.Remove(descriptor);

            services.AddDbContext<MahlDbContext>(options => options.UseNpgsql(connectionString));
        });
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        if (disposing && Directory.Exists(_webRoot))
            Directory.Delete(_webRoot, recursive: true);
    }
}

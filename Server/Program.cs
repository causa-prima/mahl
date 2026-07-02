using mahl.Infrastructure;
using mahl.Server.Endpoints;
using mahl.Server.Middleware;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<MahlDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();

app.UseCollectionETag();
app.MapIngredientsEndpoints();

// E2E-Test-Isolation (ADR-S084-4 Addendum): NUR in der E2E-Umgebung. Die E2E läuft gegen eine eigene DB
// (appsettings.E2E.json -> mahl_e2e), nie gegen dev/prod. Provisioniert das Schema pro Lauf und mappt
// den per-Test-Reset-Endpoint. Ausgelagert in E2ETestSupport, damit Main keine relationalen APIs direkt
// referenziert (sonst scheitert der InMemory-Test-Host am JIT von Main – siehe E2ETestSupport.cs).
if (app.Environment.IsEnvironment("E2E"))
{
    await app.UseE2ETestSupportAsync();
}

await app.RunAsync();

#pragma warning disable CA1515 // Required for WebApplicationFactory<Program> in test project
public partial class Program { }
#pragma warning restore CA1515

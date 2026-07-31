using mahl.Infrastructure;
using mahl.Server.Endpoints;
using mahl.Server.Middleware;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<MahlDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();

// Bewusst KEIN globaler Exception-Handler / ProblemDetails-Fallback im SKELETON. Was ohne ihn
// passiert, ergibt sich allein aus Framework-Defaults – hier dokumentiert, weil es sonst nirgends
// im Code sichtbar ist (verifiziert an learn.microsoft.com, "Handle errors in ASP.NET Core"):
//   Development: WebApplication.CreateBuilder aktiviert die Developer Exception Page AUTOMATISCH,
//                ohne UseDeveloperExceptionPage()-Aufruf. Eine unbehandelte Exception liefert dort
//                Stack-Trace und Quellcode-Ausschnitte im Response-Body. Development wird nur in
//                Properties/launchSettings.json gesetzt (lokaler Start), nie in einem Deployment.
//   Production:  Kestrel beantwortet die Exception mit 500 OHNE Response-Body – kein Leak.
// ADR-S112-1: Ab MVP gehört hierhin ein UNBEDINGT (nicht umgebungsabhängig) registrierter
// UseExceptionHandler, der unbehandelte Exceptions generisch auf RFC-7807-ProblemDetails mappt
// und den Stack-Trace serverseitig LOGGT statt ihn auszuliefern. Damit verschwindet der
// Umgebungs-Zweig oben – und E2E übt denselben Fehlerpfad aus wie Produktion.
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

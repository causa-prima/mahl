using mahl.Server.Data;
using mahl.Server.Endpoints;
using Microsoft.EntityFrameworkCore;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection")
    ?? "Host=localhost;Port=5432;Database=mahl;Username=mahl_user;Password=mahl_dev_password";

builder.Services.AddDbContext<MahlDbContext>(options =>
    options.UseNpgsql(connectionString));
builder.Services.AddDatabaseDeveloperPageExceptionFilter();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("http://localhost:5173", "http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

const string serilogOutputTemplate = "[{Timestamp:HH:mm:ss} {Level:u3}] [TraceId: {TraceId}] {Message:lj}{NewLine}{Exception}";
if (!builder.Environment.IsDevelopment())
    // The automated tests would not write to the test log sink if this was always configured,
    // so we only configure it if the environment is not development
    builder.Host.UseSerilog((context, services, loggerConfiguration) =>
    {
        // CA1305: Serilog sinks accept an IFormatProvider parameter but manage their own formatting
        //         via output templates; passing a provider has no effect on the actual log output.
#pragma warning disable CA1305
        loggerConfiguration
            .ReadFrom.Configuration(context.Configuration)
            .ReadFrom.Services(services)
            .Enrich.FromLogContext()
            .WriteTo.Console(outputTemplate: serilogOutputTemplate)
            .WriteTo.File("logs/log-.txt", rollingInterval: RollingInterval.Day, outputTemplate: serilogOutputTemplate);
#pragma warning restore CA1305
    });

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}
else
    // The automated tests would throw an exception if this was called,
    // as builder.Host.UseSerilog was not called in that case (see above).
    app.UseSerilogRequestLogging();

app.UseCors();
app.UseHttpsRedirection();
app.UseStaticFiles();

app.MapIngredientsEndpoints();
app.MapRecipesEndpoints();
app.MapWeeklyPoolEndpoints();
app.MapShoppingListEndpoints();

app.MapFallbackToFile("index.html");

if (args.Contains("--seed-data"))
{
    await app.SeedDatabase();
    return;
}

await app.RunAsync();

public partial class Program { }

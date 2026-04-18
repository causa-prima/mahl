using mahl.Infrastructure;
using mahl.Server.Endpoints;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<MahlDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();

app.MapIngredientsEndpoints();

await app.RunAsync();

#pragma warning disable CA1515 // Required for WebApplicationFactory<Program> in test project
public partial class Program { }
#pragma warning restore CA1515

using mahl.Server.Data;
using mahl.Server.Endpoints;
using Microsoft.EntityFrameworkCore;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddRazorPages();

var connectionString = builder.Configuration.GetConnectionString("MariaDbConnectionString");
var serverVersion = new MariaDbServerVersion(new Version(10, 11, 8));
builder.Services.AddDbContext<MariaDbContext>(options => options.UseMySql(connectionString, serverVersion));
builder.Services.AddDatabaseDeveloperPageExceptionFilter();

const string serilogOutputTemplate = "[{Timestamp:HH:mm:ss} {Level:u3}] [TraceId: {TraceId}] {Message:lj}{NewLine}{Exception}";
if (!builder.Environment.IsDevelopment())
    // The automated tests would not write to the test log sink if this was always configured,
    // so we only configure it if the environment is not developments
    builder.Host.UseSerilog((context, services, loggerConfiguration) =>
    {
        loggerConfiguration
            .ReadFrom.Configuration(context.Configuration)
            .ReadFrom.Services(services)
            .Enrich.FromLogContext() // Necessary for having the TraceIdentifier in the logs
            .WriteTo.Console(outputTemplate: serilogOutputTemplate)
            .WriteTo.File("logs/log-.txt", rollingInterval: RollingInterval.Day, outputTemplate: serilogOutputTemplate);
    });

var app = builder.Build();



// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
    app.UseWebAssemblyDebugging();
}
else
    // The automated tests would throw an exception if this was called,
    // as builder.Host.UserSerilog was not called in that case (see above).
    // Thus, only call it in case it is NOT an development environment.
    app.UseSerilogRequestLogging();

app.UseRouting();

app.UseHttpsRedirection();

app.UseBlazorFrameworkFiles();
app.UseStaticFiles();

// app.UseRouting();
app.MapShoppingListEndpoints();
app.MapShoppingListItemEndpoints();
app.MapSuggestionEndpoints();

app.MapRazorPages();
app.MapFallbackToFile("index.html");

app.Run();

public partial class Program { }

// using Microsoft.AspNetCore.ResponseCompression;

// var builder = WebApplication.CreateBuilder(args);

// // Add services to the container.

// builder.Services.AddControllersWithViews();
// builder.Services.AddRazorPages();

// var app = builder.Build();

// // Configure the HTTP request pipeline.
// if (app.Environment.IsDevelopment())
// {
//     app.UseWebAssemblyDebugging();
// }
// else
// {
//     app.UseExceptionHandler("/Error");
//     // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
//     app.UseHsts();
// }

// app.UseHttpsRedirection();

// app.UseBlazorFrameworkFiles();
// app.UseStaticFiles();

// app.UseRouting();


// app.MapRazorPages();
// app.MapControllers();
// app.MapFallbackToFile("index.html");

// app.Run();

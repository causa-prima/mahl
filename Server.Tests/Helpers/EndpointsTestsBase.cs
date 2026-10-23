using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace mahl.Server.Tests.Helpers;

// ADR-S105-1: Das Schema stellt PostgresContainerFixture je Testlauf bereit (ADR-S137-2) – hier wird pro
// Test nur der Datenbestand zurückgesetzt (TruncateAllTablesAsync), nicht das Schema.
public class EndpointsTestsBase : IAsyncLifetime
{
    private readonly PostgresContainerFixture _postgres;
    private TestWebApplicationFactory _factory = null!;
    private IServiceScope _scope = null!;
    private HttpClient _client = null!;
    private MahlDbContext _db = null!;

    protected HttpClient Client => _client;
    protected MahlDbContext Db => _db;

    protected EndpointsTestsBase(PostgresContainerFixture postgres)
    {
        _postgres = postgres;
    }

    // Test-Data-Builder (docs/process/tdd-process.md#TDD-test-data-builder): kommt ein Pflichtfeld
    // hinzu, wird nur der Builder angepasst. Ohne id eine frische UUIDv7 wie im Schreibpfad (ADR-S030-1);
    // mit id für Expected-Objekte, deren Id aus Response oder DB stammt.
    protected static IngredientDbType AnIngredient(
        string name = "Butter", string unit = "g", DateTimeOffset? deletedAt = null, Guid? id = null) =>
        new() { Id = id ?? Guid.CreateVersion7(), Name = name, BaseUnit = unit, DeletedAt = deletedAt };

    protected static RecipeDbType ARecipe(string title = "Pfannkuchen", Guid? id = null) =>
        new() { Id = id ?? Guid.CreateVersion7(), Title = title };

    // Kind-Zeilen des Rezepts: ohne eigene Id, der Schlüssel ist (Rezept, Position/Nummer).
    protected static RecipeIngredientDbType ARecipeIngredient(
        Guid recipeId, int position, Guid ingredientId, decimal? quantity = null) =>
        new() { RecipeId = recipeId, Position = position, IngredientId = ingredientId, Quantity = quantity };

    protected static StepDbType AStep(Guid recipeId, int stepNumber, string instruction = "Teig rühren.") =>
        new() { RecipeId = recipeId, StepNumber = stepNumber, Instruction = instruction };

    public async ValueTask InitializeAsync()
    {
        _factory = new TestWebApplicationFactory(_postgres.ConnectionString);
        _client = _factory.CreateClient();
        _scope = _factory.Services.CreateScope();
        _db = _scope.ServiceProvider.GetRequiredService<MahlDbContext>();
        await _db.TruncateAllTablesAsync();
    }

    public async ValueTask DisposeAsync()
    {
        await _db.DisposeAsync();
        _scope.Dispose();
        _client.Dispose();
        await _factory.DisposeAsync();
        GC.SuppressFinalize(this);
    }
}

using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using Microsoft.EntityFrameworkCore;
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

    // Request-Builder: kommt ein Pflichtfeld hinzu, wird nur er angepasst. Tests nennen die Werte, auf
    // die es ihnen ankommt; der Rest ist ein gültiges Rezept (Zutat "Mehl" muss dafür existieren).
    protected static StepPayload AStepPayload(string instruction = "Teig rühren.") => new(instruction);

    protected static CreateRecipeRequest ACreateRecipe(
        string title = "Pfannkuchen", string ingredients = "250 g Mehl", IReadOnlyList<StepPayload>? steps = null) =>
        new(title, ingredients, steps ?? [AStepPayload()]);

    // Gemeinsamer Then-Teil der Ablehnungen: 422 (ADR-S090-1) mit genau diesen Feldmeldungen (Full State)
    // und nichts gespeichert.
    protected async Task AssertRejectedWithAsync(HttpResponseMessage response, IReadOnlyDictionary<string, IReadOnlyList<string>> expectedErrors)
    {
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        var body = await response.Content.ReadFromJsonAsync<ValidationErrorResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Errors.Should().BeEquivalentTo(expectedErrors);
        await AssertNothingPersistedAsync();
    }

    protected static IReadOnlyDictionary<string, IReadOnlyList<string>> SingleError(string key, string message) =>
        new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal) { [key] = [message] };

    protected async Task AssertNothingPersistedAsync()
    {
        (await Db.Recipes.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEmpty("no recipe row may be written");
        (await Db.RecipeIngredients.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEmpty("no recipe ingredient row may be written");
        (await Db.Steps.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEmpty("no step row may be written");
    }

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

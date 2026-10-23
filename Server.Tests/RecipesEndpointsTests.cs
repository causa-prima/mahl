using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace mahl.Server.Tests;

[Collection(PostgresCollectionDefinition.Name)]
public class RecipesEndpointsTests(PostgresContainerFixture postgres) : EndpointsTestsBase(postgres)
{
#pragma warning disable CA1812 // instantiated by JSON deserializer via reflection
    // ADR-S027-1: ein Schritt trägt nur die Anweisung – die Nummer ist die Listenposition.
    private sealed record StepPayload(string Instruction);
    // ADR-S135-2: die Zutaten gehen als roher Text des Zutatenfelds hinaus, eine Zutat je Zeile.
    private sealed record CreateRecipeRequest(string Title, string Ingredients, IReadOnlyList<StepPayload> Steps);
    // ADR-S020-1: Quantity und Unit sind beide null (ohne Menge) oder beide gesetzt.
    private sealed record RecipeIngredientResponse(string Name, decimal? Quantity, string? Unit);
    private sealed record RecipeResponse(
        Guid Id, string Title, IReadOnlyList<RecipeIngredientResponse> Ingredients, IReadOnlyList<StepPayload> Steps);
    private sealed record RecipeSummaryResponse(Guid Id, string Title);
#pragma warning restore CA1812

    // Helper: legt Zutaten an und leert danach den Tracker – folgende Full-State-Abfragen lesen so die
    // DB, nicht die getrackten Seed-Instanzen.
    private async Task SeedIngredientsAsync(params IngredientDbType[] ingredients)
    {
        Db.Ingredients.AddRange(ingredients);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        Db.ChangeTracker.Clear();
    }

    // Felder des Rezept-DTOs kommen mit den Szenarien, die sie fordern; eine leere Liste hat keine.
    [Fact]
    public async Task US602_HappyPath_GetRecipes_EmptyDb_Returns200WithEmptyList()
    {
        // Given: keine Rezepte vorhanden (leere Test-Datenbank)
        // When
        var response = await Client.GetAsync("/api/recipes", TestContext.Current.CancellationToken);

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<object[]>(TestContext.Current.CancellationToken);
        body.Should().BeEmpty();
    }

    // @US-602-happy-path „Rezept anlegen": Zutatenzeilen mit und ohne Menge, zwei Schritte. Die erste
    // Zeile ohne Menge steht bewusst vorn – die Reihenfolge im Rezept ist die Zeilenreihenfolge, nicht
    // eine nach Menge oder Name sortierte.
    [Fact]
    public async Task US602_HappyPath_CreateRecipe_ValidData_Returns201AndPersistsRecipe()
    {
        const string title = "Pfannkuchen";
        const string stir = "Mehl und Milch verrühren.";
        const string fry = "In der Pfanne ausbacken.";
        // Given: die Zutaten "Mehl" (g), "Milch" (ml) und "Salz" (g) existieren
        var mehl = AnIngredient("Mehl", "g");
        var milch = AnIngredient("Milch", "ml");
        var salz = AnIngredient("Salz", "g");
        await SeedIngredientsAsync(mehl, milch, salz);
        var request = new CreateRecipeRequest(
            Title: title, Ingredients: "Salz\n250 g Mehl\n500 ml Milch",
            Steps: [new StepPayload(stir), new StepPayload(fry)]);

        // When: das Rezept wird gespeichert
        var response = await Client.PostAsJsonAsync("/api/recipes", request, TestContext.Current.CancellationToken);

        // Then: 201 Created (ADR-S068-1)
        response.StatusCode.Should().Be(HttpStatusCode.Created);

        // Then: genau ein Rezept mit dem eingegebenen Titel ist gespeichert (Full State; die Id vergibt der Server)
        var recipes = await Db.Recipes.ToListAsync(TestContext.Current.CancellationToken);
        recipes.Should().BeEquivalentTo([ARecipe(title)], o => o.Excluding(r => r.Id));
        var recipeId = recipes[0].Id;

        // Then: der Body ist das ganze Rezept – Zutaten in Zeilenreihenfolge mit den gespeicherten Werten
        // der Zutat (Einheit = Basiseinheit, ADR-S135-2), Schritte in Listenreihenfolge (ADR-S027-1)
        var body = await response.Content.ReadFromJsonAsync<RecipeResponse>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo(
            new RecipeResponse(
                Id: recipeId, Title: title,
                Ingredients:
                [
                    new RecipeIngredientResponse(Name: "Salz", Quantity: null, Unit: null),
                    new RecipeIngredientResponse(Name: "Mehl", Quantity: 250m, Unit: "g"),
                    new RecipeIngredientResponse(Name: "Milch", Quantity: 500m, Unit: "ml"),
                ],
                Steps: [new StepPayload(stir), new StepPayload(fry)]),
            o => o.WithStrictOrdering());

        // Then: der Location-Header zeigt auf das neue Rezept (ADR-S068-1)
        response.Headers.Location.Should().Be($"/api/recipes/{recipeId}");

        // Then: die Rezept-Zutaten verweisen in Zeilenreihenfolge auf die Zutaten; ohne Menge NULL (ADR-S020-1)
        var recipeIngredients = await Db.RecipeIngredients.ToListAsync(TestContext.Current.CancellationToken);
        recipeIngredients.Should().BeEquivalentTo(
        [
            ARecipeIngredient(recipeId: recipeId, position: 1, ingredientId: salz.Id, quantity: null),
            ARecipeIngredient(recipeId: recipeId, position: 2, ingredientId: mehl.Id, quantity: 250m),
            ARecipeIngredient(recipeId: recipeId, position: 3, ingredientId: milch.Id, quantity: 500m),
        ]);

        // Then: die Schritte sind einzeln gespeichert, nummeriert nach Listenposition (ADR-S027-1)
        (await Db.Steps.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo(
        [
            AStep(recipeId: recipeId, stepNumber: 1, instruction: stir),
            AStep(recipeId: recipeId, stepNumber: 2, instruction: fry),
        ]);

        // Then: die Zutaten sind unverändert
        (await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo([mehl, milch, salz]);
    }

    // Kategorie „Protokoll-/Infrastruktur-Mechanik" (ADR-S106-3, kein US-Tag): POST liefert den
    // xmin-ETag der neu angelegten Zeile (ADR-S106-1, ADR-S000-12) – hier gegen den xmin der
    // Rezeptzeile gepinnt, nicht nur auf das Format.
    [Fact]
    public async Task CreateRecipe_ValidData_Returns201WithXminETagHeader()
    {
        // Given: die Zutat "Salz" existiert
        await SeedIngredientsAsync(AnIngredient("Salz", "g"));
        var request = new CreateRecipeRequest(
            Title: "Salzwasser", Ingredients: "Salz", Steps: [new StepPayload("Salz in Wasser lösen.")]);

        // When: das Rezept wird gespeichert
        var response = await Client.PostAsJsonAsync("/api/recipes", request, TestContext.Current.CancellationToken);

        // Then: 201 Created mit dem xmin der Rezeptzeile als ETag (ADR-S058-3: hex-kodiert, quoted)
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var xmin = await Db.Recipes
            .Select(r => EF.Property<uint>(r, "xmin"))
            .SingleAsync(TestContext.Current.CancellationToken);
        response.Headers.ETag.Should().NotBeNull();
        response.Headers.ETag.Tag.Should().Be($"\"{xmin:x8}\"");
    }

    // @US-602-happy-path „Rezept anlegen", letzter Then-Schritt: das Rezept steht genau einmal in der
    // Rezept-Liste. Das Rezept wird direkt in der DB angelegt, damit der Test den GET unabhängig vom POST prüft.
    [Fact]
    public async Task US602_HappyPath_GetRecipes_ExistingRecipe_ReturnsIdAndTitle()
    {
        // Given: das Rezept "Pfannkuchen" existiert
        var recipe = ARecipe("Pfannkuchen");
        Db.Recipes.Add(recipe);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When: die Rezept-Liste wird abgerufen
        var response = await Client.GetAsync("/api/recipes", TestContext.Current.CancellationToken);

        // Then: 200 OK mit genau diesem Rezept – Id und Titel
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<RecipeSummaryResponse[]>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo([new RecipeSummaryResponse(Id: recipe.Id, Title: "Pfannkuchen")]);
    }
}

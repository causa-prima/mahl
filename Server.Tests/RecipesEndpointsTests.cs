using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure;
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
    private sealed record ProblemDetailsResponse(string? Detail, string? ErrorCode);
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
        response.Headers.ETag.Should().NotBeNull();
        response.Headers.ETag.Tag.Should().Be(await ExpectedXminETagAsync(Db.Recipes));
    }

    // Helper: der erwartete ETag der einen Rezeptzeile, die die Abfrage liefert – hex-kodierter, gequoteter xmin.
    private static async Task<string> ExpectedXminETagAsync(IQueryable<RecipeDbType> recipe)
    {
        var xmin = await recipe
            .Select(r => EF.Property<uint>(r, XminExtensions.ColumnName))
            .SingleAsync(TestContext.Current.CancellationToken);
        return $"\"{xmin:x8}\"";
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

    // @US-602-happy-path „Mehrere Rezepte erscheinen alphabetisch sortiert": ADR-S142-1, deutsches Locale ohne
    // Rang-Unterschied der Schreibweise, Umlaut wie Grundbuchstabe. Insertion-Order, Byte-Order (Brot,
    // Mohnkuchen, Mohrrübeneintopf, Möhrensuppe, Zwiebelkuchen, apfelstrudel, Ölkuchen) und ICU-Order sind bei
    // diesen Titeln paarweise verschieden – ein schlichtes OrderBy bleibt rot. Mohnkuchen/Möhrensuppe/
    // Mohrrübeneintopf pinnen zudem, dass Ö wie O zählt (nicht wie „oe", nicht ans Ende).
    // Die Byte-Order gilt für die Default-Collation des gepinnten postgres:18-alpine (musl, ADR-S142-1); auf
    // einem glibc-Image sortierte ein schlichtes OrderBy schon richtig und dieser Test verlöre seine Trennschärfe.
    [Fact]
    public async Task US602_HappyPath_GetRecipes_MultipleRecipes_ReturnsAlphabeticallySorted()
    {
        // Given: sieben Rezepte, in nicht-alphabetischer Reihenfolge angelegt – je ein Save, damit die
        //   Insert-Reihenfolge feststeht und ein unsortierter Endpoint sie sichtbar durchreicht
        foreach (var title in new[]
                 { "Zwiebelkuchen", "Mohrrübeneintopf", "Ölkuchen", "apfelstrudel", "Möhrensuppe", "Brot", "Mohnkuchen" })
        {
            Db.Recipes.Add(ARecipe(title));
            await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        }

        // When: die Rezept-Liste wird abgerufen
        var response = await Client.GetAsync("/api/recipes", TestContext.Current.CancellationToken);

        // Then: 200 OK, Titel in deutscher Alphabet-Reihenfolge
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<RecipeSummaryResponse[]>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Select(r => r.Title).Should().Equal(
            "apfelstrudel", "Brot", "Mohnkuchen", "Möhrensuppe", "Mohrrübeneintopf", "Ölkuchen", "Zwiebelkuchen");
    }

    // Helper: legt Rezept samt Kind-Zeilen direkt in der DB an. Die Kind-Zeilen gehen absteigend nach
    // Position/Nummer und je mit eigenem Save hinein – ein GET ohne Sortierung gäbe sie sichtbar in
    // falscher Reihenfolge zurück.
    private async Task SeedRecipeAsync(
        RecipeDbType recipe, RecipeIngredientDbType[] ingredients, StepDbType[] steps)
    {
        Db.Recipes.Add(recipe);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        foreach (var row in ingredients.OrderByDescending(i => i.Position))
        {
            Db.RecipeIngredients.Add(row);
            await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        }
        foreach (var row in steps.OrderByDescending(s => s.StepNumber))
        {
            Db.Steps.Add(row);
            await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        }
        Db.ChangeTracker.Clear();
    }

    // Die beiden Rezepte aus dem Feature-Kommentar: „Brot" steht vor „Pfannkuchen", und „500 g Weizenmehl"
    // erscheint, wenn die Kind-Zeilen nicht nach Rezept gefiltert werden. Pfannkuchen hat zusätzlich eine
    // Zeile ohne Menge und einen zweiten Schritt, damit Reihenfolge und Null-Menge mitgeprüft sind: Die
    // Detailansicht lädt auch nach dem Anlegen per GET (ADR-S142-2), deshalb fordert das Szenario „Rezept
    // anlegen" (Zutaten in eingegebener Reihenfolge, „Salz" ohne Menge) beides vom GET.
    private async Task<Guid> SeedPfannkuchenAndBrotAsync()
    {
        var mehl = AnIngredient("Mehl", "g");
        var salz = AnIngredient("Salz", "g");
        var weizenmehl = AnIngredient("Weizenmehl", "g");
        await SeedIngredientsAsync(mehl, salz, weizenmehl);
        var brot = ARecipe("Brot");
        await SeedRecipeAsync(
            brot,
            [ARecipeIngredient(brot.Id, position: 1, ingredientId: weizenmehl.Id, quantity: 500m)],
            [AStep(brot.Id, stepNumber: 1, instruction: "Teig kneten.")]);
        var pfannkuchen = ARecipe("Pfannkuchen");
        await SeedRecipeAsync(
            pfannkuchen,
            [
                ARecipeIngredient(pfannkuchen.Id, position: 1, ingredientId: salz.Id),
                ARecipeIngredient(pfannkuchen.Id, position: 2, ingredientId: mehl.Id, quantity: 250m),
            ],
            [
                AStep(pfannkuchen.Id, stepNumber: 1, instruction: "Teig rühren."),
                AStep(pfannkuchen.Id, stepNumber: 2, instruction: "Ausbacken."),
            ]);
        return pfannkuchen.Id;
    }

    // @US-602-happy-path „Rezept aus der Rezept-Liste öffnen" und „Rezept per Direktlink aufrufen": die
    // Detailansicht lädt das Rezept über seine Id – genau dieses, mit seinen Zutaten und Schritten (ADR-S142-2).
    [Fact]
    public async Task US602_HappyPath_GetRecipe_TwoRecipes_ReturnsOnlyRequestedRecipeInPositionOrderIncludingIngredientWithoutQuantity()
    {
        // Szenario: Rezept aus der Rezept-Liste öffnen
        // Szenario: Rezept per Direktlink aufrufen
        // Given: die Rezepte "Pfannkuchen" und "Brot" existieren
        var pfannkuchenId = await SeedPfannkuchenAndBrotAsync();

        // When: das Rezept "Pfannkuchen" wird über seine Id abgerufen
        var response = await Client.GetAsync($"/api/recipes/{pfannkuchenId}", TestContext.Current.CancellationToken);

        // Then: 200 OK mit genau diesem Rezept – Zutaten in Zeilenreihenfolge, Schritte in Reihenfolge,
        //   nichts vom Rezept "Brot" (ADR-S135-2, ADR-S027-1)
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<RecipeResponse>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo(
            new RecipeResponse(
                Id: pfannkuchenId, Title: "Pfannkuchen",
                Ingredients:
                [
                    new RecipeIngredientResponse(Name: "Salz", Quantity: null, Unit: null),
                    new RecipeIngredientResponse(Name: "Mehl", Quantity: 250m, Unit: "g"),
                ],
                Steps: [new StepPayload("Teig rühren."), new StepPayload("Ausbacken.")]),
            o => o.WithStrictOrdering());
    }

    // Fest statt zufällig, damit der Test reproduzierbar ist; kein Seed-Rezept trägt sie.
    private static readonly Guid UnknownRecipeId = Guid.Parse("00000000-0000-7000-8000-00000000dead");

    // @US-602-error „Direktlink auf ein Rezept, das es nicht gibt", Beispiel „gültig aufgebaute, unbekannte
    // Kennung": 404 mit ProblemDetails (ADR-S142-2).
    [Fact]
    public async Task US602_Error_GetRecipe_UnknownGuid_Returns404ProblemDetails()
    {
        // Szenario: Direktlink auf ein Rezept, das es nicht gibt
        // Given: ein Rezept existiert, die abgefragte Id gehört aber keinem Rezept
        await SeedPfannkuchenAndBrotAsync();

        // When: die unbekannte Id wird abgerufen
        var response = await Client.GetAsync($"/api/recipes/{UnknownRecipeId}", TestContext.Current.CancellationToken);

        // Then: 404 mit der fixen deutschen Meldung und maschinenlesbarem errorCode (wie ADR-S054-6)
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        response.Content.Headers.ContentType.Should().NotBeNull();
        response.Content.Headers.ContentType.MediaType.Should().Be("application/problem+json");
        var body = await response.Content.ReadFromJsonAsync<ProblemDetailsResponse>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo(new ProblemDetailsResponse(Detail: "Rezept wurde nicht gefunden.", ErrorCode: "RECIPE_NOT_FOUND"));
    }

    // @US-602-error „Direktlink auf ein Rezept, das es nicht gibt", Beispiel „ungültige Kennung": die
    // Route-Constraint {id:guid} beantwortet es mit 404 (ADR-S142-2).
    [Fact]
    public async Task US602_Error_GetRecipe_NonGuid_Returns404()
    {
        // Szenario: Direktlink auf ein Rezept, das es nicht gibt
        // Given: kein Rezept nötig – die Route greift vor jedem Zugriff auf die Daten
        // When: eine Kennung, die keine GUID ist, wird abgerufen
        var response = await Client.GetAsync("/api/recipes/kein-guid", TestContext.Current.CancellationToken);

        // Then: 404 Not Found
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    // Kategorie „Protokoll-/Infrastruktur-Mechanik" (ADR-S106-3, kein US-Tag): der GET liefert den xmin der
    // Rezeptzeile als ETag (ADR-S142-2, ADR-S058-3) – nicht den Content-Hash der Middleware (ADR-S084-1).
    [Fact]
    public async Task GetRecipe_ExistingRecipe_ReturnsXminETagHeader()
    {
        // Given: ein Rezept existiert
        var recipeId = await SeedPfannkuchenAndBrotAsync();

        // When
        var response = await Client.GetAsync($"/api/recipes/{recipeId}", TestContext.Current.CancellationToken);

        // Then: der ETag ist der hex-kodierte, gequotete xmin der Rezeptzeile
        response.Headers.ETag.Should().NotBeNull();
        response.Headers.ETag.Tag.Should().Be(await ExpectedXminETagAsync(Db.Recipes.Where(r => r.Id == recipeId)));
    }

    // Kategorie „Protokoll-/Infrastruktur-Mechanik" (ADR-S106-3, kein US-Tag): ein If-None-Match, das dem
    // xmin-ETag gleicht, ergibt 304 ohne Body (ADR-S142-2).
    [Fact]
    public async Task GetRecipe_IfNoneMatchEqualsETag_Returns304WithoutBody()
    {
        // Given: ein Rezept und sein xmin-ETag aus der DB – unabhängig vom Endpoint, den der Test prüft
        var recipeId = await SeedPfannkuchenAndBrotAsync();
        var etag = await ExpectedXminETagAsync(Db.Recipes.Where(r => r.Id == recipeId));

        // When: der GET mit genau diesem ETag als If-None-Match wiederholt wird
        using var request = new HttpRequestMessage(HttpMethod.Get, $"/api/recipes/{recipeId}");
        request.Headers.TryAddWithoutValidation("If-None-Match", etag);
        var response = await Client.SendAsync(request, TestContext.Current.CancellationToken);

        // Then: 304 ohne Body, der Antwort-ETag ist der angefragte
        response.StatusCode.Should().Be(HttpStatusCode.NotModified);
        (await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken)).Should().BeEmpty();
        response.Headers.ETag.Should().NotBeNull();
        response.Headers.ETag.Tag.Should().Be(etag);
    }

    // Xmin 0 ist in Postgres die ungültige Transaktions-Id (InvalidTransactionId); eine echte Zeile trägt
    // nie 0, dieser ETag kann also nie dem eines Rezepts gleichen.
    private const string ForeignETag = "\"00000000\"";

    // Kategorie „Protokoll-/Infrastruktur-Mechanik" (ADR-S106-3, kein US-Tag): ein anderer If-None-Match
    // ergibt 200 mit dem Rezept (ADR-S142-2).
    [Fact]
    public async Task GetRecipe_IfNoneMatchStaleETag_Returns200WithBody()
    {
        // Given: ein Rezept
        var recipeId = await SeedPfannkuchenAndBrotAsync();

        // When: der GET mit einem fremden ETag als If-None-Match
        using var request = new HttpRequestMessage(HttpMethod.Get, $"/api/recipes/{recipeId}");
        request.Headers.TryAddWithoutValidation("If-None-Match", ForeignETag);
        var response = await Client.SendAsync(request, TestContext.Current.CancellationToken);

        // Then: 200 OK mit dem Rezept
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<RecipeResponse>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        body.Id.Should().Be(recipeId);
    }
}

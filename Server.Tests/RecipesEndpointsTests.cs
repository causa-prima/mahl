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
    private sealed record RecipeResponse(
        Guid Id, string Title, IReadOnlyList<RecipeIngredientResponse> Ingredients, IReadOnlyList<StepPayload> Steps);
    private sealed record ProblemDetailsResponse(string? Detail, string? ErrorCode);
#pragma warning restore CA1812

    // Alle geseedeten Zutaten – der erwartete Zutatenbestand nach jedem Anlegen (die Zutaten bleiben unverändert).
    private readonly List<IngredientDbType> _seededIngredients = [];

    // Helper: legt Zutaten an und leert danach den Tracker – folgende Full-State-Abfragen lesen so die
    // DB, nicht die getrackten Seed-Instanzen.
    private async Task SeedIngredientsAsync(params IngredientDbType[] ingredients)
    {
        _seededIngredients.AddRange(ingredients);
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
        var request = ACreateRecipe(
            title: title, ingredients: "Salz\n250 g Mehl\n500 ml Milch",
            steps: [AStepPayload(stir), AStepPayload(fry)]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

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
        var request = ACreateRecipe(
            title: "Salzwasser", ingredients: "Salz", steps: [AStepPayload("Salz in Wasser lösen.")]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

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

    // Nur dieses Testfile postet Rezepte; PostRawJsonAsync (Raw-JSON-Theorien) liegt ebenfalls hier.
    private async Task<HttpResponseMessage> PostRecipeAsync(CreateRecipeRequest request) =>
        await Client.PostAsJsonAsync("/api/recipes", request, TestContext.Current.CancellationToken);

    private async Task<HttpResponseMessage> PostRawJsonAsync(string json)
    {
        using var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
        return await Client.PostAsync("/api/recipes", content, TestContext.Current.CancellationToken);
    }

    // Szenario: Leeres Formular speichern zeigt alle Pflichtmeldungen gleichzeitig
    // Das Frontend sendet hier {"title":"","ingredients":"","steps":[]} (leere Schrittfelder gehen nicht mit).
    [Fact]
    public async Task US602_Error_CreateRecipe_EmptyForm_Returns422WithAllRequiredMessages()
    {
        // Given: ein leeres Formular
        var request = ACreateRecipe(title: "", ingredients: "", steps: []);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: alle drei Pflichtmeldungen gleichzeitig (ADR-S135-3, ADR-S051-2), nichts gespeichert
        await AssertRejectedWithAsync(response, new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal)
        {
            ["title"] = ["Titel darf nicht leer sein."],
            ["ingredients"] = ["Rezept muss mindestens eine Zutat haben."],
            ["steps"] = ["Rezept muss mindestens einen Schritt haben."],
        });
    }

    // Szenario: Rezept ohne Zutat oder ohne Schritt
    // Die ersten drei Beispiele der Outline: Zutatenfeld leer, Zutatenfeld nur aus leeren Zeilen und
    // Leerzeichen, Schritte leer. Das Beispiel mit dem Schritt aus Leerzeichen sendet das Frontend nicht
    // mit, es bleibt dem E2E-Test.
    [Theory]
    [InlineData("""{"title":"Pfannkuchen","ingredients":"","steps":[{"instruction":"Teig rühren."}]}""", "ingredients", "Rezept muss mindestens eine Zutat haben.")]
    [InlineData("""{"title":"Pfannkuchen","ingredients":"\n   \n\n  \n","steps":[{"instruction":"Teig rühren."}]}""", "ingredients", "Rezept muss mindestens eine Zutat haben.")]
    [InlineData("""{"title":"Pfannkuchen","ingredients":"250 g Mehl","steps":[]}""", "steps", "Rezept muss mindestens einen Schritt haben.")]
    public async Task US602_Error_CreateRecipe_WithoutIngredientOrStep_Returns422WithMessage(
        string json, string expectedKey, string expectedMessage)
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept wird gespeichert
        var response = await PostRawJsonAsync(json);

        // Then: die Meldung am betroffenen Feld, nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError(expectedKey, expectedMessage));
    }

    // Szenario: Ein Rezept mit einer leeren Schritt-Anweisung wird abgelehnt
    // ADR-S144-1: der Key trägt den 0-basierten Index in der gesendeten Liste.
    [Fact]
    public async Task US602_Error_CreateRecipe_BlankSecondStep_Returns422AtSecondStep()
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));
        var request = ACreateRecipe(steps: [AStepPayload("Teig rühren."), AStepPayload("   ")]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: die Meldung am zweiten Schritt, nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError("steps[1].instruction", "Schritt-Anweisung darf nicht leer sein."));
    }

    // Szenario: Ungültiger Titel
    // Beispiel: alle
    [Theory]
    [MemberData(nameof(InvalidTitles))]
    public async Task US602_Error_CreateRecipe_InvalidTitle_Returns422AtTitle(string title, string expectedMessage)
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));
        var request = ACreateRecipe(title: title);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: die Meldung am Titel, nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError("title", expectedMessage));
    }

    // Anzeigename benennt den Fall lesbar im roten Lauf; Parameter: Titel, Meldung.
    public static IEnumerable<TheoryDataRow<string, string>> InvalidTitles =>
    [
        new("   ", "Titel darf nicht leer sein.") { TestDisplayName = "Titel aus Leerzeichen" },
        new(new string('a', 101), "Titel darf maximal 100 Zeichen lang sein.") { TestDisplayName = "Titel mit 101 Zeichen" },
    ];

    // Kombinierendes Trema als Codepunkt (CGG-naming: nie Literal, nie \u-Escape).
    private static readonly string CombiningDiaeresis = char.ConvertFromUtf32(0x0308);

    // Szenario: Titel existiert bereits – unabhängig von Schreibweise und Leerraum
    // Beispiel: alle
    [Theory]
    [MemberData(nameof(ExistingTitles))]
    public async Task US602_Error_CreateRecipe_TitleExists_Returns422AtTitleAndKeepsExistingRecipe(string existingTitle, string requestTitle, string titleInMessage)
    {
        // Given: das Rezept existiert, die Zutat "Mehl" mit Einheit "g" existiert
        var existing = await SeedExistingRecipeAsync(existingTitle);

        // When: ein Rezept mit demselben Titel in abweichender Schreibweise wird gespeichert
        var response = await PostRecipeAsync(ACreateRecipe(title: requestTitle));

        // Then: 422, die Meldung nennt den normalisierten eingegebenen Titel; nur das vorhandene Rezept bleibt
        await AssertRejectedKeepingExistingAsync(
            response, SingleError("title", TitleExists(titleInMessage)), existing);
    }

    // Parameter: vorhandener Titel, eingegebener Titel, Titel in der Meldung (normalisiert, ADR-S135-1).
    public static IEnumerable<TheoryDataRow<string, string, string>> ExistingTitles =>
    [
        new("Pfannkuchen", "Pfannkuchen", "Pfannkuchen") { TestDisplayName = "gleich" },
        new("Pfannkuchen", "PFANNKUCHEN", "PFANNKUCHEN") { TestDisplayName = "Großschreibung" },
        new("Pfannkuchen", "  pfannkuchen  ", "pfannkuchen") { TestDisplayName = "Leerraum außen" },
        new("Käsekuchen", "KÄSEKUCHEN", "KÄSEKUCHEN") { TestDisplayName = "Umlaut groß" },
        new("Käsekuchen", $"Ka{CombiningDiaeresis}sekuchen", "Käsekuchen") { TestDisplayName = "kombinierendes Trema" },
        new("Apfel Strudel", "apfel   strudel", "apfel strudel") { TestDisplayName = "Leerraum innen" },
    ];

    // Szenario: Titel-Eindeutigkeit wird erst geprüft, wenn alle übrigen Prüfungen bestanden sind
    [Fact]
    public async Task US602_Error_CreateRecipe_TitleExistsAndIngredientInvalid_ReportsTitleOnlyAfterIngredientIsFixed()
    {
        // Given: das Rezept "Pfannkuchen" existiert, die Zutat "Mehl" mit Einheit "g" existiert
        var existing = await SeedExistingRecipeAsync("Pfannkuchen");

        // When: mit unbekannter Zutat gespeichert
        var first = await PostPancakesAsync("250 g Mehk");

        // Then: genau die Zutatenmeldung, keine am Titel
        await AssertRejectedKeepingExistingAsync(
            first, SingleError("ingredients", $"„250 g Mehk“: {NotFound("Mehk")}"), existing);

        // When: mit gültiger Zutat erneut gespeichert
        var second = await PostPancakesAsync("250 g Mehl");

        // Then: nur noch die Meldung am Titel
        await AssertRejectedKeepingExistingAsync(
            second, SingleError("title", TitleExists("Pfannkuchen")), existing);
    }

    // Die Meldung, wenn ein Rezept mit dem (normalisierten) Titel bereits existiert.
    private static string TitleExists(string title) => $"Ein Rezept mit dem Titel '{title}' existiert bereits.";

    // Seedet "Mehl" und ein Rezept mit einer Zutatenzeile und einem Schritt; leert danach den Tracker.
    private async Task<ExistingRecipe> SeedExistingRecipeAsync(string title)
    {
        var mehl = AnIngredient("Mehl", "g");
        await SeedIngredientsAsync(mehl);
        var recipe = ARecipe(title);
        var line = ARecipeIngredient(recipe.Id, 1, mehl.Id, 100m);
        var step = AStep(recipe.Id, 1, "Vorhandener Schritt.");
        Db.Recipes.Add(recipe);
        Db.RecipeIngredients.Add(line);
        Db.Steps.Add(step);
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        Db.ChangeTracker.Clear();
        return new ExistingRecipe(recipe, line, step);
    }

    private sealed record ExistingRecipe(RecipeDbType Recipe, RecipeIngredientDbType Line, StepDbType Step);

    // Then-Teil: 422 mit genau diesen Meldungen; gespeichert ist weiterhin nur das vorhandene Rezept (Full State).
    private async Task AssertRejectedKeepingExistingAsync(
        HttpResponseMessage response, IReadOnlyDictionary<string, IReadOnlyList<string>> expectedErrors, ExistingRecipe existing)
    {
        await AssertValidationErrorsAsync(response, expectedErrors);
        // AsNoTracking: der Helfer läuft im selben Test mehrfach auf demselben Kontext; getrackt bekäme der zweite
        // Aufruf die Instanzen des ersten zurück (Identity Resolution) und sähe eine veränderte Zeile nicht.
        (await Db.Recipes.AsNoTracking().ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo([existing.Recipe]);
        (await Db.RecipeIngredients.AsNoTracking().ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo([existing.Line]);
        (await Db.Steps.AsNoTracking().ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo([existing.Step]);
    }

    // Szenario: Schritt-Anweisung mit mehr als 1000 Zeichen
    [Fact]
    public async Task US602_Error_CreateRecipe_InstructionTooLong_Returns422AtStep()
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));
        var request = ACreateRecipe(
            steps: [AStepPayload("Teig rühren."), AStepPayload(new string('a', 1001))]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: die Meldung am zweiten Schritt (ADR-S144-1), nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError("steps[1].instruction", InstructionTooLongMessage));
    }

    private const string InstructionTooLongMessage = "Schritt-Anweisung darf maximal 1000 Zeichen lang sein.";

    // Szenario: Alle fehlerhaften Schritte werden gemeldet, der Fokus liegt auf dem ersten
    [Fact]
    public async Task US602_Error_CreateRecipe_SeveralInstructionsTooLong_Returns422AtEachStep()
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));
        var request = ACreateRecipe(
            steps: [AStepPayload("Teig rühren."), AStepPayload(new string('a', 1001)), AStepPayload(new string('b', 1001))]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: je eine Meldung an Schritt 2 und 3, keine an Schritt 1, nichts gespeichert
        await AssertRejectedWithAsync(response, new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal)
        {
            ["steps[1].instruction"] = [InstructionTooLongMessage],
            ["steps[2].instruction"] = [InstructionTooLongMessage],
        });
    }

    // Roh-Eingabe aus dem normalisierten Wert: je zwei Leerzeichen davor/dahinter, inneres Leerzeichen verdoppelt.
    private static string WithExtraSpaces(string text) => $"  {text.Replace(" ", "  ", StringComparison.Ordinal)}  ";

    // Gemeinsamer Then-Teil von „Rezept mit einem Schritt gespeichert" (Full State): 201, genau ein Rezept in der DB
    // (Id vergibt der Server; sie wird über recipes[0].Id gegen den Body geprüft), Body in Zutatenreihenfolge,
    // Rezept-Zutaten in Zeilenreihenfolge (Position = Index + 1, Menge aus der erwarteten Anzeige), ein Schritt
    // und unveränderte Zutaten (alle geseedeten, auch die, die keine Zeile nennt). Je Zutat ein Paar aus geseedeter
    // Zutat und erwarteter Anzeige, in Zeilenreihenfolge.
    private async Task AssertRecipeWithOneStepStoredAsync(
        HttpResponseMessage response, string title, string instruction,
        params (IngredientDbType Seed, RecipeIngredientResponse Expected)[] ingredients)
    {
        response.StatusCode.Should().Be(HttpStatusCode.Created, "das Rezept wird angelegt");
        var recipes = await Db.Recipes.ToListAsync(TestContext.Current.CancellationToken);
        recipes.Should().BeEquivalentTo([ARecipe(title)], o => o.Excluding(r => r.Id), "genau ein Rezept ist gespeichert");
        var body = await response.Content.ReadFromJsonAsync<RecipeResponse>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo(
            new RecipeResponse(
                Id: recipes[0].Id, Title: title, Ingredients: ingredients.Select(i => i.Expected).ToList(),
                Steps: [AStepPayload(instruction)]),
            o => o.WithStrictOrdering(), "der Body trägt das gespeicherte Rezept in Zutatenreihenfolge");
        (await Db.RecipeIngredients.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo(
            ingredients.Select((ingredient, index) => ARecipeIngredient(
                recipeId: recipes[0].Id, position: index + 1, ingredientId: ingredient.Seed.Id,
                quantity: ingredient.Expected.Quantity)),
            "die Rezept-Zutaten stehen in Zeilenreihenfolge mit der erwarteten Menge");
        (await Db.Steps.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo(
            [AStep(recipeId: recipes[0].Id, stepNumber: 1, instruction: instruction)], "genau ein Schritt ist gespeichert");
        (await Db.Ingredients.ToListAsync(TestContext.Current.CancellationToken)).Should().BeEquivalentTo(
            _seededIngredients, "die Zutaten bleiben unverändert");
    }

    // Szenario: Titel und Anweisung mit genau der zulässigen Länge werden gespeichert
    // Gemessen wird am normalisierten Wert (ADR-S135-1): roh 105 bzw. 1005 Zeichen, normalisiert 100 bzw. 1000.
    [Fact]
    public async Task US602_EdgeCase_CreateRecipe_ExactMaxLengthAfterNormalization_Returns201AndPersistsNormalized()
    {
        // Given: Titel aus 100 und Anweisung aus 1000 Zeichen (normalisiert)
        var title = $"{new string('a', 49)} {new string('b', 50)}";
        var instruction = $"{new string('c', 499)} {new string('d', 500)}";
        title.Length.Should().Be(100);
        instruction.Length.Should().Be(1000);

        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        var mehl = AnIngredient("Mehl", "g");
        await SeedIngredientsAsync(mehl);
        var request = ACreateRecipe(title: WithExtraSpaces(title), steps: [AStepPayload(WithExtraSpaces(instruction))]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: 201, Body und gespeicherter Stand tragen Titel und Anweisung normalisiert (Full State)
        await AssertRecipeWithOneStepStoredAsync(
            response, title, instruction, (mehl, new RecipeIngredientResponse(Name: "Mehl", Quantity: 250m, Unit: "g")));
    }

    // Szenario: Zutatenzeilen in typischer Schreibweise werden erkannt und wie gespeichert angezeigt
    // Beispiel: alle
    // Angezeigt wird der gespeicherte Name mit der Basiseinheit der Zutat (ADR-S135-2), nicht die Schreibweise der Zeile.
    [Theory]
    [MemberData(nameof(TypicalIngredientLines))]
    public async Task US602_EdgeCase_CreateRecipe_IngredientLineInTypicalNotation_Returns201AndShowsStoredIngredient(
        string baseUnit, string line, RecipeIngredientResponse expectedDisplay)
    {
        // Given: die Zutat (gespeicherter Name = Name der erwarteten Anzeige) existiert
        var ingredient = AnIngredient(expectedDisplay.Name, baseUnit);
        await SeedIngredientsAsync(ingredient);
        const string title = "Testrezept";
        const string instruction = "Alles mischen.";
        var request = ACreateRecipe(title: title, ingredients: line, steps: [AStepPayload(instruction)]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: 201, der Body zeigt die Zutat mit gespeichertem Namen und Basiseinheit
        // Menge als Dezimalzahl (ADR-S020-1); die Rezept-Zutat verweist auf die gefundene Zutat
        await AssertRecipeWithOneStepStoredAsync(response, title, instruction, (ingredient, expectedDisplay));
    }

    // Parameter: Basiseinheit der Zutat, Zeile im Zutatenfeld, erwartete Anzeige (Outline: Name | Einheit | Zeile | Anzeige).
    // Die Spalte „Name" ist in jedem Beispiel gleich dem Namen der Anzeige; der Test seedet die Zutat deshalb unter
    // expectedDisplay.Name. Ein künftiges Beispiel mit abweichendem Namen bräuchte eine eigene Spalte.
    public static IEnumerable<TheoryDataRow<string, string, RecipeIngredientResponse>> TypicalIngredientLines =>
    [
        new("g", "125 g rote Linsen", new RecipeIngredientResponse("rote Linsen", 125m, "g")) { TestDisplayName = "125 g rote Linsen" },
        new("Pck.", "1 Pck. Vanillezucker", new RecipeIngredientResponse("Vanillezucker", 1m, "Pck.")) { TestDisplayName = "1 Pck. Vanillezucker" },
        new("g", "250 G mehl", new RecipeIngredientResponse("Mehl", 250m, "g")) { TestDisplayName = "250 G mehl" },
        new("Prise", "schwarzer pfeffer", new RecipeIngredientResponse("schwarzer Pfeffer", null, null)) { TestDisplayName = "schwarzer pfeffer (ohne Menge und Einheit)" },
    ];

    // Szenario: Ungültige Menge in einer Zutatenzeile
    // Beispiel: alle
    // Die Meldung zitiert die Zeile in „…“ (U+201E/U+201C, ADR-S051-2) und steht allein auf `ingredients`; bei
    // mehreren verletzten Regeln gilt die erste: Zahlform, größer als 0, Nachkommastellen, Maximum (ADR-S135-2).
    [Theory]
    [MemberData(nameof(InvalidQuantityLines))]
    public async Task US602_Error_CreateRecipe_InvalidQuantity_Returns422AtIngredients(string line, string expectedMessage)
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept wird gespeichert
        var response = await PostPancakesAsync(line);

        // Then: genau die eine Meldung bei den Zutaten, nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError("ingredients", $"„{line}“: {expectedMessage}"));
    }

    // Das Rezept „Pfannkuchen“ mit einem Schritt und genau diesen Zutatenzeilen.
    private Task<HttpResponseMessage> PostPancakesAsync(string ingredients) =>
        PostRecipeAsync(ACreateRecipe(title: "Pfannkuchen", ingredients: ingredients, steps: [AStepPayload("Teig rühren.")]));

    // Die Meldung ohne Zitat der Zeile, wenn die Zutat nicht (aktiv) im Bestand ist.
    private static string NotFound(string name) =>
        $"Zutat '{name}' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt.";

    private const string NotANumber = "Menge muss eine Zahl sein (z. B. 1,5).";
    private const string NotPositive = "Menge muss größer als 0 sein.";
    private const string TooManyDecimals = "Menge darf maximal 3 Nachkommastellen haben.";
    private const string TooLarge = "Menge darf maximal 9999,999 sein.";

    // Parameter: Zeile, Meldung ohne Zitat der Zeile.
    public static IEnumerable<TheoryDataRow<string, string>> InvalidQuantityLines =>
    [
        new("0 g Mehl", NotPositive) { TestDisplayName = "0 g Mehl" },
        new("0,0005 g Mehl", TooManyDecimals) { TestDisplayName = "0,0005 g Mehl" },
        new("10000,0005 g Mehl", TooManyDecimals) { TestDisplayName = "10000,0005 g Mehl" },
        new("1,0000000000000000000000000000001 g Mehl", TooManyDecimals) { TestDisplayName = "1,(30 Nullen)1 g Mehl" },
        new("0,0000000000000000000000000000001 g Mehl", TooManyDecimals) { TestDisplayName = "0,(30 Nullen)1 g Mehl" },
        new("10000 g Mehl", TooLarge) { TestDisplayName = "10000 g Mehl" },
        new("10000,000 g Mehl", TooLarge) { TestDisplayName = "10000,000 g Mehl" },
        new("100000000000000000000000000000 g Mehl", TooLarge) { TestDisplayName = "10^29 g Mehl" },
        new("1.5 g Mehl", NotANumber) { TestDisplayName = "1.5 g Mehl" },
        new("1.000 g Mehl", NotANumber) { TestDisplayName = "1.000 g Mehl" },
        new("5, g Mehl", NotANumber) { TestDisplayName = "5, g Mehl" },
        new("1,5,5 g Mehl", NotANumber) { TestDisplayName = "1,5,5 g Mehl" },
    ];

    // Szenario: Zutat nicht gefunden oder Einheit falsch
    // Beispiel: alle
    // „250 g Butter": eine gelöschte Zutat gilt als nicht gefunden (ADR-S135-2). „1": nach der Menge steht kein
    // Wort mehr, die Zutat fehlt (ADR-S135-2, Addendum S148).
    [Theory]
    [MemberData(nameof(UnresolvableIngredientLines))]
    public async Task US602_Error_CreateRecipe_IngredientNotFoundOrUnitWrong_Returns422AtIngredients(
        string line, string expectedMessage)
    {
        // Given: "Mehl" (g) und "Zwiebel" (Stück) existieren, "Butter" (g) existiert und wurde gelöscht
        await SeedIngredientsAsync(
            AnIngredient("Mehl", "g"),
            AnIngredient("Zwiebel", "Stück"),
            AnIngredient("Butter", "g", deletedAt: DateTimeOffset.UtcNow));

        // When: das Rezept wird gespeichert
        var response = await PostPancakesAsync(line);

        // Then: genau die eine Meldung bei den Zutaten, nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError("ingredients", $"„{line}“: {expectedMessage}"));
    }

    // Parameter: Zeile, Meldung ohne Zitat der Zeile.
    public static IEnumerable<TheoryDataRow<string, string>> UnresolvableIngredientLines =>
    [
        new("250 g Mehk", NotFound("Mehk")) { TestDisplayName = "250 g Mehk" },
        new("250 g Butter", NotFound("Butter")) { TestDisplayName = "250 g Butter (gelöscht)" },
        new("2 EL Mehl", "Einheit 'EL' passt nicht zu 'Mehl' (möglich: 'g').") { TestDisplayName = "2 EL Mehl" },
        new("1 Zwiebel", "Einheit fehlt (für 'Zwiebel': 'Stück').") { TestDisplayName = "1 Zwiebel" },
        new("1", "Zutat fehlt.") { TestDisplayName = "1 (nur Menge)" },
    ];

    // Szenario: Alle fehlerhaften Zutatenzeilen werden gemeinsam und in Zeilenreihenfolge gemeldet
    [Fact]
    public async Task US602_Error_CreateRecipe_SeveralInvalidIngredientLines_Returns422InLineOrder()
    {
        // Given: die Zutaten "Mehl" (g) und "Milch" (ml) existieren
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"), AnIngredient("Milch", "ml"));

        // When: das Rezept wird gespeichert
        var response = await PostPancakesAsync("250 g Mehl\n2 Eier\n500 Milch");

        // Then: beide Meldungen gemeinsam und in Zeilenreihenfolge bei den Zutaten, nichts gespeichert
        await AssertRejectedWithAsync(response, new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal)
        {
            ["ingredients"] =
            [
                $"„2 Eier“: {NotFound("Eier")}",
                "„500 Milch“: Einheit fehlt (für 'Milch': 'ml').",
            ],
        });
    }

    // Szenario: Eine Zutat, die schon in einer früheren Zeile steht, wird gemeldet
    [Fact]
    public async Task US602_Error_CreateRecipe_IngredientInEarlierLine_Returns422AtIngredients()
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept wird gespeichert
        var response = await PostPancakesAsync("250 g Mehl\n100 g Mehl");

        // Then: genau die Meldung zur zweiten Zeile, nichts gespeichert
        await AssertRejectedWithAsync(
            response, SingleError("ingredients", "„100 g Mehl“: Zutat 'Mehl' steht bereits in einer früheren Zeile."));
    }

    // ADR-S135-2 (Addendum S148) (kein US-Tag, ADR-S106-3 „Stryker-blinde Invariante"): Prüfreihenfolge einer Zeile –
    // die Menge kommt vor „Zutat fehlt". Eine Zeile nur aus ungültiger Menge nennt die Menge; ein Umtausch der
    // Prüfungen ist kein Mutant.
    [Fact]
    public async Task CreateRecipe_LineOfInvalidQuantityOnly_ReportsQuantityBeforeMissingIngredient()
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept wird gespeichert
        var response = await PostPancakesAsync("0");

        // Then: die Mengenmeldung, nicht „Zutat fehlt.", nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError("ingredients", "„0“: Menge muss größer als 0 sein."));
    }

    // ADR-S135-2 (Addendum S148) (kein US-Tag, ADR-S106-3 „Stryker-blinde Invariante"): doppelt ist eine Zeile nur
    // gegenüber einer früheren FEHLERFREIEN Zeile – die fehlerhafte erste Zeile zählt nicht als Zutat. Die Zutat
    // schon beim Auflösen zu merken (vor der Einheitenprüfung) ist kein Mutant.
    [Fact]
    public async Task CreateRecipe_EarlierLineWithWrongUnit_DoesNotMakeLaterLineDuplicate()
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept wird gespeichert
        var response = await PostPancakesAsync("2 EL Mehl\n100 g Mehl");

        // Then: genau eine Meldung, zur ersten Zeile; keine Doppelt-Meldung zur zweiten
        await AssertRejectedWithAsync(
            response, SingleError("ingredients", "„2 EL Mehl“: Einheit 'EL' passt nicht zu 'Mehl' (möglich: 'g')."));
    }

    // ADR-S135-2 (Addendum S148) (kein US-Tag, ADR-S106-3 „Stryker-blinde Invariante"): doppelt ist die Zutat, nicht
    // die Schreibweise – Groß-/Kleinschreibung und eine fehlende Menge in der früheren Zeile ändern daran nichts.
    // Ein Vergleich über den Namen aus der Zeile statt über die Zutat ist kein Mutant.
    [Theory]
    [InlineData("250 g Mehl\n100 g mehl", "„100 g mehl“: Zutat 'mehl' steht bereits in einer früheren Zeile.")]
    [InlineData("Mehl\n250 g Mehl", "„250 g Mehl“: Zutat 'Mehl' steht bereits in einer früheren Zeile.")]
    public async Task CreateRecipe_SameIngredientInOtherSpellingOrWithoutQuantity_ReportsDuplicateAtLaterLine(
        string ingredients, string expectedMessage)
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept wird gespeichert
        var response = await PostPancakesAsync(ingredients);

        // Then: genau die Doppelt-Meldung zur späteren Zeile, nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError("ingredients", expectedMessage));
    }

    // ADR-S135-3 (kein US-Tag, ADR-S106-3 „Stryker-blinde Invariante"): alle Feldprüfungen laufen gesammelt – auch
    // die Prüfung der Zeile, die den Zutatenbestand braucht, steht neben der Titelmeldung. Ein kurzschließender
    // Umbau (Titel zuerst, dann Zeilen) ist kein Mutant.
    [Fact]
    public async Task CreateRecipe_EmptyTitleAndUnknownIngredient_Returns422WithBothMessages()
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert; Titel leer, Zeile mit unbekannter Zutat
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));
        var request = ACreateRecipe(title: "", ingredients: "250 g Mehk");

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: beide Meldungen gleichzeitig, nichts gespeichert
        await AssertRejectedWithAsync(response, new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal)
        {
            ["title"] = ["Titel darf nicht leer sein."],
            ["ingredients"] = [$"„250 g Mehk“: {NotFound("Mehk")}"],
        });
    }

    // ADR-S135-2, Addendum S148 (kein US-Tag, ADR-S106-3 „Stryker-blinde Invariante"): eine Zeile trifft die Zutat,
    // die unter LOWER – der Funktion des Unique-Index (ADR-S105-2) – gleich heißt, also höchstens eine. „µg-Mix"
    // (Mikro-Zeichen U+00B5) und „μg-Mix" (griechisches My U+03BC) lässt der Index beide zu; ein .NET-Vergleich mit
    // OrdinalIgnoreCase hielte sie für gleich. Was der Test trennt: OrdinalIgnoreCase gegen LOWER. Was nicht: ob
    // LOWER in der DB oder als ToLowerInvariant in .NET läuft – für dieses Paar fallen beide gleich aus.
    [Fact]
    public async Task CreateRecipe_IngredientNamesEqualOnlyUnderNetCaseFolding_ReferencesIngredientNamedInLine()
    {
        // Given: die Zutaten „µg-Mix" und „μg-Mix" existieren
        var micro = AnIngredient(char.ConvertFromUtf32(0x00B5) + "g-Mix", "g");
        var my = AnIngredient(char.ConvertFromUtf32(0x03BC) + "g-Mix", "g");
        await SeedIngredientsAsync(micro, my);
        const string title = "Testrezept";
        const string instruction = "Alles mischen.";
        var request = ACreateRecipe(title: title, ingredients: my.Name, steps: [AStepPayload(instruction)]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: 201, die Rezept-Zutat verweist auf „μg-Mix", nicht auf „µg-Mix" (Full State)
        await AssertRecipeWithOneStepStoredAsync(
            response, title, instruction, (my, new RecipeIngredientResponse(Name: my.Name, Quantity: null, Unit: null)));
    }

    // Szenario: Mengen an den Grenzen werden gespeichert und angezeigt
    // Beispiel: alle
    // Nullen am Ende zählen nicht als Nachkommastellen; die Menge wird exakt gespeichert.
    [Theory]
    [MemberData(nameof(BoundaryQuantityLines))]
    public async Task US602_EdgeCase_CreateRecipe_QuantityAtBoundary_Returns201AndShowsQuantity(
        string line, decimal expectedQuantity)
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        var mehl = AnIngredient("Mehl", "g");
        await SeedIngredientsAsync(mehl);
        const string title = "Pfannkuchen";
        const string instruction = "Teig rühren.";
        var request = ACreateRecipe(title: title, ingredients: line, steps: [AStepPayload(instruction)]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: 201, die Menge steht exakt im Body und in der DB
        await AssertRecipeWithOneStepStoredAsync(
            response, title, instruction, (mehl, new RecipeIngredientResponse("Mehl", expectedQuantity, "g")));
    }

    // Parameter: Zeile, erwartete Menge der Anzeige (Outline: Zeile | Anzeige).
    public static IEnumerable<TheoryDataRow<string, decimal>> BoundaryQuantityLines =>
    [
        new("0,001 g Mehl", 0.001m) { TestDisplayName = "0,001 g Mehl" },
        new("9999,999 g Mehl", 9999.999m) { TestDisplayName = "9999,999 g Mehl" },
        new("0,0010 g Mehl", 0.001m) { TestDisplayName = "0,0010 g Mehl" },
        new("9999,9990 g Mehl", 9999.999m) { TestDisplayName = "9999,9990 g Mehl" },
        new("1,5 g Mehl", 1.5m) { TestDisplayName = "1,5 g Mehl" },
    ];

    // Szenario: Leere Zeilen und Zeilen aus Leerzeichen im Zutatenfeld werden übergangen
    // „Leer" heißt nach der Normalisierung leer (ADR-S135-1): auch eine Zeile nur aus Leerzeichen ohne Breite
    // (U+200B) ergibt keine Zutat – string.IsNullOrWhiteSpace erkennt sie nicht.
    [Fact]
    public async Task US602_EdgeCase_CreateRecipe_BlankIngredientLines_Returns201AndSkipsThem()
    {
        // Given: die Zutaten "Mehl" (g) und "Milch" (ml) existieren
        var mehl = AnIngredient("Mehl", "g");
        var milch = AnIngredient("Milch", "ml");
        await SeedIngredientsAsync(mehl, milch);
        const string title = "Pfannkuchen";
        const string instruction = "Teig rühren.";
        // Die Zeilen des Szenarios: "250 g Mehl", eine leere Zeile, eine Zeile aus Leerzeichen, eine Zeile nur
        // aus Leerzeichen ohne Breite (U+200B), "500 ml Milch".
        var lines = new[] { "250 g Mehl", "", "   ", char.ConvertFromUtf32(0x200B), "500 ml Milch" };
        var request = ACreateRecipe(
            title: title, ingredients: string.Join('\n', lines), steps: [AStepPayload(instruction)]);

        // When: das Rezept wird gespeichert
        var response = await PostRecipeAsync(request);

        // Then: 201, nur die beiden Zutaten in dieser Reihenfolge
        await AssertRecipeWithOneStepStoredAsync(
            response, title, instruction,
            (mehl, new RecipeIngredientResponse(Name: "Mehl", Quantity: 250m, Unit: "g")),
            (milch, new RecipeIngredientResponse(Name: "Milch", Quantity: 500m, Unit: "ml")));
    }

    // ADR-S144-2 (kein US-Tag, ADR-S106-3 „Protokoll-/Infrastruktur-Mechanik"): explizites null zählt wie
    // leer und bekommt die Pflichtmeldung des Feldes. Das jeweils andere Feld ist gültig, damit genau
    // eine Meldung erwartet wird.
    [Theory]
    [InlineData("""{"title":null,"ingredients":"250 g Mehl","steps":[{"instruction":"Teig rühren."}]}""", "title", "Titel darf nicht leer sein.")]
    [InlineData("""{"title":"Pfannkuchen","ingredients":null,"steps":[{"instruction":"Teig rühren."}]}""", "ingredients", "Rezept muss mindestens eine Zutat haben.")]
    [InlineData("""{"title":"Pfannkuchen","ingredients":"250 g Mehl","steps":null}""", "steps", "Rezept muss mindestens einen Schritt haben.")]
    public async Task CreateRecipe_NullProperty_Returns422LikeEmpty(string json, string expectedKey, string expectedMessage)
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept mit explizitem null gesendet wird
        var response = await PostRawJsonAsync(json);

        // Then: die Pflichtmeldung am betroffenen Feld, nichts gespeichert
        await AssertRejectedWithAsync(response, SingleError(expectedKey, expectedMessage));
    }

    // ADR-S144-2 (kein US-Tag, ADR-S106-3 „Protokoll-/Infrastruktur-Mechanik"): ein Body, dem ein
    // Property ganz fehlt, ist ein fehlerhafter Request (400), kein Validierungsfall und kein 500.
    [Theory]
    [InlineData("""{"ingredients":"250 g Mehl","steps":[{"instruction":"Teig rühren."}]}""")]
    [InlineData("""{"title":"Pfannkuchen","steps":[{"instruction":"Teig rühren."}]}""")]
    [InlineData("""{"title":"Pfannkuchen","ingredients":"250 g Mehl"}""")]
    public async Task CreateRecipe_MissingRequiredProperty_Returns400AndPersistsNothing(string json)
    {
        // Given: die Zutat "Mehl" mit Einheit "g" existiert
        await SeedIngredientsAsync(AnIngredient("Mehl", "g"));

        // When: das Rezept mit fehlendem Property gesendet wird
        var response = await PostRawJsonAsync(json);

        // Then: 400 Bad Request, nichts gespeichert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        await AssertNothingPersistedAsync();
    }
}

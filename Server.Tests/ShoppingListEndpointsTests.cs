using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace mahl.Server.Tests;

[Collection(PostgresCollectionDefinition.Name)]
public class ShoppingListEndpointsTests(PostgresContainerFixture postgres) : EndpointsTestsBase(postgres)
{
    // Szenario: Eine noch nie gefüllte Einkaufsliste zeigt einen Hinweis
    [Fact]
    public async Task US201_HappyPath_GetShoppingList_NeverFilled_Returns200WithEmptyList()
    {
        // Given: das Rezept "Pfannkuchen" ist vorgemerkt, die Einkaufsliste ist leer (noch nie gefüllt)
        var pancake = ARecipe("Pfannkuchen");
        Db.Recipes.Add(pancake);
        Db.PlannedRecipes.Add(new PlannedRecipeDbType { RecipeId = pancake.Id });
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);

        // When
        var response = await Client.GetAsync("/api/shopping-list", TestContext.Current.CancellationToken);

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<object[]>(TestContext.Current.CancellationToken);
        body.Should().BeEmpty();
    }

    // Szenario: Die Zutaten der vorgemerkten Rezepte alphabetisch auf die Einkaufsliste übernehmen
    [Fact]
    public async Task US201_HappyPath_PostGenerate_PlannedRecipes_Returns204AndListsTotalsAlphabetically()
    {
        // Given: Pfannkuchen und Kartoffelsuppe vorgemerkt, Linsensalat existiert ohne Vormerkung
        var pancake = await SeedRecipeAsync("Pfannkuchen", planned: true, ("Mehl", "g", 250m), ("Milch", "l", 0.5m), ("Eier", "Stück", 3m));
        var soup = await SeedRecipeAsync("Kartoffelsuppe", planned: true, ("Kartoffeln", "g", 1000m), ("Salz", "g", null));
        await SeedRecipeAsync("Linsensalat", planned: false, ("Linsen", "g", 200m));

        // When
        var response = await GenerateAsync();

        // Then: 204, genau diese Einträge in dieser Reihenfolge, die Vormerkungen sind unverändert
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        await AssertShoppingListAsync(
            ("Eier", 3m, "Stück"),
            ("Kartoffeln", 1000m, "g"),
            ("Mehl", 250m, "g"),
            ("Milch", 0.5m, "l"),
            ("Salz", null, null));
        await AssertPlannedRecipesAsync(pancake.Id, soup.Id);
    }

    // Szenario: Dieselbe Zutat aus mehreren Rezepten steht einmal mit der Gesamtmenge da
    [Fact]
    public async Task US201_HappyPath_PostGenerate_SameIngredientInSeveralRecipes_ListsItOnceWithTotal()
    {
        // Given
        await SeedRecipeAsync("Pfannkuchen", planned: true, ("Mehl", "g", 250m), ("Milch", "l", 0.5m));
        await SeedRecipeAsync("Waffeln", planned: true, ("Mehl", "g", 300m), ("Butter", "g", 100m));

        // When
        var response = await GenerateAsync();

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        await AssertShoppingListAsync(
            ("Butter", 100m, "g"),
            ("Mehl", 550m, "g"),
            ("Milch", 0.5m, "l"));
    }

    // Szenario: Die Einkaufsliste bleibt bis zum erneuten Übernehmen unverändert, das sie dann ersetzt
    [Fact]
    public async Task US201_HappyPath_PostGenerate_PlannedRecipesChangedAfterwards_KeepsSnapshotUntilNextGenerateReplacesIt()
    {
        // Given: übernommen mit Pfannkuchen und Kartoffelsuppe; danach Kartoffelsuppe nicht mehr, Linsensalat vorgemerkt
        await SeedRecipeAsync("Pfannkuchen", planned: true, ("Mehl", "g", 250m), ("Milch", "l", 0.5m));
        var soup = await SeedRecipeAsync("Kartoffelsuppe", planned: true, ("Kartoffeln", "g", 1000m), ("Salz", "g", null));
        var lentils = await SeedRecipeAsync("Linsensalat", planned: false, ("Linsen", "g", 200m));
        await GenerateAsync();
        Db.PlannedRecipes.Remove(await Db.PlannedRecipes.SingleAsync(p => p.RecipeId == soup.Id, TestContext.Current.CancellationToken));
        Db.PlannedRecipes.Add(new PlannedRecipeDbType { RecipeId = lentils.Id });
        await Db.SaveChangesAsync(TestContext.Current.CancellationToken);
        // Vorbedingung (erster Then-Schritt des Szenarios): bis zum erneuten Übernehmen zeigt die Liste die Momentaufnahme
        (await GetShoppingListAsync()).Should().Equal(
            new ShoppingListItemResponse(Name: "Kartoffeln", Quantity: 1000m, Unit: "g"),
            new ShoppingListItemResponse(Name: "Mehl", Quantity: 250m, Unit: "g"),
            new ShoppingListItemResponse(Name: "Milch", Quantity: 0.5m, Unit: "l"),
            new ShoppingListItemResponse(Name: "Salz", Quantity: null, Unit: null));

        // When
        var response = await GenerateAsync();

        // Then: zweiter Then-Schritt des Szenarios – die Liste ist durch die neue ersetzt
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        await AssertShoppingListAsync(
            ("Linsen", 200m, "g"),
            ("Mehl", 250m, "g"),
            ("Milch", 0.5m, "l"));
    }

    // Szenario: Zutaten ohne Menge auf der Einkaufsliste
    // Beispiel: alle
    [Theory]
    [MemberData(nameof(NoQuantityCases))]
    public async Task US201_EdgeCase_PostGenerate_SameIngredientWithAndWithoutQuantity_ListsQuantityOnlyIfAnyGiven(
        string ingredient, string unit, decimal? pancakeQuantity, decimal? wafflesQuantity,
        decimal? expectedQuantity, string? expectedUnit)
    {
        // Given: Pfannkuchen und Waffeln vorgemerkt
        await SeedPancakesAndWafflesAsync(ingredient, unit, pancakeQuantity, wafflesQuantity);

        // When
        var response = await GenerateAsync();

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        await AssertShoppingListAsync((ingredient, expectedQuantity, expectedUnit));
    }

    // Zutat, Basiseinheit, Menge Pfannkuchen, Menge Waffeln, erwartete Menge, erwartete Einheit
    public static TheoryData<string, string, decimal?, decimal?, decimal?, string?> NoQuantityCases => new()
    {
        { "Zucker", "g", 50m, null, 50m, "g" },
        { "Zucker", "g", null, 50m, 50m, "g" },
        { "Salz", "g", null, null, null, null },
    };

    // Szenario: Gesamtmengen stehen in deutscher Schreibweise da
    // Beispiel: alle
    [Theory]
    [MemberData(nameof(TotalCases))]
    // Zwei Grundriss-Szenarien mit gleichem Ablauf, getrennt für die Traceability – Sonar S4144 meldete sonst die
    // identischen Rümpfe der beiden Theories.
#pragma warning disable S4144
    public async Task US201_EdgeCase_PostGenerate_SameIngredientInTwoRecipes_ListsExactDecimalTotal(
        string ingredient, string unit, decimal? pancakeQuantity, decimal? wafflesQuantity,
        decimal? expectedQuantity, string? expectedUnit)
#pragma warning restore S4144
    {
        // Given: Pfannkuchen und Waffeln vorgemerkt
        await SeedPancakesAndWafflesAsync(ingredient, unit, pancakeQuantity, wafflesQuantity);

        // When
        var response = await GenerateAsync();

        // Then: die Gesamtmenge ist die exakte Dezimalsumme (die Schreibweise macht der Client)
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        await AssertShoppingListAsync((ingredient, expectedQuantity, expectedUnit));
    }

    // Zutat, Basiseinheit, Menge Pfannkuchen, Menge Waffeln, erwartete Menge, erwartete Einheit. Auf dem Server sind
    // alle Zeilen nur Summen; was ihre Fälle unterscheidet („keine Nullen am Ende", „ganze Zahl ohne Komma"), prüft
    // erst die Schreibweise im Client.
    public static TheoryData<string, string, decimal?, decimal?, decimal?, string?> TotalCases => new()
    {
        { "Milch", "l", 0.1m, 0.2m, 0.3m, "l" },
        { "Milch", "l", 0.125m, 0.375m, 0.5m, "l" },
        { "Milch", "l", 0.5m, 0.5m, 1m, "l" },
        { "Milch", "l", 0.125m, 0.25m, 0.375m, "l" },
        { "Mehl", "g", 6000m, 5000m, 11000m, "g" },
    };

    // Kategorie „Vertrag aus dem Feature-Kopf", kein US-Tag: features/shopping-lists.feature, Abschnitt „Invarianten":
    // „Scheitert Übernehmen, bleibt die bisherige Einkaufsliste unverändert" (ADR-S154-2/-3: Ersetzen in einer
    // Transaktion). Die Summe überschreitet 99999,999; der Statuscode der Meldung ist ungeregelt (TD-S154-5)
    // und bleibt ungeprüft.
    // ADR-S106-3
    [Fact]
    public async Task PostGenerate_TotalExceedsLimit_Fails_KeepsPreviousShoppingList()
    {
        // Given: eine übernommene Liste, danach 11 vorgemerkte Rezepte mit je 9999,999 Mehl (Summe über 99999,999)
        var plannedIds = new List<Guid>
        {
            (await SeedRecipeAsync("Pfannkuchen", planned: true, ("Mehl", "g", 250m), ("Milch", "l", 0.5m))).Id,
        };
        await GenerateAsync();
        for (var number = 1; number <= 11; number++)
        {
            plannedIds.Add((await SeedRecipeAsync($"Mehlkuchen {number}", planned: true, ("Mehl", "g", 9999.999m))).Id);
        }

        // When
        var response = await GenerateAsync();

        // Then: kein Erfolg, Ausgangszustand – bisherige Liste in DB und GET, Vormerkungen unverändert
        response.IsSuccessStatusCode.Should().BeFalse();
        await AssertShoppingListAsync(
            ("Mehl", 250m, "g"),
            ("Milch", 0.5m, "l"));
        await AssertPlannedRecipesAsync([.. plannedIds]);
    }

    // Kategorie „Vertrag aus dem Feature-Kopf", kein US-Tag: features/shopping-lists.feature, Abschnitt „Regeln":
    // „Findet der Server beim Übernehmen keine Vormerkung …, wird die Einkaufsliste leer".
    // ADR-S106-3
    [Fact]
    public async Task PostGenerate_NoPlannedRecipesAnymore_Returns204AndEmptiesShoppingList()
    {
        // Given: eine übernommene Liste, danach alle Vormerkungen entfernt
        await SeedRecipeAsync("Pfannkuchen", planned: true, ("Mehl", "g", 250m));
        await GenerateAsync();
        await Db.PlannedRecipes.ExecuteDeleteAsync(TestContext.Current.CancellationToken);

        // When
        var response = await GenerateAsync();

        // Then
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        await AssertShoppingListAsync();
    }

    // Kategorie „Vertrag aus dem Feature-Kopf", kein US-Tag: features/shopping-lists.feature, Abschnitt „Regeln":
    // „„Alphabetisch" heißt deutsche Sortierung wie bei allen Listen (ADR-S142-1): Umlaute beim Grundbuchstaben,
    // Klein- und Großschreibung ohne Vorrang." Trennschärfe wie bei
    // US904_HappyPath_GetIngredients_UmlautAndLowercaseNames_ReturnsAlphabeticallySorted: „basilikum" (klein) und
    // „Öl"/„Möhre" (Umlaut) sortieren nach Byte-Reihenfolge anders als nach de-x-icu.
    // ADR-S106-3
    [Fact]
    public async Task PostGenerate_UmlautAndLowercaseNames_ListsGermanAlphabetically()
    {
        // Given: ein vorgemerktes Rezept mit sieben Zutaten in nicht-alphabetischer Reihenfolge
        await SeedRecipeAsync("Gemüsepfanne", planned: true,
            ("Zwiebel", "Stück", 1m), ("Mohrrübe", "Stück", 2m), ("Öl", "ml", 30m), ("basilikum", "Bund", 1m),
            ("Möhre", "Stück", 3m), ("Mohn", "g", 10m), ("Apfel", "Stück", 4m));

        // When
        var response = await GenerateAsync();

        // Then: Namen in deutscher Alphabet-Reihenfolge
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        await AssertShoppingListAsync(
            ("Apfel", 4m, "Stück"),
            ("basilikum", 1m, "Bund"),
            ("Mohn", 10m, "g"),
            ("Möhre", 3m, "Stück"),
            ("Mohrrübe", 2m, "Stück"),
            ("Öl", 30m, "ml"),
            ("Zwiebel", 1m, "Stück"));
    }

    private Task<HttpResponseMessage> GenerateAsync() =>
        Client.PostAsync("/api/shopping-list/generate", null, TestContext.Current.CancellationToken);

    // Legt Pfannkuchen und Waffeln mit je einer Menge derselben Zutat an und merkt beide vor.
    private async Task SeedPancakesAndWafflesAsync(
        string ingredient, string unit, decimal? pancakeQuantity, decimal? wafflesQuantity)
    {
        await SeedRecipeAsync("Pfannkuchen", planned: true, (ingredient, unit, pancakeQuantity));
        await SeedRecipeAsync("Waffeln", planned: true, (ingredient, unit, wafflesQuantity));
    }

    // Legt das Rezept an (Zutaten bei Bedarf, je Name einmal) und merkt es auf Wunsch vor.
    private async Task<RecipeDbType> SeedRecipeAsync(
        string title, bool planned, params (string Name, string Unit, decimal? Quantity)[] ingredients)
    {
        var ct = TestContext.Current.CancellationToken;
        var recipe = ARecipe(title);
        Db.Recipes.Add(recipe);
        var position = 1;
        foreach (var (name, unit, quantity) in ingredients)
        {
            var ingredient = await Db.Ingredients.SingleOrDefaultAsync(i => i.Name == name, ct);
            if (ingredient is null)
            {
                ingredient = AnIngredient(name, unit);
                Db.Ingredients.Add(ingredient);
                await Db.SaveChangesAsync(ct);
            }
            Db.RecipeIngredients.Add(ARecipeIngredient(recipe.Id, position++, ingredient.Id, quantity));
        }
        if (planned)
        {
            Db.PlannedRecipes.Add(new PlannedRecipeDbType { RecipeId = recipe.Id });
        }
        await Db.SaveChangesAsync(ct);
        return recipe;
    }

    private async Task<ShoppingListItemResponse[]> GetShoppingListAsync()
    {
        var response = await Client.GetAsync("/api/shopping-list", TestContext.Current.CancellationToken);
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<ShoppingListItemResponse[]>(TestContext.Current.CancellationToken);
        body.Should().NotBeNull();
        return body;
    }

    // Prüft GET (in dieser Reihenfolge) und DB (Full State, ohne Reihenfolge) aus einer Erwartungsliste.
    private async Task AssertShoppingListAsync(params (string Name, decimal? Quantity, string? Unit)[] expected)
    {
        (await GetShoppingListAsync()).Should().Equal(
            expected.Select(e => new ShoppingListItemResponse(Name: e.Name, Quantity: e.Quantity, Unit: e.Unit)));
        var expectedDb = new List<ShoppingListItemDbType>();
        foreach (var (name, quantity, _) in expected)
        {
            expectedDb.Add(new ShoppingListItemDbType { IngredientId = await IngredientIdAsync(name), Quantity = quantity });
        }
        (await GetShoppingListItemsFromDbAsync()).Should().BeEquivalentTo(expectedDb);
    }

    private async Task AssertPlannedRecipesAsync(params Guid[] recipeIds) =>
        (await Db.PlannedRecipes.AsNoTracking().ToListAsync(TestContext.Current.CancellationToken))
            .Should().BeEquivalentTo(recipeIds.Select(id => new PlannedRecipeDbType { RecipeId = id }));

    private Task<List<ShoppingListItemDbType>> GetShoppingListItemsFromDbAsync() =>
        Db.ShoppingListItems.AsNoTracking().ToListAsync(TestContext.Current.CancellationToken);

    private Task<Guid> IngredientIdAsync(string name) =>
        Db.Ingredients.Where(i => i.Name == name).Select(i => i.Id).SingleAsync(TestContext.Current.CancellationToken);

    private sealed record ShoppingListItemResponse(string Name, decimal? Quantity, string? Unit);
}

using System.Globalization;
using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Middleware;
using Microsoft.EntityFrameworkCore;

// Eine zerlegte Zutatenzeile (ADR-S135-2): der Name, unter dem die Zutat nachgeschlagen wird, und die
// Menge. Tupel-Alias statt eigenem Typ aus demselben Grund wie IngredientValues in IngredientsEndpoints:
// keine Invariante, nur Zwischenstand an der Grenze.
using ParsedIngredientLine = (string Name, mahl.Server.Domain.Quantity Quantity);

namespace mahl.Server.Endpoints;

internal static class RecipesEndpoints
{
    internal static void MapRecipesEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/recipes");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact (ADR-S136-1)
        group.WithTags("Recipes");

        // Noch unsortiert: die alphabetische Sortierung – und mit ihr ein stabiler Collection-ETag
        // (ADR-S084-1) – kommt mit dem Szenario „Mehrere Rezepte erscheinen alphabetisch sortiert".
        group.MapGet(
            "",
            async (MahlDbContext db) =>
                Results.Ok(await db.Recipes.Select(r => new RecipeSummaryDto(r.Id, r.Title)).ToListAsync()));

        // Handler-Logik ausgelagert wie IngredientsEndpoints.CreateIngredient – diese Methode bleibt
        // eine Routentabelle.
        group.MapPost("", RecipeMappings.CreateRecipe);
    }
}

file static class RecipeMappings
{
    // ADR-S030-1: hier – und nur hier – entsteht die Identität des Rezepts (RecipeId.New() unten), weil hier
    // die Zeile entsteht.
    // Ohne Validierung und ohne Fehlerantworten: die kommen mit den Fehler-Szenarien (Pflichtfelder,
    // Zeile nicht gefunden, Einheit falsch …). Bis dahin ist eine unbekannte Zeile unbestimmt.
    internal static async Task<IResult> CreateRecipe(CreateRecipeDto dto, MahlDbContext db, HttpContext httpContext)
    {
        // Bewusst ohne RequestAborted: Das Backend reicht Abbruch nirgends durch (Sonar S8949 verlangt die explizite Wahl).
        var ingredientsByName = await db.Ingredients.ToDictionaryAsync(i => i.Name, StringComparer.Ordinal, CancellationToken.None);
        var ingredientsById = ingredientsByName.Values.ToDictionary(i => i.Id);
        var recipe = ToRecipe(dto, RecipeId.New(), name => ingredientsByName[name].Id);

        var recipeRow = recipe.ToDbType();
        db.Recipes.Add(recipeRow);
        db.RecipeIngredients.AddRange(recipe.ToRecipeIngredientDbTypes());
        db.Steps.AddRange(recipe.ToStepDbTypes());
        await db.SaveChangesAsync(CancellationToken.None);

        // ADR-S106-1/ADR-S000-12: der xmin der neu angelegten Rezeptzeile geht als ETag mit dem 201 heraus.
        var xmin = (uint) db.Entry(recipeRow).Property("xmin").CurrentValue!;
        httpContext.Response.Headers.ETag = XminETag.Format(xmin);
        return Results.Created($"/api/recipes/{recipe.Id.Value}", recipe.ToDto(id => ingredientsById[id.Value]));
    }

    // Der Lookup Name -> Zutat-Id kommt als Funktion herein: die Zerlegung kennt keine DB.
    private static Recipe ToRecipe(CreateRecipeDto dto, RecipeId id, Func<string, Guid> ingredientIdByName) =>
        Recipe.Create(
            id,
            RecipeTitle.Create(dto.Title),
            [.. dto.Ingredients.Split('\n').Select(ParseLine).Select(line => ToRecipeIngredient(line, ingredientIdByName))],
            [.. dto.Steps.Select(step => StepInstruction.Create(step.Instruction))]);

    private static RecipeIngredient ToRecipeIngredient(ParsedIngredientLine line, Func<string, Guid> ingredientIdByName) =>
        RecipeIngredient.Create(IngredientId.Create(ingredientIdByName(line.Name)), line.Quantity);

    // ADR-S135-2, Ausschnitt des Gutfalls: beginnt die Zeile mit einer Ziffer, ist sie „Menge Einheit
    // Zutat"; sonst ist die ganze Zeile die Zutat, ohne Menge (ADR-S020-1). Die Einheit wird noch nicht
    // gelesen – sie ist die Basiseinheit der Zutat; ihre Prüfung kommt mit dem Szenario „Einheit falsch".
    private static ParsedIngredientLine ParseLine(string line) =>
        char.IsAsciiDigit(line[0]) ? ParseLineWithQuantity(line.Split(' ')) : (line, Quantity.Unspecified);

    private static ParsedIngredientLine ParseLineWithQuantity(string[] words)
    {
        // Wort 1 ist die Einheit, noch ungelesen (s. ParseLine). Kein List-Pattern: `is [var amount, _, var name]`
        // bräuchte einen Zweig für andere Wortzahlen, den noch kein Szenario fordert.
        var (amount, name) = (words[0], words[2]);
        return (name, Quantity.Specified(decimal.Parse(amount, CultureInfo.InvariantCulture)));
    }

    private static RecipeDbType ToDbType(this Recipe recipe) =>
        new() { Id = recipe.Id.Value, Title = recipe.Title.Value };

    // ADR-S135-2: Position = Zeilenreihenfolge, 1-basiert. ADR-S020-1: ohne Menge NULL.
    private static IEnumerable<RecipeIngredientDbType> ToRecipeIngredientDbTypes(this Recipe recipe) =>
        recipe.Ingredients.Select((ingredient, index) => new RecipeIngredientDbType
        {
            RecipeId = recipe.Id.Value,
            Position = index + 1,
            IngredientId = ingredient.Ingredient.Value,
            Quantity = ingredient.Quantity.Match<decimal?>(amount => amount, () => null),
        });

    // ADR-S027-1: StepNumber = Index + 1 der Listenposition, nur in der DB-Entität.
    private static IEnumerable<StepDbType> ToStepDbTypes(this Recipe recipe) =>
        recipe.Steps.Select((step, index) => new StepDbType
        {
            RecipeId = recipe.Id.Value, StepNumber = index + 1, Instruction = step.Value,
        });

    private static RecipeDto ToDto(this Recipe recipe, Func<IngredientId, IngredientDbType> ingredientRow) =>
        new(
            recipe.Id.Value,
            recipe.Title.Value,
            [.. recipe.Ingredients.Select(ingredient => ingredient.ToDto(ingredientRow(ingredient.Ingredient)))],
            [.. recipe.Steps.Select(step => new StepDto(step.Value))]);

    // ADR-S135-2: mit Menge ist die Einheit die Basiseinheit der Zutat; ohne Menge sind Menge und
    // Einheit null (ADR-S020-1).
    private static RecipeIngredientDto ToDto(this RecipeIngredient ingredient, IngredientDbType row) =>
        ingredient.Quantity.Match(
            amount => new RecipeIngredientDto(row.Name, amount, row.BaseUnit),
            () => new RecipeIngredientDto(row.Name, Quantity: null, Unit: null));
}

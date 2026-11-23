namespace mahl.Server.Tests.Helpers;

// MA0048: File name must match type name – diese Records sind die Wire-Formate der Rezept-Tests
//         (Request, Schritt, 422-Body) und ändern sich nur gemeinsam mit dem Endpoint-Vertrag.
#pragma warning disable MA0048, CA1812 // CA1812: instantiated by JSON deserializer via reflection
// ADR-S027-1: ein Schritt trägt nur die Anweisung – die Nummer ist die Listenposition.
public sealed record StepPayload(string Instruction);

// ADR-S135-2: die Zutaten gehen als roher Text des Zutatenfelds hinaus, eine Zutat je Zeile.
public sealed record CreateRecipeRequest(string Title, string Ingredients, IReadOnlyList<StepPayload> Steps);

// ADR-S020-1: Quantity und Unit sind beide null (ohne Menge) oder beide gesetzt.
// public und hier, weil die Theory-Daten der Rezept-Tests den Typ in öffentlichen Signaturen tragen.
public sealed record RecipeIngredientResponse(string Name, decimal? Quantity, string? Unit);

// ADR-S090-1: 422-Body feld-keyed.
public sealed record ValidationErrorResponse(IReadOnlyDictionary<string, IReadOnlyList<string>> Errors);

// Wire-Format der Rezept-Liste (GET /api/recipes und GET /api/planned-recipes).
public sealed record RecipeSummaryResponse(Guid Id, string Title);
#pragma warning restore MA0048, CA1812

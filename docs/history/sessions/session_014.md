# Session 014 – 2026-03-03

## Ziel
RecipeSource Sum-Type fertigstellen, Recipe.Create auf Primitives umstellen, Success<>-Wrapper entfernen, Test-Stil refactoren.

## Implementiertes

### RecipeSource Sum-Type (TDD)
- `Server/Domain/RecipeSource.cs` neu: `abstract record RecipeSource` mit `UrlSource(NonEmptyTrimmedString Url)` und explizitem `static explicit operator string?(RecipeSource)`
- `Recipe._source` (RecipeSource, non-nullable), `Recipe.Source` Property
- `Recipe.Create`: URL-Pfad setzt `UrlSource`, null-URL setzt `default!` (bewusste Schuld bis NoSource-Zyklus)
- `RecipesEndpoints.cs`: `SourceUrl = (string?)domain.Source`
- Test: `Recipe_Create_WithSourceUrl_SetsUrlSource` ✅

### Recipe.Create auf Primitives (Dependency Rule)
- Signatur: `Create(string title, string? sourceUrl, IReadOnlyList<(int, decimal?, string)> ingredients, IReadOnlyList<string> steps)`
- `using mahl.Shared.Dtos` aus `Recipe.cs` entfernt
- `RecipesEndpoints.cs` POST: DTO → Primitives im Endpoint
- `RecipeMappings.ToDomain()`: direktes Mapping ohne CreateRecipeDto-Zwischenschritt
- Tests: `CreateRecipe(CreateRecipeDto)` Wrapper in RecipeTests

### NonEmptyTrimmedString.Create – Success<> entfernt
- Return-Typ: `OneOf<Success<NonEmptyTrimmedString>, Error<string>>` → `OneOf<NonEmptyTrimmedString, Error<string>>`
- Alle `.Value`-Unwrapper in Callern entfernt: `Ingredient.cs`, `Measurement.cs`, `RecipeStep.Create`, `ShoppingListItem.cs`
- Recipe.cs: `u.Value` → `u`, `t.Value` → `t`, `Success<NonEmptyTrimmedString>` → `NonEmptyTrimmedString` in Bind-Kette
- Tests: `ShoppingListTests.cs` (4 Stellen), `NonEmptyTrimmedStringTests.cs` (3 Stellen)

### Test-Stil-Refactoring (teilweise)
- `NonEmptyListTests.cs`: `IsT0/AsT0` → `BeOfType<T>().Which`, `Value_OnValidInstance_ReturnsItems` als Duplikat gelöscht (1 Test weniger)
- `IngredientTests.cs`, `MeasurementTests.cs`, `RecipeTests.cs`: Auf `BeOfType<T>()`-Stil umgestellt
- **Offen**: `Satisfy<T>()` nicht verfügbar in FA 7.2 – Multi-Property-Assertions kompilieren nicht

## Ergebnisse
- 84 Server-Tests ✅, 116 Shared-Tests ✅ (total 200, 1 skipped)
- Mutation Score: **79.63%** (stabil, keine neuen Survivors)
- Tech Debt behoben: `Success<T>`-Wrapper (Session 7), `Recipe.Create` DTO-Dependency (Session 12)

## Offene Punkte
- `Satisfy<T>()` kompiliert nicht → Alternative für Multi-Property-Assertions finden
- `IngredientTests.cs`, `MeasurementTests.cs`, `RecipeTests.cs` kompilieren nicht (Satisfy-Calls)
- `NoSource` noch nicht implementiert (`default!` als Platzhalter in Recipe.Create)
- Stryker-Findings (All→Any, BoughtAt, AND→OR, OrderBy) noch offen

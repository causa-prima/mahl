# Session 34 – 2026-03-23

## Ziel
Stryker-Survivors aus Session 33 beheben, Test-Qualität verbessern (Partial Assertions → Full State, Konsolidierungen), Guidelines ergänzen.

## Umgesetzt

### Stryker-Survivors behoben (3)
- `OneOfExtensions.cs:41` – `ValueOrThrowUnreachable`: Test für exakte Exception-Message ergänzt
- `Types/NonEmptyList.cs:12` – Message-String: `.WithMessage(...)` in bestehendem Test ergänzt
- `Server/Endpoints/RecipesEndpoints.cs:58` – Object-Initializer: `GetAllRecipeIngredientsFromDb()`-Helper + DB-Level-Assertions für `Id` und `IngredientId` in `Post_ValidRecipe_Returns201AndPersistsData`

### Full State Assertions
Systematisch alle Partial Assertions in allen Testdateien auf Full State umgestellt:
- `IngredientsEndpointsTests`: GetById, Create (DTO + DB), SoftDeleted-Conflict, Restore, UniqueName
- `RecipesEndpointsTests`: GetById (inkl. Steps/Ingredients aus DB), Post_ValidRecipe (alle DB-Reads zusammengezogen, cross-referenzierte IDs)
- `WeeklyPoolEndpointsTests`: Post (beforePost + BeCloseTo für AddedAt, Id aus Response), Delete (stateBeforeAction für nicht-tautologische IDs)
- `ShoppingListEndpointsTests`: Generate, Check, Uncheck (stateBeforeAction-Pattern), Get, EmptyList-Tests

### Benannte Parameter
Für Konstruktoren datenführender Typen (Records) in Tests konsequent benannte Argumente eingeführt (`new IngredientDto(Id: id, Name: "Butter", ...)`). Als Guideline in `TDD_PROCESS.md` dokumentiert. Flächendeckend in allen Testdateien umgesetzt: `IngredientsEndpointsTests`, `RecipesEndpointsTests`, `WeeklyPoolEndpointsTests`, `ShoppingListEndpointsTests`, `RecipeTests` (inkl. `ValidDto`-Hilfsmethode).

### Test-Konsolidierungen via [TestCase]
- `IngredientTests`: `Create_EmptyName` + `Create_WhitespaceName` → `Create_InvalidName_ReturnsError` mit 5 TestCases (inkl. `\t`, `\n`, ` \t\n `)
- `RecipeTests`:
  - `RecipeIngredient_Create_EmptyUnit` + `QuantityWithNullUnit` → `QuantityWithMissingUnit_ReturnsError` mit `[TestCase(""), TestCase(null)]`
  - `Recipe_Create_WithSourceUrl` + `WithoutSourceUrl` → `Source_ReflectsSourceUrl` mit `[TestCase("https://..."), TestCase(null)]`
  - `Recipe_Create_IngredientWithEmptyUnit` (1 + 2 Zutaten) → `[TestCase(1), TestCase(2)]`
  - `Recipe_Create_StepWithEmptyInstruction` (1 + 2 Schritte) → `[TestCase(1), TestCase(2)]`

### Guidelines aktualisiert (`TDD_PROCESS.md`)
- Neue Regel: Benannte Parameter für Konstruktoren datenführender Typen in Tests
- Neue Entscheidungshilfe im Abschnitt „Parametrisierte Tests": Wann eigener Test, wann `[TestCase]`?

## Ergebnisse
- 155 Tests ✅
- Stryker: **100%**

## Offene Punkte
- Endpoint-404-Tests (Recipes + WeeklyPool): `GetById_UnknownId` + `GetById_SoftDeletedRecipe` sind `[TestCase]`-Kandidaten – aber Setup-Unterschied (kein Seed vs. Seed mit deletedAt); Entscheidung bewusst vertagt (TDD_PROCESS.md: „Nicht parametrisieren wenn Setup-Logik unterschiedlich")
- Frontend-Neuimplementierung (4 Seiten) steht noch aus

# Session 031 – 2026-03-17

## Ziel
Stryker-Gesamtlauf (veraltet seit Session 20) + Stryker-Findings beheben + Domain-ID-Migration fortführen

## Durchgeführt

### 1. Stryker 4.13.0 → 4.14.0 Upgrade
- **Problem:** `dotnet stryker` schlug mit `CompilationException: Internal error due to compile error` fehl – Stryker 4.13.0 inkompatibel mit .NET 10
- **Fix:** `dotnet tool update -g dotnet-stryker` → 4.14.0 ✅

### 2. Stryker Gesamtlauf: 90.7% (15 Survivors)
Survivors kategorisiert:
- **A (8):** WithTags-Strings + "/" Route-Äquivalenz → `// Stryker disable once String,Statement` bzw. `String`
- **B (7):** Fehlende Tests (WeeklyPool error bodies, POST response, ShoppingList RemoveRange, Ingredient DB-Inkonsistenz)

### 3. Stryker-Findings behoben → 100%

**Code-Änderungen (Stryker disable):**
- `IngredientsEndpoints`, `ShoppingListEndpoints`, `WeeklyPoolEndpoints`: `MapGroup(...).WithTags(...)` aufgesplittet + `// Stryker disable once String,Statement`
- `RecipesEndpoints`: `// Stryker disable once String` → `String,Statement` (Leerzeichen-Syntax war gebrochen)
- `IngredientsEndpoints`, `ShoppingListEndpoints`, `WeeklyPoolEndpoints`: MapGet/MapPost "/" → `// Stryker disable once String`

**Neue Tests (+2):**
- `IngredientsEndpointsTests.GetAll_WithDbInconsistency_Returns500` – testet Null-Coalescing-Pfad (firstError)
- `ShoppingListEndpointsTests.Generate_WithExistingItems_ReplacesAllItems` – testet `RemoveRange` (Statement mutation)
  - Neuer Helper `SeedShoppingListItems()` in `EndpointsTestsBase`
  - Nutzt `BeCloseTo(beforeGenerate, TimeSpan.FromSeconds(1))` für `GeneratedAt`-Assertion

**Test-Erweiterungen:**
- `WeeklyPoolEndpointsTests`: 3 Tests um Body-Assertion erweitert (`ReadFromJsonAsync<string>()`)
- `WeeklyPoolEndpointsTests.Post_ValidRecipeId_Returns201AndPersists`: Location-Header + Response-Body-Assertion

**Erkenntnis:** `Results.UnprocessableEntity(string)` serialisiert als JSON → `ReadAsStringAsync()` liefert `"\"text\""`. Korrekt: `ReadFromJsonAsync<string>()`.

### 4. Domain-ID-Migration: Ingredient + RecipeIngredient (TDD)

**`Ingredient.Create(Guid id, string name, string defaultUnit)`:**
- `Guid Id`-Property hinzugefügt (kein Guard ohne Test – Gold-Plating vermieden)
- Alle Caller aktualisiert:
  - `IngredientsEndpoints.ToDomain()`: `Ingredient.Create(db.Id, ...)`
  - `IngredientsEndpoints` POST: `Ingredient.Create(Guid.CreateVersion7(), ...)` + `entity.Id = ingredient.Id`
  - `RecipeIngredient.Create()` intern: `Ingredient.Create(ingredientId, ...)`

**`RecipeIngredient._ingredientId` Workaround entfernt:**
- `private readonly Guid _ingredientId` gelöscht
- Privater Ctor: `(Guid ingredientId, Ingredient, Quantity)` → `(Ingredient, Quantity)`
- `IngredientId`-Property vollständig entfernt (redundant – Caller nutzen `Ingredient.Id`)
- `RecipesEndpoints.ToDto`: `i.IngredientId` → `i.Ingredient.Id`

**Offen (nächste Session):**
- `Recipe.Guid Id` – RED-Zyklus unterbrochen (Kontext voll)
- `RecipeIngredient.Id` + `RecipeStep.Id` → danach `ToDto(Recipe)` ohne RecipeDbType möglich

## Ergebnisse
- Stryker: **100%** (alle Endpoints)
- Tests: **98 ✅** (vorher 96)
- `Ingredient` Domain-Typ trägt `Guid Id`
- `RecipeIngredient._ingredientId` Workaround beseitigt

## Offene Punkte
- `Recipe.Guid Id` + `RecipeIngredient.Id` + `RecipeStep.Id` → `ToDto(Recipe)` ohne RecipeDbType
- Frontend-Neuimplementierung (nach Domain-Migration)

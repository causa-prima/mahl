# Session 27 – 2026-03-15

## Phase
SKELETON – Domain-Refactoring + Tooling

## Implementiertes

### stryker-summary.py --detail
- Argument-Parsing auf `argparse` umgestellt (positional `report` + `--detail` Flag)
- `--detail` zeigt alle nicht-getöteten Mutanten (Survived/Ignored/Timeout/NoCoverage) mit Status, StatusReason, Zeile, Spalte, mutatorName, Replacement
- Dokumentation in `docs/DEV_WORKFLOW.md` + Hook-Fehlermeldung aktualisiert

### Domain-Refactoring: RecipeIngredient + SourceImagePath + StepNumber
**RecipeIngredient trägt jetzt volles `Ingredient`-Domain-Objekt:**
- `RecipeIngredient`: neues `_ingredient: Ingredient`-Feld, `_ingredientId: int` bleibt (bis UUID-Migration)
- `RecipeIngredient.Create()`: neue Signatur `(int ingredientId, string ingredientName, string defaultUnit, decimal? quantity, string? unit)`
- `Recipe.Create()`: Tupel-Parameter erweitert auf `(int IngredientId, string IngredientName, string DefaultUnit, decimal? Quantity, string? Unit)`

**SourceImagePath aus Domain + DTO entfernt (YAGNI):**
- Feature nicht implementiert im SKELETON-Endpoint → DB-Feld bleibt nullable, Domain und DTO wissen nichts davon
- `RecipeDto`, `RecipeSummaryDto`: `SourceImagePath` entfernt

**StepNumber aus `StepDto` entfernt:**
- Redundant in ordered list – Index impliziert die Nummer
- In DB + POST-Handler bleibt `StepNumber = idx + 1` (Ordering, Readability)

**POST-Handler umstrukturiert:**
- DB-Lookup der Zutaten vor `Recipe.Create()` (nötig, damit Ingredient-Name übergeben werden kann)
- `ingredientLookup[i.IngredientId].Name/.DefaultUnit` wird an `Recipe.Create()` übergeben

**`ToDto()` verbessert:**
- Ingredient-Daten (Name, Quantity, Unit) kommen jetzt aus Domain statt aus DB
- `dbIngrById`-Dictionary für ID-Lookup nach IngredientId
- `db` bleibt als 2. Parameter für PKs (Recipe.Id, RecipeIngredient.Id, Step.Id) – bis UUID-Migration

### Tests + Stryker
- `GetAllStepsFromDb()` als separater Helfer in `EndpointsTestsBase` eingeführt
- `Post_ValidRecipe_Returns201AndPersistsData`: Full State Assertion auf Steps ausgebaut:
  - `stepsInDb.Should().BeEquivalentTo([{StepNumber=1,...},{StepNumber=2,...}], opts.Excluding(Id))`
  - `created.Steps.Should().BeEquivalentTo([...stepsInDb[0].Id,...], opts.WithStrictOrdering())`
- Zirkuläre ID-Referenzen entfernt (`created.Steps[0].Id` → `stepsInDb[0].Id`)
- Neuer Test: `RecipeIngredient_Create_QuantityWithNullUnit_ReturnsError`
- **95 Tests ✅** (war 94)
- **RecipesEndpoints: 100% Mutation Score, 0 Survivors**
- **Recipe.cs: 4 pre-existierende Unreachable-Survivors** (Zeilen 115/117/122/124, vorher 107/109/114/116)

## Architektur-Entscheidungen (diskutiert)

| Thema | Entscheidung |
|-------|-------------|
| **UUID vs. int-PKs** | UUID v7 gewünscht – Migration nach .NET 10-Upgrade (Guid.CreateVersion7() nativ in .NET 9+) |
| **SourceImagePath** | Aus Domain/DTO entfernt bis Image-Upload-Feature implementiert wird |
| **Ingredient in RecipeIngredient** | Volles Domain-Objekt – DDD-konform (RecipeIngredient ist konzeptuell Ingredient + Quantity), ermöglicht perspektivisch ToDto() ohne DB-Objekt (sobald Ingredient-ID im Domain-Typ enthalten ist) |
| **StepNumber im DTO** | Entfernt – redundant in ordered list |
| **IngredientId in RecipeIngredient** | Bleibt bis UUID (Ingredient domain hat noch keine ID) |
| **Mutable Lists in DTOs** | Technische Schuld, separat behandeln |

## Offene Punkte (nächste Session)
- Schritt 4–6 des implementing-feature-Workflows noch ausstehend: Autor-Review, Review-Agenten, Commit
- .NET 10 Upgrade planen
- UUID v7 Migration nach Upgrade
- Stryker-Findings: `"Unreachable."` in Recipe.cs (L115/117/122/124)

# Session 006 – 2026-02-25

## Ziel

Sofort-Fixes aus Review, Phasen-Korrektur, Docs-Anpassungen, TDD-Fortsetzung RecipesEndpoints (GET + DELETE).

---

## Implementiertes

### 1. Docs-Anpassungen

- `docs/REVIEW_CHECKLIST.md`: Persistenz-Check-Punkt mit `GetAllXxx()` + `BeEquivalentTo` zusammengeführt.
- `docs/ARCHITECTURE.md`: REFACTOR-Phase um zwei Guideline-Compliance-Checkpunkte erweitert (ROP, TypeScript Branded Types).
- `docs/AGENT_MEMORY.md`: Phase korrigiert – SKELETON 🔄 (Neuimplementierung läuft), nicht MVP.
- `docs/slow-commands.md`: WSL/Windows Build-Workaround dokumentiert.

### 2. Sofort-Fixes aus Review

- `GetAllIngredients()` → `GetAllIngredientsFromDb()` (klarer: enthält auch soft-deleted)
- `HaveCount(1)` → `BeEquivalentTo([new { Name = "Aktiv" }])` in `GetAll_ExcludesSoftDeletedIngredients`
- `SoftDeletedConflict` file record entfernt → `SoftDeletedConflictDto` aus Shared genutzt

### 3. Builder-Verbesserung

- `ARecipe()` ohne Argumente erzeugt valides Rezept: 1 Zutat (Tomate, 200g) + 1 Schritt
- `ARecipeIngredient(ingredient, quantity, unit)` als neuer Builder
- `SeedRecipes()` + `GetAllRecipesFromDb()` in `EndpointsTestsBase`
- `GetAllRecipesFromDb()` lädt KEINE Navigations-Properties (verhindert zyklische Referenz-Fehler)

### 4. RecipesEndpoints – GET

Tests (alle grün):
- `GetAll_EmptyDb_Returns200WithEmptyList`
- `GetAll_ReturnsSortedByTitle`
- `GetAll_ExcludesSoftDeletedRecipes`
- `GetById_UnknownId_Returns404`
- `GetById_ExistingId_Returns200WithCorrectData`
- `GetById_SoftDeletedRecipe_Returns404`
- `GetById_Returns200WithStepsOrderedByStepNumber`

Implementierung: `GET /api/recipes` (WHERE DeletedAt IS NULL, ORDER BY Title), `GET /api/recipes/{id}` (mit Ingredients+Steps Include, DeletedAt-Filter, NotFound).

### 5. RecipesEndpoints – DELETE (gestartet)

Test: `Delete_ExistingId_Returns204AndSoftDeletes` ✅

Minimale Implementierung: `FindAsync` → `DeletedAt = UtcNow` → `SaveChangesAsync` → `NoContent`.

---

## Probleme / Hindernisse

- **MSB3492**: Regelmäßig – Workaround: separat bauen + warten
- **DLL-Sperre**: `mahl.Server.dll` gesperrt wenn Test-Runner noch aktiv
- **Zyklische Referenz**: `GetAllRecipesFromDb()` mit Include → FluentAssertions-Fehler → Includes entfernt
- **Gold-Plating (2×)**: `DeletedAt`-Filter und `NotFound`-Guard je einen Zyklus zu früh → Gold-Plating-Pflicht-Check greift nicht mechanisch

---

## Offene Punkte (für nächste Session)

| # | Aufgabe |
|---|---------|
| 1 | `Delete_NonExistingId_Returns404` |
| 2 | `Delete_AlreadySoftDeleted_Returns404` |
| 3 | `POST /api/recipes` via TDD (komplexester Endpoint) |
| 4 | `WeeklyPoolEndpoints` via TDD |
| 5 | `ShoppingListEndpoints` via TDD |
| 6 | ARCHITECTURE.md: Regel für `GetAllXxxFromDb()` ohne Include |

---

## Ergebnis

- 31 Tests, alle grün (23 Ingredients + 8 Recipes GET+DELETE)
- `GET /api/recipes`, `GET /api/recipes/{id}`, `DELETE /api/recipes/{id}` (teilweise) implementiert

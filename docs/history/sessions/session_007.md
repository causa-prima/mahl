# Session 007 – 2026-02-25

## Ziel

TDD-Fortsetzung RecipesEndpoints (DELETE + POST), WeeklyPoolEndpoints komplett, Doku-Verbesserungen, Design-Fragen klären.

---

## Implementiertes

### 1. Doku-Verbesserungen

- `docs/ARCHITECTURE.md`: REFACTOR-Phase um Box erweitert – Tests sind gleichwertig mit Produktionscode; Test-Lesbarkeit (Builder für Request-DTOs) als expliziter Checklisten-Punkt.
- `docs/SKELETON_SPEC.md`: Status von `✅ Abgeschlossen` auf `🔄 Neuimplementierung läuft` korrigiert; expliziter Hinweis auf Frontend-Neuimplementierungspflicht.
- `docs/AGENT_MEMORY.md`: Frontend-Status von `⏸ noch nicht überprüft` auf `❌ muss komplett nach Guidelines neu erstellt werden` korrigiert.

### 2. RecipesEndpoints – DELETE (abgeschlossen)

Tests (alle grün):
- `Delete_NonExistingId_Returns404`
- `Delete_AlreadySoftDeleted_Returns404`

Implementierung: `FindAsync` → `if (recipe is null || recipe.DeletedAt != null) return NotFound()`.

### 3. RecipesEndpoints – POST

Tests (alle grün):
- `Post_EmptyTitle_Returns422`
- `Post_EmptyIngredients_Returns422`
- `Post_EmptySteps_Returns422`
- `Post_UnknownIngredientId_Returns422`
- `Post_ValidRecipe_Returns201AndPersistsData`

Implementierung: ROP-Kette via `NonEmptyTrimmedString.Create(dto.Title).MapError(...).Bind(...).Bind(...).BindAsync(...).MatchAsync(...)`. Zutaten werden aus DB geladen und per Lookup zugeordnet, Steps mit fortlaufender StepNumber.

REFACTOR: `ACreateRecipeDto(ingredientId, ...)` Builder in `EndpointsTestsBase` extrahiert; `Post_EmptyTitle_Returns422` vereinfacht (unnötiges DB-Seeding entfernt).

### 4. WeeklyPoolEndpoints

Tests (alle grün):
- `GetAll_EmptyPool_Returns200WithEmptyList`
- `GetAll_ReturnsExistingEntries`
- `Post_ValidRecipeId_Returns201AndPersists`
- `Post_NonExistingRecipeId_Returns422`
- `Post_SoftDeletedRecipeId_Returns422`
- `Delete_ExistingRecipeId_Returns204AndRemovesAllEntries`

Implementierung:
- `GET /api/weekly-pool`: `db.WeeklyPoolEntries.Select(e => new WeeklyPoolEntryDto(..., e.Recipe.Title, ...))` via EF-Projektion (kein Include nötig)
- `POST /api/weekly-pool`: `AnyAsync(r => r.Id == dto.RecipeId && r.DeletedAt == null)` → 422 oder `Add(entry)` → 201
- `DELETE /api/weekly-pool/recipes/{recipeId}`: Hard-Delete aller Entries für dieses Rezept

Gold-Plating erkannt: `e.Recipe.Title` im GET war Gold-Plating für `GetAll_EmptyPool`-Test → rückgängig gemacht, dann durch `GetAll_ReturnsExistingEntries` erzwungen.

### 5. Neue Helfer in EndpointsTestsBase

- `ACreateRecipeDto(ingredientId, ...)` – Builder für POST-Request-DTOs
- `SeedPool(entries)` + `GetAllPoolEntriesFromDb()`

---

## Probleme / Hindernisse

- **`Success<T>`-Wrapper**: `NonEmptyTrimmedString.Create` gibt `OneOf<Success<NonEmptyTrimmedString>, Error<string>>` zurück → im `.Bind`-Typ muss `Success<NonEmptyTrimmedString>` explizit angegeben werden. Laut, aber funktional.
- **Duplikat-Testmethode**: Abgebrochenes Tool-Edit hatte `Post_EmptySteps_Returns422` doppelt geschrieben → manuell bereinigt.
- **Designfrage WeeklyPool DELETE**: Session endete mit offenem Design-Entscheid.
- **`ExcludingMissingMembers`-Frage**: Session endete vor Klärung/Umsetzung.

---

## Offene Punkte (für nächste Session)

| # | Aufgabe |
|---|---------|
| 1 | **Design-Entscheid WeeklyPool DELETE**: Entry-ID (einzeln) vs. Recipe-ID + Duplikatverbot vs. Status quo (alle löschen) – User-Entscheid ausstehend |
| 2 | **`ExcludingMissingMembers`-Review**: Prüfen welche Usages korrekt sind, welche durch vollständige Assertions ersetzt werden sollten; ggf. Guideline in ARCHITECTURE.md ergänzen |
| 3 | `ShoppingListEndpoints` via TDD |
| 4 | `ARCHITECTURE.md` Regel ergänzen: `GetAllXxxFromDb()` lädt keine Navigations-Properties (noch ausstehend aus Session 6) |

---

## Ergebnis

- **44 Tests, alle grün** (23 Ingredients + 15 Recipes + 6 WeeklyPool)
- `GET/POST/DELETE /api/recipes` vollständig implementiert
- `GET/POST/DELETE /api/weekly-pool` vollständig implementiert (vorbehaltlich Design-Entscheid DELETE)

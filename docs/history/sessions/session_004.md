# Session 004 – 2026-02-24

## Ziel

Bestehenden Server-Code (Endpoints + Tests) löschen und mit striktem TDD + aktuellen Guidelines
neu implementieren. Außerdem: Quantity nullable machen in RecipeIngredient und ShoppingListItem.

---

## Implementiertes

### Gelöscht
- Alle alten Endpoint-Implementierungen (`Recipes`, `WeeklyPool`, `ShoppingList`)
- Alle alten Integrationstests (`Recipes`, `WeeklyPool`, `ShoppingList`, `ShoppingListItem`, `Suggestions`)
- `Helpers/MappingExtensions.cs`

### Geändert (Shared)
- `Shared/Dtos/RecipeDto.cs`: `decimal Quantity` → `decimal? Quantity` in `RecipeIngredientDto` und `CreateRecipeIngredientDto`
- `Shared/Dtos/ShoppingListDto.cs`: `decimal Quantity` → `decimal? Quantity` in `ShoppingListItemDto`
- `Server/Data/DatabaseTypes/RecipeIngredientDbType.cs`: `decimal Quantity` → `decimal? Quantity`
- `Shared/Dtos/IngredientDto.cs`: `SoftDeletedConflictDto` hinzugefügt

### Neu implementiert via TDD (19 Tests, alle grün)

**`Server/Endpoints/IngredientsEndpoints.cs`**
- `GET /api/ingredients` – sortiert, nur aktive
- `GET /api/ingredients/{id}` – 404 für unbekannte/soft-gelöschte
- `POST /api/ingredients` – ROP-Validierung, Duplicate-Check (aktiv + soft-deleted), 409 mit `SoftDeletedConflict`-DTO
- `DELETE /api/ingredients/{id}` – Soft-Delete, 404 für nicht-existierende

**`mahl.Server.Tests/EndpointsTestsBase.cs`**
- Neu erstellt mit `SeedIngredients`, `GetAllIngredients`, `AnIngredient` (Builder)

**`mahl.Server.Tests/IngredientsEndpointsTests.cs`**
- 19 Tests (inkl. parametrisierte Validierungstests mit 4 Varianten)

### Guidelines aktualisiert
- `docs/ARCHITECTURE.md`:
  - TDD Phase 2: PFLICHT-CHECK Minimalität vor dem Speichern
  - TDD Phase 3: Minimalitäts-Punkt in Refactor-Checkliste
  - TDD Phase 1: Business-Entscheidungs-Checkpoint
  - Neu: Full State Assertion (BeEquivalentTo als Standard)
  - Neu: Test-Data-Builder Pattern
  - Neu: Parametrisierte Tests (wann ja, wann nein)
- `.claude/commands/feature.md`: "GENAU EINEN Test" explizit

---

## Entscheidungen

- `POST /api/ingredients` bei Namenskonflikt mit soft-deleted Eintrag: **409 + SoftDeletedConflictDto**
  (nicht transparentes Reaktivieren, nicht Neu-Anlegen neben soft-deleted)
  → Begründung: 409 + Client-Orchestrierung hält jeden Endpoint klar und einzeln testbar.
  → `docs/history/decisions.md` ergänzen (noch offen)

---

## Offene Punkte

- `IngredientsEndpoints`: `Delete_AlreadySoftDeleted_Returns404` – noch nicht implementiert
- Restore-Endpoint für Ingredients fehlt noch (wird durch 409-Strategie benötigt)
- `RecipesEndpoints`, `WeeklyPoolEndpoints`, `ShoppingListEndpoints` – alle noch zu implementieren
- EF Core Migration für `RecipeIngredient.Quantity` nullable (für Production-DB)
- Mutation Testing noch nicht gelaufen (erst nach allen Endpoints)

---

## Ergebnisse

| Metrik | Wert |
|--------|------|
| Tests gesamt | 19 (IngredientsEndpoints) + bestehende Shared-Tests |
| Fehlschläge | 0 |
| Mutation Testing | noch nicht gelaufen |

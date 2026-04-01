# Session 032 – 2026-03-18

## Phase
SKELETON – Qualität / Refactoring

## Ziel
Domain-ID-Migration abschließen (`Recipe.Id`, `RecipeIngredient.Id`, `RecipeStep.Id`), Guideline-Lücke für `default(T)`-Schutz schließen, Tech-Schuld abbauen.

## Implementiertes

### Domain-ID-Migration (vollständig)
- `Recipe.Id` + `Recipe.Create(Guid id, ...)` + Guard (`_id == default ? throw : _id`) per TDD ✅
- `RecipeIngredient.Id` + Guard + `Create(Guid id, Guid ingredientId, ...)` ✅
- `RecipeStep.Id` + Guard + `Create(Guid id, string instruction)` ✅
- `ToDto(Recipe)` ohne `RecipeDbType` – Signatur vereinfacht, `domain.Id/i.Id/s.Id` direkt genutzt ✅
- POST-Handler: `Id = domain.Id`, `Id = i.Id`, `Id = s.Id` in DB-Types gesetzt ✅

### Guideline + AGENT_MEMORY
- `CODING_GUIDELINE_CSHARP.md` Abschnitt 3: `default(T)`-Schutz-Regel explizit dokumentiert (Guard-Pattern + Pflicht-Tests) ✅
- Kanonisches Beispiel Abschnitt 7: `Guid id`-Parameter + Guard aktualisiert ✅
- "Gold-Plating" → "TDD-Verletzung" in AGENT_MEMORY + Session-31-Lessons-Learned-Eintrag korrigiert ✅

### DTOs
- `List<T>` → `IReadOnlyList<T>` in `RecipeDto`, `CreateRecipeDto`, `ShoppingListResponseDto` ✅

### Recipe.Create – Doppelte Traversierung behoben
- `Sequence<T>` in `OneOfExtensions.cs` mit `ImmutableList<T> + Aggregate` (Fail-Fast, funktional, kein Side Effect) ✅
- `Recipe.Create` nutzt `Sequence<T>` – validate-pass + construct-pass zu einem Pass zusammengeführt ✅
- 4 Tests für `Sequence<T>` in `OneOfExtensionsTests.cs` ✅
- `Sequence<T>` ist bewusste Übergangslösung (Fail-Fast-Semantik) bis MVP, wo Validation-Semantik mit strukturierten Mehrfach-Fehlern implementiert werden soll ✅

## Ergebnisse
- 103 Tests `mahl.Server.Tests` ✅
- 121 Tests `mahl.Shared.Test` ✅ (4 neue `Sequence<T>`-Tests)
- Stryker `Domain/Recipe.cs`: 100% ✅
- Stryker `Domain/Ingredient.cs`: 100% ✅
- Stryker `mahl.Shared.csproj`: 1 Survivor ungeklärt (Session-Ende) – kein JSON-Report generiert, Summary-Script konnte nicht genutzt werden

## Offene Punkte
- Stryker Shared-Projekt: kein JSON-Report → Summary-Script findet ihn nicht → Survivor aus dieser Session unbekannt. In nächster Session klären warum kein JSON generiert wird.
- Tech-Schuld Backend: 4 verbleibende Punkte in AGENT_MEMORY
- Frontend-Neuimplementierung noch ausstehend

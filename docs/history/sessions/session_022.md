# Session 22 – 2026-03-09: Stryker-Findings + Layer-Isolation (IngredientsEndpoints)

## Kontext
TDD-Session: Stryker-Findings für `IngredientsEndpoints` behoben. Layer-Isolation-Prinzip in Ingredients-Read-Pfad umgesetzt. Kein anderer Endpoint-Code geändert.

---

## Implementiertes

### 1. Layer-Isolation: `ToDomain()` → `OneOf<Ingredient, Error<string>>`
`IngredientDbType.ToDomain()` wirft keine Exception mehr, sondern gibt `OneOf<Ingredient, Error<string>>` zurück. Alle lesenden Endpoints (`GET /`, `GET /{id}`, `POST /{id}/restore`) nutzen jetzt `Results.Problem(detail, statusCode: 500)` statt unbehandeltem `throw` – strukturiertes `application/problem+json`, testbar per ContentType- und Body-Assertion.

Mapping-Helfer in `file static class IngredientMappings` (am Ende von `IngredientsEndpoints.cs`):
```csharp
public static OneOf<Ingredient, Error<string>> ToDomain(this IngredientDbType db) =>
    Ingredient.Create(db.Name, db.DefaultUnit)
        .MapError(e => new Error<string>($"DB inconsistency in Ingredient #{db.Id}: {e.Value}"));
```

### 2. Stryker-Finding IngredientsEndpoints L48: AND→OR behoben
**Problem:** Mutation `&&` → `||` im Soft-Delete-Check (aktive Zutat) überlebte, weil kein Test eine aktive Zutat mit anderem Namen beim POST geprüft hat.

**Fix:** Test `Create_UniqueName_WhenOtherActiveIngredientsExist_Returns201` – POST mit neuem Namen wenn eine andere aktive Zutat existiert → 201 (zuvor hätte AND→OR-Mutation fälschlicherweise 409 zurückgegeben).

### 3. Test: GetById_CorruptIngredient_Returns500WithProblemDetails
Neuer Test dokumentiert das Layer-Isolation-Verhalten: DB-Inkonsistenz (leerer Name) → 500 mit `application/problem+json` + präziser Fehlermeldung.

---

## Probleme

### `dotnet test --no-build` mit veralteten Binaries
Nach Codeänderungen vergessener Build → falsche Testergebnisse (200 statt 500). Ursache: MSBuild-Lock beim kombinierten Build+Test verhinderte Rebuild. Diagnose: Codeänderungen waren vorhanden, Test-Output stimmte nicht mit Erwartung überein.

### `Write` statt `Edit`
Breites Hook-Delta → False-Positive Primitive-Obsession-Warnungen für unveränderte Zeilen.

---

## Ergebnisse
- 91 Server-Tests (waren 89, +2 neue für Ingredients)
- `IngredientsEndpoints` L48 Stryker-Finding: ✅ behoben
- Layer-Isolation in Ingredients vollständig implementiert (`ToDomain()` → OneOf, `Results.Problem()`)
- Kein Stryker-Gesamtlauf durchgeführt (Session durch Kontext-Limit unterbrochen)

## Offene Punkte
- Stryker-Findings RecipesEndpoints L52, L37, L86/99 unverändert offen
- Domain/Recipe.cs L107/109/114/116 unverändert offen
- WeeklyPoolEndpoints (7 Findings) unverändert offen
- Route-String-Mutations (alle Endpoints) offen
- ShoppingListEndpoints L34 offen
- DEV_WORKFLOW.md: `$CLAUDE_PROJECT_DIR`-Hinweis (Session 21) noch ausstehend (User-Approval)
- docs-Änderungsvorschläge aus Session 22 (CODING_GUIDELINE_CSHARP, ARCHITECTURE, TDD_PROCESS) ausstehend

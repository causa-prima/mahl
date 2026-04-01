# Session 026 – 2026-03-12

## Phase: SKELETON (Qualität – Stryker RecipesEndpoints)

## Implementiertes

### Layer-Isolation RecipesEndpoints (TDD)
- `ToDomain()` von `Recipe` (wirft) → `OneOf<Recipe, Error<string>>` (ROP)
- GET /{id}: `_ => Results.Ok(recipe.ToDto())` → `domain => Results.Ok(domain.ToDto(recipe))`
- Neuer Test: `GetById_CorruptRecipe_Returns500WithProblemDetails` (leerer Titel direkt in DB)

### Architektur-Fix: ToDto von DbType auf Domain verschoben
- Alt: `ToDto(this RecipeDbType r)` – Verletzung der Coding-Guideline (Read-Pfad geht immer durch Domain)
- Neu: `ToDto(this Recipe domain, RecipeDbType db)` – Domain ist autoritativ für Step-Reihenfolge
- POST-Endpoint: `OneOf<RecipeDbType, IResult>` → `OneOf<(RecipeDbType, Recipe), IResult>` (wie IngredientsEndpoints)
- **Folge**: OrderBy-Stryker-Survivor (ToDomain) jetzt von `GetById_Returns200WithStepsOrderedByStepNumber` gekillt

### Neue Tests (gesamt 23 RecipesEndpoints-Tests)
- `GetById_CorruptRecipe_Returns500WithProblemDetails`
- `Post_UnknownIngredientId_Returns422` – Body-Assertion ergänzt
- `Post_ValidRecipe_Returns201WithCorrectLocationHeader`

### Stryker-Findings RecipesEndpoints: 0 Survivors (100%)
| Mutation | Status | Behandlung |
|---|---|---|
| `WithTags("Recipes")` → `""` | Ignored | `// Stryker disable once String` (kein Routing-Einfluss) |
| `MapGet("/")` → `MapGet("")` | Ignored | `// Stryker disable once String` (ASP.NET Core äquivalent) |
| `MapPost("/")` → `MapPost("")` | Ignored | `// Stryker disable once String` (ASP.NET Core äquivalent) |
| Fehlermeldung → `""` | Killed | Neuer Body-Test |
| Location-URL → `$""` | Killed | Neuer Location-Header-Test |
| OrderBy in ToDomain | Killed | Architektur-Fix (ToDto nutzt Domain-Reihenfolge) |

### NTFS-Read-Problem behoben bestätigt
- Memory-Eintrag entfernt; `Read`-Tool funktioniert wieder normal für alle Projektdateien

## Erkenntnisse / Probleme

### Stryker `disable once` Statement-Scope
- `disable once` gilt für das **nächste syntaktische Statement**, nicht die nächste Zeile
- `MapPost(comment_hier "/", lambda)` → deaktiviert alle Mutations im gesamten MapPost-Aufruf
- Fix: Kommentar nur direkt vor dem Ziel-String-Literal (kein zweiter Kommentar auf äußerer Statement-Ebene)

### Ad-hoc Python-Skripte (offen)
- Mehrfach manuelle Python-Skripte zur JSON-Report-Analyse genutzt → erfordern User-Bestätigung
- **Task für nächste Session**: `stryker-summary.py` um `--detail`-Flag erweitern (zeigt alle nicht-killed Mutanten mit Status, Reason, Zeile/Spalte)

### ToDto mit RecipeDbType als Parameter (offen)
- `ToDto(this Recipe domain, RecipeDbType db)` benötigt noch das DB-Objekt für: Step-IDs, RecipeIngredient-IDs, Ingredient-Namen
- Step-Nummern könnten aus Listenposition (idx+1) abgeleitet werden
- Vollständige Lösung: Domain müsste IDs/Namen tragen oder DTO-Konstruktion anders strukturieren
- **Technische Schuld** – nächste Session

## Dokumentations-Updates (Ende Session)
- `docs/REVIEW_CHECKLIST.md`: Eintrag ergänzt – „ToDto auf DbType statt Domain-Typ" als Review-Punkt
- `docs/DEV_WORKFLOW.md` (Stryker-Sektion): `disable once`-Scope-Verhalten dokumentiert mit Erklärung und korrektem Beispiel für Lambda-Aufrufe

## Ergebnisse
- RecipesEndpoints: 23 Tests ✅, 100% Mutation Score, 0 Survivors
- Alle Server-Tests: 23 neue + bestehende (5 Failures aus paralleler Session unverändert)

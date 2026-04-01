# Session 039 – 2026-03-25 – CA1054/CA1056: Uri statt string für SourceUrl

## Ziel

Tech-Debt-Abbau: CA1054/CA1056-Analyzer-Regeln für `SourceUrl` beheben. DTOs und Domain-Layer von `string?` auf `System.Uri?` umstellen, globale editorconfig-Suppressionen entfernen.

## Implementiert

### CA1054/CA1056-Fix

- **DTOs**: `CreateRecipeDto`, `RecipeDto`, `RecipeSummaryDto` — `string? SourceUrl` → `Uri? SourceUrl`
- **Domain**: `Recipe.Create(Uri? sourceUrl)` — nimmt `Uri?` direkt als BCL-Primitive
- **`RecipeSource`**: `FromUrl(NonEmptyTrimmedString)` → `FromUrl(Uri)` — `Uri` garantiert Nicht-Leerheit durch Konstruktor; `Match<T>` gibt jetzt `Uri` statt `NonEmptyTrimmedString` zurück
- **`Recipe.Create`**: `IsAbsoluteUri`-Guard — relative URI → `Error<string>("Quell-URL muss eine absolute URI sein.")` → 422
- **`RecipeSource.explicit operator string?`**: nutzt `url.OriginalString` (kein Trailing-Slash durch .NET-Normalisierung)
- **`RecipesEndpoints.cs`**: `ToDto()` vereinfacht (`domain.Source.Match(url => (Uri?)url, () => null)`); `ToUri()` durch `ToSummaryDtoOrError()` + `Sequence()` ersetzt
- **`.editorconfig`**: globale CA1054/CA1056-Suppressionen entfernt; gezielt `CA1056` für DbTypes, `CA1054` für Test-Builder beibehalten

### Bug-Fix (aus Review)

`GET /api/recipes` gab bei korrupter `SourceUrl` in der DB still `null` zurück — inconsistent zu `GET /api/recipes/{id}` (500). Behoben: `ToSummaryDtoOrError()` gibt `OneOf<RecipeSummaryDto, Error<string>>` zurück; `Sequence()` propagiert Fehler; Endpoint gibt `Results.Problem(..., 500)` zurück.

### Tests

- `Recipe_Create_RelativeSourceUrl_ReturnsError` (Domain-Unit-Test für IsAbsoluteUri-Guard)
- `GetAll_RecipeWithInvalidStoredUrl_Returns500WithProblemDetails`
- `GetAll_RecipeSummaryIncludesSourceUrl` (SourceUrl-Mapping in GetAll)
- `GetAll_ExcludesSoftDeletedRecipes` (entkoppelt vom SourceUrl-Test)
- `Post_ValidRecipe_Returns201WithCorrectResponseBody` + `Post_ValidRecipe_PersistsCorrectDataToDb` (Split von `Returns201AndPersistsData`)
- Diverse ⚠️-Fixes: `ReadFromJsonAsync<string>()`, `.BeEmpty()`, Einrückung in `Recipe.Create`

## Ergebnis

163 Tests ✅ | Stryker 100%

## Dokumentation

- `docs/history/decisions.md`: 3 neue Einträge (Uri als BCL-Primitive, OriginalString Round-Trip, GetAll 500 statt null)
- `docs/CODING_GUIDELINE_CSHARP.md`: `Uri` als akzeptierter BCL-Typ in Abschnitt "Primitive Obsession" ergänzt
- `docs/REVIEW_CHECKLIST.md`: Prüfpunkt für inkonsistente Fehlerbehandlung bei mehreren Konvertierungspfaden desselben DB-Werts

## Offene Punkte / Tech Debt

- STJ-Deserialisierungsverhalten bei ungültigem URI-String noch nicht verifiziert (400 oder 500?)
- `OriginalString`-Serialisierung durch STJ noch nicht durch Test abgesichert
- Beide Punkte zusammen in Session 040 angehen

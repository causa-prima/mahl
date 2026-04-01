# Session 38 – 2026-03-25

## Ziel
`FromT0`/`FromT1` durch idiomatischen impliziten Cast ersetzen; Best Practice dokumentieren; Post-Hook planen.

## Durchgeführte Arbeiten

### Analyse & Diskussion
- Pro/Contra `FromT0` vs. impliziter Cast vs. expliziter Cast diskutiert und dokumentiert.
- Alle 10 `FromT*`-Stellen im Codebase via Grep identifiziert.

### CODING_GUIDELINE_CSHARP.md
- Neuen Abschnitt "OneOf-Instanz erzeugen" im ROP-Kapitel ergänzt.
- Ausnahme-Tabelle (4 Fälle) dokumentiert — besonders: Interface-Typen erfordern zwingend `FromT1`.
- Pattern-Beispiel auf impliziten Cast + `FromT1` für IResult aktualisiert.

### Code-Fixes (10 Stellen)
| Datei | Änderung |
|-------|----------|
| `RecipesEndpoints.cs:74` | `FromT0(domain)` → `(OneOf<Recipe, IResult>) domain` (Inferenz-Hint) |
| `IngredientsEndpoints.cs` | `BindAsync` auf explizite Typargumente; `FromT0` auf Tuple entfernt; `FromT1` für IResult bleibt (Interface-Zwang) |
| `Domain/Recipe.cs:34` | `FromT0(new RecipeIngredient(...))` → direkter Konstruktoraufruf |
| `Domain/Recipe.cs:113,116` | `FromT0(t)` → `(OneOf<NonEmptyTrimmedString, Error<string>>) t` |
| `OneOfExtensions.cs:31` | `FromT1` bleibt — nackter Typparameter `TError` |
| `OneOfExtensions.cs:46` | `FromT0(ImmutableList<T>.Empty)` → expliziter Cast |
| `OneOfExtensionsTests.cs` | Alle 5 `FromT*`-Stellen auf impliziten Cast / deklarierte Typen umgestellt |

### Stryker (100% → 98.4% → 100%)
- Stryker-Lauf nach den Fixes: 2 neue Survivors in `NonEmptyList.cs` — `GetHashCode` und `!=`-Operator nicht abgedeckt.
- Ursache: `NonEmptyList` wurde ohne TDD implementiert (Tests wurden nachträglich für `IEquatable` geschrieben, aber `GetHashCode` und `!=` fehlten).
- Fix: 2 neue Tests (`GetHashCode_DifferentLists_ReturnDifferentHashes`, `InequalityOperator_DifferentLists_ReturnsTrue`). 157 Tests ✅, Stryker 100%.

### AGENT_MEMORY.md
- Tech-Debt-Eintrag für `FromT*` hinzugefügt (während Analyse) und nach Behebung entfernt.
- Architektur-Entscheidung "OneOf-Instanz erzeugen – Rangfolge" ergänzt.
- Test-Pattern `ValueOrThrowUnreachable()` in Unit-Tests ergänzt.

## Geplant (nicht umgesetzt)
- Post-Hook zum Abfangen von `FromT*`-Verwendungen (folgt in nächster Session).

## Ergebnisse
- **Build**: 0 Warnings, 0 Errors ✅
- **Tests**: 157 ✅
- **Stryker**: 100% ✅

## Probleme / Learnings
- C# wendet user-defined implicit operators für Interface-Typen nicht an (weder implizit noch explicit cast) → `FromT1` zwingend für `IResult` & Co.
- Bei `BindAsync`-Lambdas mit mehreren `return`-Statements: explizite Typargumente am Methodenaufruf lösen das Inferenz-Problem eleganter als Casts in jedem Statement.
- TDD-Hook beim Stryker-Fix verletzt (3 Tests auf einmal geschrieben) — künftig auch bei Survivor-Fixes einen Test pro Zyklus.

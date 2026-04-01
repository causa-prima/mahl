# Session 012 – 2026-03-02: DDD-Architektur (Domain-Typen) + Stryker-Auswertung

## Ziel

Vollständige DDD-Systemgrenz-Architektur umsetzen: Domain-Typen für alle Entities mit Create-Vorgängen, Endpoints umstellen, Stryker-Lauf + Auswertung.

---

## Implementiert

### Neue Dateien
- `Shared/Types/NonEmptyList.cs` – generischer Value-Object-Wrapper (`readonly struct`, Create → OneOf)
- `mahl.Shared.Test/Types/NonEmptyListTests.cs` – 4 Tests
- `Server/Domain/Measurement.cs` – `(decimal? Quantity, NonEmptyTrimmedString Unit)`, `readonly struct`, `Create` only
- `Server/Domain/Ingredient.cs` – `(NonEmptyTrimmedString Name, DefaultUnit)`, `readonly struct`, `Create` only
- `Server/Domain/Recipe.cs` – `RecipeIngredient`, `RecipeStep`, `Recipe` als `readonly struct`, `Create` only
- `mahl.Server.Tests/Domain/MeasurementTests.cs` – 6 Tests
- `mahl.Server.Tests/Domain/IngredientTests.cs` – 7 Tests
- `mahl.Server.Tests/Domain/RecipeTests.cs` – 14 Tests

### Geänderte Dateien
- `Server/Endpoints/IngredientsEndpoints.cs` – Domain-Typen genutzt, neue `IngredientMappings`-Extensions
- `Server/Endpoints/RecipesEndpoints.cs` – Domain-Typen genutzt, neue `RecipeMappings`-Extensions, `Recipe.Create(dto)` im POST-Pfad
- `docs/CODING_GUIDELINE_CSHARP.md` – Abschnitt 7 (Domain-Typen, Systemgrenz-Architektur) hinzugefügt

### Architekturentscheid (User): Kein `From()`
`From()`-Methoden wurden nach Diskussion **aus allen Domain-Typen entfernt**. DB-Rekonstruktion erfolgt im Mapping-Layer (file-level Extensions in Endpoint-Dateien) via:
```csharp
Domain.Create(primitives).Match(ok => ok, e => throw new InvalidOperationException($"DB inconsistency: {e.Value}"))
```
Begründung: Das "throw bei Inkonsistenz"-Verhalten ist eine Mapping-Entscheidung, keine Domain-Entscheidung.

---

## Probleme & Fixes

### CS8958: private parameterloser Konstruktor auf struct (C# 10 VS-MSBuild)
Stryker fällt auf MSBuild von Visual Studio zurück. VS-Roslyn interpretiert `langversion:latest` als C# 10, wo private parameterlose Konstruktoren auf Structs verboten sind.
- **Fix**: Expliziten privaten Ctor entfernt; `Value`-Property-Guard (`_items == null`) übernimmt Schutz.
- **Offener Punkt**: Damit müssen alle Domain-Typen als `readonly struct` (nicht `record struct`) deklariert werden, was `IEquatable<T>` von Hand erzwingt → nächste Session: Hook-Erweiterung + Umstieg auf `readonly record struct`.

### Fehlende `using mahl.Shared;` nach Cache-Invalidierung
Der erste `dotnet test`-Lauf nutzte gecachte Artefakte; nach `NonEmptyList.cs`-Änderung wurde alles neu gebaut und die fehlenden `using`-Direktiven in allen Domain-Dateien und `RecipesEndpoints.cs` sichtbar.
- **Fix**: `using mahl.Shared;` in `Measurement.cs`, `Ingredient.cs`, `Recipe.cs`, `RecipesEndpoints.cs` ergänzt.

### Test-Assertions: `domain.Name.Value.Should().Be("Butter")` schlägt fehl
`NonEmptyTrimmedString.Value` gibt `TrimmedString` zurück (nicht `string`). FluentAssertions' `Be("Butter")` vergleicht Typen und schlägt deshalb fehl.
- **Fix**: `((string)domain.Name).Should().Be("Butter")` – nutzt den impliziten `string`-Operator.

---

## Stryker-Ergebnis: 71.86%

| Datei | Score | Killed | Survived |
|-------|-------|--------|---------|
| Domain/Ingredient.cs | 33% | 2 | 4 |
| Domain/Measurement.cs | 25% | 1 | 3 |
| Domain/Recipe.cs | 61% | 20 | 13 |
| Endpoints/IngredientsEndpoints.cs | 86% | 38 | 6 |
| Endpoints/RecipesEndpoints.cs | 74% | 26 | 9 |
| Endpoints/ShoppingListEndpoints.cs | 75% | 15 | 5 |
| Endpoints/WeeklyPoolEndpoints.cs | 72% | 18 | 7 |

Details der priorisierten überlebenden Mutanten: `docs/AGENT_MEMORY.md` (Technische Schuld / Stryker-Findings).

---

## Offene Architektur-Diskussionen (Entscheide getroffen, noch nicht implementiert)

### 1. RecipeSource Sum-Type
`SourceUrl string?` und `SourceImagePath string?` auf `Recipe` sind mutual exclusive → Sum-Type:
```csharp
public abstract record RecipeSource;
public sealed record UrlSource(string Url) : RecipeSource;
public sealed record ImageSource(string Path) : RecipeSource;
public sealed record NoSource : RecipeSource;
// In Recipe: RecipeSource Source { get; }
```
Entscheid: `NoSource` statt `null` (User-Präferenz: null nur als letztes Mittel in Sum-Types).

### 2. Recipe.Create nimmt DTO statt Primitives
Verletzt die Dependency Rule. Korrekte Signatur:
```csharp
Recipe.Create(string title, string? sourceUrl, RecipeSource source,
    IReadOnlyList<(int ingredientId, decimal? quantity, string unit)> ingredients,
    IReadOnlyList<string> instructions)
```
DTO → Primitives-Mapping passiert im Endpoint.

### 3. readonly struct → readonly record struct
Domain-Typen sollen `readonly record struct` werden (Auto-Equality, kein IEquatable-Boilerplate). Blocker: Hook blockiert `public` parameterlosen Ctor auf record structs.
Entscheid: Hook erweitern, damit das Muster `public XyzType() => throw new InvalidOperationException(...)` auf record structs erlaubt ist.

---

## Tests

**Vorher:** 169 Tests (113 Shared + 56 Server)
**Nachher:** 195 Tests (117 Shared + 78 Server) – 26 neue Domain-Unit-Tests

Alle grün ✅

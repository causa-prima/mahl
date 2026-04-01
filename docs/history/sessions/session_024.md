# Session 24 – 2026-03-11: Stryker L37+L52 + Schema NULL-Unit + Quantity.Create-Refactoring

## Kontext
Fortsetzung der Stryker-Finding-Behebung für RecipesEndpoints. Zwei Findings behoben; ausgedehnte Designdiskussion über NULL vs. leerer String für Unit-Feld und Signatur-Semantik von `string?`.

---

## Implementiertes

### 1. Stryker L37 – POST mit soft-deleted Zutat → 422
Test: `Post_SoftDeletedIngredientId_Returns422`
Fix: `&& i.DeletedAt == null` im Ingredient-Exists-Check war vorhanden aber ungetestet → delete → RED → GREEN.

### 2. Schema-Änderung: Unit → NULL statt leerer String
Entscheidung: `RecipeIngredientDbType.Unit` und `ShoppingListItemDbType.Unit` von `string NOT NULL` auf `string? NULL` umgestellt. Semantik: `NULL` = "keine Einheit" (bei `Quantity.Unspecified()`), nicht `""`.

Betroffene Dateien:
- `Server/Data/DatabaseTypes/RecipeIngredientDbType.cs` – `string?`
- `Server/Data/DatabaseTypes/ShoppingListItemDBType.cs` – `string?`
- `Shared/Dtos/RecipeDto.cs` – `RecipeIngredientDto.Unit: string?`, `CreateRecipeIngredientDto.Unit: string?`
- `Shared/Dtos/ShoppingListDto.cs` – `ShoppingListItemDto.Unit: string?`

Keine Migration nötig (keine Produktionsinstanz).

### 3. Refactoring: `Quantity.Create(decimal, NonEmptyTrimmedString)`
`Quantity.Create()` nimmt jetzt `NonEmptyTrimmedString` statt `string` – vollständig domain-typed. Validierung des Unit-Strings liegt beim Aufrufer.

### 4. Refactoring: `RecipeIngredient.Create()` – ROP-Kette mit Null-Normalisierung
```csharp
: NonEmptyTrimmedString.Create(unit ?? string.Empty)
    .MapError(_ => new Error<string>("Einheit darf nicht leer sein."))
    .Bind(u => Quantity.Create(quantity.Value, u))
    ...
```
`?? string.Empty` als interne Normalisierung akzeptiert: null und `""` bedeuten semantisch dasselbe ("keine Einheit angegeben").

### 5. Stryker L52 – POST null-Quantity → Unit=NULL in DB
Test: `Post_NullQuantity_PersistsNullUnit`
Fix: `() => string.Empty` → `() => (string?)null` im Endpoint-Mapping.

### 6. QuantityTests angepasst
`Create_WithEmptyUnit_ReturnsError` entfernt (Validierung liegt jetzt bei NonEmptyTrimmedString, nicht Quantity). Übrige Tests auf `NonEmptyTrimmedString`-Hilfsmethode `Unit(string s)` umgestellt.

---

## Probleme

### `--no-build` false GREEN
Nach Codeänderungen lieferte `dotnet test --no-build` falsche Testergebnisse (alte Binary). Immer `dotnet test` (mit Build) nach Produktionscode-Änderungen.

### Kaskadierende Schema-Änderung
Unit → `string?` zog sich durch 7 Dateien. Länger als erwartet.

---

## Ergebnisse
- 92 Server-Tests ✅ (91 + L37 + L52 – 1 entfernter QuantityTest = 92)
- 116 Shared-Tests ✅
- RecipesEndpoints L37 ✅, L52 ✅ – keine Survivors mehr
- Quantity.Create() vollständig domain-typed

## Offene Punkte
- Layer-Isolation RecipesEndpoints: `ToDomain()` wirft noch (→ nächste Prio, Zyklus 3)
- L86: Statement-Mutation (hängt von Layer-Isolation ab)
- L99: OrderBy in ToDomain() → vermutlich äquivalenter Mutant
- Domain/Recipe.cs L107/109/114/116: Unreachable
- WeeklyPoolEndpoints (7 Findings)
- Route-String-Mutations
- ShoppingListEndpoints L34
- Frontend

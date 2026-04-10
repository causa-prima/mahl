# Guideline für das Generieren von TypeScript/React-Code

<!--
wann-lesen: Bevor du TypeScript/React-Produktionscode oder Tests schreibst (nach CODING_GUIDELINE_GENERAL.md)
kritische-regeln:
  - Keine direkten string/number/uuid als Domain-Konzepte – Branded Types verwenden
  - boolean-Flags (isLoading, hasError) verboten – Discriminated Union mit status-Feld
  - Fehlerbehandlung via neverthrow Result<T, E> – kein try/catch für Validierungsfehler
  - API-Calls in src/services/, Domänen-Logik in src/domain/ – nie in Komponenten
  - any verboten – unknown + Type Guard oder konkreter Typ
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Verbotene Muster | Verbotene Muster auf einen Blick (Tabelle) | Als schnelle Referenz ohne vollständiges Lesen |
| 1. Immutability | readonly, as const, kein direktes Mutieren, Spreading statt push/assign | Beim Erstellen von State oder Datenstrukturen |
| 2. Branded Types | Branded Type Pattern, Factory Function mit Result-Rückgabe | Beim Modellieren von IDs oder Domain-Konzepten |
| 3. Discriminated Unions | RequestState-Pattern, exhaustive switch, keine Boolean-Flags | Beim Modellieren von Lade-/Fehler-/Erfolgszuständen |
| 4. Railway-Oriented Programming | neverthrow ok/err/Result/ResultAsync, .andThen()/.match() | Beim Schreiben von Validierungs- oder API-Verkettungen |
| 5. Pure Functions & Separation | src/domain/ für Logik, src/services/ für API, Komponenten nur UI | Beim Anlegen neuer Dateien oder Funktionen |
| 6. Test-Code | Was gilt, was ist gelockert (_unsafeUnwrap, as, try/catch in Tests OK) | Beim Schreiben von Frontend-Tests |

> **Voraussetzung:** Lies zuerst `docs/CODING_GUIDELINE_GENERAL.md` (KISS, Naming, Komplexität, übergreifende Paradigmen). Diese Datei beschreibt nur die TypeScript/React-spezifische Umsetzung.

Du bist ein Senior TypeScript-Entwickler, der sich auf Functional Domain-Driven Design (fDDD), Railway-Oriented Programming (ROP) und Type-Driven Development spezialisiert hat.

## Verbotene Muster (Kurzreferenz)

| Verboten | Stattdessen |
|---|---|
| `let` für Objekte/Arrays die mutiert werden | `const` + neues Objekt |
| Rohe `string`/`number` für IDs in Domain-Code | Branded Types |
| `boolean`-Flags für Zustände (isLoading, hasError) | Discriminated Union `status` |
| `try/catch` für Validierungsfehler | `neverthrow` Result |
| API-Calls in Komponenten | `src/services/` |
| Domänen-Logik in Komponenten | `src/domain/` |
| `any` | `unknown` + Type Guard oder konkreter Typ |

---

## 1. Immutability

- Objekte und Arrays sind **niemals** direkt mutierbar. Verwende `readonly` und `as const`.
- State-Updates immer als neue Objekte/Arrays zurückgeben (React erzwingt das ohnehin).
- Für komplexe State-Mutations: **Immer** `immer` (produce) oder strukturiertes Spreading nutzen.

```typescript
// Schlecht
item.name = 'Tomaten';
list.push(item);

// Gut
const updatedItem = { ...item, name: 'Tomaten' };
const updatedList = [...list, newItem];
```

---

## 2. Branded Types – kein "Primitive Obsession"

Keine rohen `string`/`number`/`uuid` direkt in Domänen-Modellen. Kapsle sie als Branded Types:

```typescript
// Value Object via Branded Type
type RecipeId = string & { readonly __brand: 'RecipeId' };
type IngredientName = string & { readonly __brand: 'IngredientName' };

// Factory Function (analog zu static Create() in C#)
// Fehlertyp ist immer ValidationError – kein nackter string (selbstdokumentierend,
// erweiterbar um code/field ohne Breaking Change)
function makeRecipeId(value: string): Result<RecipeId, ValidationError> {
  if (!value || value.trim().length === 0)
    return err({ message: 'RecipeId darf nicht leer sein' });
  return ok(value as RecipeId);
}
```

**Fehlertyp:** Factory Functions geben immer `Result<T, ValidationError>` zurück – **kein `Result<T, string>`**.
`ValidationError` ist in `src/types/validationError.ts` definiert:

```typescript
/** Validierungsfehler aus Domain-Factory-Functions und Service-Layer. */
export type ValidationError = { readonly message: string }
```

**Faustregel:** Wenn ein String-Parameter mehrere verschiedene Konzepte darstellen könnte (z.B. `id` für Rezept, Zutat und Wochenpool), braucht jedes Konzept einen eigenen Branded Type.

**Dependency Rule:** Factory Functions nehmen Domain-Typen oder Primitives (`string`, `number`) entgegen – niemals API-Response-Typen (DTOs) oder direkte Zugriffe auf `fetch`-Ergebnisse. Das Mapping API-Response → Primitives findet im Service-Layer (`src/services/`) statt.

---

## 3. "Make Illegal States Unrepresentable" – Discriminated Unions

TypeScript ist hier stärker als C#. Nutze Discriminated Unions um unmögliche Zustände im Typsystem auszuschließen:

```typescript
// Schlecht: Boolean-Flag erlaubt inkonsistente Zustände
type Request = {
  isLoading: boolean;
  data: Recipe | null;   // Was bedeutet isLoading=false, data=null?
  error: string | null;
};

// Gut: Jeder Zustand ist eindeutig
type RequestState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string };

// Exhaustive Pattern Matching
function render(state: RequestState<Recipe>) {
  switch (state.status) {
    case 'idle':    return <Placeholder />;
    case 'loading': return <Spinner />;
    case 'success': return <RecipeCard recipe={state.data} />;
    case 'error':   return <ErrorMessage message={state.message} />;
    // TypeScript prüft, ob alle Fälle abgedeckt sind
  }
}
```

---

## 4. Railway-Oriented Programming – `neverthrow`

Verwende die Bibliothek **`neverthrow`** für Fehlerbehandlung ohne Exceptions. Kein `try/catch` für Domänen- oder Validierungsfehler.

```typescript
import { ok, err, Result, ResultAsync } from 'neverthrow';
import type { ValidationError } from '../types/validationError';

// Factory Function gibt Result zurück – Fehlertyp ist ValidationError, nie string
function makeIngredientName(input: string): Result<IngredientName, ValidationError> {
  const trimmed = input?.trim();
  if (!trimmed)
    return err({ message: 'Name darf nicht leer sein' });
  if (trimmed.length > 200)
    return err({ message: 'Name darf maximal 200 Zeichen haben' });
  return ok(trimmed as IngredientName);
}

// Verkettung (analog zu .Bind() / .Match() in C#)
const result = makeIngredientName(rawInput)
  .andThen(name => saveIngredient(name))  // ResultAsync
  .match(
    (saved) => toast.success(`${saved.name} gespeichert`),
    (error) => toast.error(error.message),
  );
```

**Exceptions** sind nur für echte technische Ausnahmezustände (Netzwerk-Ausfall, unerwarteter Server-Fehler mit 5xx) erlaubt – nicht für Validierungsfehler.

---

## 5. Pure Functions & Separation of Concerns

- **API-Calls** gehören in dedizierte Service-Dateien (`src/services/`), nicht in Komponenten.
- **Domänen-Logik** (Validierung, Transformationen) gehört in `src/domain/`, nicht in Komponenten.
- **Komponenten** sind rein presentational: empfangen Props, rendern UI, delegieren Events.

```typescript
// src/domain/recipe.ts – Pure Domain Functions
export function makeRecipeTitle(
  title: string
): Result<RecipeTitle, ValidationError> { ... }

export function calculateTotalCalories(
  ingredients: ReadonlyArray<RecipeIngredient>
): Calories { ... }

// src/services/recipesApi.ts – API-Calls
export async function fetchRecipes(): ResultAsync<Recipe[], ApiError> { ... }

// src/components/RecipeForm.tsx – nur UI
function RecipeForm({ onSubmit }: Props) {
  const result = validateRecipeTitle(titleInput);
  // ...
}
```

---

## 6. Test-Code – Pragmatische Regeln

Diese Richtlinie gilt für Test-Code mit den folgenden Abschwächungen:

**Anwenden:**
- Branded Types auch in Tests verwenden (sofern verfügbar) – keine nackten Strings für IDs
- Testdaten als `const` / `readonly` definieren – keine mutierten Test-Fixtures
- Discriminated Unions für erwartete Zustände (z.B. `expect(result.status).toBe('success')`)

**Explizit lockern:**
- Factory Functions dürfen in Tests mit `.unwrap()` oder `._unsafeUnwrap()` aufgerufen werden, wenn der Wert bekannt gültig ist
- `as` Type Assertions sind in Tests für bekannte Mock-Daten erlaubt
- `try/catch` ist in Tests erlaubt – Vitest/Jest-Assertions werfen Exceptions, das ist gewollt

```typescript
// Test-Beispiel – pragmatisch aber typsicher
const validName = makeIngredientName('Tomaten')._unsafeUnwrap();
// _unsafeUnwrap() ist in Tests OK, weil der Wert bekannt gültig ist
```


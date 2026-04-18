# Guideline für das Generieren von TypeScript/React-Code

<!--
wann-lesen: Bevor du TypeScript/React-Produktionscode oder Tests schreibst (nach CODING_GUIDELINE_GENERAL.md)
kritische-regeln:
  - Alle Domain-Konzepte als Branded Types ausdrücken (string/number/uuid nie direkt verwenden)
  - Zustände als Discriminated Union mit status-Feld modellieren, nie als boolean-Flags
  - Validierungsfehler ausschließlich via neverthrow Result<T, E> behandeln
  - API-Calls in src/services/, Domänen-Logik in src/domain/ ablegen
  - Ausschließlich unknown + Type Guard oder konkreten Typ verwenden (kein any)
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
> **UX/Interaction Design:** Bei jeder React-Komponente zusätzlich `docs/CODING_GUIDELINE_UX.md` lesen (Feedback, Fehlermeldungen, Terminologie, leere Zustände, destructive Actions).

Du bist ein Senior TypeScript-Entwickler, der sich auf Functional Domain-Driven Design (fDDD), Railway-Oriented Programming (ROP) und Type-Driven Development spezialisiert hat.

## Verbotene Muster (Kurzreferenz)

| Verboten | Stattdessen |
|---|---|
| `let` für Objekte/Arrays die mutiert werden | `const` + neues Objekt |
| Rohe `string`/`number` für IDs in Domain-Code | Branded Types |
| `boolean`-Flags für Zustände (isLoading, hasError) | Discriminated Union `status` |
| `try/catch` für Validierungsfehler | `neverthrow` Result |
| `throw` für Domain-Fehler im Service-Layer | `return err(...)` / `ResultAsync` |
| `useQuery`/`useMutation` direkt | `useResultQuery` / `useResultMutation` |
| Direkter `state.status`-Zugriff in Komponenten | `matchState()` / `matchKind()` |
| API-Calls in Komponenten | `src/services/` |
| Domänen-Logik in Komponenten | `src/domain/` |
| `any` | `unknown` + Type Guard oder konkreter Typ |

---

## 1. Immutability

- Objekte und Arrays immer als `readonly` / `as const` definieren.
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

Alle `string`/`number`/`uuid`-Werte in Domänen-Modellen als Branded Types kapseln:

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

## 4b. React Query – useResultMutation / useResultQuery

React Query ausschließlich über zwei generische Wrapper nutzen (einmalig definiert in `src/hooks/`):

### Typen

```typescript
// src/types/mutationState.ts
export type MutationState<T, E> =
  | { status: 'idle' }
  | { status: 'pending' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: E }
```

### Wrapper: Mutation (POST/PUT/DELETE)

```typescript
// src/hooks/useResultMutation.ts
export function useResultMutation<TData, TError, TVariables>(
    fn: (variables: TVariables) => ResultAsync<TData, TError>
): [(variables: TVariables) => void, MutationState<TData, TError>] {

    const mutation = useMutation<Result<TData, TError>, Error, TVariables>({
        mutationFn: (vars) => fn(vars),  // Result<T,E> ist der Rückgabewert – kein throw für Domain-Fehler
        throwOnError: true,              // nur echte Ausnahmen (Netzwerk/5xx) → QueryCache.onError → Toast
    });

    const state: MutationState<TData, TError> = (() => {
        switch (mutation.status) {
            case 'idle':    return { status: 'idle' };
            case 'pending': return { status: 'pending' };
            case 'error':   return { status: 'idle' }; // Toast zentral angezeigt
            case 'success': return mutation.data.match(
                (value) => ({ status: 'success', data:  value } as const),
                (error) => ({ status: 'error',   error: error } as const),
            );
            default: {
                const _exhaustive: never = mutation.status;
                throw new Error(`Unhandled mutation status: ${_exhaustive}`);
            }
        }
    })();

    return [mutation.mutate, state];
}
```

**Warum kein `throw` für Domain-Fehler:** Ein `Err(domainError)` ist ein erwarteter Wert, keine Ausnahme. React Query bekommt ihn als normales resolved-Ergebnis; der Wrapper liest `mutation.data.isErr()` und baut daraus den `error`-State. Nur Netzwerkfehler/5xx werfen tatsächlich und landen im globalen Handler.

### Wrapper: Query (GET)

```typescript
// src/hooks/useResultQuery.ts
export function useResultQuery<TData, TError>(
    key: readonly unknown[],
    fn: () => ResultAsync<TData, TError>
): MutationState<TData, TError> {  // gleicher State-Typ, kein mutate

    const query = useQuery<Result<TData, TError>, Error>({
        queryKey: key,
        queryFn: () => fn(),
        throwOnError: true,
    });

    switch (query.status) {
        case 'pending': return { status: 'pending' };
        case 'error':   return { status: 'idle' }; // Toast zentral angezeigt
        case 'success': return query.data.match(
            (value) => ({ status: 'success', data:  value } as const),
            (error) => ({ status: 'error',   error: error } as const),
        );
        default: {
            const _exhaustive: never = query.status;
            throw new Error(`Unhandled query status: ${_exhaustive}`);
        }
    }
}
```

### match()-Helpers

```typescript
// src/utils/match.ts

// Äußerer Zustand (idle / pending / success / error)
export function matchState<T, E, R>(
    state: MutationState<T, E>,
    cases: {
        idle:    ()           => R;
        pending: ()           => R;
        success: (data:  T)   => R;
        error:   (error: E)   => R;
    }
): R { /* switch auf state.status */ }

// Discriminated-Union-Fehler / Success-Sum-Types
export function matchKind<T extends { kind: string }, R>(
    value: T,
    cases: { [K in T['kind']]: (v: Extract<T, { kind: K }>) => R }
): R { return (cases as any)[value.kind](value); }
```

### Custom Hook: eine Zeile

```typescript
// src/hooks/ingredients/useSaveIngredient.ts
export const useSaveIngredient = () => useResultMutation(saveIngredient);
```

### Komponente: vollständiges Beispiel

```tsx
function CreateIngredientForm() {
    const [save, state] = useSaveIngredient();

    return matchState(state, {
        idle:    ()  => <button onClick={() => save({ name: '...' })}>Speichern</button>,
        pending: ()  => <Spinner />,
        success: (s) => <p>"{s.data.name}" gespeichert.</p>,
        error:   (s) => matchKind(s.error, {
            ActiveConflict:   (e) => <p>Bereits aktiv: {e.existing.name}</p>,
            ValidationErrors: (e) => <ul>{e.errors.map(m => <li>{m}</li>)}</ul>,
        }),
    });
}
```

**Pflicht:** Komponenten verwenden ausschließlich `matchState()`/`matchKind()` – kein direkter `state.status`-Zugriff (Review-Kriterium: direkter Zugriff = CRITICAL Finding).

### QueryCache-Setup (App-Root, einmalig)

```typescript
// src/main.tsx
const queryClient = new QueryClient({
    queryCache:    new QueryCache({    onError: (e) => toast.error('Ein Fehler ist aufgetreten') }),
    mutationCache: new MutationCache({ onError: (e) => toast.error('Ein Fehler ist aufgetreten') }),
});
```

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

## 6. Test-Architektur – Teststrategie und HTTP-Mocking

### Testbare Oberfläche: Komponenten, nicht Service-Funktionen

Die testbare Oberfläche im Frontend ist die **gerenderte Komponente** – analog zum Backend, das nur über HTTP-Endpoints getestet wird. Service-Funktionen (`fetchIngredients`, etc.) sind Implementierungsdetails und werden durch die Komponente abgedeckt, **nicht direkt getestet**.

```
✓  IngredientsPage rendert → useQuery → fetchIngredients → fetch('/api/ingredients') → MSW
✗  fetchIngredients direkt importieren und mit fetch-Mock testen
```

Konsequenz: Kein separater `*.test.ts` für Service-Dateien. Wenn Stryker NoCoverage für eine Service-Funktion meldet, ist das Signal, dass der Komponenten-Test noch keinen echten HTTP-Call auslöst – nicht, dass ein neuer Unit-Test fehlt.

### HTTP-Mocking: ausschließlich MSW

**Einzige erlaubte Mocking-Strategie für HTTP-Calls: MSW (`msw/node`).**

```typescript
// ✓ Korrekt – testet HTTP-Kontrakt, unabhängig von der Implementierung
server.use(http.get('/api/ingredients', () => HttpResponse.json([])))

// ✗ Verboten – koppelt Test an Implementierungsdetail
vi.mock('../services/ingredientsApi')
vi.stubGlobal('fetch', vi.fn().mockResolvedValue(...))
```

`vi.mock` auf Service-Modulen ist ein Antipattern: Es testet ob `fetchIngredients` aufgerufen wird, nicht ob `GET /api/ingredients` korrekt funktioniert. Beim Wechsel von `fetch` auf `axios` bricht der Test obwohl das Verhalten identisch ist.

**Setup:** `src/mocks/server.ts` + `src/test/setup.ts` (MSW-Server wird global für alle Tests gestartet, mit `onUnhandledRequest: 'error'`).

### vi.mock – wann erlaubt?

`vi.mock` ist für HTTP-kommunizierende Module verboten. Für reine Utility-Funktionen (kein HTTP, keine Side Effects) ist es unnötig – pure Functions können direkt aufgerufen werden.

---

## 7. Test-Code – Pragmatische Regeln

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


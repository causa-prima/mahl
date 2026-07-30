import { ResultAsync, errAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'
import { conditionalGetJson } from './conditionalGet'

// ADR-S090-1: 422-Body ist feld-keyed. Das Frontend konsumiert ausschließlich `errors`.
type FieldErrorBody = { readonly errors: Readonly<Record<string, readonly string[]>> }

// ADR-S004-1: 409-Body von POST /api/ingredients bei soft-deleted-Duplikat. Nur `id` wird
// konsumiert (der `code` ist der einzig mögliche POST-409-Grund, kein zusätzlicher Zweig nötig).
type SoftDeletedConflictBody = { readonly id: string }

// ADR-S111-1: 409-Body von POST /{id}/restore, wenn die Zeile bereits aktiv ist, aber mit
// abweichenden Werten – der gespeicherte Stand geht mit, damit der Client ihn benennen kann.
type AlreadyActiveConflictBody = { readonly ingredient: Ingredient }

export type Ingredient = {
  readonly id: string
  readonly name: string
  readonly defaultUnit: string
  // ADR-S108-1: per-Zeile xmin-ETag (hex, "{xmin:x8}") aus dem GET-Body – die If-Match-Quelle
  // fürs Löschen einer aus der Liste geladenen Zutat.
  readonly etag: string
}

export type NewIngredient = {
  readonly name: string
  readonly defaultUnit: string
}

// ADR-S111-1/-3: `createIngredient` liefert im Ok-Pfad zwei unterscheidbare Erfolgsfälle – ein
// echtes Anlegen/Reaktivieren ('Saved') oder eine Reaktivierung, die auf eine parallel bereits
// mit ABWEICHENDEN Werten wiederhergestellte Zeile trifft ('ReactivationConflict'). Beide sind
// Ok, weil der Vorgang fachlich erfolgreich ist (die Zutat existiert danach) – nur ein Err hätte
// verhindert, dass `useResultMutation`s onSuccess feuert (Dialog schließen, Liste neu laden).
export type CreateIngredientResult =
  | { readonly kind: 'Saved'; readonly ingredient: Ingredient }
  | {
      readonly kind: 'ReactivationConflict'
      readonly requestedName: string
      readonly savedIngredient: Ingredient
    }

// ADR-S111-1: der Restore-Endpoint unterscheidet über den HTTP-Status, ob reaktiviert wurde oder
// die Zeile bereits mit abweichenden Werten aktiv war. Der Client liest nur diese Entscheidung –
// ein eigener Wertevergleich im Client würde das serverseitige Trimmen (ADR-S051-1) duplizieren
// und bei Whitespace-Eingaben fälschlich einen Konflikt melden, obwohl nichts parallel geschah.
type RestoreOutcome =
  | { readonly kind: 'Restored'; readonly ingredient: Ingredient }
  | { readonly kind: 'AlreadyActiveConflict'; readonly ingredient: Ingredient }

export function fetchIngredients(): ResultAsync<readonly Ingredient[], ApiError> {
  // ADR-S058-1: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304) via Content-Hash-ETag.
  return conditionalGetJson<readonly Ingredient[]>('/api/ingredients')
}

export function createIngredient(ingredient: NewIngredient): ResultAsync<CreateIngredientResult, ApiError> {
  return ResultAsync.fromPromise(
    fetch('/api/ingredients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ingredient),
    }),
    (e): ApiError => ({ kind: 'Unexpected', message: String(e) }),
  ).andThen((response) => toCreateIngredientResult(response, ingredient))
}

// ADR-S108-1/S058-1: DELETE einer Zutat verlangt If-Match; der Wert ist der per-Zeile-xmin-ETag
// aus dem GET-Body. Nur Erfolgspfad (run-8) – die Response wird nicht ausgewertet.
export function deleteIngredient(id: string, etag: string): ResultAsync<Response, ApiError> {
  return ResultAsync.fromPromise(
    fetch(`/api/ingredients/${id}`, {
      method: 'DELETE',
      headers: { 'If-Match': etag },
    }),
    (e): ApiError => ({ kind: 'Unexpected', message: String(e) }),
  )
}

// ADR-S111-1 (überholt ADR-S108-2): Restore verlangt ab run-11 einen Pflicht-Body { name,
// defaultUnit } – auch der Undo-Aufruf (run-8/9, useDeleteIngredientWithUndo) schickt ihn jetzt
// mit, fachlich ein No-op, aber ein einziger Codepfad im Endpoint. Erfolgs-Status 200 (statt 204).
export function restoreIngredient(id: string, name: string, defaultUnit: string): ResultAsync<RestoreOutcome, ApiError> {
  return ResultAsync.fromPromise(
    fetch(`/api/ingredients/${id}/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, defaultUnit }),
    }),
    (e): ApiError => ({ kind: 'Unexpected', message: String(e) }),
  ).andThen(toRestoreOutcome)
}

// ADR-S090-1: 422 -> feld-keyed Validierungsfehler (Err). ADR-S004-1: 409 -> der Name existiert
// soft-deleted, der Client ruft transparent den Restore mit den eigenen Eingaben auf
// (ADR-S051-4). Sonst der angelegte/reaktivierte Datensatz ('Saved').
function toCreateIngredientResult(response: Response, requested: NewIngredient): ResultAsync<CreateIngredientResult, ApiError> {
  if (response.status === 422) {
    return ResultAsync.fromSafePromise(response.json() as Promise<FieldErrorBody>).andThen((body) =>
      errAsync<CreateIngredientResult, ApiError>({ kind: 'FieldErrors', fields: body.errors }),
    )
  }
  if (response.status === 409) {
    return ResultAsync.fromSafePromise(response.json() as Promise<SoftDeletedConflictBody>).andThen((body) =>
      reactivateSoftDeletedIngredient(body.id, requested),
    )
  }
  return ResultAsync.fromSafePromise(response.json() as Promise<Ingredient>).map(
    (created): CreateIngredientResult => ({ kind: 'Saved', ingredient: created }),
  )
}

function reactivateSoftDeletedIngredient(id: string, requested: NewIngredient): ResultAsync<CreateIngredientResult, ApiError> {
  return restoreIngredient(id, requested.name, requested.defaultUnit).map((outcome): CreateIngredientResult =>
    outcome.kind === 'Restored'
      ? { kind: 'Saved', ingredient: outcome.ingredient }
      : {
          kind: 'ReactivationConflict',
          requestedName: requested.name,
          savedIngredient: outcome.ingredient,
        },
  )
}

function toRestoreOutcome(response: Response): ResultAsync<RestoreOutcome, ApiError> {
  if (response.status === 409) {
    return ResultAsync.fromSafePromise(response.json() as Promise<AlreadyActiveConflictBody>).map(
      (body): RestoreOutcome => ({ kind: 'AlreadyActiveConflict', ingredient: body.ingredient }),
    )
  }
  return ResultAsync.fromSafePromise(response.json() as Promise<Ingredient>).map(
    (ingredient): RestoreOutcome => ({ kind: 'Restored', ingredient }),
  )
}

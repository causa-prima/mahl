import { ResultAsync, errAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'
import { conditionalGetJson } from './conditionalGet'

// ADR-S090-1: 422-Body ist feld-keyed. Das Frontend konsumiert ausschließlich `errors`.
type FieldErrorBody = { readonly errors: Readonly<Record<string, readonly string[]>> }

export type Ingredient = {
  readonly id: string
  readonly name: string
  readonly defaultUnit: string
}

export type NewIngredient = {
  readonly name: string
  readonly defaultUnit: string
}

export function fetchIngredients(): ResultAsync<readonly Ingredient[], ApiError> {
  // ADR-S058-1: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304) via Content-Hash-ETag.
  return conditionalGetJson<readonly Ingredient[]>('/api/ingredients')
}

export function createIngredient(ingredient: NewIngredient): ResultAsync<Ingredient, ApiError> {
  return ResultAsync.fromPromise(
    fetch('/api/ingredients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ingredient),
    }),
    (e): ApiError => ({ kind: 'Unexpected', message: String(e) }),
  ).andThen(toIngredientResult)
}

// ADR-S090-1: 422 -> feld-keyed Validierungsfehler (Err); sonst der angelegte Datensatz.
function toIngredientResult(response: Response): ResultAsync<Ingredient, ApiError> {
  if (response.status === 422) {
    return ResultAsync.fromSafePromise(response.json() as Promise<FieldErrorBody>).andThen((body) =>
      errAsync<Ingredient, ApiError>({ kind: 'FieldErrors', fields: body.errors }),
    )
  }
  return ResultAsync.fromSafePromise(response.json() as Promise<Ingredient>)
}

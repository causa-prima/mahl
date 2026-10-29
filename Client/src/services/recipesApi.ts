import { errAsync, okAsync, ResultAsync } from 'neverthrow'
import { toUnexpectedError } from '../types/apiError'
import type { ApiError } from '../types/apiError'
import type { NewRecipe, Recipe, RecipeSummary } from '../domain/recipe'
import { conditionalGetJson } from './conditionalGet'
import { toFieldErrors } from './fieldErrors'

export function fetchRecipes(): ResultAsync<readonly RecipeSummary[], ApiError> {
  // ADR-S084-3: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304).
  return conditionalGetJson<readonly RecipeSummary[]>('/api/recipes')
}

// ADR-S142-2: Jedes 404 ist der erwartete Fall "Rezept nicht gefunden" und reist als Erfolgswert.
export type RecipeLookup =
  | { readonly kind: 'Found'; readonly recipe: Recipe }
  | { readonly kind: 'NotFound' }

export function fetchRecipe(id: string): ResultAsync<RecipeLookup, ApiError> {
  return conditionalGetJson<Recipe>(`/api/recipes/${encodeURIComponent(id)}`)
    .map((recipe): RecipeLookup => ({ kind: 'Found', recipe }))
    .orElse((error) => (error.kind === 'NotFound' ? okAsync<RecipeLookup, ApiError>({ kind: 'NotFound' }) : errAsync(error)))
}

// ADR-S068-1: Die 201-Antwort trägt das volle Rezept, ein zweiter GET entfällt.
// ADR-S090-1: 422 -> feld-keyed Validierungsfehler (Err).
export function createRecipe(recipe: Readonly<NewRecipe>): ResultAsync<Recipe, ApiError> {
  return ResultAsync.fromPromise(
    fetch('/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recipe),
    }),
    toUnexpectedError,
  ).andThen((response) =>
    response.status === 422
      ? toFieldErrors<Recipe>(response)
      : ResultAsync.fromSafePromise(response.json() as Promise<Recipe>),
  )
}

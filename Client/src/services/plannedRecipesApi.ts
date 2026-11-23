import { errAsync, okAsync, ResultAsync } from 'neverthrow'
import { toUnexpectedError } from '../types/apiError'
import type { ApiError } from '../types/apiError'
import type { RecipeId, RecipeSummary } from '../domain/recipe'
import { conditionalGetJson } from './conditionalGet'

// ADR-S153-1: Die vorgemerkten Rezepte liegen unter /api/planned-recipes, je Eintrag { id, title } wie /api/recipes.
export function fetchPlannedRecipes(): ResultAsync<readonly RecipeSummary[], ApiError> {
  // ADR-S084-3: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304).
  return conditionalGetJson<readonly RecipeSummary[]>('/api/planned-recipes')
}

// ADR-S153-1: Vormerken ist ein idempotentes PUT auf die Rezept-ID, ohne Body und ohne If-Match (204).
// Jede Nicht-2xx-Antwort ist ein Fehler: der Zustand ändert sich dann nicht.
export const planRecipe = (id: RecipeId): ResultAsync<Response, ApiError> => sendToPlannedRecipe('PUT', id)

// ADR-S153-1, ADR-S000-5: Aufheben ist ein idempotentes DELETE auf dieselbe URL (204, auch wenn nicht vorgemerkt).
export const unplanRecipe = (id: RecipeId): ResultAsync<Response, ApiError> => sendToPlannedRecipe('DELETE', id)

function sendToPlannedRecipe(method: 'PUT' | 'DELETE', id: RecipeId): ResultAsync<Response, ApiError> {
  const url = `/api/planned-recipes/${encodeURIComponent(id)}`
  return ResultAsync.fromPromise(fetch(url, { method }), toUnexpectedError).andThen((response) =>
    response.ok
      ? okAsync<Response, ApiError>(response)
      : errAsync<Response, ApiError>({ kind: 'Unexpected', message: `${method} ${url} fehlgeschlagen: ${String(response.status)}` }),
  )
}

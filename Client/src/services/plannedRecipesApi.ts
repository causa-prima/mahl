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
export function planRecipe(id: RecipeId): ResultAsync<Response, ApiError> {
  return ResultAsync.fromPromise(
    fetch(`/api/planned-recipes/${encodeURIComponent(id)}`, { method: 'PUT' }),
    toUnexpectedError,
  ).andThen((response) =>
    response.ok
      ? okAsync<Response, ApiError>(response)
      : errAsync<Response, ApiError>({ kind: 'Unexpected', message: `Vormerken fehlgeschlagen: ${String(response.status)}` }),
  )
}

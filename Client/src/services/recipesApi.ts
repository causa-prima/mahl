import { ResultAsync } from 'neverthrow'
import { toUnexpectedError } from '../types/apiError'
import type { ApiError } from '../types/apiError'
import type { NewRecipe, Recipe, RecipeSummary } from '../domain/recipe'
import { conditionalGetJson } from './conditionalGet'

export function fetchRecipes(): ResultAsync<readonly RecipeSummary[], ApiError> {
  // ADR-S084-3: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304).
  return conditionalGetJson<readonly RecipeSummary[]>('/api/recipes')
}

// ADR-S068-1: Die 201-Antwort trägt das volle Rezept, ein zweiter GET entfällt. Nur Erfolgspfad.
export function createRecipe(recipe: Readonly<NewRecipe>): ResultAsync<Recipe, ApiError> {
  return ResultAsync.fromPromise(
    fetch('/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recipe),
    }),
    toUnexpectedError,
  ).andThen((response) => ResultAsync.fromSafePromise(response.json() as Promise<Recipe>))
}

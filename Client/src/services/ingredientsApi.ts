import { ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'
import { conditionalGetJson } from './conditionalGet'

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
    }).then((r) => r.json() as Promise<Ingredient>),
    (e) => ({ message: String(e) }),
  )
}

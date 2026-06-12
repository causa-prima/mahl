import { ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'

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
  return ResultAsync.fromPromise(
    fetch('/api/ingredients').then((r) => r.json() as Promise<readonly Ingredient[]>),
    (e) => ({ message: String(e) }),
  )
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

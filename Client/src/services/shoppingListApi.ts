import type { ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'
import type { RecipeIngredient } from '../domain/recipe'
import { conditionalGetJson } from './conditionalGet'
import { sendWithoutBody } from './sendWithoutBody'

// ADR-S154-3: je Eintrag { name, quantity, unit } wie eine Rezept-Zutat; quantity und unit sind beide null ohne Menge
// (ADR-S020-1). Die Reihenfolge liefert der Server (ADR-S142-1).
export type ShoppingListItem = RecipeIngredient

export function fetchShoppingList(): ResultAsync<readonly ShoppingListItem[], ApiError> {
  // ADR-S084-3: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304).
  return conditionalGetJson<readonly ShoppingListItem[]>('/api/shopping-list')
}

// ADR-S154-3: Übernehmen ist ein POST ohne Body (204); der Server liest die Vormerkungen selbst.
export const generateShoppingList = (): ResultAsync<Response, ApiError> => sendWithoutBody('POST', '/api/shopping-list/generate')

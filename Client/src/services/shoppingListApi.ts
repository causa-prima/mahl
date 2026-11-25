import type { ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'
import { conditionalGetJson } from './conditionalGet'

// Die Einträge sind noch nicht typisiert: dieser Stand der Seite unterscheidet nur leer von nicht leer.
export function fetchShoppingList(): ResultAsync<readonly unknown[], ApiError> {
  // ADR-S084-3: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304).
  return conditionalGetJson<readonly unknown[]>('/api/shopping-list')
}

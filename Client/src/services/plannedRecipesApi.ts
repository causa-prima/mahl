import type { ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'
import { conditionalGetJson } from './conditionalGet'

// ADR-S153-1: Die vorgemerkten Rezepte liegen unter /api/planned-recipes.
// Der Element-Typ ist offen, bis eine Darstellung der Einträge ihn bestimmt.
export function fetchPlannedRecipes(): ResultAsync<readonly unknown[], ApiError> {
  // ADR-S084-3: GET nutzt HTTP-Conditional-Requests (If-None-Match / 304).
  return conditionalGetJson<readonly unknown[]>('/api/planned-recipes')
}

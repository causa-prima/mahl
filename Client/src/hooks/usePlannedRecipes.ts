import { useQueryClient } from '@tanstack/react-query'
import { fetchPlannedRecipes, planRecipe } from '../services/plannedRecipesApi'
import { useResultMutation } from './useResultMutation'
import { useResultQuery } from './useResultQuery'

const plannedRecipesKey = ['planned-recipes'] as const

// Rezept-Liste, Detailansicht und Vorgemerkt-Seite teilen diese eine Query.
export const usePlannedRecipes = () => useResultQuery(plannedRecipesKey, fetchPlannedRecipes)

// Der Umschalter zeigt den neuen Zustand erst mit der Antwort des Servers: Nach dem Vormerken lädt die Query neu.
export function usePlanRecipe() {
  const queryClient = useQueryClient()
  // Stryker disable next-line ObjectLiteral: Invalidierungs-Filter, ohne ihn lädt nur mehr neu (ADR-S153-2)
  return useResultMutation(planRecipe, () => { void queryClient.invalidateQueries({ queryKey: plannedRecipesKey }) })
}

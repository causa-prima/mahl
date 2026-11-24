import { useQueryClient } from '@tanstack/react-query'
import { fetchPlannedRecipes, planRecipe, unplanRecipe } from '../services/plannedRecipesApi'
import { useResultMutation } from './useResultMutation'
import { useResultQuery } from './useResultQuery'

const plannedRecipesKey = ['planned-recipes'] as const

// Rezept-Liste, Detailansicht und Vorgemerkt-Seite teilen diese eine Query.
export const usePlannedRecipes = () => useResultQuery(plannedRecipesKey, fetchPlannedRecipes)

// Lädt die Vormerkungen neu, nachdem sie sich auf dem Server geändert haben.
export function useInvalidatePlannedRecipes() {
  const queryClient = useQueryClient()
  // Stryker disable next-line ObjectLiteral: Invalidierungs-Filter, ohne ihn lädt nur mehr neu (ADR-S153-2)
  return () => { void queryClient.invalidateQueries({ queryKey: plannedRecipesKey }) }
}

// Der Umschalter zeigt den neuen Zustand erst mit der Antwort des Servers: Nach dem Vormerken lädt die Query neu.
export function usePlanRecipe() {
  return useResultMutation(planRecipe, useInvalidatePlannedRecipes())
}

// Ebenso nach dem Aufheben: die Query lädt neu, erst dann zeigt der Umschalter "Vormerken".
export function useUnplanRecipe() {
  return useResultMutation(unplanRecipe, useInvalidatePlannedRecipes())
}

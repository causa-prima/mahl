import { expect } from '../fixtures'
import type { Page } from '@playwright/test'
import { planRecipeViaApi } from '../api/plannedRecipesApi'
import { seedRecipesWithSaltViaApi } from '../api/recipesApi'
import type { TouchTargetPageDefinition } from './touchTargetPage'

// Die Einträge der Vorgemerkt-Seite: eine Liste, benannt nach der Überschrift der Seite.
export function plannedEntries(page: Readonly<Page>) {
  return page.getByRole('list', { name: 'Vorgemerkt' }).getByRole('listitem')
}

// Der Titel eines Eintrags der Vorgemerkt-Seite – der Link zu seiner Detailansicht.
export function plannedRecipeLink(page: Readonly<Page>, title: string) {
  return page.getByRole('list', { name: 'Vorgemerkt' }).getByRole('link', { name: title, exact: true })
}

// Zustände der Vorgemerkt-Seite für die Touch-Target-Suite (planned-recipes.feature, Querschnitts-
// Deklaration „Bedienbarkeit per Finger"). Der DB-Reset der Fixture lässt keine Vormerkung übrig; der
// Zustand „Liste" merkt danach ein Rezept über die API vor und lädt die Seite neu.
export const plannedRecipesTouchTargets: TouchTargetPageDefinition = {
  name: 'Vorgemerkt',
  states: (page, request) => [
    {
      name: 'Leerzustand',
      reach: async () => {
        await page.goto('/planned')
        await expect(page.getByRole('link', { name: 'Zur Rezept-Liste' })).toBeVisible()
      },
    },
    {
      name: 'Liste',
      reach: async () => {
        const [pancakesId] = await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')
        await planRecipeViaApi(request, pancakesId)
        await page.reload()
        await expect(plannedRecipeLink(page, 'Pfannkuchen')).toBeVisible()
      },
    },
  ],
}

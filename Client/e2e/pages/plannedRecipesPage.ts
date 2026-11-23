import { expect } from '../fixtures'
import type { Page } from '@playwright/test'
import type { TouchTargetPageDefinition } from './touchTargetPage'

// Die Einträge der Vorgemerkt-Seite: eine Liste, benannt nach der Überschrift der Seite.
export function plannedEntries(page: Readonly<Page>) {
  return page.getByRole('list', { name: 'Vorgemerkt' }).getByRole('listitem')
}

// Zustände der Vorgemerkt-Seite für die Touch-Target-Suite (planned-recipes.feature, Querschnitts-
// Deklaration „Bedienbarkeit per Finger"). Der DB-Reset der Fixture lässt keine Vormerkung übrig.
export const plannedRecipesTouchTargets: TouchTargetPageDefinition = {
  name: 'Vorgemerkt',
  states: (page) => [
    {
      name: 'Leerzustand',
      reach: async () => {
        await page.goto('/planned')
        await expect(page.getByRole('link', { name: 'Zur Rezept-Liste' })).toBeVisible()
      },
    },
  ],
}

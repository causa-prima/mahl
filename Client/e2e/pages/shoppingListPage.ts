import { expect } from '../fixtures'
import type { Page } from '@playwright/test'
import type { TouchTargetPageDefinition } from './touchTargetPage'

// Der Leerzustand-Hinweis der Einkaufsliste.
export function emptyShoppingListHint(page: Readonly<Page>) {
  return page.getByText('Die Einkaufsliste ist leer.')
}

// Der Link des Leerzustands zur Vorgemerkt-Seite.
export function toPlannedRecipesLink(page: Readonly<Page>) {
  return page.getByRole('link', { name: 'Zu den vorgemerkten Rezepten' })
}

// Zustände der Einkaufsliste für die Touch-Target-Suite (shopping-lists.feature, Querschnitts-Verträge
// „Bedienbarkeit per Finger"). Der DB-Reset der Fixture lässt die Einkaufsliste leer.
export const shoppingListTouchTargets: TouchTargetPageDefinition = {
  name: 'Einkaufsliste',
  states: (page) => [
    {
      name: 'Leerzustand',
      reach: async () => {
        await page.goto('/shopping-list')
        await expect(toPlannedRecipesLink(page)).toBeVisible()
      },
    },
  ],
}

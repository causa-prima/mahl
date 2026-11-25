import { expect } from '../fixtures'
import type { Page } from '@playwright/test'
import { planRecipeViaApi } from '../api/plannedRecipesApi'
import { seedRecipesWithIngredientsViaApi } from '../api/recipesApi'
import { generateShoppingListViaApi } from '../api/shoppingListApi'
import type { TouchTargetPageDefinition } from './touchTargetPage'

// Der Leerzustand-Hinweis der Einkaufsliste.
export function emptyShoppingListHint(page: Readonly<Page>) {
  return page.getByText('Die Einkaufsliste ist leer.')
}

// Der Link des Leerzustands zur Vorgemerkt-Seite.
export function toPlannedRecipesLink(page: Readonly<Page>) {
  return page.getByRole('link', { name: 'Zu den vorgemerkten Rezepten' })
}

// Die Einträge der Einkaufsliste: eine Liste, benannt nach der Überschrift der Seite.
export function shoppingListItems(page: Readonly<Page>) {
  return page.getByRole('list', { name: 'Einkaufsliste' }).getByRole('listitem')
}

// Ein Eintrag, wie das Feature-File ihn nennt: „–“ als Menge heißt, es ist keine Menge angezeigt.
export type ShoppingListRow = { readonly name: string; readonly quantity: string }

// Liest je Eintrag Name und Menge getrennt (Step-Hinweis in features/shopping-lists.feature): Die Kachel zeigt beide
// als eigene Zeilen (ADR-S067-1), ohne Menge nur die Namenszeile. Mehr als zwei Zeilen landen ungeteilt in der Menge
// und lassen den Vergleich scheitern, statt still eine Zeile zu verlieren.
async function readShoppingList(page: Readonly<Page>): Promise<readonly ShoppingListRow[]> {
  const tiles = await shoppingListItems(page).allInnerTexts()
  return tiles.map((text) => {
    const [name = '', ...quantity] = text.split('\n').filter((line) => line.trim() !== '')
    // Das geschützte Leerzeichen zwischen Zahl und Einheit liest sich wie ein gewöhnliches, so wie es das Szenario
    // schreibt („250 g“); dass es geschützt ist, prüft der Komponententest der Einkaufsliste.
    return { name, quantity: quantity.length === 0 ? '–' : quantity.join('\n').replaceAll(String.fromCodePoint(0xa0), ' ') }
  })
}

// „zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge“ – navigiert nicht selbst und schließt den
// Leerzustand aus (Step-Hinweis in features/shopping-lists.feature).
export async function expectShoppingList(page: Readonly<Page>, rows: readonly ShoppingListRow[]): Promise<void> {
  await expect.poll(() => readShoppingList(page)).toEqual(rows)
  await expect(emptyShoppingListHint(page)).toBeHidden()
}

// „sehe ich die Einkaufsliste“: die Seite unter ihrer Adresse, erkennbar an der Überschrift.
export async function expectShoppingListPage(page: Readonly<Page>): Promise<void> {
  await expect(page).toHaveURL(/\/shopping-list$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Einkaufsliste' })).toBeVisible()
}

// Zustände der Einkaufsliste für die Touch-Target-Suite (shopping-lists.feature, Querschnitts-Verträge
// „Bedienbarkeit per Finger"). Der DB-Reset der Fixture lässt die Einkaufsliste leer; der Zustand „Liste" merkt
// danach ein Rezept vor, übernimmt über die API und lädt die Seite neu.
export const shoppingListTouchTargets: TouchTargetPageDefinition = {
  name: 'Einkaufsliste',
  states: (page, request) => [
    {
      name: 'Leerzustand',
      reach: async () => {
        await page.goto('/shopping-list')
        await expect(toPlannedRecipesLink(page)).toBeVisible()
      },
    },
    {
      name: 'Liste',
      // Die Kacheln sind nicht anklickbar (Abhaken kommt mit US-303); die Navigation misst die Suite getrennt.
      withoutControls: true,
      reach: async () => {
        const [pancakesId] = await seedRecipesWithIngredientsViaApi(request, { title: 'Pfannkuchen', lines: ['250 g Mehl'] })
        await planRecipeViaApi(request, pancakesId)
        await generateShoppingListViaApi(request)
        await page.reload()
        await expect(shoppingListItems(page)).toHaveCount(1)
      },
    },
  ],
}

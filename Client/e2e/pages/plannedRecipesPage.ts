import { expect } from '../fixtures'
import type { APIRequestContext, Page } from '@playwright/test'
import { planRecipeViaApi } from '../api/plannedRecipesApi'
import { seedIngredientViaApi } from '../api/ingredientsApi'
import { createRecipeViaApi } from '../api/recipesApi'
import type { DeleteWithUndoPageDefinition, ListEntry } from './interactionPage'
import type { TouchTargetPageDefinition } from './touchTargetPage'

// Die Einträge der Vorgemerkt-Seite: eine Liste, benannt nach der Überschrift der Seite.
export function plannedEntries(page: Readonly<Page>) {
  return page.getByRole('list', { name: 'Vorgemerkt' }).getByRole('listitem')
}

// Der Titel eines Eintrags der Vorgemerkt-Seite – der Link zu seiner Detailansicht.
export function plannedRecipeLink(page: Readonly<Page>, title: string) {
  return page.getByRole('list', { name: 'Vorgemerkt' }).getByRole('link', { name: title, exact: true })
}

// „Entfernen“ bei einem Eintrag der Vorgemerkt-Seite: Der Name für Screenreader nennt das Rezept.
export function removeButton(page: Readonly<Page>, title: string) {
  return page.getByRole('button', { name: `${title} entfernen`, exact: true })
}

// „Auf die Einkaufsliste“ – der Name für Screenreader steht im Kopf von features/shopping-lists.feature. Klick und
// die Prüfung, dass der Button fehlt, nutzen diesen einen Locator (Step-Hinweis dort).
export function toShoppingListButton(page: Readonly<Page>) {
  return page.getByRole('button', { name: 'Zutaten aller vorgemerkten Rezepte auf die Einkaufsliste', exact: true })
}

// Der Leerzustand-Hinweis der Vorgemerkt-Seite.
export function noPlannedRecipesHint(page: Readonly<Page>) {
  return page.getByText('Noch keine Rezepte vorgemerkt.')
}

// Ein vorgemerktes Rezept für die Querschnitts-Suite: Seed legt Zutat und Rezept an und merkt es vor. Jeder
// Eintrag hat eine eigene Zutat, weil die Suite die Einträge parallel seedet – eine gemeinsame Zutat ("Salz")
// würde beim zweiten Anlegen als Duplikat abgewiesen.
function plannedEntry(page: Readonly<Page>, request: Readonly<APIRequestContext>, title: string, ingredient: string): ListEntry {
  return {
    // `has` sucht innerhalb der Zeile – deshalb der Link ohne den Listen-Vorsatz von plannedRecipeLink.
    row: plannedEntries(page).filter({ has: page.getByRole('link', { name: title, exact: true }) }),
    deleteButton: removeButton(page, title),
    deletedToast: `${title} entfernt`,
    seed: async () => {
      await seedIngredientViaApi(request, ingredient, 'g')
      const id = await createRecipeViaApi(request, { title, ingredients: ingredient, instruction: 'Zubereiten.' })
      await planRecipeViaApi(request, id)
    },
  }
}

// Fähigkeit „Löschen mit Rückgängig-Toast“ der Vorgemerkt-Seite (features/planned-recipes.feature,
// Querschnitts-Verträge): Die Aktion heißt „Entfernen“, der Toast „<Titel> entfernt“.
export const plannedRecipesDeleteWithUndo: DeleteWithUndoPageDefinition = {
  name: 'Vorgemerkt',
  create: (page, request) => ({
    entries: [plannedEntry(page, request, 'Kartoffelsuppe', 'Kartoffeln'), plannedEntry(page, request, 'Pfannkuchen', 'Mehl')],
    list: page.getByRole('list', { name: 'Vorgemerkt' }),
    emptyState: noPlannedRecipesHint(page),
    // Glob `*` matcht kein `/`: trifft nur `/api/planned-recipes/{id}`, nicht das Collection-GET. Die Suite
    // verzögert dort nur DELETE – das Wiederherstellen ist ein PUT auf dieselbe URL (ADR-S153-1).
    deleteRoute: '**/api/planned-recipes/*',
    goto: async () => { await page.goto('/planned') },
  }),
}

// Zustände der Vorgemerkt-Seite für die Touch-Target-Suite (planned-recipes.feature, Querschnitts-
// Deklaration „Bedienbarkeit per Finger") – über dasselbe Page Object wie die Querschnitts-Suite, damit
// Selektoren und Testdaten nur dort leben. Der DB-Reset der Fixture lässt keine Vormerkung übrig; der
// Zustand „Liste" merkt danach ein Rezept vor und lädt die Seite neu, der Zustand „Undo-Toast" entfernt es wieder.
export const plannedRecipesTouchTargets: TouchTargetPageDefinition = {
  name: 'Vorgemerkt',
  states: (page, request) => {
    const deleteWithUndo = plannedRecipesDeleteWithUndo.create(page, request)
    const [entry] = deleteWithUndo.entries
    return [
      {
        name: 'Leerzustand',
        reach: async () => {
          await deleteWithUndo.goto()
          await expect(page.getByRole('link', { name: 'Zur Rezept-Liste' })).toBeVisible()
        },
      },
      {
        name: 'Liste',
        reach: async () => {
          await entry.seed()
          await page.reload()
          await expect(entry.row).toBeVisible()
        },
      },
      {
        name: 'Undo-Toast',
        reach: async () => {
          await entry.deleteButton.click()
          await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
        },
      },
    ]
  },
}

import type { APIRequestContext, Page } from '@playwright/test'
import { expect } from '../fixtures'
import { seedIngredientViaApi } from '../api/ingredientsApi'
import type { CreateDialogPageDefinition, DeleteWithUndoPageDefinition, ListEntry } from './interactionPage'
import type { TouchTargetPageDefinition } from './touchTargetPage'

function ingredientEntry(page: Readonly<Page>, request: Readonly<APIRequestContext>, name: string, baseUnit: string): ListEntry {
  // exact: Playwrights Default-Textmatch ist Substring-basiert – "g" steckt in fast jedem Namen.
  const row = page.getByTestId('ingredient-list').getByRole('listitem')
    .filter({ has: page.getByText(name, { exact: true }) })
    .filter({ has: page.getByText(baseUnit, { exact: true }) })
  return {
    row,
    deleteButton: page.getByRole('button', { name: `${name} löschen` }),
    deletedToast: `${name} gelöscht`,
    seed: () => seedIngredientViaApi(request, name, baseUnit),
  }
}

const gotoIngredients = (page: Readonly<Page>) => async () => { await page.goto('/ingredients') }

export const ingredientsCreateDialog: CreateDialogPageDefinition = {
  name: 'Zutaten',
  create: (page) => ({
    createRoute: '**/api/ingredients',
    goto: gotoIngredients(page),
    openCreateDialog: () => page.getByRole('button', { name: 'Zutat anlegen' }).click(),
    fillCreateDialogWithValidEntry: async () => {
      await page.getByLabel('Name').fill('Tomaten')
      await page.getByLabel('Einheit').fill('Stück')
    },
  }),
}

export const ingredientsDeleteWithUndo: DeleteWithUndoPageDefinition = {
  name: 'Zutaten',
  create: (page, request) => ({
    entries: [ingredientEntry(page, request, 'Mehl', 'g'), ingredientEntry(page, request, 'Zucker', 'g')],
    list: page.getByTestId('ingredient-list'),
    emptyState: page.getByText('Noch keine Zutaten angelegt.'),
    // Glob `*` matcht kein `/`: trifft nur `/api/ingredients/{id}` – weder das Collection-GET
    // (`/api/ingredients`) noch den Restore (`/api/ingredients/{id}/restore`).
    deleteRoute: '**/api/ingredients/*',
    goto: gotoIngredients(page),
  }),
}

// Zustände für die Touch-Target-Suite: Liste, Anlege-Dialog, Undo-Toast – über dieselben Page Objects
// wie die Listen-Suite, damit Selektoren und Testdaten nur dort leben.
export const ingredientsTouchTargets: TouchTargetPageDefinition = {
  name: 'Zutaten',
  states: (page, request) => {
    const deleteWithUndo = ingredientsDeleteWithUndo.create(page, request)
    const createDialog = ingredientsCreateDialog.create(page, request)
    const [entry] = deleteWithUndo.entries
    return [
      {
        name: 'Liste',
        reach: async () => {
          await entry.seed()
          await deleteWithUndo.goto()
          await expect(entry.row).toBeVisible()
        },
      },
      {
        name: 'Anlege-Dialog',
        reach: async () => {
          await createDialog.openCreateDialog()
          await expect(page.getByRole('dialog')).toBeVisible()
        },
      },
      {
        name: 'Undo-Toast',
        reach: async () => {
          await page.getByRole('button', { name: 'Abbrechen' }).click()
          await expect(page.getByRole('dialog')).toHaveCount(0)
          await entry.deleteButton.click()
          await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
        },
      },
    ]
  },
}

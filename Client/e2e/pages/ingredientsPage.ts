import type { APIRequestContext, Page } from '@playwright/test'
import { seedIngredientViaApi } from '../api/ingredientsApi'
import type { ListEntry, ListPage, ListPageDefinition } from './listPage'

function ingredientEntry(page: Readonly<Page>, request: Readonly<APIRequestContext>, name: string, baseUnit: string): ListEntry {
  // exact: Playwrights Default-Textmatch ist Substring-basiert – "g" steckt in fast jedem Namen.
  const row = page.getByTestId('ingredient-list').getByRole('listitem')
    .filter({ has: page.getByText(name, { exact: true }) })
    .filter({ has: page.getByText(baseUnit, { exact: true }) })
  return {
    label: name,
    row,
    deleteButton: page.getByRole('button', { name: `${name} löschen` }),
    seed: () => seedIngredientViaApi(request, name, baseUnit),
  }
}

export const ingredientsPage: ListPageDefinition = {
  name: 'Zutaten',
  create: (page, request): ListPage => ({
    entries: [ingredientEntry(page, request, 'Mehl', 'g'), ingredientEntry(page, request, 'Zucker', 'g')],
    list: page.getByTestId('ingredient-list'),
    emptyState: page.getByText('Noch keine Zutaten angelegt.'),
    createRoute: '**/api/ingredients',
    // Glob `*` matcht kein `/`: trifft nur `/api/ingredients/{id}` – weder das Collection-GET
    // (`/api/ingredients`) noch den Restore (`/api/ingredients/{id}/restore`).
    deleteRoute: '**/api/ingredients/*',
    goto: async () => { await page.goto('/ingredients') },
    openCreateDialog: () => page.getByRole('button', { name: 'Zutat anlegen' }).click(),
    fillCreateDialogWithValidEntry: async () => {
      await page.getByLabel('Name').fill('Tomaten')
      await page.getByLabel('Einheit').fill('Stück')
    },
  }),
}

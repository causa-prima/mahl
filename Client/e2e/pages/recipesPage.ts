import { expect } from '../fixtures'
import { seedRecipesWithSaltViaApi, UNKNOWN_RECIPE_ID } from '../api/recipesApi'
import type { Page } from '@playwright/test'
import type { TouchTargetPageDefinition } from './touchTargetPage'

// Die Nachfrage „Eingaben verwerfen?" des Rezeptformulars – eine Bestätigung vor einer destruktiven
// Aktion, daher alertdialog (UX-Guideline, Visuelle Baseline).
export function discardQuestion(page: Readonly<Page>) {
  return page.getByRole('alertdialog', { name: 'Eingaben verwerfen?' })
}

// Zustände der Rezeptseiten für die Touch-Target-Suite: Rezept-Liste, Formular samt Nachfrage
// „Eingaben verwerfen?" und Detailansicht (recipes.feature, Querschnitts-Deklaration „Bedienbarkeit per
// Finger"). Die Reihenfolge ist Vorbedingung: Jeder Zustand startet dort, wo der vorige endet („Formular"
// auf der Liste, „Nachfrage" im offenen Formular).
// Die Detailansicht eines gefundenen Rezepts hat noch kein eigenes Bedienelement – gemessen werden dort nur
// die Einträge der Navigationsleiste, die für den Leerlauf-Schutz nicht zählen. Der Zustand steht trotzdem
// hier, weil die Deklaration sie einschließt: Ein künftiges Bedienelement wird ohne weiteren Eingriff
// gemessen, und die Suite meldet dann, dass `withoutControls` zu entfernen ist. Der einzige Button der
// Detailansicht steht im Zustand „Rezept nicht gefunden".
export const recipesTouchTargets: TouchTargetPageDefinition = {
  name: 'Rezepte',
  states: (page, request) => [
    {
      name: 'Rezept-Liste',
      reach: async () => {
        await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')
        await page.goto('/recipes')
        await expect(page.getByRole('link', { name: 'Pfannkuchen' })).toBeVisible()
      },
    },
    {
      name: 'Formular',
      reach: async () => {
        await page.getByRole('button', { name: 'Rezept anlegen' }).click()
        await expect(page.getByRole('heading', { level: 1, name: 'Rezept anlegen' })).toBeVisible()
      },
    },
    {
      name: 'Nachfrage',
      reach: async () => {
        await page.getByLabel('Titel').fill('Pfannkuchen')
        await page.getByRole('button', { name: 'Abbrechen' }).click()
        await expect(discardQuestion(page)).toBeVisible()
      },
    },
    {
      name: 'Detailansicht',
      withoutControls: true,
      reach: async () => {
        await page.goto('/recipes')
        await page.getByRole('link', { name: 'Pfannkuchen' }).click()
        await expect(page.getByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeVisible()
      },
    },
    {
      name: 'Rezept nicht gefunden',
      reach: async () => {
        await page.goto(`/recipes/${UNKNOWN_RECIPE_ID}`)
        await expect(page.getByText('Rezept nicht gefunden.')).toBeVisible()
      },
    },
  ],
}

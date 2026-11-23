import { expect } from '../fixtures'
import { seedRecipesWithSaltViaApi, UNKNOWN_RECIPE_ID } from '../api/recipesApi'
import type { Page } from '@playwright/test'
import type { TouchTargetPageDefinition } from './touchTargetPage'

// Die Nachfrage „Eingaben verwerfen?" des Rezeptformulars – eine Bestätigung vor einer destruktiven
// Aktion, daher alertdialog (UX-Guideline, Visuelle Baseline).
export function discardQuestion(page: Readonly<Page>) {
  return page.getByRole('alertdialog', { name: 'Eingaben verwerfen?' })
}

// Die Titel der Rezept-Liste: je Zeile genau ein Link zur Detailansicht. Gelesen über die Links, nicht über die
// Zeilen – eine Zeile enthält auch den Umschalter „Vormerken“ samt Text.
export function recipeListTitles(page: Readonly<Page>) {
  return page.getByRole('list', { name: 'Rezepte' }).getByRole('link')
}

// Der Umschalter „Vormerken“ eines Rezepts in Rezept-Liste oder Detailansicht, im genannten Zustand: Sein Name
// nennt Rezept und Zustand („Pfannkuchen vormerken“ / „Pfannkuchen vorgemerkt“, Kopf von planned-recipes.feature).
export type ToggleState = 'vormerken' | 'vorgemerkt'

export function planningToggle(page: Readonly<Page>, title: string, state: ToggleState) {
  return page.getByRole('button', { name: `${title} ${state}`, exact: true })
}

// Zustände der Rezeptseiten für die Touch-Target-Suite: Rezept-Liste, Formular samt Nachfrage
// „Eingaben verwerfen?" und Detailansicht (recipes.feature, Querschnitts-Deklaration „Bedienbarkeit per
// Finger"; der Umschalter „Vormerken“ nach planned-recipes.feature). Die Reihenfolge ist Vorbedingung: Jeder
// Zustand startet dort, wo der vorige endet („Formular" auf der Liste, „Nachfrage" im offenen Formular).
// Rezept-Liste und Detailansicht warten auf den Umschalter: Er erscheint erst, wenn die Vormerkungen geladen sind.
export const recipesTouchTargets: TouchTargetPageDefinition = {
  name: 'Rezepte',
  states: (page, request) => [
    {
      name: 'Rezept-Liste',
      reach: async () => {
        await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')
        await page.goto('/recipes')
        await expect(planningToggle(page, 'Pfannkuchen', 'vormerken')).toBeVisible()
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
      reach: async () => {
        await page.goto('/recipes')
        await page.getByRole('link', { name: 'Pfannkuchen' }).click()
        await expect(page.getByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeVisible()
        await expect(planningToggle(page, 'Pfannkuchen', 'vormerken')).toBeVisible()
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

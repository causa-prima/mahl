import type { Page } from '@playwright/test'
import { test, expect } from './fixtures'
import { navEntry } from './pages/navigation'

// Querschnitt @CROSS-navigation (features/navigation.feature, ADR-S103-1): Jede Hauptseite ist über die
// Navigationsleiste erreichbar. Die Leiste ist ein Landmark „Hauptnavigation“ (navEntry); der Eintrag der
// geöffneten Seite trägt aria-current="page" (freigegebener UI-Entwurf: aktiver Eintrag markiert).

const pages = {
  Zutaten: '/ingredients',
  Rezepte: '/recipes',
} as const

type PageName = keyof typeof pages

async function gotoPage(page: Readonly<Page>, name: PageName): Promise<void> {
  await page.goto(pages[name])
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(name)
}

// Then „sehe ich die <Ziel>-Seite": Adresse, Seitentitel und markierter Eintrag der Leiste – der andere
// Eintrag (`other`) ist nicht markiert.
async function expectPageShown(page: Readonly<Page>, name: PageName, other: PageName): Promise<void> {
  await expect(page).toHaveURL(pages[name])
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(name)
  await expect(navEntry(page, name)).toHaveAttribute('aria-current', 'page')
  await expect(navEntry(page, other)).not.toHaveAttribute('aria-current')
}

test.describe('CROSS_Navigation: Navigationsleiste', () => {
  // Szenario: Von der Zutaten-Seite zur Rezepte-Seite navigieren
  test('CROSS_Navigation_IngredientsToRecipes_ClickNavigationEntry_ShowsRecipesPage', async ({ page }) => {
    // Given: ich navigiere zur Zutaten-Seite
    await gotoPage(page, 'Zutaten')

    // When: ich in der Navigationsleiste auf "Rezepte" klicke
    await navEntry(page, 'Rezepte').click()

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown(page, 'Rezepte', 'Zutaten')
  })

  // Szenario: Von der Rezepte-Seite zur Zutaten-Seite navigieren
  test('CROSS_Navigation_RecipesToIngredients_ClickNavigationEntry_ShowsIngredientsPage', async ({ page }) => {
    // Given: ich navigiere zur Rezepte-Seite
    await gotoPage(page, 'Rezepte')

    // When: ich in der Navigationsleiste auf "Zutaten" klicke
    await navEntry(page, 'Zutaten').click()

    // Then: sehe ich die Zutaten-Seite
    await expectPageShown(page, 'Zutaten', 'Rezepte')
  })
})

test.describe('CROSS_Navigation: Einstieg', () => {
  // Szenario: Ohne Adresse öffnet die Anwendung die Rezepte-Seite
  test('CROSS_Navigation_StartPage_OpenWithoutPath_ShowsRecipesPage', async ({ page }) => {
    // Given: die Anwendung ist gestartet (Background)
    // When: ich die Anwendung ohne Pfad öffne
    await page.goto('/')

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown(page, 'Rezepte', 'Zutaten')
  })

  // Szenario: Eine unbekannte Adresse zeigt „Seite nicht gefunden.“ mit Navigationsleiste
  test('CROSS_Navigation_UnknownAddress_OpenUnknownPath_ShowsNotFoundWithNavigationBar', async ({ page }) => {
    // Given: die Anwendung ist gestartet (Background)
    // When: ich die Adresse "/zutatn" öffne
    await page.goto('/zutatn')

    // Then: sehe ich die Meldung "Seite nicht gefunden."
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Seite nicht gefunden.')

    // When: ich in der Navigationsleiste auf "Rezepte" klicke
    await navEntry(page, 'Rezepte').click()

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown(page, 'Rezepte', 'Zutaten')
  })
})

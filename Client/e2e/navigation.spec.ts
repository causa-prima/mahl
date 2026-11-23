import type { Page } from '@playwright/test'
import { test, expect } from './fixtures'
import { navEntry } from './pages/navigation'
import { createRecipeViaApi } from './api/recipesApi'
import { seedIngredientViaApi } from './api/ingredientsApi'

// Querschnitt @CROSS-navigation (features/navigation.feature, ADR-S103-1): Jede Hauptseite ist über die
// Navigationsleiste erreichbar. Die Leiste ist ein Landmark „Hauptnavigation“ (navEntry); der Eintrag der
// geöffneten Seite trägt aria-current="page" (freigegebener UI-Entwurf: aktiver Eintrag markiert).

const pages = {
  Zutaten: '/ingredients',
  Rezepte: '/recipes',
  Vorgemerkt: '/planned',
} as const

type PageName = keyof typeof pages
const pageNames = Object.keys(pages) as PageName[]

async function gotoPage(page: Readonly<Page>, name: PageName): Promise<void> {
  await page.goto(pages[name])
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(name)
}

// Then „sehe ich die <Ziel>-Seite": Adresse, Seitentitel und markierter Eintrag der Leiste.
async function expectPageShown(page: Readonly<Page>, name: PageName): Promise<void> {
  await expect(page).toHaveURL(pages[name])
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(name)
  await expectOnlyMarked(page, name)
}

// Then „ist in der Navigationsleiste nur der Eintrag <name> markiert": Er trägt aria-current="page", jeder
// andere Eintrag steht in der Leiste und ist nicht markiert.
async function expectOnlyMarked(page: Readonly<Page>, name: PageName): Promise<void> {
  await expect(navEntry(page, name)).toHaveAttribute('aria-current', 'page')
  await Promise.all(pageNames.filter((other) => other !== name).map(async (other) => {
    await expect(navEntry(page, other)).toBeVisible()
    await expect(navEntry(page, other)).not.toHaveAttribute('aria-current')
  }))
}

test.describe('CROSS_Navigation: Navigationsleiste', () => {
  // Szenario: Von der Zutaten-Seite zur Rezepte-Seite navigieren
  test('CROSS_Navigation_IngredientsToRecipes_ClickNavigationEntry_ShowsRecipesPage', async ({ page }) => {
    // Given: ich navigiere zur Zutaten-Seite
    await gotoPage(page, 'Zutaten')

    // When: ich in der Navigationsleiste auf "Rezepte" klicke
    await navEntry(page, 'Rezepte').click()

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown(page, 'Rezepte')
  })

  // Szenario: Von der Rezepte-Seite zur Zutaten-Seite navigieren
  test('CROSS_Navigation_RecipesToIngredients_ClickNavigationEntry_ShowsIngredientsPage', async ({ page }) => {
    // Given: ich navigiere zur Rezepte-Seite
    await gotoPage(page, 'Rezepte')

    // When: ich in der Navigationsleiste auf "Zutaten" klicke
    await navEntry(page, 'Zutaten').click()

    // Then: sehe ich die Zutaten-Seite
    await expectPageShown(page, 'Zutaten')
  })

  // Szenario: Von der Detailansicht eines Rezepts zur Rezept-Liste navigieren
  test('CROSS_Navigation_RecipeToRecipes_ClickNavigationEntryAfterDirectLink_ShowsRecipeList', async ({ context, request }) => {
    // Given: das Rezept "Pfannkuchen" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')
    const pancakesId = await createRecipeViaApi(request, { title: 'Pfannkuchen', ingredients: '250 g Mehl', instruction: 'Teig rühren.' })

    // Given: ich habe den Direktlink des Rezepts "Pfannkuchen" in einem neuen Browserfenster geöffnet – eine neue
    //   Seite ohne vorher geladene Anwendung; der Direktlink ist die Adresse /recipes/{id} (ADR-S135-5). Die
    //   Detailansicht muss geladen sein, bevor geklickt wird, sonst prüfte der Test den Weg von einer halb
    //   geladenen Seite.
    const newWindow = await context.newPage()
    await newWindow.goto(`/recipes/${pancakesId}`)
    await expect(newWindow.getByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeVisible()

    // When: ich in der Navigationsleiste auf "Rezepte" klicke
    await navEntry(newWindow, 'Rezepte').click()

    // Then: sehe ich die Rezept-Liste mit "Pfannkuchen"
    await expectPageShown(newWindow, 'Rezepte')
    await expect(newWindow.getByRole('link', { name: 'Pfannkuchen' })).toBeVisible()
  })

  // Szenario: Von der Rezepte-Seite zur Vorgemerkt-Seite navigieren
  test('CROSS_Navigation_RecipesToPlanned_ClickNavigationEntry_ShowsPlannedPage', async ({ page }) => {
    // Given: ich navigiere zur Rezepte-Seite
    await gotoPage(page, 'Rezepte')

    // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
    await navEntry(page, 'Vorgemerkt').click()

    // Then: sehe ich die Vorgemerkt-Seite
    await expectPageShown(page, 'Vorgemerkt')
  })
})

test.describe('CROSS_Navigation: Markierung', () => {
  // Eine Zeile je Beispiel der Scenario Outline.
  const subpages = [
    { name: 'die Detailansicht des Rezepts "Pfannkuchen"', path: (id: string) => `/recipes/${id}`, heading: 'Pfannkuchen' },
    { name: 'das Formular "Rezept anlegen"', path: () => '/recipes/new', heading: 'Rezept anlegen' },
  ] as const

  subpages.forEach(({ name, path, heading }) => {
    // Szenario: Auf einer Unterseite der Rezepte ist „Rezepte“ markiert
    // Beispiel: alle
    test(`CROSS_Navigation_ActiveEntryOnSubpage_OpenSubpage_MarksOnlyRecipes (${name})`, async ({ page, request }) => {
      // Given: das Rezept "Pfannkuchen" existiert
      await seedIngredientViaApi(request, 'Salz', 'g')
      const pancakesId = await createRecipeViaApi(request, { title: 'Pfannkuchen', ingredients: 'Salz', instruction: 'Zubereiten.' })

      // When: ich <Unterseite> öffne – über die Adresse; die Seite muss geladen sein, bevor die Leiste geprüft wird
      await page.goto(path(pancakesId))
      await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible()

      // Then: ist in der Navigationsleiste nur der Eintrag "Rezepte" markiert
      await expectOnlyMarked(page, 'Rezepte')
    })
  })
})

test.describe('CROSS_Navigation: Einstieg', () => {
  // Szenario: Ohne Adresse öffnet die Anwendung die Rezepte-Seite
  test('CROSS_Navigation_StartPage_OpenWithoutPath_ShowsRecipesPage', async ({ page }) => {
    // Given: die Anwendung ist gestartet (Background)
    // When: ich die Anwendung ohne Pfad öffne
    await page.goto('/')

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown(page, 'Rezepte')
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
    await expectPageShown(page, 'Rezepte')
  })
})

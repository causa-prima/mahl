import type { Page } from '@playwright/test'
import { test, expect } from './fixtures'
import { planRecipeViaApi, unplanRecipeViaApi } from './api/plannedRecipesApi'
import { seedIngredientViaApi } from './api/ingredientsApi'
import { createRecipeViaApi, seedRecipesWithSaltViaApi } from './api/recipesApi'
import { exactly } from './exactText'
import { navEntry } from './pages/navigation'
import { noPlannedRecipesHint, plannedEntries, plannedRecipeLink, removeButton } from './pages/plannedRecipesPage'
import { planningToggle, type ToggleState } from './pages/recipesPage'

// „zeigt die Rezept-Liste bei "<Rezept>" "<Zustand>" und bei "<Rezept>" "<Zustand>"“
async function expectRecipeListToggles(page: Readonly<Page>, toggles: Readonly<Record<string, ToggleState>>) {
  await expect(page.getByRole('heading', { level: 1, name: 'Rezepte' })).toBeVisible()
  await Promise.all(Object.entries(toggles).map(([title, state]) => expect(planningToggle(page, title, state)).toBeVisible()))
}

// „sehe ich keinen Toast“ – erst prüfen, nachdem die Anzeige die Antwort des Servers zeigt; ein Toast trägt die Rolle
// alert (MUI-Snackbar) oder status
async function expectNoToast(page: Readonly<Page>) {
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByRole('status')).toHaveCount(0)
}

const onlyPancakesPlanned = { Pfannkuchen: 'vorgemerkt', Kartoffelsuppe: 'vormerken' } as const
const onlyPotatoSoupPlanned = { Pfannkuchen: 'vormerken', Kartoffelsuppe: 'vorgemerkt' } as const

// Die Orte, an denen der Umschalter steht: `open` öffnet den Ort, `expectShown` prüft, dass er weiter zu sehen ist.
// `expectPlanned` und `expectUnplanned` sind die <Anzeige> der Beispielzeile nach dem Vormerken bzw. Aufheben.
const places = [
  {
    name: 'die Rezept-Liste',
    open: async (page: Readonly<Page>) => { await page.goto('/recipes') },
    expectShown: async (page: Readonly<Page>) => {
      await expect(page).toHaveURL(/\/recipes$/)
      await expect(page.getByRole('heading', { level: 1, name: 'Rezepte' })).toBeVisible()
    },
    expectPlanned: async (page: Readonly<Page>) => { await expectRecipeListToggles(page, onlyPancakesPlanned) },
    expectUnplanned: async (page: Readonly<Page>) => { await expectRecipeListToggles(page, onlyPotatoSoupPlanned) },
  },
  {
    name: 'die Detailansicht des Rezepts "Pfannkuchen"',
    open: async (page: Readonly<Page>, pancakesId: string) => { await page.goto(`/recipes/${pancakesId}`) },
    expectShown: async (page: Readonly<Page>, pancakesId: string) => {
      await expect(page).toHaveURL(new RegExp(`/recipes/${pancakesId}$`))
      await expect(page.getByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeVisible()
    },
    expectPlanned: async (page: Readonly<Page>) => { await expect(planningToggle(page, 'Pfannkuchen', 'vorgemerkt')).toBeVisible() },
    expectUnplanned: async (page: Readonly<Page>) => { await expect(planningToggle(page, 'Pfannkuchen', 'vormerken')).toBeVisible() },
  },
] as const

// @US-803-happy-path
test.describe('US803_HappyPath: Vorgemerkt-Seite', () => {
  // Szenario: Ohne Vormerkungen zeigt die Vorgemerkt-Seite einen Hinweis
  test('US803_HappyPath_GetPlannedRecipes_NonePlanned_ShowsHintAndLinkToRecipeList', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" existiert, und kein Rezept ist vorgemerkt (DB-Reset der Auto-Fixture)
    await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')

    // When: ich zur Vorgemerkt-Seite navigiere
    await page.goto('/planned')

    // Then: ich sehe den Hinweis "Noch keine Rezepte vorgemerkt." und den Link "Zur Rezept-Liste"
    await expect(page.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeVisible()
    await expect(noPlannedRecipesHint(page)).toBeVisible()
    const toRecipeList = page.getByRole('link', { name: 'Zur Rezept-Liste' })
    await expect(toRecipeList).toBeVisible()

    // When: ich auf "Zur Rezept-Liste" klicke
    await toRecipeList.click()

    // Then: ich sehe die Rezept-Liste mit "Pfannkuchen"
    await expect(page).toHaveURL(/\/recipes$/)
    await expect(page.getByRole('heading', { level: 1, name: 'Rezepte' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Pfannkuchen' })).toBeVisible()
  })

  // Szenario: Die Vorgemerkt-Seite zeigt nur die vorgemerkten Rezepte, alphabetisch
  test('US803_HappyPath_GetPlannedRecipes_SeveralPlanned_ShowsOnlyPlannedAlphabetically', async ({ page, request }) => {
    // Given: die Rezepte "Pfannkuchen", "Spaghetti Bolognese", "Linsensalat" und "Kartoffelsuppe" existieren, in dieser
    // Reihenfolge angelegt
    const [pancakesId, spaghettiId, , potatoSoupId] = await seedRecipesWithSaltViaApi(
      request, 'Pfannkuchen', 'Spaghetti Bolognese', 'Linsensalat', 'Kartoffelsuppe')

    // And: die Rezepte "Spaghetti Bolognese", "Kartoffelsuppe" und "Pfannkuchen" sind in dieser Reihenfolge vorgemerkt
    await planRecipeViaApi(request, spaghettiId)
    await planRecipeViaApi(request, potatoSoupId)
    await planRecipeViaApi(request, pancakesId)

    // When: ich zur Vorgemerkt-Seite navigiere
    await page.goto('/planned')

    // Then: zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen", "Spaghetti Bolognese" in
    // dieser Reihenfolge – „genau“ schließt "Linsensalat" und den Leerzustand-Hinweis aus
    await expect(plannedEntries(page))
      .toHaveText([exactly('Kartoffelsuppe'), exactly('Pfannkuchen'), exactly('Spaghetti Bolognese')])
    await expect(noPlannedRecipesHint(page)).toBeHidden()
  })

  // Szenario: Ein vorgemerktes Rezept von der Vorgemerkt-Seite aus öffnen
  test('US803_HappyPath_OpenPlannedRecipe_ClickTitle_ShowsDetailWithPlannedToggle', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" mit der Zutat "250 g Mehl" ist vorgemerkt
    await seedIngredientViaApi(request, 'Mehl', 'g')
    const pancakesId = await createRecipeViaApi(request, { title: 'Pfannkuchen', ingredients: '250 g Mehl', instruction: 'Teig rühren.' })
    await planRecipeViaApi(request, pancakesId)

    // And: das Rezept "Kartoffelsuppe" ist vorgemerkt – es steht alphabetisch vor "Pfannkuchen", ein Klick auf den
    // falschen Eintrag fiele also auf
    const [potatoSoupId] = await seedRecipesWithSaltViaApi(request, 'Kartoffelsuppe')
    await planRecipeViaApi(request, potatoSoupId)

    // When: ich zur Vorgemerkt-Seite navigiere
    await page.goto('/planned')

    // And: ich auf "Pfannkuchen" klicke
    await plannedRecipeLink(page, 'Pfannkuchen').click()

    // Then: sehe ich die Detailansicht des Rezepts "Pfannkuchen" mit der Zutat "250 g Mehl" (genau diese Zutat)
    await expect(page.getByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeVisible()
    await expect(page.getByRole('list', { name: 'Zutaten' }).getByRole('listitem')).toHaveText(['250 g Mehl'])

    // And: zeigt der Umschalter "Vorgemerkt"
    await expect(planningToggle(page, 'Pfannkuchen', 'vorgemerkt')).toBeVisible()
  })
})

// @US-803-happy-path
test.describe('US803_HappyPath: Vormerken', () => {
  places.forEach(({ name, open, expectShown, expectPlanned }) => {
    // Szenario: Ein Rezept vormerken
    // Beispiel: alle
    test(`US803_HappyPath_PlanRecipe_ClickToggle_ShowsPlannedEverywhere (${name})`, async ({ page, request }) => {
      // Given: die Rezepte "Kartoffelsuppe" und "Pfannkuchen" existieren, und kein Rezept ist vorgemerkt (DB-Reset der Auto-Fixture)
      const [, pancakesId] = await seedRecipesWithSaltViaApi(request, 'Kartoffelsuppe', 'Pfannkuchen')

      // When: ich <Ort> öffne
      await open(page, pancakesId)

      // And: ich bei "Pfannkuchen" auf "Vormerken" klicke
      await planningToggle(page, 'Pfannkuchen', 'vormerken').click()

      // Then: <Anzeige>
      await expectPlanned(page)

      // And: sehe ich weiterhin <Ort>
      await expectShown(page, pancakesId)

      // And: sehe ich keinen Toast
      await expectNoToast(page)

      // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
      await navEntry(page, 'Vorgemerkt').click()

      // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen" – „genau“ schließt den Leerzustand-Hinweis aus
      await expect(plannedEntries(page)).toHaveText([exactly('Pfannkuchen')])
      await expect(noPlannedRecipesHint(page)).toBeHidden()

      // When: ich in der Navigationsleiste auf "Rezepte" klicke
      await navEntry(page, 'Rezepte').click()

      // Then: zeigt die Rezept-Liste bei "Pfannkuchen" "Vorgemerkt" und bei "Kartoffelsuppe" "Vormerken"
      await expectRecipeListToggles(page, onlyPancakesPlanned)

      // When: ich die Seite neu lade
      await page.reload()

      // Then: zeigt die Rezept-Liste bei "Pfannkuchen" "Vorgemerkt" und bei "Kartoffelsuppe" "Vormerken"
      await expectRecipeListToggles(page, onlyPancakesPlanned)
    })
  })
})

// @US-803-happy-path
test.describe('US803_HappyPath: Vormerkung aufheben', () => {
  places.forEach(({ name, open, expectShown, expectUnplanned }) => {
    // Szenario: Eine Vormerkung per Umschalter aufheben
    // Beispiel: alle
    test(`US803_HappyPath_UnplanRecipe_ClickToggle_ShowsUnplannedEverywhere (${name})`, async ({ page, request }) => {
      // Given: die Rezepte "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt
      const [potatoSoupId, pancakesId] = await seedRecipesWithSaltViaApi(request, 'Kartoffelsuppe', 'Pfannkuchen')
      await planRecipeViaApi(request, potatoSoupId)
      await planRecipeViaApi(request, pancakesId)

      // When: ich <Ort> öffne
      await open(page, pancakesId)

      // And: ich bei "Pfannkuchen" auf "Vorgemerkt" klicke
      await planningToggle(page, 'Pfannkuchen', 'vorgemerkt').click()

      // Then: <Anzeige>
      await expectUnplanned(page)

      // And: sehe ich weiterhin <Ort>
      await expectShown(page, pancakesId)

      // And: sehe ich keinen Toast
      await expectNoToast(page)

      // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
      await navEntry(page, 'Vorgemerkt').click()

      // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Kartoffelsuppe"
      await expect(plannedEntries(page)).toHaveText([exactly('Kartoffelsuppe')])

      // When: ich in der Navigationsleiste auf "Rezepte" klicke
      await navEntry(page, 'Rezepte').click()

      // Then: zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt"
      await expectRecipeListToggles(page, onlyPotatoSoupPlanned)

      // When: ich die Seite neu lade
      await page.reload()

      // Then: zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt"
      await expectRecipeListToggles(page, onlyPotatoSoupPlanned)
    })
  })
})

// @US-803-edge-case
test.describe('US803_EdgeCase: Vormerken', () => {
  // Szenario: Ein inzwischen anderswo vorgemerktes Rezept vormerken
  test('US803_EdgeCase_PlanRecipe_AlreadyPlannedElsewhere_ShowsPlannedOnce', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" existiert, und kein Rezept ist vorgemerkt (DB-Reset der Auto-Fixture)
    const [pancakesId] = await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')

    // And: ich habe die Rezept-Liste geöffnet – geladen, sobald der Umschalter steht
    await page.goto('/recipes')
    await expect(planningToggle(page, 'Pfannkuchen', 'vormerken')).toBeVisible()

    // And: das Rezept "Pfannkuchen" wird danach auf einem anderen Gerät vorgemerkt
    await planRecipeViaApi(request, pancakesId)

    // When: ich bei "Pfannkuchen" auf "Vormerken" klicke
    await planningToggle(page, 'Pfannkuchen', 'vormerken').click()

    // Then: zeigt die Rezept-Liste bei "Pfannkuchen" "Vorgemerkt"
    await expect(planningToggle(page, 'Pfannkuchen', 'vorgemerkt')).toBeVisible()

    // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
    await navEntry(page, 'Vorgemerkt').click()
    await expect(page.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeVisible()

    // And: ich die Seite neu lade
    await page.reload()

    // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen" – „genau“ schließt den Leerzustand-Hinweis aus
    await expect(plannedEntries(page)).toHaveText([exactly('Pfannkuchen')])
    await expect(noPlannedRecipesHint(page)).toBeHidden()
  })
})

// @US-803-edge-case
test.describe('US803_EdgeCase: Vormerkung aufheben', () => {
  // Szenario: Eine inzwischen anderswo aufgehobene Vormerkung aufheben
  test('US803_EdgeCase_UnplanRecipe_AlreadyUnplannedElsewhere_ShowsUnplanned', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" ist vorgemerkt, und sonst ist kein Rezept vorgemerkt (DB-Reset der Auto-Fixture)
    const [pancakesId] = await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')
    await planRecipeViaApi(request, pancakesId)

    // And: ich habe die Rezept-Liste geöffnet – geladen, sobald der Umschalter steht
    await page.goto('/recipes')
    await expect(planningToggle(page, 'Pfannkuchen', 'vorgemerkt')).toBeVisible()

    // And: die Vormerkung von "Pfannkuchen" wird danach auf einem anderen Gerät aufgehoben
    await unplanRecipeViaApi(request, pancakesId)

    // When: ich bei "Pfannkuchen" auf "Vorgemerkt" klicke
    await planningToggle(page, 'Pfannkuchen', 'vorgemerkt').click()

    // Then: zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken"
    await expect(planningToggle(page, 'Pfannkuchen', 'vormerken')).toBeVisible()

    // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
    await navEntry(page, 'Vorgemerkt').click()
    await expect(page.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeVisible()

    // And: ich die Seite neu lade
    await page.reload()

    // Then: sehe ich den Hinweis "Noch keine Rezepte vorgemerkt."
    await expect(noPlannedRecipesHint(page)).toBeVisible()
  })
})

// „sehe ich den Toast "<Text>" mit "Rückgängig"-Aktion“
async function expectUndoToast(page: Readonly<Page>, text: string) {
  await expect(page.getByText(text, { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
}

// run-5 „Entfernen·Rückgängig“. Was auf jeder Seite mit Rückgängig-Toast gleich ist (Toast-Lebensdauer, mehrere
// Toasts, Sperre beim Entfernen), prüft die Querschnitts-Suite interaction.spec.ts über plannedRecipesDeleteWithUndo;
// hier steht nur, was die Vorgemerkt-Seite betrifft: das Verb, die Wirkung auf die Rezept-Liste und die
// alphabetische Wiedereinordnung.
// @US-803-happy-path
test.describe('US803_HappyPath: Vormerkung entfernen', () => {
  // Szenario: Eine Vormerkung auf der Vorgemerkt-Seite entfernen
  test('US803_HappyPath_RemovePlannedRecipe_FromPlannedPage_ShowsRemovedEverywhere', async ({ page, request }) => {
    // Given: die Rezepte "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt
    const [potatoSoupId, pancakesId] = await seedRecipesWithSaltViaApi(request, 'Kartoffelsuppe', 'Pfannkuchen')
    await planRecipeViaApi(request, potatoSoupId)
    await planRecipeViaApi(request, pancakesId)

    // When: ich zur Vorgemerkt-Seite navigiere
    await page.goto('/planned')

    // And: ich bei "Pfannkuchen" auf "Entfernen" klicke
    await removeButton(page, 'Pfannkuchen').click()

    // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Kartoffelsuppe"
    await expect(plannedEntries(page)).toHaveText([exactly('Kartoffelsuppe')])

    // And: sehe ich den Toast "Pfannkuchen entfernt" mit "Rückgängig"-Aktion
    await expectUndoToast(page, 'Pfannkuchen entfernt')

    // When: ich in der Navigationsleiste auf "Rezepte" klicke
    await navEntry(page, 'Rezepte').click()

    // Then: zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt"
    await expectRecipeListToggles(page, onlyPotatoSoupPlanned)

    // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
    await navEntry(page, 'Vorgemerkt').click()
    await expect(page.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeVisible()

    // And: ich die Seite neu lade
    await page.reload()

    // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Kartoffelsuppe"
    await expect(plannedEntries(page)).toHaveText([exactly('Kartoffelsuppe')])
  })

  // Szenario: Das Entfernen einer Vormerkung rückgängig machen
  test('US803_HappyPath_UndoRemovePlannedRecipe_ViaToast_ReturnsInAlphabeticalOrder', async ({ page, request }) => {
    // Given: die Rezepte "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt
    const [potatoSoupId, pancakesId] = await seedRecipesWithSaltViaApi(request, 'Kartoffelsuppe', 'Pfannkuchen')
    await planRecipeViaApi(request, potatoSoupId)
    await planRecipeViaApi(request, pancakesId)

    // When: ich zur Vorgemerkt-Seite navigiere
    await page.goto('/planned')

    // And: ich bei "Kartoffelsuppe" auf "Entfernen" klicke
    await removeButton(page, 'Kartoffelsuppe').click()

    // And: ich im Toast auf "Rückgängig" klicke
    await page.getByRole('button', { name: 'Rückgängig' }).click()

    // Then: zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen" in dieser Reihenfolge –
    //   das zurückgeholte Rezept steht wieder vorn, nicht angehängt
    await expect(plannedEntries(page)).toHaveText([exactly('Kartoffelsuppe'), exactly('Pfannkuchen')])

    // And: sehe ich den Toast "Kartoffelsuppe entfernt" nicht mehr
    await expect(page.getByText('Kartoffelsuppe entfernt', { exact: true })).toBeHidden()

    // When: ich die Seite neu lade
    await page.reload()

    // Then: zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen" in dieser Reihenfolge
    await expect(plannedEntries(page)).toHaveText([exactly('Kartoffelsuppe'), exactly('Pfannkuchen')])
  })
})

// @US-803-edge-case
test.describe('US803_EdgeCase: Vormerkung entfernen', () => {
  // Szenario: Die letzte Vormerkung entfernen und zurückholen
  test('US803_EdgeCase_RemoveLastPlannedRecipe_UndoViaToast_ListReplacesHint', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" ist vorgemerkt, und sonst ist kein Rezept vorgemerkt (DB-Reset der Auto-Fixture)
    const [pancakesId] = await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')
    await planRecipeViaApi(request, pancakesId)

    // When: ich zur Vorgemerkt-Seite navigiere
    await page.goto('/planned')

    // And: ich bei "Pfannkuchen" auf "Entfernen" klicke
    await removeButton(page, 'Pfannkuchen').click()

    // Then: sehe ich den Hinweis "Noch keine Rezepte vorgemerkt." und den Link "Zur Rezept-Liste"
    await expect(noPlannedRecipesHint(page)).toBeVisible()
    await expect(page.getByRole('link', { name: 'Zur Rezept-Liste' })).toBeVisible()

    // And: sehe ich den Toast "Pfannkuchen entfernt" mit "Rückgängig"-Aktion
    await expectUndoToast(page, 'Pfannkuchen entfernt')

    // When: ich im Toast auf "Rückgängig" klicke
    await page.getByRole('button', { name: 'Rückgängig' }).click()

    // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen"
    await expect(plannedEntries(page)).toHaveText([exactly('Pfannkuchen')])

    // And: sehe ich den Hinweis "Noch keine Rezepte vorgemerkt." nicht mehr
    await expect(noPlannedRecipesHint(page)).toBeHidden()
  })
})

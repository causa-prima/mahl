import type { APIRequestContext, Page } from '@playwright/test'
import { test, expect } from './fixtures'
import { planRecipeViaApi, unplanRecipeViaApi } from './api/plannedRecipesApi'
import { seedRecipesWithIngredientsViaApi, seedRecipesWithSaltViaApi } from './api/recipesApi'
import { generateShoppingListViaApi } from './api/shoppingListApi'
import { exactly } from './exactText'
import { navEntry } from './pages/navigation'
import { noPlannedRecipesHint, plannedEntries, toShoppingListButton } from './pages/plannedRecipesPage'
import { emptyShoppingListHint, expectShoppingList, expectShoppingListPage, toPlannedRecipesLink } from './pages/shoppingListPage'
import type { ShoppingListRow } from './pages/shoppingListPage'

// And: ich auf "Auf die Einkaufsliste" klicke – der Locator nutzt den Namen für Screenreader, deshalb wird der
// sichtbare Text eigens geprüft.
async function clickToShoppingList(page: Readonly<Page>): Promise<void> {
  await expect(toShoppingListButton(page)).toHaveText('Auf die Einkaufsliste')
  await toShoppingListButton(page).click()
}

// When: ich zur Vorgemerkt-Seite navigiere / And: ich auf "Auf die Einkaufsliste" klicke
async function transferFromPlannedPage(page: Readonly<Page>): Promise<void> {
  await page.goto('/planned')
  await clickToShoppingList(page)
}

// Given: das Rezept "Pfannkuchen" mit der Zutat "<Zeile Pfannkuchen>" ist vorgemerkt / And: das Rezept "Waffeln" mit
// der Zutat "<Zeile Waffeln>" ist vorgemerkt – die gemeinsame Vorbedingung der beiden Grundrisse.
async function planPancakesAndWaffles(request: Readonly<APIRequestContext>, pancakesLine: string, wafflesLine: string): Promise<void> {
  const ids = await seedRecipesWithIngredientsViaApi(
    request,
    { title: 'Pfannkuchen', lines: [pancakesLine] },
    { title: 'Waffeln', lines: [wafflesLine] },
  )
  await Promise.all(ids.map((id) => planRecipeViaApi(request, id)))
}

// @US-201-happy-path
test.describe('US201_HappyPath: Einkaufsliste', () => {
  // Szenario: Eine noch nie gefüllte Einkaufsliste zeigt einen Hinweis
  test('US201_HappyPath_GetShoppingList_NeverFilled_ShowsHintAndLinkToPlannedRecipes', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" ist vorgemerkt
    const [pancakesId] = await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')
    await planRecipeViaApi(request, pancakesId)

    // And: die Einkaufsliste ist leer (DB-Reset der Auto-Fixture)

    // When: ich zur Einkaufsliste navigiere
    await page.goto('/shopping-list')

    // Then: sehe ich den Hinweis "Die Einkaufsliste ist leer." und den Link "Zu den vorgemerkten Rezepten"
    await expect(page.getByRole('heading', { level: 1, name: 'Einkaufsliste' })).toBeVisible()
    await expect(emptyShoppingListHint(page)).toBeVisible()
    await expect(toPlannedRecipesLink(page)).toBeVisible()

    // When: ich auf "Zu den vorgemerkten Rezepten" klicke
    await toPlannedRecipesLink(page).click()

    // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen" – „genau“ schließt den Leerzustand-Hinweis aus
    await expect(page.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeVisible()
    await expect(plannedEntries(page)).toHaveText([exactly('Pfannkuchen')])
    await expect(noPlannedRecipesHint(page)).toBeHidden()
  })
})

// @US-201-happy-path
test.describe('US201_HappyPath: Übernehmen', () => {
  // Szenario: Die Zutaten der vorgemerkten Rezepte alphabetisch auf die Einkaufsliste übernehmen
  test('US201_HappyPath_GenerateShoppingList_TwoPlannedRecipes_ShowsIngredientsAlphabetically', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" mit den Zutaten "250 g Mehl", "0,5 l Milch" und "3 Stück Eier" ist vorgemerkt
    // And: das Rezept "Kartoffelsuppe" mit den Zutaten "1000 g Kartoffeln" und "Salz" ist vorgemerkt
    // And: das Rezept "Linsensalat" mit der Zutat "200 g Linsen" existiert und ist nicht vorgemerkt
    const [pancakesId, soupId] = await seedRecipesWithIngredientsViaApi(
      request,
      { title: 'Pfannkuchen', lines: ['250 g Mehl', '0,5 l Milch', '3 Stück Eier'] },
      { title: 'Kartoffelsuppe', lines: ['1000 g Kartoffeln', 'Salz'] },
      { title: 'Linsensalat', lines: ['200 g Linsen'] },
    )
    await planRecipeViaApi(request, pancakesId)
    await planRecipeViaApi(request, soupId)

    // And: die Einkaufsliste ist leer (DB-Reset der Auto-Fixture)

    // When: ich zur Vorgemerkt-Seite navigiere / And: ich auf "Auf die Einkaufsliste" klicke
    await transferFromPlannedPage(page)

    // Then: sehe ich die Einkaufsliste
    await expectShoppingListPage(page)

    // And: zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge
    const expected: readonly ShoppingListRow[] = [
      { name: 'Eier', quantity: '3 Stück' },
      { name: 'Kartoffeln', quantity: '1000 g' },
      { name: 'Mehl', quantity: '250 g' },
      { name: 'Milch', quantity: '0,5 l' },
      { name: 'Salz', quantity: '–' },
    ]
    await expectShoppingList(page, expected)

    // When: ich die Seite neu lade
    await page.reload()

    // Then: zeigt die Einkaufsliste genau dieselben Einträge in derselben Reihenfolge
    await expectShoppingList(page, expected)

    // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
    await navEntry(page, 'Vorgemerkt').click()

    // Then: zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen" in dieser Reihenfolge
    await expect(plannedEntries(page)).toHaveText([exactly('Kartoffelsuppe'), exactly('Pfannkuchen')])
  })

  // Szenario: Dieselbe Zutat aus mehreren Rezepten steht einmal mit der Gesamtmenge da
  test('US201_HappyPath_GenerateShoppingList_SameIngredientInTwoRecipes_ShowsOneEntryWithTotal', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" mit den Zutaten "250 g Mehl" und "0,5 l Milch" ist vorgemerkt
    // And: das Rezept "Waffeln" mit den Zutaten "300 g Mehl" und "100 g Butter" ist vorgemerkt
    const ids = await seedRecipesWithIngredientsViaApi(
      request,
      { title: 'Pfannkuchen', lines: ['250 g Mehl', '0,5 l Milch'] },
      { title: 'Waffeln', lines: ['300 g Mehl', '100 g Butter'] },
    )
    await Promise.all(ids.map((id) => planRecipeViaApi(request, id)))

    // When: ich zur Vorgemerkt-Seite navigiere / And: ich auf "Auf die Einkaufsliste" klicke
    await transferFromPlannedPage(page)

    // Then: zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge
    await expectShoppingList(page, [
      { name: 'Butter', quantity: '100 g' },
      { name: 'Mehl', quantity: '550 g' },
      { name: 'Milch', quantity: '0,5 l' },
    ])
  })

  // Szenario: Die Einkaufsliste bleibt bis zum erneuten Übernehmen unverändert, das sie dann ersetzt
  test('US201_HappyPath_GenerateShoppingList_PlannedRecipesChangedAfterwards_KeepsListUntilReplaced', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" mit den Zutaten "250 g Mehl" und "0,5 l Milch" ist vorgemerkt
    // And: das Rezept "Kartoffelsuppe" mit den Zutaten "1000 g Kartoffeln" und "Salz" ist vorgemerkt
    // And: das Rezept "Linsensalat" mit der Zutat "200 g Linsen" existiert
    const [pancakesId, soupId, lentilsId] = await seedRecipesWithIngredientsViaApi(
      request,
      { title: 'Pfannkuchen', lines: ['250 g Mehl', '0,5 l Milch'] },
      { title: 'Kartoffelsuppe', lines: ['1000 g Kartoffeln', 'Salz'] },
      { title: 'Linsensalat', lines: ['200 g Linsen'] },
    )
    await planRecipeViaApi(request, pancakesId)
    await planRecipeViaApi(request, soupId)

    // And: die Zutaten der vorgemerkten Rezepte sind auf die Einkaufsliste übernommen
    await generateShoppingListViaApi(request)

    // And: danach ist "Kartoffelsuppe" nicht mehr vorgemerkt und "Linsensalat" vorgemerkt
    await unplanRecipeViaApi(request, soupId)
    await planRecipeViaApi(request, lentilsId)

    // When: ich zur Einkaufsliste navigiere
    await page.goto('/shopping-list')

    // Then: zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge
    await expectShoppingList(page, [
      { name: 'Kartoffeln', quantity: '1000 g' },
      { name: 'Mehl', quantity: '250 g' },
      { name: 'Milch', quantity: '0,5 l' },
      { name: 'Salz', quantity: '–' },
    ])

    // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke / And: ich auf "Auf die Einkaufsliste" klicke
    await navEntry(page, 'Vorgemerkt').click()
    await clickToShoppingList(page)

    // Then: zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge
    const replaced: readonly ShoppingListRow[] = [
      { name: 'Linsen', quantity: '200 g' },
      { name: 'Mehl', quantity: '250 g' },
      { name: 'Milch', quantity: '0,5 l' },
    ]
    await expectShoppingList(page, replaced)

    // When: ich die Seite neu lade
    await page.reload()

    // Then: zeigt die Einkaufsliste genau dieselben Einträge in derselben Reihenfolge
    await expectShoppingList(page, replaced)
  })
})

// @US-201-edge-case
test.describe('US201_EdgeCase: Übernehmen', () => {
  // Beispiel-Spalten = Spalten der Beispieltabelle im Feature-File.
  const withoutQuantityExamples = [
    { pancakesLine: '50 g Zucker', wafflesLine: 'Zucker', name: 'Zucker', quantity: '50 g' },
    { pancakesLine: 'Zucker', wafflesLine: '50 g Zucker', name: 'Zucker', quantity: '50 g' },
    { pancakesLine: 'Salz', wafflesLine: 'Salz', name: 'Salz', quantity: '–' },
  ] as const
  withoutQuantityExamples.forEach(({ pancakesLine, wafflesLine, name, quantity }) => {
    // Szenario: Zutaten ohne Menge auf der Einkaufsliste
    // Beispiel: alle
    test(`US201_EdgeCase_GenerateShoppingList_IngredientWithoutQuantity_ShowsTotalOrNoQuantity (${pancakesLine} + ${wafflesLine})`, async ({ page, request }) => {
      // Given: das Rezept "Pfannkuchen" mit der Zutat "<Zeile Pfannkuchen>" ist vorgemerkt
      // And: das Rezept "Waffeln" mit der Zutat "<Zeile Waffeln>" ist vorgemerkt
      await planPancakesAndWaffles(request, pancakesLine, wafflesLine)

      // When: ich zur Vorgemerkt-Seite navigiere / And: ich auf "Auf die Einkaufsliste" klicke
      await transferFromPlannedPage(page)

      // Then: zeigt die Einkaufsliste genau den Eintrag "<Zutat>" mit der Menge "<Menge>"
      await expectShoppingList(page, [{ name, quantity }])
    })
  })

  // Beispiel-Spalten = Spalten der Beispieltabelle im Feature-File; `fall` ist die Spalte „Fall“.
  const notationExamples = [
    { pancakesLine: '0,1 l Milch', wafflesLine: '0,2 l Milch', name: 'Milch', quantity: '0,3 l', fall: 'exakt dezimal addiert' },
    { pancakesLine: '0,125 l Milch', wafflesLine: '0,375 l Milch', name: 'Milch', quantity: '0,5 l', fall: 'keine Nullen am Ende' },
    { pancakesLine: '0,5 l Milch', wafflesLine: '0,5 l Milch', name: 'Milch', quantity: '1 l', fall: 'ganze Zahl ohne Komma' },
    { pancakesLine: '0,125 l Milch', wafflesLine: '0,25 l Milch', name: 'Milch', quantity: '0,375 l', fall: 'drei Nachkommastellen bleiben' },
    { pancakesLine: '6000 g Mehl', wafflesLine: '5000 g Mehl', name: 'Mehl', quantity: '11000 g', fall: 'über dem Rezept-Maximum, ohne Tausenderpunkt' },
  ] as const
  notationExamples.forEach(({ pancakesLine, wafflesLine, name, quantity, fall }) => {
    // Szenario: Gesamtmengen stehen in deutscher Schreibweise da
    // Beispiel: alle
    test(`US201_EdgeCase_GenerateShoppingList_TotalQuantity_ShowsGermanNotation (${fall})`, async ({ page, request }) => {
      // Given: das Rezept "Pfannkuchen" mit der Zutat "<Zeile Pfannkuchen>" ist vorgemerkt
      // And: das Rezept "Waffeln" mit der Zutat "<Zeile Waffeln>" ist vorgemerkt
      await planPancakesAndWaffles(request, pancakesLine, wafflesLine)

      // When: ich zur Vorgemerkt-Seite navigiere / And: ich auf "Auf die Einkaufsliste" klicke
      await transferFromPlannedPage(page)

      // Then: zeigt die Einkaufsliste genau den Eintrag "<Zutat>" mit der Menge "<Menge>"
      await expectShoppingList(page, [{ name, quantity }])
    })
  })
})

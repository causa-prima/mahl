import { test, expect } from './fixtures'
import { seedIngredientViaApi } from './api/ingredientsApi'
import type { APIRequestContext, Page } from '@playwright/test'
import { createRecipeViaApi, seedRecipesWithSaltViaApi } from './api/recipesApi'

// @US-602-happy-path
test.describe('US602_HappyPath: Rezepte erfassen', () => {
  // Szenario: Rezept-Liste ist leer wenn keine Rezepte vorhanden sind
  test('US602_HappyPath_GetRecipes_EmptyDb_ShowsEmptyList', async ({ page }) => {
    // Given: keine Rezepte vorhanden (DB-Reset der Auto-Fixture)
    // When: ich zur Rezepte-Seite navigiere
    // Die Antwort des Listen-GET wird abgewartet und ihr Status geprüft: Solange ein fehlgeschlagenes
    // GET im Frontend als leere Liste erscheint (TD-S083-1) und die Ladephase denselben Leerzustand
    // zeigt (TD-S101-1), belegte der Hinweis allein weder, dass das Backend geantwortet hat, noch,
    // dass die Seite fertig geladen ist.
    const recipesResponse = page.waitForResponse((response) => new URL(response.url()).pathname === '/api/recipes')
    await page.goto('/recipes')
    expect((await recipesResponse).status()).toBe(200)

    // Then: Hinweis und Button sind sichtbar
    await expect(page.getByText('Noch keine Rezepte angelegt.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Rezept anlegen' })).toBeVisible()
  })

  // Szenario: Rezept anlegen
  test('US602_HappyPath_CreateRecipe_ValidData_ShowsDetailAndAppearsInList', async ({ page, request }) => {
    // Given: die Zutaten "Mehl" (g), "Milch" (ml) und "Salz" (g) existieren
    await seedIngredientViaApi(request, 'Mehl', 'g')
    await seedIngredientViaApi(request, 'Milch', 'ml')
    await seedIngredientViaApi(request, 'Salz', 'g')

    // When: ich zur Rezepte-Seite navigiere und auf "Rezept anlegen" klicke
    await page.goto('/recipes')
    await page.getByRole('button', { name: 'Rezept anlegen' }).click()
    // When: Titel, Zutaten (eine je Zeile) und zwei Schritte eingeben, dann speichern
    await page.getByLabel('Titel').fill('Pfannkuchen')
    await page.getByLabel('Zutaten').fill('Salz\n250 g Mehl\n500 ml Milch')
    await page.getByLabel('Schritt 1').fill('Mehl und Milch verrühren.')
    await page.getByRole('button', { name: 'Schritt hinzufügen' }).click()
    await page.getByLabel('Schritt 2').fill('In der Pfanne ausbacken.')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: die Detailansicht des Rezepts "Pfannkuchen" (eigene Adresse, ADR-S135-5)
    await expect(page).toHaveURL(/\/recipes\/[0-9a-f-]{36}$/)
    await expect(page.getByRole('heading', { name: 'Pfannkuchen' })).toBeVisible()
    // Then: die Zutaten in der eingegebenen Reihenfolge, so angezeigt wie eingegeben
    await expect(page.getByRole('list', { name: 'Zutaten' }).getByRole('listitem'))
      .toHaveText(['Salz', '250 g Mehl', '500 ml Milch'])
    // Then: die Schritte als einzelne Einträge mit sichtbarer Nummer – geprüft wird der Text, nicht
    //   ein Listen-Marker per CSS, der im Text nicht vorkommt (sichtbares Signal, e2e-testing.md)
    await expect(page.getByRole('list', { name: 'Zubereitung' }).getByRole('listitem'))
      .toHaveText([/^1\D+Mehl und Milch verrühren\.$/, /^2\D+In der Pfanne ausbacken\.$/])

    // Then: "Pfannkuchen" steht genau einmal in der Rezept-Liste (die Liste hat genau diesen Eintrag)
    await page.goto('/recipes')
    await expect(page.getByRole('list', { name: 'Rezepte' }).getByRole('listitem')).toHaveText(['Pfannkuchen'])
  })

  // Szenario: Mehrere Rezepte erscheinen alphabetisch sortiert
  // Die Anlege-Reihenfolge weicht von der erwarteten ab, und die Titel prüfen jeden Teil der Regel
  // (deutsches Locale, ohne Unterschied der Groß-/Kleinschreibung, Umlaut wie Grundbuchstabe): Nach
  // Bytes sortiert stünde "apfelstrudel" hinter "Zwiebelkuchen", "Ölkuchen" am Ende und "Möhrensuppe"
  // hinter "Mohrrübeneintopf"; mit Ö als „oe" stünde "Möhrensuppe" vor "Mohnkuchen".
  test('US602_HappyPath_GetRecipes_MultipleRecipes_AppearAlphabeticallySorted', async ({ page, request }) => {
    // Given: die Rezepte "Zwiebelkuchen", "Mohrrübeneintopf", "Ölkuchen", "apfelstrudel", "Möhrensuppe",
    //   "Brot" und "Mohnkuchen" existieren
    await seedRecipesWithSaltViaApi(request, 'Zwiebelkuchen', 'Mohrrübeneintopf', 'Ölkuchen', 'apfelstrudel', 'Möhrensuppe', 'Brot', 'Mohnkuchen')

    // When: ich zur Rezepte-Seite navigiere
    await page.goto('/recipes')

    // Then: die Rezept-Liste zeigt genau diese Einträge in dieser Reihenfolge
    await expect(page.getByRole('list', { name: 'Rezepte' }).getByRole('listitem'))
      .toHaveText(['apfelstrudel', 'Brot', 'Mohnkuchen', 'Möhrensuppe', 'Mohrrübeneintopf', 'Ölkuchen', 'Zwiebelkuchen'])
  })
})

// Given beider Detail-Szenarien: zwei Rezepte, damit ein falsch geladenes Rezept auffällt – „Brot"
// steht in der Liste vor „Pfannkuchen", und „500 g Weizenmehl" erscheint, wenn die Zutaten nicht nach
// Rezept gefiltert werden. Gibt die Id von „Pfannkuchen" zurück (Ziel des Direktlinks).
async function seedPancakesAndBread(request: Readonly<APIRequestContext>): Promise<string> {
  await seedIngredientViaApi(request, 'Mehl', 'g')
  await seedIngredientViaApi(request, 'Weizenmehl', 'g')
  const pancakesId = await createRecipeViaApi(request, { title: 'Pfannkuchen', ingredients: '250 g Mehl', instruction: 'Teig rühren.' })
  await createRecipeViaApi(request, { title: 'Brot', ingredients: '500 g Weizenmehl', instruction: 'Teig kneten.' })
  return pancakesId
}

// Then beider Detail-Szenarien: die Detailansicht von „Pfannkuchen" mit genau seiner Zutat. toHaveText
// mit Array pinnt die Anzahl – „zeigt sie nicht die Zutat '500 g Weizenmehl'" ist damit mitgeprüft.
async function expectPancakesDetail(page: Readonly<Page>): Promise<void> {
  await expect(page.getByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeVisible()
  await expect(page.getByRole('list', { name: 'Zutaten' }).getByRole('listitem')).toHaveText(['250 g Mehl'])
}

// @US-602-happy-path
test.describe('US602_HappyPath: Rezept-Detailansicht', () => {
  // Szenario: Rezept aus der Rezept-Liste öffnen
  test('US602_HappyPath_OpenRecipe_FromList_ShowsDetailOfClickedRecipe', async ({ page, request }) => {
    // Given: die Rezepte "Pfannkuchen" (250 g Mehl, „Teig rühren.") und "Brot" (500 g Weizenmehl, „Teig kneten.")
    await seedPancakesAndBread(request)

    // When: ich zur Rezepte-Seite navigiere und auf "Pfannkuchen" klicke
    await page.goto('/recipes')
    await page.getByRole('link', { name: 'Pfannkuchen' }).click()

    // Then: die Detailansicht von "Pfannkuchen" mit der Zutat "250 g Mehl" und ohne "500 g Weizenmehl"
    await expectPancakesDetail(page)
    // Then: Schritt 1 "Teig rühren." – geprüft wird der sichtbare Text samt Nummer (e2e-testing.md)
    await expect(page.getByRole('list', { name: 'Zubereitung' }).getByRole('listitem'))
      .toHaveText([/^1\D+Teig rühren\.$/])
  })

  // Szenario: Rezept per Direktlink aufrufen
  test('US602_HappyPath_OpenRecipe_ByDirectLinkInNewWindow_ShowsDetail', async ({ context, request }) => {
    // Given: die Rezepte "Pfannkuchen" und "Brot" existieren
    const pancakesId = await seedPancakesAndBread(request)

    // When: ich den Direktlink des Rezepts "Pfannkuchen" in einem neuen Browserfenster öffne – eine
    //   neue Seite ohne vorher geladene Anwendung; der Direktlink ist die Adresse /recipes/{id} (ADR-S135-5)
    const newWindow = await context.newPage()
    await newWindow.goto(`/recipes/${pancakesId}`)

    // Then: die Detailansicht von "Pfannkuchen" mit der Zutat "250 g Mehl" und ohne "500 g Weizenmehl"
    await expectPancakesDetail(newWindow)
  })
})

// @US-602-error – eine Zeile je Beispiel der Scenario Outline
test.describe('US602_Error: Direktlink ins Leere', () => {
  const links = [
    { kennung: 'einer gültig aufgebauten, unbekannten Kennung', id: '01900000-0000-7000-8000-000000000000' },
    { kennung: 'einer ungültigen Kennung', id: 'keine-kennung' },
  ] as const
  links.forEach(({ kennung, id }) => {
    // Szenario: Direktlink auf ein Rezept, das es nicht gibt
    test(`US602_Error_OpenRecipe_UnknownLink_ShowsNotFoundAndWayBack (${kennung})`, async ({ page }) => {
      // When: ich einen Rezept-Link mit <Kennung> öffne
      await page.goto(`/recipes/${id}`)

      // Then: sehe ich den Hinweis "Rezept nicht gefunden."
      await expect(page.getByText('Rezept nicht gefunden.')).toBeVisible()

      // When: ich auf "Zur Rezept-Liste" klicke
      await page.getByRole('link', { name: 'Zur Rezept-Liste' }).click()

      // Then: sehe ich die Rezept-Liste
      await expect(page).toHaveURL(/\/recipes$/)
      await expect(page.getByRole('heading', { level: 1, name: 'Rezepte' })).toBeVisible()
    })
  })
})

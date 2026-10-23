import { test, expect } from './fixtures'
import { seedIngredientViaApi } from './api/ingredientsApi'

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
})

import { test, expect } from '@playwright/test'

// @US-904-happy-path
test.describe('US904_HappyPath: Zutaten verwalten', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ingredients')
  })

  // Szenario: Zutaten-Liste ist leer wenn keine Zutaten vorhanden sind
  test('US904_HappyPath_GetIngredients_EmptyDb_ShowsEmptyList', async ({ page }) => {
    // Given + When: keine Zutaten vorhanden, Zutaten-Seite geöffnet (Background im beforeEach)
    // Then: Hinweis und Button sind sichtbar
    await expect(page.getByText('Noch keine Zutaten angelegt.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Zutat anlegen' })).toBeVisible()
  })

  // Szenario: Felder sind beim Öffnen des Dialogs leer
  test('US904_HappyPath_OpenCreateDialog_FieldsAreEmpty', async ({ page }) => {
    // When: ich auf "Zutat anlegen" klicke
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()

    // Then: Name-Feld und Einheit-Feld sind leer
    await expect(page.getByLabel('Name')).toHaveValue('')
    await expect(page.getByLabel('Einheit')).toHaveValue('')
  })

  // Szenario: Felder sind nach Abbrechen beim erneuten Öffnen wieder leer
  test('US904_HappyPath_ReopenDialogAfterCancel_FieldsAreEmpty', async ({ page }) => {
    // When: Dialog öffnen, beide Felder befüllen, abbrechen, erneut öffnen
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Knoblauch')
    await page.getByLabel('Einheit').fill('Zehen')
    await page.getByRole('button', { name: 'Abbrechen' }).click()
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()

    // Then: Name-Feld und Einheit-Feld sind wieder leer
    await expect(page.getByLabel('Name')).toHaveValue('')
    await expect(page.getByLabel('Einheit')).toHaveValue('')
  })

  // Szenario: Abbrechen schließt Dialog und verwirft Eingaben
  test('US904_HappyPath_CancelDialog_ClosesDialogAndDiscardsInput', async ({ page }) => {
    // When: Dialog öffnen, Name eingeben, abbrechen
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Oregano')
    await page.getByRole('button', { name: 'Abbrechen' }).click()

    // Then: Dialog ist geschlossen -> nicht mehr sichtbar
    await expect(page.getByRole('dialog')).toBeHidden()
    // Then: "Oregano" ist nicht in der Zutaten-Liste
    await expect(page.getByText('Oregano')).toHaveCount(0)
  })

  // Szenario: Zutat anlegen
  test('US904_HappyPath_CreateIngredient_ValidData_IngredientAppearsInList', async ({ page }) => {
    // When: Dialog öffnen, Name + Einheit eingeben, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Tomaten')
    await page.getByLabel('Einheit').fill('Stück')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: "Tomaten" mit Einheit "Stück" erscheint in der Zutaten-Liste
    await expect(page.getByTestId('ingredient-list').getByText('Tomaten')).toBeVisible()
    await expect(page.getByTestId('ingredient-list').getByText('Stück')).toBeVisible()
    // Then: der "Zutat anlegen"-Dialog ist geschlossen
    await expect(page.getByRole('dialog')).toBeHidden()
  })
})

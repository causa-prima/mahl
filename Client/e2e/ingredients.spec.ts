import { test, expect, type Page } from '@playwright/test'

// Erfasst die Zutaten-Liste samt Ausgangs-Anzahl für "Liste bleibt unverändert"-Assertions.
// networkidle: initiales GET abklingen lassen – während des Ladens zeigt die Seite denselben
// Empty-State wie bei echt-leerer Liste, ein zu früher Count wäre fälschlich 0.
// includeHidden: der gleich offene Dialog (MUI Modal) setzt den Hintergrund inkl. Liste auf
// aria-hidden -> Vor- und Nach-Count brauchen dieselbe Basis.
async function captureIngredientList(page: Readonly<Page>) {
  await page.waitForLoadState('networkidle')
  const listItems = page.getByTestId('ingredient-list').getByRole('listitem', { includeHidden: true })
  return { listItems, itemsBefore: await listItems.count() }
}

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

// @US-904-error
test.describe('US904_Error: Zutaten-Validierung', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ingredients')
  })

  // Szenario: Zutat mit leerem Namen anlegen schlägt fehl
  test('US904_Error_CreateIngredient_EmptyName_ShowsErrorAndListUnchanged', async ({ page }) => {
    // Given: Ausgangs-Anzahl der Zutaten (für "bleibt unverändert")
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, keinen Namen eingeben, "g" als Einheit, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: Fehlermeldung erscheint
    await expect(page.getByText('Name darf nicht leer sein.')).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert (DB-Ausgangszustand nach Fehler,
    // e2e-testing.md "Assertion-Tiefe"). toHaveCount retryt, bis der Zustand stabil ist.
    await expect(listItems).toHaveCount(itemsBefore)
  })

  // Szenario: Zutat mit Namen aus nur Leerzeichen anlegen schlägt fehl
  test('US904_Error_CreateIngredient_WhitespaceName_ShowsErrorAndListUnchanged', async ({ page }) => {
    // Given: Ausgangs-Anzahl der Zutaten (für "bleibt unverändert")
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, nur Leerzeichen als Name, "g" als Einheit, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('   ')
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: dieselbe Fehlermeldung wie bei leerem Namen erscheint (beobachtbares Verhalten).
    // Das serverseitige Trimming (Whitespace -> leer, ADR-S051-1) selbst prüft der Backend-Test.
    await expect(page.getByText('Name darf nicht leer sein.')).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert
    await expect(listItems).toHaveCount(itemsBefore)
  })

  // Szenario: Zutat mit leerer Einheit anlegen schlägt fehl
  test('US904_Error_CreateIngredient_EmptyUnit_ShowsErrorAndListUnchanged', async ({ page }) => {
    // Given: Ausgangs-Anzahl der Zutaten (für "bleibt unverändert")
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, "Salz" als Name, keine Einheit, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Salz')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: Fehlermeldung erscheint
    await expect(page.getByText('Einheit darf nicht leer sein.')).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert
    await expect(listItems).toHaveCount(itemsBefore)
  })

  // Szenario: Zutat mit Einheit aus nur Leerzeichen anlegen schlägt fehl
  test('US904_Error_CreateIngredient_WhitespaceUnit_ShowsErrorAndListUnchanged', async ({ page }) => {
    // Given: Ausgangs-Anzahl der Zutaten (für "bleibt unverändert")
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, "Salz" als Name, nur Leerzeichen als Einheit, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Salz')
    await page.getByLabel('Einheit').fill('   ')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: dieselbe Fehlermeldung wie bei leerer Einheit erscheint (beobachtbares Verhalten).
    // Das serverseitige Trimming (Whitespace -> leer, ADR-S051-1) selbst prüft der Backend-Test.
    await expect(page.getByText('Einheit darf nicht leer sein.')).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert
    await expect(listItems).toHaveCount(itemsBefore)
  })

  // Szenario: Beide Pflichtfelder leer – beide Fehlermeldungen erscheinen gleichzeitig
  test('US904_Error_CreateIngredient_BothFieldsEmpty_ShowsBothErrorsAndListUnchanged', async ({ page }) => {
    // Given: Ausgangs-Anzahl der Zutaten (für "bleibt unverändert")
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, weder Name noch Einheit eingeben, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: BEIDE Fehlermeldungen erscheinen gleichzeitig (collect-all, ADR-S000-1/S090-1).
    // Treibt den Backend-Merge: kurzschließende Validierung lieferte nur die Name-Meldung.
    await expect(page.getByText('Name darf nicht leer sein.')).toBeVisible()
    await expect(page.getByText('Einheit darf nicht leer sein.')).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert
    await expect(listItems).toHaveCount(itemsBefore)
  })
})

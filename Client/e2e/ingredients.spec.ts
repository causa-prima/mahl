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

// > MUI theme.transitions.duration.leavingScreen (225ms, MUI-Default) + Marge. Settle-Fenster
// VOR Assertions, die sich auf "Dialog noch sichtbar" verlassen: eine (fälschliche) Close-
// Transition bräuchte diese Zeit, um zu greifen – ohne das Fenster wäre die Assertion ein
// Transition-Artefakt statt echtes Verhalten.
const DIALOG_EXIT_SETTLE_MS = 400

// Rule-of-Three: die 3 Pending-Tests unten (Speichern-/Abbrechen-Button disabled, Escape
// schließt nicht) teilen dieses Setup – künstlich verzögerter POST (damit der Pending-Zustand
// vor der Antwort beobachtbar ist) + Dialog öffnen/befüllen/Speichern-Klick.
async function submitWithDelayedPost(page: Readonly<Page>): Promise<void> {
  await page.route('**/api/ingredients', async (route) => {
    if (route.request().method() !== 'POST') { await route.continue(); return }
    await new Promise((resolve) => setTimeout(resolve, 1000))
    await route.continue()
  })

  await page.getByRole('button', { name: 'Zutat anlegen' }).click()
  await page.getByLabel('Name').fill('Tomaten')
  await page.getByLabel('Einheit').fill('Stück')
  await page.getByRole('button', { name: 'Speichern' }).click()
}

// ADR-S084-4 Addendum: per-Test-DB-Isolation. Vor JEDEM Test die E2E-DB leeren (E2E-only Reset-Endpoint,
// nur bei ASPNETCORE_ENVIRONMENT=E2E gemappt) -> jeder Test startet gegen eine leere DB, keine
// Residual-Akkumulation über Läufe/Tests hinweg. Auf Datei-Ebene registriert -> läuft vor den
// describe-eigenen beforeEach (page.goto), also VOR dem initialen GET. (Bei einem zweiten Spec-File
// nach `e2e/fixtures.ts` als geteilte Auto-Fixture ziehen, damit kein Spec den Reset vergessen kann.)
test.beforeEach(async ({ request }) => {
  const res = await request.post('http://localhost:5059/api/test/reset')
  // Laut scheitern, falls der Reset-Endpoint nicht existiert (falsche Umgebung) statt still zu no-op'en.
  expect(res.status(), 'Reset-Endpoint muss in der E2E-Umgebung 204 liefern').toBe(204)
})

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

  // Szenario: Pflichtfelder im Dialog sind als solche markiert
  test('US904_HappyPath_OpenCreateDialog_RequiredFieldsAreMarked', async ({ page }) => {
    // When: ich auf "Zutat anlegen" klicke
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()

    // Then: Name-Feld und Einheit-Feld sind als Pflichtfeld markiert. Geprüft wird das
    //   USER-SICHTBARE Signal – der Asterisk im Label – als maßgebliche Beobachtung von
    //   "markiert" (UX-Guideline Prinzip 8). Zusätzlich die native `required`-Property, die
    //   die semantische/a11y-Zuschreibung absichert (aria-required) und den Mutanten
    //   "required-Prop entfernt" tötet. getByLabel matcht per Substring weiter "Name"/"Einheit".
    const dialog = page.getByRole('dialog')
    await expect(dialog.locator('label').filter({ hasText: /^Name/ })).toContainText('*')
    await expect(dialog.locator('label').filter({ hasText: /^Einheit/ })).toContainText('*')
    await expect(page.getByLabel('Name')).toHaveJSProperty('required', true)
    await expect(page.getByLabel('Einheit')).toHaveJSProperty('required', true)
  })

  // Szenario: Beim Öffnen des Dialogs liegt der Fokus auf dem ersten Feld
  test('US904_HappyPath_OpenCreateDialog_FocusOnFirstField', async ({ page }) => {
    // When: ich auf "Zutat anlegen" klicke
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()

    // Then: das Name-Feld ist das erste Eingabefeld im Dialog (DOM-Reihenfolge == visuelle
    //   Reihenfolge, UX-Guideline: Felder nicht per CSS umsortieren). Regex /Name/ ist robust,
    //   falls der Pflicht-Asterisk in den Accessible Name einfließt ("Name *").
    const inputs = page.getByRole('dialog').getByRole('textbox')
    await expect(inputs.first()).toHaveAccessibleName(/Name/)
    // Then: das Name-Feld hat den Fokus
    await expect(page.getByLabel('Name')).toBeFocused()
  })

  // Szenario: Speichern-Button ist während des Speicherns deaktiviert
  test('US904_HappyPath_SaveInFlight_SaveButtonIsDisabled', async ({ page }) => {
    // Given + When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper) –
    //   der POST bleibt künstlich verzögert, das Pending-Fenster ist so beobachtbar.
    await submitWithDelayedPost(page)

    // Then: der "Speichern"-Button ist deaktiviert, solange die Antwort aussteht
    await expect(page.getByRole('button', { name: 'Speichern' })).toBeDisabled()
  })

  // Szenario: Abbrechen ist während des Speicherns deaktiviert
  test('US904_HappyPath_SaveInFlight_CancelButtonIsDisabled', async ({ page }) => {
    // Given + When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper)
    await submitWithDelayedPost(page)

    // Then: der "Abbrechen"-Button ist deaktiviert, solange die Antwort aussteht
    await expect(page.getByRole('button', { name: 'Abbrechen' })).toBeDisabled()
  })

  // Szenario: Der Dialog lässt sich während des Speicherns nicht per Escape schließen
  test('US904_HappyPath_SaveInFlight_EscapeDoesNotCloseDialog', async ({ page }) => {
    // Given + When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper)
    await submitWithDelayedPost(page)
    // When (Zwischenzustand, Parität zum Component-Test): Pending-Zustand ist erreicht,
    //   bevor Escape gedrückt wird – schließt den Race, in dem Escape vor dem Pending-Zustand
    //   feuert und der Guard das Fenster verpasst.
    await expect(page.getByRole('button', { name: 'Speichern' })).toBeDisabled()
    // When: ich Escape drücke – aus dem noch aktiven Name-Feld heraus (Fokus IM Dialog): sonst
    //   fiele der Fokus vom deaktivierten Speichern-Button auf <body> außerhalb des Modals, und
    //   der MUI-Escape-Handler würde gar nicht erst erreicht -> der Test wäre ohne echten Guard
    //   grün (Fokus-Artefakt statt Verhalten). So schlägt Escape ohne Guard tatsächlich bis zum
    //   onClose durch.
    await page.getByLabel('Name').press('Escape')

    // Then: der "Zutat anlegen"-Dialog ist weiterhin geöffnet, solange die Antwort aussteht.
    //   Settle-Fenster VOR der Assertion (s. DIALOG_EXIT_SETTLE_MS): eine (fälschliche) Escape-
    //   getriebene Close-Transition hätte damit Zeit zu greifen – sonst sähe toBeVisible den
    //   Dialog während des Ausblendens noch fälschlich als sichtbar. DIALOG_EXIT_SETTLE_MS
    //   liegt sicher im 1000-ms-Pending-Fenster, der POST ist also noch offen: das Einzige, was
    //   den Dialog schließen könnte, wäre ein fehlender Escape-Guard.
    await page.waitForTimeout(DIALOG_EXIT_SETTLE_MS)
    await expect(page.getByRole('dialog')).toBeVisible()
  })

  // Szenario: Der Dialog lässt sich während des Speicherns nicht per Backdrop-Klick schließen
  test('US904_HappyPath_SaveInFlight_BackdropClickDoesNotCloseDialog', async ({ page }) => {
    // Given + When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper)
    await submitWithDelayedPost(page)
    // When (Zwischenzustand, Parität zum Escape-Test): Pending-Zustand ist erreicht, bevor
    //   der Backdrop-Klick erfolgt – schließt den Race, in dem der Klick vor dem Pending-Zustand
    //   feuert und der Guard das Fenster verpasst.
    await expect(page.getByRole('button', { name: 'Speichern' })).toBeDisabled()
    // When: ich neben den Dialog klicke. MUI löst den Backdrop-Klick über den Klick auf den
    //   `.MuiDialog-container` (role=presentation, füllt den Viewport, liegt ÜBER dem Backdrop)
    //   aus: nur ein Klick, dessen target === currentTarget (also der Container selbst, nicht das
    //   Paper), zählt als backdropClick. Position nahe der Ecke -> trifft den Container, nicht das
    //   zentrierte Paper. Ohne Guard triggert das MUIs onClose(reason='backdropClick').
    await page.locator('.MuiDialog-container').click({ position: { x: 5, y: 5 } })

    // Then: der "Zutat anlegen"-Dialog ist weiterhin geöffnet, solange die Antwort aussteht.
    //   Settle-Fenster VOR der Assertion (s. DIALOG_EXIT_SETTLE_MS, analog Escape-Test): eine
    //   (fälschliche) Close-Transition hätte damit Zeit zu greifen. Der POST ist im Pending-
    //   Fenster noch offen: das Einzige, was den Dialog schließen könnte, wäre ein fehlender Guard.
    await page.waitForTimeout(DIALOG_EXIT_SETTLE_MS)
    await expect(page.getByRole('dialog')).toBeVisible()
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

// @US-904-edge-case
test.describe('US904_EdgeCase: Zutaten verwalten', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ingredients')
  })

  // Szenario: Führende und nachfolgende Leerzeichen werden beim Speichern entfernt
  test('US904_EdgeCase_CreateIngredient_WhitespacePaddedInput_TrimmedValueAppearsInList', async ({ page }) => {
    // When: Dialog öffnen, Name + Einheit mit umgebenden Leerzeichen eingeben, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('  Oregano  ')
    await page.getByLabel('Einheit').fill('  g  ')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: der GETRIMMTE Name "Oregano" / die getrimmte Einheit "g" erscheinen in der Liste –
    // exakt, OHNE die gesendeten umgebenden Leerzeichen. Assertion-Technik: Regex statt String.
    // Playwrights String-Matcher (getByText / toHaveText('x')) normalisieren Whitespace IMMER
    // (auch exact:true trimmt) und könnten getrimmt/ungetrimmt nicht unterscheiden; eine Regex
    // matcht den rohen DOM-Text "as is" -> /^Oregano$/ schlägt bei "  Oregano  " fehl. exact:true
    // dient nur dem Lokalisieren der Zeile (normalisiert; "g" ist Substring von "Oregano" ->
    // sonst Strict-Mode-Kollision), die Regex prüft dann den ungetrimmten Rohtext.
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Oregano', { exact: true })).toHaveText(/^Oregano$/)
    await expect(list.getByText('g', { exact: true })).toHaveText(/^g$/)
    // Then: der "Zutat anlegen"-Dialog ist geschlossen
    await expect(page.getByRole('dialog')).toBeHidden()
  })

  // Szenario: Nach fehlgeschlagenem Speichern und Abbrechen ist der Dialog beim erneuten Öffnen fehlerfrei
  test('US904_EdgeCase_ReopenDialogAfterFailedSaveAndCancel_IsErrorFree', async ({ page }) => {
    // When: Dialog öffnen, nur Einheit "g" eingeben (Name bleibt leer), speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // When: die Fehlermeldung "Name darf nicht leer sein." erscheint (realer 422 vom Backend)
    await expect(page.getByText('Name darf nicht leer sein.')).toBeVisible()

    // When: ich auf "Abbrechen" klicke -> Dialog schließt (Close-Transition abwarten)
    await page.getByRole('button', { name: 'Abbrechen' }).click()
    await expect(page.getByRole('dialog')).toBeHidden()

    // When: ich erneut auf "Zutat anlegen" klicke
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()

    // Then: keine Fehlermeldung sichtbar (der alte Fehlerzustand ist zurückgesetzt)
    await expect(page.getByText('Name darf nicht leer sein.')).toHaveCount(0)
    // Then: das Name-Feld ist nicht als ungültig markiert (aria-invalid zurückgesetzt)
    await expect(page.getByLabel('Name')).toHaveAttribute('aria-invalid', 'false')
  })

  // Szenario: Name mit exakt 30 Zeichen wird akzeptiert
  test('US904_EdgeCase_CreateIngredient_NameExactly30Chars_AppearsInList', async ({ page }) => {
    // When: Dialog öffnen, einen Namen mit genau 30 Zeichen (Grenzwert, ADR-S051-3: max. 30
    //   ist gültig -> die Grenze liegt bei > 30, nicht >= 30), "g" als Einheit, speichern
    const nameWith30Chars = 'a'.repeat(30)
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill(nameWith30Chars)
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: die neue Zutat (30-Zeichen-Name) erscheint in der Zutaten-Liste
    await expect(page.getByTestId('ingredient-list').getByText(nameWith30Chars)).toBeVisible()
    // Then: der "Zutat anlegen"-Dialog ist geschlossen (Erfolgspfad)
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

  // Szenario: Zutat mit zu langem Namen anlegen schlägt fehl
  test('US904_Error_CreateIngredient_NameTooLong_ShowsErrorAndListUnchanged', async ({ page }) => {
    // Given: Ausgangs-Anzahl der Zutaten (für "bleibt unverändert")
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, einen Namen mit 31 Zeichen (> 30, ADR-S051-3), "g" als Einheit, speichern
    const nameWith31Chars = 'a'.repeat(31)
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill(nameWith31Chars)
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: Fehlermeldung erscheint (ADR-S051-2: fixer Text)
    await expect(page.getByText('Name darf maximal 30 Zeichen lang sein.')).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert (DB-Ausgangszustand nach Fehler)
    await expect(listItems).toHaveCount(itemsBefore)
  })
})

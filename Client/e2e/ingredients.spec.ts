import { test, expect, type Page, type APIRequestContext } from '@playwright/test'

// E2E-Backend (ASPNETCORE_URLS in playwright.config.ts). An einer Stelle statt mehrfach hartkodiert.
const E2E_API_BASE = 'http://localhost:5059'

// Low-Level-Seed über den API-Port: legt eine Zutat an und gibt Id + xmin-ETag zurück (der ETag
// wird für ein nachfolgendes If-Match beim DELETE gebraucht, ADR-S058-3). Gemeinsame Basis für
// alle Seed-Varianten und den Löschen·Konflikt-Test – so lebt der POST-201-Block an einer Stelle.
async function createIngredientViaApi(request: Readonly<APIRequestContext>, name: string, defaultUnit: string): Promise<{ id: string; etag: string }> {
  const response = await request.post(`${E2E_API_BASE}/api/ingredients`, { data: { name, defaultUnit } })
  expect(response.status(), 'Seed-Zutat muss angelegt werden (201)').toBe(201)
  const { id } = await response.json() as { id: string }
  return { id, etag: response.headers()['etag'] }
}

// Legt eine Zutat direkt über die API an (Vorbedingung "die Zutat X existiert"), vor dem Laden der
// Seite. Ein zweiter POST käme als Duplikat nicht durch – der direkte API-Seed ist der saubere Weg,
// den Ausgangszustand über den ausgehenden Port herzustellen. Id/ETag werden hier nicht gebraucht.
async function seedIngredientViaApi(request: Readonly<APIRequestContext>, name: string, defaultUnit: string): Promise<void> {
  await createIngredientViaApi(request, name, defaultUnit)
}

// Legt eine Zutat an und löscht sie direkt wieder (soft-delete) – Vorbedingung "die Zutat X
// existiert und wurde gelöscht". Der ETag aus dem POST-Response geht als If-Match ins DELETE
// (Plumbing: DELETE verlangt als mutierender Single-Resource-Endpoint einen If-Match, ADR-S058-1).
async function seedDeletedIngredientViaApi(request: Readonly<APIRequestContext>, name: string, defaultUnit: string): Promise<void> {
  const { id, etag } = await createIngredientViaApi(request, name, defaultUnit)
  const deleteResponse = await request.delete(`${E2E_API_BASE}/api/ingredients/${id}`, { headers: { 'If-Match': etag } })
  expect(deleteResponse.status(), 'Seed-Löschen muss gelingen (204)').toBe(204)
}

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
  const res = await request.post(`${E2E_API_BASE}/api/test/reset`)
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

  // Szenario: Einheit mit exakt 20 Zeichen wird akzeptiert
  test('US904_EdgeCase_CreateIngredient_UnitExactly20Chars_AppearsInList', async ({ page }) => {
    // When: Dialog öffnen, "Salz" als Name, eine Einheit mit genau 20 Zeichen (Grenzwert,
    //   ADR-S051-3: max. 20 ist gültig -> die Grenze liegt bei > 20, nicht >= 20), speichern
    const unitWith20Chars = 'a'.repeat(20)
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Salz')
    await page.getByLabel('Einheit').fill(unitWith20Chars)
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: die neue Zutat (mit 20-Zeichen-Einheit) erscheint in der Zutaten-Liste
    await expect(page.getByTestId('ingredient-list').getByText('Salz')).toBeVisible()
    await expect(page.getByTestId('ingredient-list').getByText(unitWith20Chars)).toBeVisible()
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
    // Then: der Fokus liegt auf dem Einheit-Feld. Es ist das erste (hier einzige) fehlerhafte
    //   Feld — Name "Salz" ist gültig (UX-Guideline Prinzip 8 "Fokus aufs erste fehlerhafte
    //   Feld" / TD-S094-1). Pinnt zugleich den "nur späteres Feld fehlerhaft"-Fall: der Fokus
    //   landet NICHT hart auf dem (visuell ersten) Name-Feld, sondern auf dem fehlerhaften.
    await expect(page.getByLabel('Einheit')).toBeFocused()
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
    // Then: der Fokus liegt auf dem Name-Feld. Beide Felder sind fehlerhaft -> "mehrere ->
    //   das erste" (UX-Guideline Prinzip 8 / TD-S094-1, Fokus-Priorität in DOM-Reihenfolge
    //   Name vor Einheit). Pinnt den Mehrfeld-Fall, den die Einzelfeld-Fokus-Tests nicht
    //   abdecken: ein Prioritäts-Swap im Fokus-Hook (Einheit vor Name) bliebe sonst
    //   unentdeckt (Stryker kann diesen menschlichen Refactor strukturell nicht fangen).
    await expect(page.getByLabel('Name')).toBeFocused()
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

  // Szenario: Zutat mit zu langer Einheit anlegen schlägt fehl
  test('US904_Error_CreateIngredient_UnitTooLong_ShowsErrorAndListUnchanged', async ({ page }) => {
    // Given: Ausgangs-Anzahl der Zutaten (für "bleibt unverändert")
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, "Salz" als Name, eine Einheit mit 21 Zeichen (> 20, ADR-S051-3), speichern
    const unitWith21Chars = 'a'.repeat(21)
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Salz')
    await page.getByLabel('Einheit').fill(unitWith21Chars)
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: Fehlermeldung erscheint (ADR-S051-2: fixer Text)
    await expect(page.getByText('Einheit darf maximal 20 Zeichen lang sein.')).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert (DB-Ausgangszustand nach Fehler)
    await expect(listItems).toHaveCount(itemsBefore)
  })
})

// @US-904-error: aktives Duplikat (run-6). Der Name-Eindeutigkeits-Check ist case-insensitiv und misst
// den getrimmten Namen (ADR-S051-3); die Fehlermeldung nennt den getrimmten *Request*-Wert (nicht den
// gespeicherten) und erscheint feld-keyed am Name-Feld als 422 (ADR-S004-1 Addendum S105 / ADR-S090-1).
// Die Duplikat-Zutat wird per API angelegt – VOR dem Laden der Seite, damit der initiale GET sie enthält
// (5059 = E2E-Backend wie im Reset-beforeEach). Explizite Tests pro Szenario (die `// Szenario:`-
// Traceability verlangt einen Kommentar je Test, daher keine Parametrisierungs-Schleife).
test.describe('US904_Error: Duplikat-Name', () => {
  // Szenario: Zutat mit bereits vorhandenem Namen anlegen schlägt fehl
  test('US904_Error_CreateIngredient_ExactDuplicateName_ShowsErrorAndListUnchanged', async ({ page, request }) => {
    // Given: die Zutat "Zucker" (g) existiert bereits (aktiv)
    await seedIngredientViaApi(request, 'Zucker', 'g')
    await page.goto('/ingredients')
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, denselben Namen "Zucker" (andere Einheit "kg") anlegen, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Zucker')
    await page.getByLabel('Einheit').fill('kg')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: Duplikat-Fehlermeldung mit dem eingegebenen Namen erscheint
    await expect(page.getByText("Eine Zutat mit dem Namen 'Zucker' existiert bereits.")).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert (kein zweiter Eintrag angelegt)
    await expect(listItems).toHaveCount(itemsBefore)
  })

  // Szenario: Zutat mit vorhandenem Namen in abweichender Schreibweise anlegen schlägt fehl
  // Umlaut "Öl"/"öl": prüft Case-Insensitivität UND das umlaut-faltende E2E-DB-Locale (ADR-S105-1) – der
  // einzige Test, der eine falsch konfigurierte docker-compose-Locale fängt (Server.Tests nutzt den Container-Default).
  test('US904_Error_CreateIngredient_CaseInsensitiveDuplicateName_ShowsErrorAndListUnchanged', async ({ page, request }) => {
    // Given: die Zutat "Öl" (ml) existiert bereits (aktiv)
    await seedIngredientViaApi(request, 'Öl', 'ml')
    await page.goto('/ingredients')
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, "öl" (nur Groß-/Kleinschreibung abweichend) anlegen, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('öl')
    await page.getByLabel('Einheit').fill('l')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: Duplikat-Fehlermeldung mit dem getippten Namen "öl" (case-insensitiv erkannt)
    await expect(page.getByText("Eine Zutat mit dem Namen 'öl' existiert bereits.")).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert (kein zweiter Eintrag angelegt)
    await expect(listItems).toHaveCount(itemsBefore)
  })

  // Szenario: Fehlermeldung bei Duplikat zeigt getrimmten Namen
  test('US904_Error_CreateIngredient_WhitespacePaddedDuplicateName_ShowsTrimmedNameError', async ({ page, request }) => {
    // Given: die Zutat "Tomaten" (Stück) existiert bereits (aktiv)
    await seedIngredientViaApi(request, 'Tomaten', 'Stück')
    await page.goto('/ingredients')
    const { listItems, itemsBefore } = await captureIngredientList(page)

    // When: Dialog öffnen, "tomaten " (mit Trailing-Space) anlegen, speichern
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('tomaten ')
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: die Meldung zeigt den GETRIMMTEN Namen "tomaten" (nicht "tomaten ")
    await expect(page.getByText("Eine Zutat mit dem Namen 'tomaten' existiert bereits.")).toBeVisible()
    // Then: die Zutaten-Liste bleibt unverändert (kein zweiter Eintrag angelegt)
    await expect(listItems).toHaveCount(itemsBefore)
  })
})

// @US-904-edge-case: run-10 „Löschen·Konflikt" (Singleton). Reiner API-Pfad – laut Feature-Kommentar gibt
// es keinen UI-Weg, den Lösch-Befehl erneut abzusenden; der Step mappt direkt auf DELETE /api/ingredients/{id}.
// ADR-S000-5: DELETE ist nicht-idempotent -> erneutes Löschen einer bereits soft-deleted Zutat gibt 404
// (nicht 204), damit ein doppelter Aufruf einen echten Fehler sichtbar macht. Die Fehlermeldung liegt im
// ProblemDetails-`detail` (ADR-S054-6).
// If-Match ist hier reines PLUMBING (wie Content-Type): DELETE verlangt als mutierender Single-Resource-
// Endpoint einen If-Match-Header (ADR-S058-1), sonst 428 – ohne ihn käme der Test nie zum 204/404 des
// Szenarios. Der xmin-ETag kommt aus dem POST-Response (ADR-S058-3). Das ETag-/If-Match-VERHALTEN selbst
// (428/412, POST liefert ETag) wird bewusst NICHT hier, sondern nur in Server.Tests geprüft – exakt wie
// der Collection-ETag (ETagMiddlewareTests). Beim erneuten Löschen dominiert der Not-Found-Check VOR dem
// If-Match-Check -> 404 (nicht 412), auch mit stale ETag.
test.describe('US904_EdgeCase: Löschen·Konflikt', () => {
  // Szenario: Bereits gelöschte Zutat erneut löschen schlägt fehl
  test('US904_EdgeCase_DeleteIngredient_AlreadyDeleted_Returns404NotFound', async ({ request }) => {
    // Given: die Zutat "Pfeffer" (g) existiert und wurde gelöscht (POST anlegen + erster DELETE = 204).
    //   Der ETag aus dem POST wird als If-Match mitgeschickt (Plumbing, s.o.).
    const { id, etag } = await createIngredientViaApi(request, 'Pfeffer', 'g')
    const firstDelete = await request.delete(`${E2E_API_BASE}/api/ingredients/${id}`, { headers: { 'If-Match': etag } })
    expect(firstDelete.status(), 'Erstes Löschen muss gelingen (204)').toBe(204)

    // When: ich den Lösch-Befehl für "Pfeffer" erneut absende (gleicher, nun stale ETag)
    const secondDelete = await request.delete(`${E2E_API_BASE}/api/ingredients/${id}`, { headers: { 'If-Match': etag } })

    // Then: 404 mit der Fehlermeldung "Zutat wurde nicht gefunden." (ADR-S000-5 / ProblemDetails detail);
    //   Not-Found dominiert vor If-Match -> 404, nicht 412.
    expect(secondDelete.status(), 'Erneutes Löschen muss fehlschlagen (404)').toBe(404)
    const body = await secondDelete.json() as { detail?: string }
    expect(body.detail).toBe('Zutat wurde nicht gefunden.')
  })
})

// @US-904-happy-path: run-7 „Liste". Die alphabetische Sortierung ist Backend-Verhalten
// (GET /api/ingredients OrderBy(name), TD-S084-2 – macht zugleich den Collection-Content-Hash-
// ETag erstmals deterministisch, ADR-S084-1/-2). Das Frontend rendert die Liste unverändert in
// der vom Server gelieferten Reihenfolge; die DOM-Reihenfolge ist die einzige E2E-beobachtbare
// Stelle der Sortierung. Seed VOR page.goto, damit der initiale GET die Zutaten enthält – daher
// eigenes describe ohne goto-beforeEach (analog zum Duplikat-Block).
test.describe('US904_HappyPath: Zutaten-Liste sortiert', () => {
  // Szenario: Mehrere Zutaten erscheinen alphabetisch sortiert
  test('US904_HappyPath_GetIngredients_MultipleIngredients_AppearAlphabeticallySorted', async ({ page, request }) => {
    // Given: "Zwiebel" (Stück) und "Apfel" (Stück) existieren – bewusst in NICHT-alphabetischer
    //   Anlege-Reihenfolge (Zwiebel vor Apfel), damit die alphabetische Sortierung die Insertion-
    //   Order nachweislich überschreibt (ohne OrderBy stünde Zwiebel vor Apfel).
    await seedIngredientViaApi(request, 'Zwiebel', 'Stück')
    await seedIngredientViaApi(request, 'Apfel', 'Stück')
    await page.goto('/ingredients')
    // Initialen GET settlen lassen (Seed sichtbar), BEVOR der UI-POST feuert – umgeht das
    // Cold-Start-Race (TD-S083-3), ohne es zu beheben (der POST koalesziert sonst mit dem
    // noch in-flight-GET).
    await expect(page.getByTestId('ingredient-list').getByText('Apfel')).toBeVisible()

    // When: ich "Mehl" (g) über die UI anlege
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Mehl')
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()
    // Erfolgspfad: der Dialog schließt nach dem POST – erst dann steht die neu geladene Liste.
    await expect(page.getByRole('dialog')).toBeHidden()

    // Then: die Zutaten-Liste zeigt exakt "Apfel", "Mehl", "Zwiebel" in dieser Reihenfolge.
    //   toHaveText mit Array pinnt Reihenfolge UND Anzahl (genau 3 Einträge); die Regex matcht
    //   den Namen als Substring des ListItem-Textes (der zusätzlich die Einheit enthält).
    const items = page.getByTestId('ingredient-list').getByRole('listitem')
    await expect(items).toHaveText([/Apfel/, /Mehl/, /Zwiebel/])
  })
})

// @US-904-edge-case: run-7 „Liste". Soft-Delete-Filterung ist Backend-Verhalten (GET filtert
// WHERE DeletedAt IS NULL, ADR-S000-6). Eine soft-deleted Zeile kommt gar nicht erst im GET-
// Response an -> auf E2E-Ebene beobachtbar nur als "nicht in der Liste". Der Löschzustand wird
// über den API-Port hergestellt (seedDeletedIngredientViaApi), VOR page.goto.
test.describe('US904_EdgeCase: Soft-deleted Zutat', () => {
  // Szenario: Soft-deleted Zutat erscheint nicht in der Zutaten-Liste
  test('US904_EdgeCase_GetIngredients_SoftDeletedIngredient_NotVisibleInList', async ({ page, request }) => {
    // Given: die Zutat "Basilikum" (Bund) existiert und wurde gelöscht
    await seedDeletedIngredientViaApi(request, 'Basilikum', 'Bund')

    // When: ich die Zutaten-Liste betrachte
    await page.goto('/ingredients')
    // Initialen GET abklingen lassen: während des Ladens zeigt die Seite denselben Empty-State
    // wie bei echt-leerer Liste, eine zu frühe Assertion wäre ein Ladeartefakt.
    await page.waitForLoadState('networkidle')

    // Then: "Basilikum" ist nicht in der Zutaten-Liste sichtbar
    await expect(page.getByText('Basilikum')).toHaveCount(0)
  })
})

// @US-904-happy-path: run-8 „Löschen·Success". Löschen einer Zutat aus der Liste (DELETE mit dem
// per-Zeile-xmin-ETag als If-Match, ADR-S108-1) + Undo via Toast-„Rückgängig" (Restore-Endpoint
// ohne If-Match, ADR-S108-2). Black-box: der Test klickt nur, die ETag-/Restore-Mechanik ist
// interne Implementierung. Seed VOR page.goto, damit der initiale GET die Zutat enthält.
test.describe('US904_HappyPath: Zutat löschen', () => {
  // Szenario: Zutat löschen
  test('US904_HappyPath_DeleteIngredient_FromList_ListEmptyAndUndoToastShown', async ({ page, request }) => {
    // Given: nur die Zutat "Mehl" (g) existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')
    await page.goto('/ingredients')
    await expect(page.getByTestId('ingredient-list').getByText('Mehl')).toBeVisible()

    // When: ich bei "Mehl" auf Löschen klicke
    await page.getByRole('button', { name: 'Mehl löschen' }).click()

    // Then: die Zutaten-Liste ist leer -> Empty-State ersetzt die Liste (kein ingredient-list mehr).
    //   toHaveCount(0) auf die Liste statt getByText('Mehl'): der Toast-Text "Mehl gelöscht" enthält
    //   den Substring "Mehl" und würde einen globalen Text-Check fälschlich scheitern lassen.
    await expect(page.getByText('Noch keine Zutaten angelegt.')).toBeVisible()
    await expect(page.getByTestId('ingredient-list')).toHaveCount(0)
    // Then: Toast "Mehl gelöscht" mit "Rückgängig"-Aktion
    await expect(page.getByText('Mehl gelöscht')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
  })

  // Szenario: Löschen rückgängig machen via Toast
  test('US904_HappyPath_UndoDelete_ViaToast_IngredientReappearsInList', async ({ page, request }) => {
    // Given: nur die Zutat "Mehl" (g) existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')
    await page.goto('/ingredients')
    await expect(page.getByTestId('ingredient-list').getByText('Mehl')).toBeVisible()

    // When: ich bei "Mehl" auf Löschen klicke
    await page.getByRole('button', { name: 'Mehl löschen' }).click()
    // When: ich im Toast auf "Rückgängig" klicke (Playwright wartet, bis der Toast-Button da ist)
    await page.getByRole('button', { name: 'Rückgängig' }).click()

    // Then: "Mehl" ist wieder in der Zutaten-Liste mit Einheit "g" (Restore reaktiviert dieselbe
    //   Zeile; auf die Liste gescopt, damit der noch sichtbare Toast nicht mitzählt).
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Mehl')).toBeVisible()
    await expect(list.getByText('g')).toBeVisible()
  })
})

// @US-904-edge-case: run-8 „Löschen·Success". Verlässlichkeit des Undo-Wegs – der Toast ist die
// EINZIGE Wiederherstellungsmöglichkeit im UI (UX-Guideline Prinzip 5 Stufe 1), solange die
// Reaktivierung beim Neuanlegen (run-11) fehlt. Verschwindet er zu früh, ist die Zutat für den
// Nutzer weg. Die Toast-Anzeigezeit beträgt 6 s (autoHideDuration in IngredientsPage.tsx).
test.describe('US904_EdgeCase: Undo-Toast-Verlässlichkeit', () => {
  // Szenario: Undo-Toast bleibt bei einem Klick daneben erhalten
  test('US904_EdgeCase_UndoToast_ClickBesideToast_ToastRemainsVisible', async ({ page, request }) => {
    // Given: nur die Zutat "Mehl" (g) existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')
    await page.goto('/ingredients')
    await expect(page.getByTestId('ingredient-list').getByText('Mehl')).toBeVisible()

    // When: ich bei "Mehl" auf Löschen klicke
    await page.getByRole('button', { name: 'Mehl löschen' }).click()
    await expect(page.getByText('Mehl gelöscht')).toBeVisible()
    // When: ich neben den Toast klicke – der Empty-State-Text ist ein neutrales, nicht
    //   interaktives Ziel weit weg vom Toast (dieser sitzt unten links).
    await page.getByText('Noch keine Zutaten angelegt.').click()

    // Then: der Toast steht weiterhin samt "Rückgängig" – ein beiläufiger Klick darf den einzigen
    //   Weg zurück nicht wegnehmen.
    await expect(page.getByText('Mehl gelöscht')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
  })

  // Szenario: Zweites Löschen gibt dem neuen Toast die volle Rückgängig-Zeit
  test('US904_EdgeCase_SecondDelete_RestartsUndoWindow', async ({ page, request }) => {
    // Given: die Zutaten "Mehl" und "Zucker" existieren
    await seedIngredientViaApi(request, 'Mehl', 'g')
    await seedIngredientViaApi(request, 'Zucker', 'g')
    await page.goto('/ingredients')
    await expect(page.getByTestId('ingredient-list').getByText('Zucker')).toBeVisible()

    // When: ich bei "Mehl" auf Löschen klicke
    await page.getByRole('button', { name: 'Mehl löschen' }).click()
    await expect(page.getByText('Mehl gelöscht')).toBeVisible()

    // When: ich kurz vor Ablauf der Toast-Anzeigezeit bei "Zucker" auf Löschen klicke.
    //   Feste Wartezeit ist hier ausnahmsweise korrekt: die verstrichene Zeit IST der
    //   Testgegenstand, nicht ein Zustand, auf den man warten könnte. 4,5 s < 6 s Anzeigezeit,
    //   der erste Toast steht also noch.
    await page.waitForTimeout(4_500)
    await page.getByRole('button', { name: 'Zucker löschen' }).click()

    // Then: der neue Toast zeigt "Zucker gelöscht" mit "Rückgängig"
    await expect(page.getByText('Zucker gelöscht')).toBeVisible()

    // Then: "Rückgängig" ist noch verfügbar, nachdem die Anzeigezeit des ERSTEN Toasts abgelaufen
    //   wäre (t≈7 s > 6 s). Erbt der zweite Toast dessen Restlaufzeit, ist er hier bereits weg –
    //   der Nutzer verlöre die Undo-Möglichkeit für "Zucker" nach 1,5 statt 6 Sekunden.
    await page.waitForTimeout(2_500)
    await expect(page.getByText('Zucker gelöscht')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
  })

  // Szenario: Nur der zuletzt gelöschten Zutat lässt sich das Löschen rückgängig machen
  test('US904_EdgeCase_TwoDeletes_UndoRestoresOnlyTheLatest', async ({ page, request }) => {
    // Given: die Zutaten "Mehl" und "Zucker" existieren
    await seedIngredientViaApi(request, 'Mehl', 'g')
    await seedIngredientViaApi(request, 'Zucker', 'g')
    await page.goto('/ingredients')
    await expect(page.getByTestId('ingredient-list').getByText('Mehl')).toBeVisible()

    // When: ich bei "Mehl" und danach bei "Zucker" auf Löschen klicke
    await page.getByRole('button', { name: 'Mehl löschen' }).click()
    await expect(page.getByText('Mehl gelöscht')).toBeVisible()
    await page.getByRole('button', { name: 'Zucker löschen' }).click()
    await expect(page.getByText('Zucker gelöscht')).toBeVisible()

    // When: ich im Toast auf "Rückgängig" klicke
    await page.getByRole('button', { name: 'Rückgängig' }).click()

    // Then: nur "Zucker" kehrt zurück – "Mehl" bleibt gelöscht (ADR-S109-1: der Toast hält genau
    //   einen Löschvorgang vor, der zweite ersetzt den ersten). Auf die Liste gescopt, damit ein
    //   noch sichtbarer Toast-Text nicht mitzählt.
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Zucker')).toBeVisible()
    await expect(list.getByText('Mehl')).toHaveCount(0)
  })
})

// @US-904-happy-path: run-9 „Löschen·Pending" (Singleton). UX-Guideline Prinzip 3 ("Sperren
// während Pending"), analog zum Speichern-Dialog (run-2): solange der DELETE unterwegs ist, darf
// die Aktion nicht erneut auslösbar sein. Der Löschen-Button lebt in der Zeile und bleibt während
// des Pendings sichtbar (die Liste aktualisiert sich erst nach der Server-Antwort) – genau dieses
// Fenster ist der Testgegenstand.
test.describe('US904_HappyPath: Löschen·Pending', () => {
  // Szenario: Löschen-Button ist während des Löschens deaktiviert
  test('US904_HappyPath_DeleteInFlight_DeleteButtonIsDisabled', async ({ page, request }) => {
    // Given: nur die Zutat "Mehl" (g) existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')
    // Given: der DELETE bleibt künstlich verzögert, das Pending-Fenster ist so beobachtbar.
    //   Glob `*` matcht kein `/`, die Route trifft also nur `/api/ingredients/{id}` – weder das
    //   Collection-GET (`/api/ingredients`) noch den Restore (`/api/ingredients/{id}/restore`).
    await page.route('**/api/ingredients/*', async (route) => {
      if (route.request().method() !== 'DELETE') { await route.continue(); return }
      await new Promise((resolve) => setTimeout(resolve, 1000))
      await route.continue()
    })
    await page.goto('/ingredients')
    await expect(page.getByTestId('ingredient-list').getByText('Mehl')).toBeVisible()
    // Given (Vorbedingung, Pendant zum Component-Test): vor dem Klick ist der Löschen-Button
    //   aktiv. "deaktiviert solange die Antwort aussteht" ist ein Übergang – ohne diese Hälfte
    //   liefe ein dauerhaft deaktivierter Button in Playwrights Actionability-Timeout am
    //   `.click()` statt in eine sprechende Assertion.
    await expect(page.getByRole('button', { name: 'Mehl löschen' })).toBeEnabled()

    // When: ich bei "Mehl" auf Löschen klicke
    await page.getByRole('button', { name: 'Mehl löschen' }).click()

    // Then: der Löschen-Button für "Mehl" ist deaktiviert, solange die Antwort aussteht.
    //   Der 1000-ms-Delay hält das Fenster offen; danach ersetzt der Empty-State die Zeile.
    await expect(page.getByRole('button', { name: 'Mehl löschen' })).toBeDisabled()
  })
})

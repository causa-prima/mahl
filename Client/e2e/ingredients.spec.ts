import type { Page, APIRequestContext } from '@playwright/test'
import { test, expect, E2E_API_BASE } from './fixtures'
import { createIngredientViaApi, seedIngredientViaApi } from './api/ingredientsApi'

// Pending-Sperren und Undo-Toast der Zutaten-Seite laufen in der Querschnitts-Suite
// (interaction.spec.ts, ADR-S112-5) – hier steht nur, was zutatenspezifisch ist.

// Legt eine Zutat an und löscht sie direkt wieder (soft-delete) – Vorbedingung "die Zutat X
// existiert und wurde gelöscht". Der ETag aus dem POST-Response geht als If-Match ins DELETE
// (Plumbing: DELETE verlangt als mutierender Single-Resource-Endpoint einen If-Match, ADR-S058-1).
async function seedDeletedIngredientViaApi(request: Readonly<APIRequestContext>, name: string, baseUnit: string): Promise<{ id: string }> {
  const { id, etag } = await createIngredientViaApi(request, name, baseUnit)
  const deleteResponse = await request.delete(`${E2E_API_BASE}/api/ingredients/${id}`, { headers: { 'If-Match': etag } })
  expect(deleteResponse.status(), 'Seed-Löschen muss gelingen (204)').toBe(204)
  return { id }
}

// Stellt eine soft-deleted Zutat direkt über die API wieder her – der "jemand anderes"-Zugriff der
// beiden Parallelfall-Szenarien. Body ist Pflicht, Erfolgs-Status 200 (ADR-S111-1).
async function restoreIngredientViaApi(request: Readonly<APIRequestContext>, id: string, name: string, baseUnit: string): Promise<void> {
  const response = await request.post(`${E2E_API_BASE}/api/ingredients/${id}/restore`, { data: { name, baseUnit } })
  expect(response.status(), 'Paralleles Wiederherstellen muss gelingen (200)').toBe(200)
}

// Öffnet das Parallel-Fenster der beiden Nebenläufigkeits-Szenarien: Der Restore, den der Client
// nach dem 409 des POST absetzt, wird abgefangen; erst DANN stellt der Test die Zutat über die API
// wieder her und reicht den Request durch. Der Client-Restore trifft damit eine bereits aktive
// Zeile – genau die Konstellation, die die Szenarien beschreiben. Das Fenster künstlich zu öffnen
// ist der einzige deterministische Weg dorthin: würde der Test vor `page.goto` wiederherstellen,
// sähe schon der POST eine aktive Zeile und liefe in den Duplikat-Fehler (422), statt zu reaktivieren.
// `times: 1` greift nur den einen erwarteten Restore ab.
async function restoreInFlightBeforeClientRestore(
  page: Readonly<Page>, request: Readonly<APIRequestContext>, id: string, name: string, baseUnit: string,
): Promise<void> {
  await page.route('**/api/ingredients/*/restore', async (route) => {
    await restoreIngredientViaApi(request, id, name, baseUnit)
    await route.continue()
  }, { times: 1 })
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
    //   "markiert" (UX-Guideline „Formular-/Dialog-Baseline"). Zusätzlich die native `required`-Property, die
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

  // Szenario: Name mit 30 Zeichen und versehentlichen Leerzeichen wird akzeptiert
  test('US904_EdgeCase_CreateIngredient_PaddedNameAt30CharLimit_AppearsTrimmedInList', async ({ page }) => {
    // When: Dialog öffnen, 30 Zeichen MIT umgebenden Leerzeichen (34 roh) eingeben, speichern.
    //   ADR-S051-1 + ADR-S051-3: erst trimmen, dann messen -> die 30-Zeichen-Grenze gilt für den
    //   getrimmten Wert. Würde roh gemessen, käme hier fälschlich "maximal 30 Zeichen" zurück.
    const nameWith30Chars = 'a'.repeat(30)
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill(`  ${nameWith30Chars}  `)
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: die Zutat erscheint mit dem getrimmten Namen in der Liste
    await expect(page.getByTestId('ingredient-list').getByText(nameWith30Chars, { exact: true })).toBeVisible()
    // Then: der Dialog ist geschlossen (Erfolgspfad, kein Validierungsfehler)
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

  // Szenario: Einheit mit 20 Zeichen und versehentlichen Leerzeichen wird akzeptiert
  test('US904_EdgeCase_CreateIngredient_PaddedUnitAt20CharLimit_AppearsTrimmedInList', async ({ page }) => {
    // When: Dialog öffnen, "Salz" als Name, 20 Zeichen MIT umgebenden Leerzeichen (24 roh) als
    //   Einheit, speichern. Gegenstück zum Namen oben: ADR-S051-1 + ADR-S051-3, erst trimmen,
    //   dann messen – die 20er-Grenze gilt für den getrimmten Wert.
    const unitWith20Chars = 'a'.repeat(20)
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Salz')
    await page.getByLabel('Einheit').fill(`  ${unitWith20Chars}  `)
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: die Zutat erscheint mit der getrimmten Einheit in der Liste
    await expect(page.getByTestId('ingredient-list').getByText('Salz')).toBeVisible()
    await expect(page.getByTestId('ingredient-list').getByText(unitWith20Chars, { exact: true })).toBeVisible()
    // Then: der Dialog ist geschlossen (Erfolgspfad, kein Validierungsfehler)
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
    //   Feld — Name "Salz" ist gültig (UX-Guideline „Formular-/Dialog-Baseline" "Fokus aufs erste fehlerhafte
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
    //   das erste" (UX-Guideline „Formular-/Dialog-Baseline" / TD-S094-1, Fokus-Priorität in DOM-Reihenfolge
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

// @US-904-edge-case / @US-904-error: run-11 „Reaktivierung". Legt der Nutzer eine Zutat an, deren
// Name bereits soft-deleted existiert, wird die vorhandene Zeile reaktiviert statt eine zweite
// anzulegen (ADR-S004-1: POST antwortet 409 mit { code, id }, der Client ruft daraufhin den Restore
// auf – transparent, ohne Zutun des Nutzers). Der Restore übernimmt dabei Name und Einheit aus dem
// Anlege-Request (ADR-S051-4/S111-1), weshalb die beiden Folge-Tests gezielt abweichende Werte
// eingeben. Black-box: die Tests klicken nur, die 409-Orchestrierung ist interne Mechanik – ihre
// Statuscodes prüft Server.Tests. Seed VOR page.goto, damit der initiale GET den Zustand kennt.
// Namens- und Einheiten-Assertions laufen mit `exact: true`: Playwrights Default-Textmatch ist
// case-insensitiv und Substring-basiert, womit der Groß-/Kleinschreibungs-Fall („mehl" -> „Mehl")
// nicht messbar wäre.
test.describe('US904_EdgeCase: Zutat reaktivieren', () => {
  // Szenario: Gelöschte Zutat mit gleichem Namen anlegen reaktiviert diese
  test('US904_EdgeCase_CreateIngredient_SoftDeletedSameName_ReactivatesIngredient', async ({ page, request }) => {
    // Given: die Zutat "Butter" (g) existiert und wurde gelöscht
    await seedDeletedIngredientViaApi(request, 'Butter', 'g')
    await page.goto('/ingredients')
    await expect(page.getByText('Noch keine Zutaten angelegt.')).toBeVisible()

    // When: ich "Butter" (g) über die UI anlege
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Butter')
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()
    // Erfolgspfad: der Dialog schließt – erst danach steht die neu geladene Liste.
    await expect(page.getByRole('dialog')).toBeHidden()

    // Then: "Butter" steht mit Einheit "g" in der Liste – reaktiviert, kein Duplikat-Fehler
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Butter', { exact: true })).toBeVisible()
    await expect(list.getByText('g', { exact: true })).toBeVisible()
  })

  // Szenario: Reaktivierung übernimmt neue Einheit
  test('US904_EdgeCase_ReactivateIngredient_NewUnit_ListShowsNewUnit', async ({ page, request }) => {
    // Given: die Zutat "Butter" mit der ALTEN Einheit "Würfel" existiert und wurde gelöscht
    await seedDeletedIngredientViaApi(request, 'Butter', 'Würfel')
    await page.goto('/ingredients')
    await expect(page.getByText('Noch keine Zutaten angelegt.')).toBeVisible()

    // When: ich "Butter" mit der NEUEN Einheit "g" anlege
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Butter')
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()
    await expect(page.getByRole('dialog')).toBeHidden()

    // Then: die Liste zeigt die NEUE Einheit "g"; die alte "Würfel" ist verschwunden. Ohne die
    //   zweite Assertion bliebe offen, ob die Reaktivierung den Wert wirklich übernommen hat.
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Butter', { exact: true })).toBeVisible()
    await expect(list.getByText('g', { exact: true })).toBeVisible()
    await expect(list.getByText('Würfel', { exact: true })).toHaveCount(0)
  })

  // Szenario: Reaktivierung übernimmt neuen Namen bei abweichender Schreibweise
  test('US904_EdgeCase_ReactivateIngredient_DifferentCasing_ListShowsNewSpelling', async ({ page, request }) => {
    // Given: die Zutat "mehl" (kleingeschrieben) existiert und wurde gelöscht
    await seedDeletedIngredientViaApi(request, 'mehl', 'g')
    await page.goto('/ingredients')
    await expect(page.getByText('Noch keine Zutaten angelegt.')).toBeVisible()

    // When: ich "Mehl" (großgeschrieben) anlege – case-insensitiv dieselbe Zutat (ADR-S051-3)
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Mehl')
    await page.getByLabel('Einheit').fill('g')
    await page.getByRole('button', { name: 'Speichern' }).click()
    await expect(page.getByRole('dialog')).toBeHidden()

    // Then: die Liste zeigt die NEUE Schreibweise "Mehl", nicht mehr "mehl"
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Mehl', { exact: true })).toBeVisible()
    await expect(list.getByText('mehl', { exact: true })).toHaveCount(0)
  })

  // Szenario: Reaktivierung gelingt auch wenn Zutat parallel mit denselben Daten wiederhergestellt wurde
  test('US904_EdgeCase_ReactivateIngredient_ParallelRestoreSameData_Succeeds', async ({ page, request }) => {
    // Given: die Zutat "Koriander" (Bund) existiert und wurde gelöscht
    const { id } = await seedDeletedIngredientViaApi(request, 'Koriander', 'Bund')
    // Given: "Koriander" wird parallel durch jemand anderen mit DENSELBEN Daten wiederhergestellt –
    //   im Fenster zwischen dem 409 des POST und dem Restore des Clients (s. Helper-Kommentar).
    await restoreInFlightBeforeClientRestore(page, request, id, 'Koriander', 'Bund')
    await page.goto('/ingredients')
    await expect(page.getByText('Noch keine Zutaten angelegt.')).toBeVisible()

    // When: ich "Koriander" (Bund) anlege
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Koriander')
    await page.getByLabel('Einheit').fill('Bund')
    await page.getByRole('button', { name: 'Speichern' }).click()
    // Der Vorgang gilt als gelungen: der Dialog schließt wie im ungestörten Fall.
    await expect(page.getByRole('dialog')).toBeHidden()

    // Then: "Koriander" steht mit Einheit "Bund" in der Liste. Die Einheit IST hier vorhersagbar,
    //   weil der parallele Restore dieselben Werte gesetzt hat – es wurde nichts überschrieben.
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Koriander', { exact: true })).toBeVisible()
    await expect(list.getByText('Bund', { exact: true })).toBeVisible()
  })
})

// @US-904-error: run-11 „Reaktivierung", Konfliktfall. Trägt die parallel wiederhergestellte Zeile
// ABWEICHENDE Daten, würde die eigene Eingabe fremde Werte still überschreiben – der Restore
// antwortet deshalb 409 und der Nutzer bekommt einen Hinweis, der beide Seiten benennt
// (ADR-S111-1/S111-3). Der Dialog schließt trotzdem: die Zutat existiert, im Dialog gäbe es nichts
// zu korrigieren.
test.describe('US904_Error: Reaktivierungs-Konflikt', () => {
  // Szenario: Reaktivierung meldet Konflikt wenn die Zutat parallel mit anderen Daten wiederhergestellt wurde
  test('US904_Error_ReactivateIngredient_ParallelRestoreDifferentData_ShowsConflictHint', async ({ page, request }) => {
    // Given: die Zutat "Koriander" (Bund) existiert und wurde gelöscht
    const { id } = await seedDeletedIngredientViaApi(request, 'Koriander', 'Bund')
    // Given: "Koriander" wird parallel durch jemand anderen mit der ABWEICHENDEN Einheit "Töpfchen"
    //   wiederhergestellt – im Fenster vor dem Restore des Clients (s. Helper-Kommentar).
    await restoreInFlightBeforeClientRestore(page, request, id, 'Koriander', 'Töpfchen')
    await page.goto('/ingredients')
    await expect(page.getByText('Noch keine Zutaten angelegt.')).toBeVisible()

    // When: ich "Koriander" mit MEINER Einheit "Bund" anlege
    await page.getByRole('button', { name: 'Zutat anlegen' }).click()
    await page.getByLabel('Name').fill('Koriander')
    await page.getByLabel('Einheit').fill('Bund')
    await page.getByRole('button', { name: 'Speichern' }).click()

    // Then: der Hinweis nennt die eigene Eingabe UND den tatsächlich gespeicherten Stand
    await expect(page.getByText(
      "'Koriander' wurde zwischenzeitlich an anderer Stelle wiederhergestellt (z. B. auf einem anderen Gerät). Gespeichert ist 'Koriander' mit der Einheit 'Töpfchen'.",
    )).toBeVisible()
    // Then: der Dialog ist geschlossen – es gibt nichts zu korrigieren
    await expect(page.getByRole('dialog')).toBeHidden()
    // Then: die Liste zeigt den FREMDEN Stand "Töpfchen", nicht die eigene Eingabe "Bund"
    const list = page.getByTestId('ingredient-list')
    await expect(list.getByText('Koriander', { exact: true })).toBeVisible()
    await expect(list.getByText('Töpfchen', { exact: true })).toBeVisible()
    await expect(list.getByText('Bund', { exact: true })).toHaveCount(0)
  })
})

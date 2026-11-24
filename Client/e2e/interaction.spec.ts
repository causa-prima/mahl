import type { APIRequestContext, Page } from '@playwright/test'
import { test, expect } from './fixtures'
import type { DeleteWithUndoPage, ListEntry } from './pages/interactionPage'
import { CREATE_DIALOG_PAGES, DELETE_WITH_UNDO_PAGES } from './pages/interactionPages'

// Querschnitts-Suite (ADR-S112-5, Nachweis-Schicht): Verhalten, das auf JEDER Seite mit derselben
// Fähigkeit gleich sein soll, läuft hier einmal je Seite. Eine neue Seite trägt sich je Fähigkeit in die
// Registry ein (pages/interactionPages.ts) und liefert deren Page Object (pages/interactionPage.ts) – die Tests bekommt
// sie dazu, statt sie nachzubauen.
//
// Die Szenarien stehen in features/interaction.feature (Vertreter dort: die Zutaten-Seite), die
// Testnamen tragen deshalb das Präfix CROSS_Interaction_<Typ> (e2e-testing.md, Traceability).
// Jeder Testname trägt mehrere Läufe, einen je Seite; unterscheidbar sind sie über den describe-Titel
// mit dem Seitennamen. Ein Grep nach dem Testnamen findet daher eine Quellzeile.

// Verzögert die Anfragen einer Methode künstlich, damit der Pending-Zustand vor der Antwort
// beobachtbar ist.
async function delayRequests(page: Readonly<Page>, urlGlob: string, method: string): Promise<void> {
  await page.route(urlGlob, async (route) => {
    if (route.request().method() !== method) { await route.continue(); return }
    await new Promise((resolve) => setTimeout(resolve, 1000))
    await route.continue()
  })
}

// > MUI theme.transitions.duration.leavingScreen (225ms, MUI-Default) + Marge. Settle-Fenster
// VOR Assertions, die sich auf "Dialog noch sichtbar" verlassen: eine (fälschliche) Close-
// Transition bräuchte diese Zeit, um zu greifen – ohne das Fenster wäre die Assertion ein
// Transition-Artefakt statt echtes Verhalten.
const DIALOG_EXIT_SETTLE_MS = 400

// Given "die Einträge existieren": Seed VOR goto, damit der initiale GET sie enthält; die
// Sichtbarkeits-Assertion lässt den GET abklingen, bevor der Test klickt.
async function givenEntriesShown(deleteWithUndo: DeleteWithUndoPage, entries: readonly ListEntry[]): Promise<void> {
  await Promise.all(entries.map((entry) => entry.seed()))
  await deleteWithUndo.goto()
  await Promise.all(entries.map((entry) => expect(entry.row).toBeVisible()))
}

// @CROSS-interaction-pending: run-2 „Anlegen·Pending" und run-3 „Löschen·Pending". UX-Guideline „Sichtbares
// Feedback" ("Sperren während Pending"): solange die Anfrage unterwegs ist, darf die Aktion weder
// erneut auslösbar sein noch der Dialog sich schließen lassen.
CREATE_DIALOG_PAGES.forEach((definition) => {
  test.describe(`${definition.name}: Pending-Sperren beim Anlegen`, () => {
    // Setup der vier Speichern-Tests: POST verzögert, Dialog öffnen/befüllen, Speichern-Klick.
    async function submitWithDelayedCreate(page: Readonly<Page>, request: Readonly<APIRequestContext>): Promise<void> {
      const createDialog = definition.create(page, request)
      await createDialog.goto()
      await delayRequests(page, createDialog.createRoute, 'POST')
      await createDialog.openCreateDialog()
      await createDialog.fillCreateDialogWithValidEntry()
      await page.getByRole('button', { name: 'Speichern' }).click()
    }

    // Szenario: Speichern-Button ist während des Speicherns deaktiviert
    test('CROSS_Interaction_Pending_SaveInFlight_SaveButtonIsDisabled', async ({ page, request }) => {
      // When: Dialog öffnen, gültigen Eintrag eingeben, "Speichern" klicken (Helper)
      await submitWithDelayedCreate(page, request)

      // Then: der "Speichern"-Button ist deaktiviert, solange die Antwort aussteht
      await expect(page.getByRole('button', { name: 'Speichern' })).toBeDisabled()
    })

    // Szenario: Abbrechen ist während des Speicherns deaktiviert
    test('CROSS_Interaction_Pending_SaveInFlight_CancelButtonIsDisabled', async ({ page, request }) => {
      // When: Dialog öffnen, gültigen Eintrag eingeben, "Speichern" klicken (Helper)
      await submitWithDelayedCreate(page, request)

      // Then: der "Abbrechen"-Button ist deaktiviert, solange die Antwort aussteht
      await expect(page.getByRole('button', { name: 'Abbrechen' })).toBeDisabled()
    })

    // Szenario: Der Dialog lässt sich während des Speicherns nicht per Escape schließen
    test('CROSS_Interaction_Pending_SaveInFlight_EscapeDoesNotCloseDialog', async ({ page, request }) => {
      // When: Dialog öffnen, gültigen Eintrag eingeben, "Speichern" klicken (Helper)
      await submitWithDelayedCreate(page, request)
      // When (Zwischenzustand, Parität zum Component-Test): Pending-Zustand ist erreicht,
      //   bevor Escape gedrückt wird – schließt den Race, in dem Escape vor dem Pending-Zustand
      //   feuert und der Guard das Fenster verpasst.
      await expect(page.getByRole('button', { name: 'Speichern' })).toBeDisabled()
      // When: ich Escape drücke – aus dem noch aktiven ersten Feld heraus (Fokus IM Dialog): sonst
      //   fiele der Fokus vom deaktivierten Speichern-Button auf <body> außerhalb des Modals, und
      //   der MUI-Escape-Handler würde gar nicht erst erreicht -> der Test wäre ohne echten Guard
      //   grün (Fokus-Artefakt statt Verhalten). So schlägt Escape ohne Guard tatsächlich bis zum
      //   onClose durch.
      await page.getByRole('dialog').getByRole('textbox').first().press('Escape')

      // Then: der Dialog ist weiterhin geöffnet, solange die Antwort aussteht. Settle-Fenster VOR
      //   der Assertion (s. DIALOG_EXIT_SETTLE_MS): eine (fälschliche) Escape-getriebene Close-
      //   Transition hätte damit Zeit zu greifen. DIALOG_EXIT_SETTLE_MS liegt sicher im 1000-ms-
      //   Pending-Fenster, der POST ist also noch offen: das Einzige, was den Dialog schließen
      //   könnte, wäre ein fehlender Escape-Guard.
      await page.waitForTimeout(DIALOG_EXIT_SETTLE_MS)
      await expect(page.getByRole('dialog')).toBeVisible()
    })

    // Szenario: Der Dialog lässt sich während des Speicherns nicht per Backdrop-Klick schließen
    test('CROSS_Interaction_Pending_SaveInFlight_BackdropClickDoesNotCloseDialog', async ({ page, request }) => {
      // When: Dialog öffnen, gültigen Eintrag eingeben, "Speichern" klicken (Helper)
      await submitWithDelayedCreate(page, request)
      // When (Zwischenzustand, Parität zum Escape-Test): Pending-Zustand ist erreicht, bevor
      //   der Backdrop-Klick erfolgt.
      await expect(page.getByRole('button', { name: 'Speichern' })).toBeDisabled()
      // When: ich neben den Dialog klicke. MUI löst den Backdrop-Klick über den Klick auf den
      //   `.MuiDialog-container` (role=presentation, füllt den Viewport, liegt ÜBER dem Backdrop)
      //   aus: nur ein Klick, dessen target === currentTarget (also der Container selbst, nicht das
      //   Paper), zählt als backdropClick. Position nahe der Ecke -> trifft den Container, nicht das
      //   zentrierte Paper. Ohne Guard triggert das MUIs onClose(reason='backdropClick').
      await page.locator('.MuiDialog-container').click({ position: { x: 5, y: 5 } })

      // Then: der Dialog ist weiterhin geöffnet, solange die Antwort aussteht (Settle-Fenster
      //   analog Escape-Test).
      await page.waitForTimeout(DIALOG_EXIT_SETTLE_MS)
      await expect(page.getByRole('dialog')).toBeVisible()
    })
  })
})

// @CROSS-interaction-pending: run-3 „Löschen·Pending" – Seiten mit der Fähigkeit „Löschen mit Rückgängig-Toast".
DELETE_WITH_UNDO_PAGES.forEach((definition) => {
  test.describe(`${definition.name}: Pending-Sperre beim Löschen`, () => {
    // Szenario: Löschen-Button ist während des Löschens deaktiviert
    test('CROSS_Interaction_Pending_DeleteInFlight_DeleteButtonIsDisabled', async ({ page, request }) => {
      const deleteWithUndo = definition.create(page, request)
      const [entry] = deleteWithUndo.entries
      // Given: nur der Eintrag existiert, der DELETE bleibt künstlich verzögert
      await delayRequests(page, deleteWithUndo.deleteRoute, 'DELETE')
      await givenEntriesShown(deleteWithUndo, [entry])
      // Given (Vorbedingung, Pendant zum Component-Test): vor dem Klick ist der Löschen-Button
      //   aktiv. "deaktiviert solange die Antwort aussteht" ist ein Übergang – ohne diese Hälfte
      //   liefe ein dauerhaft deaktivierter Button in Playwrights Actionability-Timeout am
      //   `.click()` statt in eine sprechende Assertion.
      await expect(entry.deleteButton).toBeEnabled()

      // When: ich beim Eintrag auf Löschen klicke
      await entry.deleteButton.click()

      // Then: sein Löschen-Button ist deaktiviert, solange die Antwort aussteht. Der 1000-ms-Delay
      //   hält das Fenster offen; danach ersetzt der Empty-State die Zeile.
      await expect(entry.deleteButton).toBeDisabled()
    })
  })

  // @CROSS-interaction-undo: run-1 „Löschen·Undo-Toast". Löschen samt Undo-Toast. Der Toast
  // ist die EINZIGE Wiederherstellungsmöglichkeit im UI (UX-Guideline „Destructive Actions schützen",
  // Soft-Delete) – verschwindet er zu früh, ist der Eintrag für den Nutzer weg. Anzeigezeit: 6 s.
  // Black-box: der Test klickt nur, die ETag-/Restore-Mechanik ist interne Implementierung.
  test.describe(`${definition.name}: Undo-Toast`, () => {
    // Szenario: Zutat löschen
    test('CROSS_Interaction_Undo_DeleteEntry_FromList_ListEmptyAndUndoToastShown', async ({ page, request }) => {
      const deleteWithUndo = definition.create(page, request)
      const [entry] = deleteWithUndo.entries
      // Given: nur der Eintrag existiert
      await givenEntriesShown(deleteWithUndo, [entry])

      // When: ich beim Eintrag auf Löschen klicke
      await entry.deleteButton.click()

      // Then: die Liste ist leer -> Empty-State ersetzt die Liste. toHaveCount(0) auf die Liste statt
      //   eines globalen Text-Checks: der Toast-Text (deletedToast) enthält den Namen als Substring.
      await expect(deleteWithUndo.emptyState).toBeVisible()
      await expect(deleteWithUndo.list).toHaveCount(0)
      // Then: Toast deletedToast („<Name> gelöscht" bzw. „<Titel> entfernt") mit "Rückgängig"-Aktion
      await expect(page.getByText(entry.deletedToast)).toBeVisible()
      await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
    })

    // Szenario: Löschen rückgängig machen via Toast
    test('CROSS_Interaction_Undo_UndoDelete_ViaToast_EntryReappearsInList', async ({ page, request }) => {
      const deleteWithUndo = definition.create(page, request)
      const [entry] = deleteWithUndo.entries
      // Given: nur der Eintrag existiert
      await givenEntriesShown(deleteWithUndo, [entry])

      // When: ich beim Eintrag auf Löschen klicke und im Toast auf "Rückgängig" (Playwright wartet,
      //   bis der Toast-Button da ist)
      await entry.deleteButton.click()
      await page.getByRole('button', { name: 'Rückgängig' }).click()

      // Then: der Eintrag steht wieder in der Liste – mit allen angezeigten Werten (entry.row), weil
      //   der Restore dieselbe Zeile reaktiviert und nicht nur einen gleichnamigen Eintrag anlegt.
      await expect(entry.row).toBeVisible()
      // Then: der Toast deletedToast ist nicht mehr sichtbar – er schließt mit dem Restore, nicht
      //   erst nach Ablauf der Rückgängig-Zeit (die liegt über dem Assertion-Timeout).
      await expect(page.getByText(entry.deletedToast)).toBeHidden()
    })

    // Szenario: Undo-Toast bleibt bei einem Klick daneben erhalten
    test('CROSS_Interaction_Undo_ClickBesideToast_ToastRemainsVisible', async ({ page, request }) => {
      const deleteWithUndo = definition.create(page, request)
      const [entry] = deleteWithUndo.entries
      // Given: nur der Eintrag existiert
      await givenEntriesShown(deleteWithUndo, [entry])

      // When: ich beim Eintrag auf Löschen klicke
      await entry.deleteButton.click()
      await expect(page.getByText(entry.deletedToast)).toBeVisible()
      // When: ich neben den Toast klicke – der Empty-State ist ein neutrales, nicht interaktives
      //   Ziel weit weg vom Toast (dieser sitzt unten links).
      await deleteWithUndo.emptyState.click()

      // Then: der Toast steht weiterhin samt "Rückgängig" – ein beiläufiger Klick darf den einzigen
      //   Weg zurück nicht wegnehmen.
      await expect(page.getByText(entry.deletedToast)).toBeVisible()
      await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
    })

    // Szenario: Zweites Löschen gibt dem neuen Toast die volle Rückgängig-Zeit
    test('CROSS_Interaction_Undo_SecondDelete_RestartsUndoWindow', async ({ page, request }) => {
      const deleteWithUndo = definition.create(page, request)
      const [first, second] = deleteWithUndo.entries
      // Given: beide Einträge existieren
      await givenEntriesShown(deleteWithUndo, [first, second])

      // When: ich beim ersten Eintrag auf Löschen klicke
      await first.deleteButton.click()
      await expect(page.getByText(first.deletedToast)).toBeVisible()

      // When: ich kurz vor Ablauf der Toast-Anzeigezeit beim zweiten auf Löschen klicke.
      //   Feste Wartezeit ist hier ausnahmsweise korrekt: die verstrichene Zeit IST der
      //   Testgegenstand, nicht ein Zustand, auf den man warten könnte. 4,5 s < 6 s Anzeigezeit,
      //   der erste Toast steht also noch.
      await page.waitForTimeout(4_500)
      await second.deleteButton.click()

      // Then: der neue Toast zeigt deletedToast des zweiten Eintrags mit "Rückgängig"
      await expect(page.getByText(second.deletedToast)).toBeVisible()

      // Then: "Rückgängig" ist noch verfügbar, nachdem die Anzeigezeit des ERSTEN Toasts abgelaufen
      //   wäre (t≈7 s > 6 s). Erbt der zweite Toast dessen Restlaufzeit, ist er hier bereits weg –
      //   der Nutzer verlöre die Undo-Möglichkeit nach 1,5 statt 6 Sekunden.
      await page.waitForTimeout(2_500)
      await expect(page.getByText(second.deletedToast)).toBeVisible()
      await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
    })

    // Szenario: Nur der zuletzt gelöschten Zutat lässt sich das Löschen rückgängig machen
    test('CROSS_Interaction_Undo_TwoDeletes_UndoRestoresOnlyTheLatest', async ({ page, request }) => {
      const deleteWithUndo = definition.create(page, request)
      const [first, second] = deleteWithUndo.entries
      // Given: beide Einträge existieren
      await givenEntriesShown(deleteWithUndo, [first, second])

      // When: ich beim ersten und danach beim zweiten Eintrag auf Löschen klicke
      await first.deleteButton.click()
      await expect(page.getByText(first.deletedToast)).toBeVisible()
      await second.deleteButton.click()
      await expect(page.getByText(second.deletedToast)).toBeVisible()

      // When: ich im Toast auf "Rückgängig" klicke
      await page.getByRole('button', { name: 'Rückgängig' }).click()

      // Then: nur der zweite kehrt zurück – der erste bleibt gelöscht (ADR-S109-1: der Toast hält
      //   genau einen Löschvorgang vor, der zweite ersetzt den ersten).
      await expect(second.row).toBeVisible()
      await expect(first.row).toHaveCount(0)
    })

    // Szenario: Rückgängig während das Löschen noch läuft stellt die Zutat dauerhaft wieder her
    test('CROSS_Interaction_Undo_UndoWhileDeleteInFlight_EntryStaysRestoredAfterReload', async ({ page, request }) => {
      const deleteWithUndo = definition.create(page, request)
      const [entry] = deleteWithUndo.entries
      // Given: nur der Eintrag existiert; das Löschen bleibt künstlich verzögert, damit „Rückgängig" in sein
      //   Fenster fällt. Ein Wiederherstellen, das nicht auf das Löschen wartet, käme so immer vor ihm an.
      await delayRequests(page, deleteWithUndo.deleteRoute, 'DELETE')
      await givenEntriesShown(deleteWithUndo, [entry])

      // When: ich beim Eintrag auf Löschen klicke und im Toast auf "Rückgängig", solange die Antwort für das
      //   Löschen aussteht (der Toast steht sofort, die Antwort erst nach der Verzögerung)
      const deleteDone = page.waitForResponse((response) => response.request().method() === 'DELETE')
      // Wiederherstellen ist je Seite POST …/restore (Zutaten) oder PUT (Vorgemerkt) – weder GET noch DELETE.
      const restoreDone = page.waitForResponse((response) => !['GET', 'DELETE'].includes(response.request().method()))
      await entry.deleteButton.click()
      await page.getByRole('button', { name: 'Rückgängig' }).click()

      // When: ich die Seite neu lade – erst, wenn beide Anfragen beim Server angekommen sind: Ein Neuladen
      //   davor bräche die zurückgehaltene Anfrage ab, und der Test prüfte dann nichts.
      await Promise.all([deleteDone, restoreDone])
      await page.reload()

      // Then: der Eintrag steht in der Liste – mit allen angezeigten Werten (entry.row)
      await expect(entry.row).toBeVisible()
    })
  })
})

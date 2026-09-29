import type { Locator, Page } from '@playwright/test'
import { test, expect } from './fixtures'
import { LIST_PAGES } from './pages/listPages'

// docs/process/nfr.md (Accessibility): Touch-Targets ≥ 44×44px.
const MIN_TOUCH_TARGET_PX = 44

// Rollen, unter denen ein Bedienelement per Finger getroffen werden muss – auch solche, für die das
// Theme noch keinen Default setzt: Ein neuer Typ soll hier auffallen.
const CONTROL_ROLES = ['button', 'link', 'checkbox', 'radio', 'switch', 'tab', 'menuitem'] as const

// Das Szenario meint die Bedienung am Handy: gemessen wird im Handy-Viewport.
test.use({ viewport: { width: 390, height: 844 } })

// Rollen-Queries sehen bei offenem Dialog den Hintergrund nicht (aria-hidden) – dort ist er ohnehin
// nicht bedienbar. Textfelder zählen über ihren Rahmen, weil der ganze Rahmen den Fokus annimmt; die
// Rolle textbox träfe nur die Textzeile darin. Der Rahmen hängt an einer MUI-Klasse: Der Abgleich mit den
// sichtbaren Textfeldern lässt einen leeren Treffer (umbenannte Klasse, Feldtyp ohne diesen Rahmen) laut
// scheitern statt still grün.
async function visibleControls(page: Readonly<Page>): Promise<Locator[]> {
  const byRole = await Promise.all(CONTROL_ROLES.map((role) => page.getByRole(role).filter({ visible: true }).all()))
  const fieldFrames = await page.locator('.MuiInputBase-root').filter({ visible: true }).all()
  const textboxCount = await page.getByRole('textbox').filter({ visible: true }).count()
  expect(fieldFrames.length, 'Jedes sichtbare Textfeld braucht einen Rahmen .MuiInputBase-root').toBe(textboxCount)
  return [...byRole.flat(), ...fieldFrames]
}

// Verstoß-Beschreibung "<Beschriftung>: <Breite>×<Höhe>" oder undefined, wenn das Element groß genug ist.
// Timeout, damit ein zwischen Auflisten und Messen verschwundenes Element den Versuch abbricht statt ihn
// über das toPass-Fenster hinaus aufzuhalten.
async function touchTargetViolation(control: Readonly<Locator>): Promise<string | undefined> {
  const box = await control.boundingBox({ timeout: 500 })
  if (box && box.width >= MIN_TOUCH_TARGET_PX && box.height >= MIN_TOUCH_TARGET_PX) return undefined
  const label = await control.getAttribute('aria-label') ?? await control.innerText()
  return box ? `${label}: ${String(box.width)}×${String(box.height)}` : `${label}: ohne Box`
}

// toPass statt Einzelmessung: Dialog und Snackbar fahren mit einer Transition ein, mitten darin ist die
// Box noch skaliert (nur kleiner, nie größer – ein zu frühes Messen verzögert also nur das Grün). Eine
// echte Verletzung läuft in den Timeout – mit dem Zustand und der Liste aller Verstöße.
async function expectEveryControlMeetsTouchTarget(page: Readonly<Page>, state: string): Promise<void> {
  await expect(async () => {
    const controls = await visibleControls(page)
    expect(controls.length, `Zustand ${state}: keine Bedienelemente gefunden`).toBeGreaterThan(0)
    const violations = await Promise.all(controls.map(touchTargetViolation))
    expect(violations.filter((violation) => violation !== undefined), `Zustand ${state}`).toEqual([])
  }).toPass({ timeout: 2_000 })
}

LIST_PAGES.forEach((definition) => {
  test.describe(`${definition.name}: Touch-Targets`, () => {
    // @NFR-accessibility-touch
    // Szenario: Jedes Bedienelement ist groß genug für die Bedienung per Finger
    test('NFR_Accessibility_AllStates_EveryControlAtLeast44px', async ({ page, request }) => {
      const listPage = definition.create(page, request)
      const [entry] = listPage.entries
      // Given: ein Eintrag steht in der Liste
      await entry.seed()
      await listPage.goto()
      await expect(entry.row).toBeVisible()
      // Then (Liste): Löschen- und Anlegen-Button
      await expectEveryControlMeetsTouchTarget(page, 'Liste')

      // When: ich den Anlege-Dialog öffne
      await listPage.openCreateDialog()
      await expect(page.getByRole('dialog')).toBeVisible()
      // Then (Anlege-Dialog): Textfelder, Abbrechen, Speichern
      await expectEveryControlMeetsTouchTarget(page, 'Anlege-Dialog')

      // When: ich ihn abbreche und den Eintrag lösche
      await page.getByRole('button', { name: 'Abbrechen' }).click()
      await expect(page.getByRole('dialog')).toHaveCount(0)
      await entry.deleteButton.click()
      await expect(page.getByRole('button', { name: 'Rückgängig' })).toBeVisible()
      // Then (Undo-Toast): die Aktion "Rückgängig" neben dem Anlegen-Button
      await expectEveryControlMeetsTouchTarget(page, 'Undo-Toast')
    })
  })
})

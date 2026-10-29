import type { Locator, Page } from '@playwright/test'
import { test, expect } from './fixtures'
import { TOUCH_TARGET_PAGES } from './pages/touchTargetPages'
import type { TouchTargetState } from './pages/touchTargetPage'

// docs/process/nfr.md (Accessibility): Touch-Targets ≥ 44×44px.
const MIN_TOUCH_TARGET_PX = 44

// Rollen, unter denen ein Bedienelement per Finger getroffen werden muss – auch solche, für die das
// Theme noch keinen Default setzt: Ein neuer Typ soll hier auffallen.
const CONTROL_ROLES = ['button', 'link', 'checkbox', 'radio', 'switch', 'tab', 'menuitem'] as const

// Das Szenario meint die Bedienung am Handy: gemessen wird im Handy-Viewport.
test.use({ viewport: { width: 390, height: 844 } })

// Rollen-Queries sehen bei offenem Dialog den Hintergrund nicht (aria-hidden) – dort ist er ohnehin
// nicht bedienbar. Textfelder zählen über ihren Rahmen, weil der ganze Rahmen den Fokus annimmt; die
// Rolle textbox träfe nur die Textzeile darin. Ein Rahmen zählt nur mit einem Textfeld darin, das die
// Rollen-Query sieht – sonst mäße die Suite hinter einem offenen Dialog die Felder des Hintergrunds. Der
// Rahmen hängt an einer MUI-Klasse: Der Abgleich mit den sichtbaren Textfeldern lässt einen leeren Treffer
// (umbenannte Klasse, Feldtyp ohne diesen Rahmen) laut scheitern statt still grün.
async function visibleControls(page: Readonly<Page>): Promise<Locator[]> {
  const byRole = await Promise.all(CONTROL_ROLES.map((role) => page.getByRole(role).filter({ visible: true }).all()))
  const fieldFrames = await page.locator('.MuiInputBase-root')
    .filter({ visible: true, has: page.getByRole('textbox') }).all()
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
async function expectEveryControlMeetsTouchTarget(page: Readonly<Page>, state: Readonly<TouchTargetState>): Promise<void> {
  await expect(async () => {
    const controls = await visibleControls(page)
    const violations = await Promise.all(controls.map(touchTargetViolation))
    expect(violations.filter((violation) => violation !== undefined), `Zustand ${state.name}`).toEqual([])
    // Ein Zustand hat Bedienelemente genau dann, wenn er nicht als ohne deklariert ist – auch umgekehrt,
    // damit eine überholte Deklaration auffällt, statt still stehen zu bleiben.
    expect(controls.length > 0, state.withoutControls
      ? `Zustand ${state.name} hat jetzt ${String(controls.length)} Bedienelement(e) – withoutControls entfernen`
      : `Zustand ${state.name}: keine Bedienelemente gefunden`).toBe(!state.withoutControls)
  }).toPass({ timeout: 2_000 })
}

TOUCH_TARGET_PAGES.forEach((definition) => {
  test.describe(`${definition.name}: Touch-Targets`, () => {
    // @NFR-accessibility-touch
    // Szenario: Jedes Bedienelement ist groß genug für die Bedienung per Finger
    test('NFR_Accessibility_AllStates_EveryControlAtLeast44px', async ({ page, request }) => {
      // When/Then: je Zustand der Seite messen – nacheinander, jeder baut auf dem vorigen auf. Die
      // Promise-Kette per reduce ersetzt eine for…of-Schleife, die `functional/no-loop-statements` verbietet.
      await definition.states(page, request).reduce(async (previous, state) => {
        await previous
        await state.reach()
        await expectEveryControlMeetsTouchTarget(page, state)
      }, Promise.resolve())
    })
  })
})

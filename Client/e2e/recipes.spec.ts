import { test, expect } from './fixtures'
import { seedIngredientViaApi } from './api/ingredientsApi'
import type { APIRequestContext, Locator, Page } from '@playwright/test'
import {
  createRecipeViaApi, fetchRecipeTitlesViaApi, postRecipeViaApi, seedRecipesWithSaltViaApi, UNKNOWN_RECIPE_ID,
} from './api/recipesApi'
import { discardQuestion } from './pages/recipesPage'
import { escapeRegExp, exactly } from './exactText'

// Then „sehe ich die Detailansicht des neuen Rezepts": die eigene Adresse mit der Kennung (ADR-S135-5).
const RECIPE_DETAIL_URL = /\/recipes\/[0-9a-f-]{36}$/

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
    await saveForm(page)

    // Then: die Detailansicht des Rezepts "Pfannkuchen" (eigene Adresse, ADR-S135-5)
    await expect(page).toHaveURL(RECIPE_DETAIL_URL)
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

const INGREDIENTS_HINT = 'Eine Zutat je Zeile: Menge, Einheit, Zutat – z. B. „250 g Mehl“ oder „Salz“.'

// When der Formular-Szenarien: zur Rezepte-Seite navigieren und auf "Rezept anlegen" klicken.
async function openCreateForm(page: Readonly<Page>): Promise<void> {
  await page.goto('/recipes')
  await page.getByRole('button', { name: 'Rezept anlegen' }).click()
}

// Der Abschnitt "Schritte" als Gruppe. Name per Regex: Der Pflicht-Asterisk der Legende steht daneben.
function stepsSection(page: Readonly<Page>) {
  return page.getByRole('group', { name: /^Schritte/ })
}

// Die Nummer eines Schrittfelds ist sein sichtbares Label „Schritt N" (e2e-testing.md, sichtbares
// Signal). toHaveText mit Array pinnt Anzahl und Reihenfolge.
async function expectStepNumbers(page: Readonly<Page>, numbers: readonly number[]): Promise<void> {
  await expect(stepsSection(page).locator('label')).toHaveText(numbers.map((n) => `Schritt ${String(n)}`))
}

// Then von „Felder sind beim Öffnen leer" und „direkt öffnen": Titel und Zutaten leer, genau ein leeres
// Schrittfeld mit der Nummer 1.
async function expectEmptyForm(page: Readonly<Page>): Promise<void> {
  await expect(page.getByLabel('Titel')).toHaveValue('')
  await expect(page.getByLabel('Zutaten')).toHaveValue('')
  await expectStepNumbers(page, [1])
  await expect(stepsSection(page).getByLabel('Schritt 1')).toHaveValue('')
}

// When „ich auf "Speichern" klicke".
async function saveForm(page: Readonly<Page>): Promise<void> {
  await page.getByRole('button', { name: 'Speichern' }).click()
}

// Then „bin ich weiterhin im Formular": Adresse und Überschrift des Formulars.
async function expectForm(page: Readonly<Page>): Promise<void> {
  await expect(page).toHaveURL(/\/recipes\/new$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Rezept anlegen' })).toBeVisible()
}

// Then „sehe ich <am Element> die Fehlermeldung …": sichtbar und als Beschreibung mit dem Element
// verknüpft – „am Feld" wie beim Hinweis des Zutatenfelds.
async function expectMessageAt(page: Readonly<Page>, element: Readonly<Locator>, message: string): Promise<void> {
  await expect(page.getByText(message, { exact: true })).toBeVisible()
  await expect(element).toHaveAccessibleDescription(message)
}

// Then „sehe ich bei den Zutaten die Fehlermeldung …": Am Zutatenfeld bleibt der Hinweis zur Eingabeform
// stehen (ADR-S135-4); Hinweis und Meldung beschreiben das Feld gemeinsam, in der sichtbaren Reihenfolge.
async function expectMessageAtIngredients(page: Readonly<Page>, message: string): Promise<void> {
  await expect(page.getByText(message, { exact: true })).toBeVisible()
  await expect(page.getByText(INGREDIENTS_HINT)).toBeVisible()
  await expect(page.getByLabel('Zutaten')).toHaveAccessibleDescription(`${INGREDIENTS_HINT} ${message}`)
}

// Eingaben und Meldung der Szenarien von „Anlegen·Validierung Titel und Anweisung".
const PANCAKES = 'Pfannkuchen'
const INGREDIENTS_MEHL = '250 g Mehl'
const FIRST_STEP = 'Teig rühren.'
const INSTRUCTION_OF_1001_CHARS = 'a'.repeat(1001)
const STEP_TOO_LONG = 'Schritt-Anweisung darf maximal 1000 Zeichen lang sein.'

// Leerzeichen ohne Breite (U+200B) – als Codepunkt, nie als Literal oder Escape (CGG-naming).
const ZERO_WIDTH_SPACE = String.fromCodePoint(0x200B)
// Eine Eingabe „nur aus Leerzeichen ohne Breite": mehrere davon, damit nicht ein einzelnes Zeichen den Fall trägt.
const ONLY_ZERO_WIDTH_SPACES = ZERO_WIDTH_SPACE.repeat(2)

// Je zwei Leerzeichen davor und dahinter, im Inneren jedes einfache Leerzeichen verdoppelt.
const withExtraSpaces = (text: string): string => `  ${text.replaceAll(' ', '  ')}  `

// Das Schrittfeld mit der sichtbaren Nummer „Schritt N".
function stepField(page: Readonly<Page>, number: number): Locator {
  return stepsSection(page).getByLabel(`Schritt ${String(number)}`)
}

// When „ich <Titel> als Titel eingebe", „ich <Zutaten> als Zutaten eingebe" (ohne Angabe "250 g Mehl") und je
// Schritt „ich … als Schritt eingebe", vor jedem weiteren Schritt „ich auf "Schritt hinzufügen" klicke".
// Nacheinander per reduce: Die Reihenfolge ist Teil der Eingabe, und `functional/no-loop-statements` verbietet for…of.
async function fillRecipeForm(
  page: Readonly<Page>, title: string, steps: readonly [string, ...string[]], ingredients: string = INGREDIENTS_MEHL,
): Promise<void> {
  const [firstStep, ...furtherSteps] = steps
  await page.getByLabel('Titel').fill(title)
  await page.getByLabel('Zutaten').fill(ingredients)
  await stepField(page, 1).fill(firstStep)
  await furtherSteps.reduce(async (previous, instruction, index) => {
    await previous
    await page.getByRole('button', { name: 'Schritt hinzufügen' }).click()
    await stepField(page, index + 2).fill(instruction)
  }, Promise.resolve())
}

// Then „bin ich weiterhin im Formular mit allen Eingaben": Formular, Titel, Zutaten und jedes Schrittfeld
// mit seinem eingegebenen Wert (roh – auch Leerraum bleibt stehen).
async function expectFormWithInputs(
  page: Readonly<Page>, title: string, steps: readonly string[], ingredients: string = INGREDIENTS_MEHL,
): Promise<void> {
  await expectForm(page)
  await expect(page.getByLabel('Titel')).toHaveValue(title)
  await expect(page.getByLabel('Zutaten')).toHaveValue(ingredients)
  await expectStepNumbers(page, steps.map((_, index) => index + 1))
  await Promise.all(steps.map(async (instruction, index) => {
    await expect(stepField(page, index + 1)).toHaveValue(instruction)
  }))
}

// Then „sehe ich am <n.> Schritt die Fehlermeldung …": je genanntem Schrittfeld eine sichtbare Meldung, als
// Beschreibung mit dem Feld verknüpft, und das Feld ist als fehlerhaft markiert. Die Anzahl der sichtbaren
// Meldungen pinnt, dass keine weitere dazukommt.
async function expectMessageAtSteps(page: Readonly<Page>, numbers: readonly number[], message: string): Promise<void> {
  const messages = stepsSection(page).getByText(message, { exact: true })
  await expect(messages).toHaveCount(numbers.length)
  await Promise.all(numbers.map(async (number, index) => {
    await expect(messages.nth(index)).toBeVisible()
    await expect(stepField(page, number)).toHaveAccessibleDescription(message)
    await expect(stepField(page, number)).toHaveAttribute('aria-invalid', 'true')
  }))
}

// Then „ist der <n.> Schritt nicht als fehlerhaft markiert": ohne Meldung und nicht als fehlerhaft ausgezeichnet.
async function expectStepsNotMarked(page: Readonly<Page>, numbers: readonly number[]): Promise<void> {
  await Promise.all(numbers.map(async (number) => {
    await expect(stepField(page, number)).toHaveAccessibleDescription('')
    await expect(stepField(page, number)).not.toHaveAttribute('aria-invalid', 'true')
  }))
}

// Ein Eintrag der Schrittliste der Detailansicht, roh geprüft (exactText.ts): sichtbare Nummer „N.", höchstens ein
// Leerzeichen, dann genau diese Anweisung – ein Zeilenumbruch irgendwo fiele auf.
const numberedStep = (number: number, instruction: string): RegExp =>
  new RegExp(`^${String(number)}\\. ?${escapeRegExp(instruction)}$`)

// Then „zeigt die Detailansicht die Schritte als einzelne Einträge …": das Array pinnt Anzahl und Reihenfolge.
async function expectDetailSteps(page: Readonly<Page>, instructions: readonly string[]): Promise<void> {
  await expect(page.getByRole('list', { name: 'Zubereitung' }).getByRole('listitem'))
    .toHaveText(instructions.map((instruction, index) => numberedStep(index + 1, instruction)))
}

// Titel aus „Titel und Anweisung werden mit zusammengefasstem Leerraum … gespeichert": so gespeichert und angezeigt.
const LENTIL_SOUP = 'linsensuppe vom blech'

// @US-602-happy-path
test.describe('US602_HappyPath: Rezeptformular öffnen', () => {
  // Szenario: Felder sind beim Öffnen des Formulars leer
  test('US602_HappyPath_OpenCreateForm_FromList_FieldsAreEmpty', async ({ page }) => {
    // When: ich zur Rezepte-Seite navigiere und auf "Rezept anlegen" klicke
    await openCreateForm(page)

    // Then: Titel und Zutatenfeld leer, genau ein leeres Schrittfeld mit der Nummer 1
    await expectEmptyForm(page)
  })

  // Szenario: Pflichtfelder im Formular sind als solche markiert
  test('US602_HappyPath_OpenCreateForm_FromList_RequiredFieldsAreMarked', async ({ page }) => {
    // When: ich zur Rezepte-Seite navigiere und auf "Rezept anlegen" klicke
    await openCreateForm(page)

    // Then: Titel- und Zutatenfeld als Pflichtfeld markiert – der sichtbare Asterisk im Label ist die
    //   maßgebliche Beobachtung (e2e-testing.md, sichtbares Signal), die native required-Property sichert
    //   zusätzlich die Semantik für Screenreader. getByLabel matcht per Substring weiter "Titel *".
    await expect(page.locator('label').filter({ hasText: /^Titel/ })).toContainText('*')
    await expect(page.locator('label').filter({ hasText: /^Zutaten/ })).toContainText('*')
    await expect(page.getByLabel('Titel')).toHaveJSProperty('required', true)
    await expect(page.getByLabel('Zutaten')).toHaveJSProperty('required', true)
    // Then: der Abschnitt "Schritte" als Pflichtangabe markiert – Asterisk an seiner Legende. Die
    //   einzelnen Schrittfelder sind keine Pflichtfelder: Leere Schrittfelder werden übergangen.
    await expect(stepsSection(page).locator('legend').filter({ hasText: /^Schritte/ })).toContainText('*')
  })

  // Szenario: Das Zutatenfeld erklärt seine Eingabeform
  test('US602_HappyPath_OpenCreateForm_IngredientsField_ShowsFormatHintBeforeAndWhileTyping', async ({ page }) => {
    // When: ich zur Rezepte-Seite navigiere und auf "Rezept anlegen" klicke
    await openCreateForm(page)

    // Then: der Hinweis steht sichtbar am Zutatenfeld – "am Feld" heißt: als Beschreibung mit ihm verknüpft
    const ingredientsField = page.getByLabel('Zutaten')
    await expect(page.getByText(INGREDIENTS_HINT)).toBeVisible()
    await expect(ingredientsField).toHaveAccessibleDescription(INGREDIENTS_HINT)

    // When: ich "250 g Mehl" als Zutaten eingebe
    await ingredientsField.fill('250 g Mehl')

    // Then: der Hinweis steht weiterhin da – ein Platzhalter verschwände hier
    await expect(page.getByText(INGREDIENTS_HINT)).toBeVisible()
    await expect(ingredientsField).toHaveAccessibleDescription(INGREDIENTS_HINT)
  })

  // Szenario: Beim Öffnen des Formulars liegt der Fokus auf dem Titel
  test('US602_HappyPath_OpenCreateForm_FromList_FocusOnTitle', async ({ page }) => {
    // When: ich zur Rezepte-Seite navigiere und auf "Rezept anlegen" klicke
    await openCreateForm(page)

    // Then: der Fokus liegt auf dem Titel-Feld
    await expect(page.getByLabel('Titel')).toBeFocused()
  })

  // Szenario: Jedes Schrittfeld zeigt seine Nummer
  test('US602_HappyPath_AddStep_Twice_StepFieldsAreNumberedInOrder', async ({ page }) => {
    // When: ich das Formular öffne und zweimal auf "Schritt hinzufügen" klicke
    await openCreateForm(page)
    await page.getByRole('button', { name: 'Schritt hinzufügen' }).click()
    await page.getByRole('button', { name: 'Schritt hinzufügen' }).click()

    // Then: die Schrittfelder tragen in dieser Reihenfolge die Nummern 1, 2, 3
    await expectStepNumbers(page, [1, 2, 3])
  })

  // Szenario: Nach „Schritt hinzufügen" liegt der Fokus im neuen Schrittfeld
  test('US602_HappyPath_AddStep_AfterFirstStep_FocusOnNewStepField', async ({ page }) => {
    // When: ich das Formular öffne, "Teig rühren." als Schritt eingebe und auf "Schritt hinzufügen" klicke
    await openCreateForm(page)
    await page.getByLabel('Schritt 1').fill('Teig rühren.')
    await page.getByRole('button', { name: 'Schritt hinzufügen' }).click()

    // Then: der Fokus liegt auf dem zweiten Schrittfeld
    await expect(stepsSection(page).getByRole('textbox').nth(1)).toBeFocused()
  })
})

// @US-602-edge-case
test.describe('US602_EdgeCase: Rezeptformular direkt öffnen', () => {
  // Szenario: Das Formular lässt sich über seine Adresse direkt öffnen und ist leer
  test('US602_EdgeCase_OpenCreateForm_ByAddressInNewWindow_FieldsAreEmpty', async ({ context }) => {
    // When: ich die Adresse des Formulars in einem neuen Browserfenster öffne – eine neue Seite ohne
    //   vorher geladene Anwendung; die Adresse ist /recipes/new (ADR-S135-4: eigene Seite, eigene Adresse)
    const newWindow = await context.newPage()
    await newWindow.goto('/recipes/new')

    // Then: das Formular "Rezept anlegen" mit leeren Feldern und genau einem Schrittfeld Nummer 1
    await expect(newWindow.getByRole('heading', { level: 1, name: 'Rezept anlegen' })).toBeVisible()
    await expectEmptyForm(newWindow)
  })
})

// Then „sehe ich die Rezept-Liste": ihre Adresse und ihr Seitentitel – eine leere Liste hat keine Einträge,
// an denen man sie erkennen könnte.
async function expectRecipeList(page: Readonly<Page>): Promise<void> {
  await expect(page).toHaveURL(/\/recipes$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Rezepte' })).toBeVisible()
}

// When „ich auf "Abbrechen" klicke".
async function cancelForm(page: Readonly<Page>): Promise<void> {
  await page.getByRole('button', { name: 'Abbrechen' }).click()
}

// When der Nachfrage-Szenarien: Formular öffnen, "Pfannkuchen" als Titel eingeben, auf "Abbrechen" klicken.
async function openDiscardQuestionWithTitle(page: Readonly<Page>): Promise<void> {
  await openCreateForm(page)
  await page.getByLabel('Titel').fill('Pfannkuchen')
  await cancelForm(page)
}

// Then „sehe ich die Rezept-Liste" und „wurde ich nicht gefragt, ob ich Eingaben verwerfen möchte" – eine
// Nachfrage hätte den Weg zur Liste angehalten.
async function expectListWithoutQuestion(page: Readonly<Page>): Promise<void> {
  await expectRecipeList(page)
  await expect(discardQuestion(page)).toHaveCount(0)
}

// Then „sehe ich das Formular mit dem Titel …": das Formular ist weiter offen und behält die Eingaben.
async function expectFormWithTitle(page: Readonly<Page>, title: string): Promise<void> {
  await expect(page).toHaveURL(/\/recipes\/new$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Rezept anlegen' })).toBeVisible()
  await expect(page.getByLabel('Titel')).toHaveValue(title)
}

// @US-602-happy-path
test.describe('US602_HappyPath: Rezeptformular abbrechen', () => {
  // Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste
  test('US602_HappyPath_CancelCreateForm_WithoutInput_ShowsListWithoutQuestion', async ({ page }) => {
    // When: ich das Formular öffne und auf "Abbrechen" klicke
    await openCreateForm(page)
    await cancelForm(page)

    // Then: sehe ich die Rezept-Liste und wurde nicht gefragt, ob ich Eingaben verwerfen möchte
    await expectListWithoutQuestion(page)
  })

  // Eine Zeile je Beispiel der Scenario Outline: Jedes Feld allein macht das Formular nicht leer – auch ein
  // späteres Schrittfeld, wenn das erste leer ist; dafür fügt `prepare` das Schrittfeld erst hinzu.
  const inputs: readonly {
    readonly eingabe: string
    readonly field: string
    readonly value: string
    readonly prepare?: (page: Readonly<Page>) => Promise<void>
  }[] = [
    { eingabe: '"Pfannkuchen" als Titel', field: 'Titel', value: 'Pfannkuchen' },
    { eingabe: '"Salz" als Zutaten', field: 'Zutaten', value: 'Salz' },
    { eingabe: '"Teig rühren." als Schritt', field: 'Schritt 1', value: 'Teig rühren.' },
    {
      eingabe: '"Teig rühren." als zweiten Schritt',
      field: 'Schritt 2',
      value: 'Teig rühren.',
      prepare: async (page) => { await page.getByRole('button', { name: 'Schritt hinzufügen' }).click() },
    },
  ]
  inputs.forEach(({ eingabe, field, value, prepare }) => {
    // Szenario: Abbrechen mit Eingaben fragt nach – Verwerfen führt zur Rezept-Liste
    test(`US602_HappyPath_CancelCreateForm_WithInput_DiscardShowsList (${eingabe})`, async ({ page }) => {
      // When: ich das Formular öffne, <Eingabe> eingebe und auf "Abbrechen" klicke
      await openCreateForm(page)
      await prepare?.(page)
      await page.getByLabel(field).fill(value)
      await cancelForm(page)

      // Then: sehe ich die Nachfrage "Eingaben verwerfen?"
      await expect(discardQuestion(page)).toBeVisible()

      // When: ich auf "Verwerfen" klicke
      await discardQuestion(page).getByRole('button', { name: 'Verwerfen' }).click()

      // Then: sehe ich die Rezept-Liste
      await expectRecipeList(page)
    })
  })

  // Szenario: Abbrechen mit Eingaben fragt nach – Weiter bearbeiten behält die Eingaben
  test('US602_HappyPath_CancelCreateForm_WithInput_ContinueEditingKeepsInput', async ({ page }) => {
    // When: ich das Formular öffne, "Pfannkuchen" als Titel und "250 g Mehl" als Zutaten eingebe
    await openCreateForm(page)
    await page.getByLabel('Titel').fill('Pfannkuchen')
    await page.getByLabel('Zutaten').fill('250 g Mehl')
    // When: ich auf "Abbrechen" und dann auf "Weiter bearbeiten" klicke
    await cancelForm(page)
    await discardQuestion(page).getByRole('button', { name: 'Weiter bearbeiten' }).click()

    // Then: sehe ich das Formular mit dem Titel "Pfannkuchen" und den Zutaten "250 g Mehl"
    await expectFormWithTitle(page, 'Pfannkuchen')
    await expect(page.getByLabel('Zutaten')).toHaveValue('250 g Mehl')
    // Then: sehe ich keine Nachfrage mehr
    await expect(discardQuestion(page)).toBeHidden()
  })

  // Szenario: Beim Öffnen der Nachfrage liegt der Fokus auf „Weiter bearbeiten"
  test('US602_HappyPath_CancelCreateForm_WithInput_FocusOnContinueEditing', async ({ page }) => {
    // When: ich das Formular öffne, "Pfannkuchen" als Titel eingebe und auf "Abbrechen" klicke
    await openDiscardQuestionWithTitle(page)

    // Then: liegt in der Nachfrage der Fokus auf "Weiter bearbeiten"
    await expect(discardQuestion(page).getByRole('button', { name: 'Weiter bearbeiten' })).toBeFocused()
  })
})

// @US-602-edge-case
test.describe('US602_EdgeCase: Rezeptformular abbrechen', () => {
  // Szenario: Abbrechen fragt nicht nach, wenn nur Leerraum eingegeben wurde
  // Leer heißt nach der Normalisierung leer (ADR-S135-1): Leerraum, Zeilenumbrüche und Leerzeichen ohne
  // Breite (U+200B) bleiben dabei nicht übrig.
  test('US602_EdgeCase_CancelCreateForm_OnlyWhitespace_ShowsListWithoutQuestion', async ({ page }) => {
    // When: ich das Formular öffne und in jedes Feld nur Leerraum eingebe
    await openCreateForm(page)
    await page.getByLabel('Titel').fill(` ${ZERO_WIDTH_SPACE}  ${ZERO_WIDTH_SPACE} `)
    await page.getByLabel('Zutaten').fill(`\n  \n${ZERO_WIDTH_SPACE}\n ${ZERO_WIDTH_SPACE} \n`)
    await page.getByLabel('Schritt 1').fill('   ')
    await page.getByRole('button', { name: 'Schritt hinzufügen' }).click()
    await page.getByLabel('Schritt 2').fill(ONLY_ZERO_WIDTH_SPACES)
    // When: ich auf "Abbrechen" klicke
    await cancelForm(page)

    // Then: sehe ich die Rezept-Liste und wurde nicht gefragt, ob ich Eingaben verwerfen möchte
    await expectListWithoutQuestion(page)
  })

  // Eine Zeile je Beispiel der Scenario Outline: die Zeichen, die ADR-S135-1 außer Leerzeichen ohne Breite
  // entfernt, und U+0085 als Unicode-Leerraum, den JavaScripts trim() nicht kennt.
  const vanishingCharacters = [
    { zeichen: 'ein weiches Trennzeichen (U+00AD)', text: String.fromCodePoint(0x00AD) },
    { zeichen: 'einen Wortverbinder (U+2060)', text: String.fromCodePoint(0x2060) },
    { zeichen: 'eine Byte-Order-Mark (U+FEFF)', text: String.fromCodePoint(0xFEFF) },
    { zeichen: 'einen Zeilenumbruch „Next Line“ (U+0085)', text: String.fromCodePoint(0x0085) },
  ] as const
  vanishingCharacters.forEach(({ zeichen, text }) => {
    // Szenario: Abbrechen fragt nicht nach, wenn der Titel nur Zeichen enthält, die beim Normalisieren wegfallen
    test(`US602_EdgeCase_CancelCreateForm_TitleOnlyVanishingCharacters_ShowsListWithoutQuestion (${zeichen})`, async ({ page }) => {
      // When: ich das Formular öffne, als Titel nur <Zeichen> eingebe und auf "Abbrechen" klicke
      await openCreateForm(page)
      await page.getByLabel('Titel').fill(text)
      await cancelForm(page)

      // Then: sehe ich die Rezept-Liste und wurde nicht gefragt, ob ich Eingaben verwerfen möchte
      await expectListWithoutQuestion(page)
    })
  })

  // Eine Zeile je Beispiel der Scenario Outline. Der Klick daneben trifft die linke obere Ecke: Dort liegt
  // bei jeder Fenstergröße der Hintergrund, nicht die mittig stehende Nachfrage.
  const closings = [
    { schliessen: 'Escape drücke', close: async (page: Readonly<Page>) => { await page.keyboard.press('Escape') } },
    { schliessen: 'neben die Nachfrage klicke', close: async (page: Readonly<Page>) => { await page.mouse.click(5, 5) } },
  ] as const
  closings.forEach(({ schliessen, close }) => {
    // Szenario: Escape oder Klick neben die Nachfrage behält die Eingaben
    test(`US602_EdgeCase_CancelCreateForm_CloseQuestionAside_KeepsInput (${schliessen})`, async ({ page }) => {
      // When: ich das Formular öffne, "Pfannkuchen" als Titel eingebe und auf "Abbrechen" klicke
      await openDiscardQuestionWithTitle(page)
      // Erst wenn der Fokus in der Nachfrage liegt, erreicht Escape ihren Handler – sonst prüfte die
      // Zeile ein Timing statt des Verhaltens.
      await expect(discardQuestion(page).getByRole('button', { name: 'Weiter bearbeiten' })).toBeFocused()
      // When: ich <Schließen>
      await close(page)

      // Then: sehe ich das Formular mit dem Titel "Pfannkuchen"
      await expectFormWithTitle(page, 'Pfannkuchen')
      // Then: sehe ich keine Nachfrage mehr
      await expect(discardQuestion(page)).toBeHidden()
    })
  })

  // Szenario: Nach Verwerfen ist das Formular beim erneuten Öffnen leer
  test('US602_EdgeCase_DiscardCreateForm_ReopenForm_FieldsAreEmpty', async ({ page }) => {
    // When: ich das Formular öffne, Titel und Zutaten eingebe und einen Schritt hinzufüge
    await openCreateForm(page)
    await page.getByLabel('Titel').fill('Pfannkuchen')
    await page.getByLabel('Zutaten').fill('250 g Mehl')
    await page.getByRole('button', { name: 'Schritt hinzufügen' }).click()
    // When: ich auf "Abbrechen" und auf "Verwerfen" klicke
    await cancelForm(page)
    await discardQuestion(page).getByRole('button', { name: 'Verwerfen' }).click()
    // When: ich auf "Rezept anlegen" klicke
    await page.getByRole('button', { name: 'Rezept anlegen' }).click()

    // Then: Titel und Zutatenfeld leer, genau ein leeres Schrittfeld mit der Nummer 1
    await expectEmptyForm(page)
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
    { kennung: 'einer gültig aufgebauten, unbekannten Kennung', id: UNKNOWN_RECIPE_ID },
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
      await expectRecipeList(page)
    })
  })
})

// @US-602-error
test.describe('US602_Error: Rezept ohne Pflichtangaben', () => {
  // Szenario: Leeres Formular speichern zeigt alle Pflichtmeldungen gleichzeitig
  // Der Klick auf "Speichern" im leeren Formular hält zugleich formNoValidate: Ohne das Attribut hielte
  // der Browser das Absenden der required-Felder an, und keine Meldung käme vom Server.
  test('US602_Error_CreateRecipe_EmptyForm_ShowsAllRequiredMessagesAndFocusOnTitle', async ({ page, request }) => {
    // Given: der Stand der Rezept-Liste (für „unverändert")
    const recipesBefore = await fetchRecipeTitlesViaApi(request)

    // When: ich das Formular öffne und auf "Speichern" klicke
    await openCreateForm(page)
    await saveForm(page)

    // Then: am Titel, bei den Zutaten und bei den Schritten je die Pflichtmeldung – gleichzeitig
    await expectMessageAt(page, page.getByLabel('Titel'), 'Titel darf nicht leer sein.')
    await expectMessageAtIngredients(page, 'Rezept muss mindestens eine Zutat haben.')
    await expectMessageAt(page, stepsSection(page), 'Rezept muss mindestens einen Schritt haben.')
    // Then: der Fokus liegt auf dem Titel-Feld – alle drei sind fehlerhaft, das erste gewinnt (ADR-S135-4)
    await expect(page.getByLabel('Titel')).toBeFocused()
    // Then: weiterhin im Formular
    await expectForm(page)
    // Then: die Rezept-Liste ist unverändert
    expect(await fetchRecipeTitlesViaApi(request)).toEqual(recipesBefore)
  })

  // <Ort> und <Fokus> der Outline: wo die Meldung steht und welches Feld danach den Fokus hat.
  const atIngredients = {
    expectMessage: expectMessageAtIngredients,
    focusTarget: (page: Readonly<Page>) => page.getByLabel('Zutaten'),
  }
  const atSteps = {
    expectMessage: (page: Readonly<Page>, message: string) => expectMessageAt(page, stepsSection(page), message),
    focusTarget: (page: Readonly<Page>) => stepsSection(page).getByLabel('Schritt 1'),
  }
  // Eine Zeile je Beispiel der Scenario Outline. Leere Schrittfelder schickt das Formular nicht mit
  // (ADR-S135-3) – ein Schritt aus Leerzeichen meldet deshalb den fehlenden Schritt, nicht die leere Anweisung.
  const missingParts = [
    {
      eingabe: '"Teig rühren." als Schritt eingebe',
      ingredients: '', step: 'Teig rühren.',
      at: atIngredients, message: 'Rezept muss mindestens eine Zutat haben.',
    },
    {
      eingabe: 'als Zutaten nur leere Zeilen und Leerzeichen und "Teig rühren." als Schritt eingebe',
      ingredients: '\n   \n\n  \n', step: 'Teig rühren.',
      at: atIngredients, message: 'Rezept muss mindestens eine Zutat haben.',
    },
    {
      eingabe: '"250 g Mehl" als Zutaten eingebe',
      ingredients: '250 g Mehl', step: '',
      at: atSteps, message: 'Rezept muss mindestens einen Schritt haben.',
    },
    {
      eingabe: '"250 g Mehl" als Zutaten und "   " als Schritt eingebe',
      ingredients: '250 g Mehl', step: '   ',
      at: atSteps, message: 'Rezept muss mindestens einen Schritt haben.',
    },
  ] as const
  missingParts.forEach(({ eingabe, ingredients, step, at, message }) => {
    // Szenario: Rezept ohne Zutat oder ohne Schritt
    test(`US602_Error_CreateRecipe_WithoutIngredientOrStep_ShowsMessageAndKeepsInput (${eingabe})`, async ({ page, request }) => {
      // Given: die Zutat "Mehl" mit Einheit "g" existiert
      await seedIngredientViaApi(request, 'Mehl', 'g')
      const recipesBefore = await fetchRecipeTitlesViaApi(request)

      // When: ich das Formular öffne, "Pfannkuchen" als Titel und <Eingabe> eingebe und auf "Speichern" klicke
      await openCreateForm(page)
      await page.getByLabel('Titel').fill('Pfannkuchen')
      await page.getByLabel('Zutaten').fill(ingredients)
      await page.getByLabel('Schritt 1').fill(step)
      await saveForm(page)

      // Then: die Meldung <Ort>, der Fokus auf <Fokus>
      await at.expectMessage(page, message)
      await expect(at.focusTarget(page)).toBeFocused()
      // Then: weiterhin im Formular mit allen Eingaben
      await expectForm(page)
      await expect(page.getByLabel('Titel')).toHaveValue('Pfannkuchen')
      await expect(page.getByLabel('Zutaten')).toHaveValue(ingredients)
      await expectStepNumbers(page, [1])
      await expect(stepsSection(page).getByLabel('Schritt 1')).toHaveValue(step)
      // Then: die Rezept-Liste ist unverändert
      expect(await fetchRecipeTitlesViaApi(request)).toEqual(recipesBefore)
    })
  })

  // Szenario: Ein Rezept mit einer leeren Schritt-Anweisung wird abgelehnt
  // Der Speicher-Befehl geht direkt an die API: Das Formular schickt leere Schrittfelder gar nicht erst mit
  // (ADR-S135-3), der Server hält die Regel trotzdem ein.
  test('US602_Error_CreateRecipeViaApi_BlankSecondStep_RejectsWithMessageAtSecondStep', async ({ request }) => {
    // Given: die Zutat "Mehl" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')
    const recipesBefore = await fetchRecipeTitlesViaApi(request)

    // When: ich den Speicher-Befehl für "Pfannkuchen" mit "250 g Mehl" und den Schritten "Teig rühren." und "   " absende
    const response = await postRecipeViaApi(request, {
      title: 'Pfannkuchen',
      ingredients: '250 g Mehl',
      steps: [{ instruction: 'Teig rühren.' }, { instruction: '   ' }],
    })

    // Then: die Meldung am zweiten Schritt – und nur sie (Full State des Fehler-Bodys, ADR-S090-1).
    //   ADR-S144-1: der Key ist der Pfad des Feldes in der gesendeten Liste, 0-basiert.
    expect(response.status()).toBe(422)
    const body = await response.json() as { readonly errors: Readonly<Record<string, readonly string[]>> }
    expect(body.errors).toEqual({ 'steps[1].instruction': ['Schritt-Anweisung darf nicht leer sein.'] })
    // Then: die Rezept-Liste ist unverändert
    expect(await fetchRecipeTitlesViaApi(request)).toEqual(recipesBefore)
  })
})

// @US-602-error
test.describe('US602_Error: Titel und Anweisung ungültig', () => {
  const invalidTitles = [
    { eingabe: '"   "', title: '   ', message: 'Titel darf nicht leer sein.' },
    { eingabe: 'einen Text aus 101 Zeichen', title: 'T'.repeat(101), message: 'Titel darf maximal 100 Zeichen lang sein.' },
  ] as const
  invalidTitles.forEach(({ eingabe, title, message }) => {
    // Szenario: Ungültiger Titel
    test(`US602_Error_CreateRecipe_InvalidTitle_ShowsMessageAtTitleAndKeepsInput (${eingabe})`, async ({ page, request }) => {
      // Given: die Zutat "Mehl" mit Einheit "g" existiert
      await seedIngredientViaApi(request, 'Mehl', 'g')
      const recipesBefore = await fetchRecipeTitlesViaApi(request)

      // When: Formular öffnen, <Titel>, "250 g Mehl" und den Schritt "Teig rühren." eingeben, speichern
      await openCreateForm(page)
      await fillRecipeForm(page, title, [FIRST_STEP])
      await saveForm(page)

      // Then: am Titel die Meldung, der Fokus auf dem Titel-Feld
      await expectMessageAt(page, page.getByLabel('Titel'), message)
      await expect(page.getByLabel('Titel')).toBeFocused()
      // Then: weiterhin im Formular mit allen Eingaben
      await expectFormWithInputs(page, title, [FIRST_STEP])
      // Then: die Rezept-Liste ist unverändert
      expect(await fetchRecipeTitlesViaApi(request)).toEqual(recipesBefore)
    })
  })

  // Szenario: Schritt-Anweisung mit mehr als 1000 Zeichen
  test('US602_Error_CreateRecipe_SecondStepOf1001Chars_ShowsMessageAtSecondStepAndKeepsInput', async ({ page, request }) => {
    // Given: die Zutat "Mehl" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')
    const recipesBefore = await fetchRecipeTitlesViaApi(request)

    // When: "Pfannkuchen", "250 g Mehl", Schritt 1 "Teig rühren.", Schritt 2 aus 1001 Zeichen, speichern
    const steps = [FIRST_STEP, INSTRUCTION_OF_1001_CHARS] as const
    await openCreateForm(page)
    await fillRecipeForm(page, PANCAKES, steps)
    await saveForm(page)

    // Then: am zweiten Schritt die Meldung, der Fokus auf dem zweiten Schrittfeld
    await expectMessageAtSteps(page, [2], STEP_TOO_LONG)
    await expect(stepField(page, 2)).toBeFocused()
    // Then: weiterhin im Formular mit allen Eingaben
    await expectFormWithInputs(page, PANCAKES, steps)
    // Then: die Rezept-Liste ist unverändert
    expect(await fetchRecipeTitlesViaApi(request)).toEqual(recipesBefore)
  })

  // Szenario: Meldungen erscheinen am richtigen Schritt, auch hinter leeren Schrittfeldern
  // Das leere zweite Feld schickt das Formular nicht mit (ADR-S135-3): Der Server meldet den dritten
  // Schritt unter dem Index 1 der gesendeten Liste, das Formular zeigt die Meldung trotzdem am dritten Feld.
  test('US602_Error_CreateRecipe_LongThirdStepBehindBlankStep_ShowsMessageAtThirdStepOnly', async ({ page, request }) => {
    // Given: die Zutat "Mehl" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')

    // When: Schritt 1 "Teig rühren.", Schritt 2 "   ", Schritt 3 aus 1001 Zeichen, speichern
    await openCreateForm(page)
    await fillRecipeForm(page, PANCAKES, [FIRST_STEP, '   ', INSTRUCTION_OF_1001_CHARS])
    await saveForm(page)

    // Then: am dritten Schritt die Meldung, der erste und der zweite nicht als fehlerhaft markiert
    await expectMessageAtSteps(page, [3], STEP_TOO_LONG)
    await expectStepsNotMarked(page, [1, 2])
    // Then: der Fokus auf dem dritten Schrittfeld
    await expect(stepField(page, 3)).toBeFocused()
  })

  // Szenario: Alle fehlerhaften Schritte werden gemeldet, der Fokus liegt auf dem ersten
  test('US602_Error_CreateRecipe_TwoStepsOf1001Chars_ShowsMessageAtBothAndFocusOnFirst', async ({ page, request }) => {
    // Given: die Zutat "Mehl" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')

    // When: Schritt 1 "Teig rühren.", Schritte 2 und 3 je aus 1001 Zeichen, speichern
    await openCreateForm(page)
    await fillRecipeForm(page, PANCAKES, [FIRST_STEP, INSTRUCTION_OF_1001_CHARS, INSTRUCTION_OF_1001_CHARS])
    await saveForm(page)

    // Then: am zweiten und am dritten Schritt je die Meldung, der erste nicht als fehlerhaft markiert
    await expectMessageAtSteps(page, [2, 3], STEP_TOO_LONG)
    await expectStepsNotMarked(page, [1])
    // Then: der Fokus auf dem zweiten Schrittfeld – dem ersten fehlerhaften
    await expect(stepField(page, 2)).toBeFocused()
  })
})

// @US-602-edge-case
test.describe('US602_EdgeCase: Titel und Anweisung an der Längengrenze', () => {
  // Szenario: Titel und Anweisung mit genau der zulässigen Länge werden gespeichert
  test('US602_EdgeCase_CreateRecipe_TitleOf100AndInstructionOf1000Chars_ShowsDetailWithSingleSpaces', async ({ page, request }) => {
    // Given: die Zutat "Mehl" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')

    // When: Titel aus 100 und Anweisung aus 1000 Zeichen (normalisiert), je mit zusätzlichem Leerraum eingegeben
    const title = `${'T'.repeat(49)} ${'t'.repeat(50)}`
    const instruction = `${'A'.repeat(499)} ${'a'.repeat(500)}`
    expect(title).toHaveLength(100)
    expect(instruction).toHaveLength(1000)
    await openCreateForm(page)
    await fillRecipeForm(page, withExtraSpaces(title), [withExtraSpaces(instruction)])
    await saveForm(page)

    // Then: die Detailansicht des neuen Rezepts
    await expect(page).toHaveURL(RECIPE_DETAIL_URL)
    // Then: der Titel ist genau der Text aus 100 Zeichen, mit einfachem Leerzeichen (roher Text, exactText.ts)
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(exactly(title))
    // Then: der einzige Schritt ist genau die Anweisung aus 1000 Zeichen, mit einfachem Leerzeichen
    const stepItems = page.getByRole('list', { name: 'Zubereitung' }).getByRole('listitem')
    await expect(stepItems).toHaveCount(1)
    await expect(stepItems.getByText(instruction, { exact: true })).toHaveText(exactly(instruction))
  })
})

// @US-602-edge-case
test.describe('US602_EdgeCase: Eingaben bereinigen und erkennen', () => {
  // Szenario: Titel und Anweisung werden mit zusammengefasstem Leerraum und in eingegebener Schreibweise gespeichert
  test('US602_EdgeCase_CreateRecipe_TitleAndInstructionWithExtraWhitespace_ShowsCollapsedInEnteredCase', async ({ page, request }) => {
    // Given: die Zutat "Linsen" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Linsen', 'g')

    // When: Titel mit Leerraum außen und innen, kleingeschrieben; als Schritt eine Anweisung mit Zeilenumbrüchen,
    //   Tabulatoren und mehrfachen Leerzeichen zwischen "Linsen" und "kochen."
    await openCreateForm(page)
    await fillRecipeForm(page, '  linsensuppe   vom  blech  ', ['Linsen \n\t  \n\t kochen.'], '125 g Linsen')
    await saveForm(page)

    // Then: die Detailansicht des Rezepts "linsensuppe vom blech" – Schreibweise wie eingegeben (roher Text, exactText.ts)
    await expect(page).toHaveURL(RECIPE_DETAIL_URL)
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(exactly(LENTIL_SOUP))
    // Then: Schritt 1 "Linsen kochen." ohne Zeilenumbruch – roh geprüft, ein \n im Text fiele auf
    await expectDetailSteps(page, ['Linsen kochen.'])
    // Then: "linsensuppe vom blech" steht in der Rezept-Liste (die Liste hat genau diesen Eintrag)
    await page.goto('/recipes')
    await expect(page.getByRole('list', { name: 'Rezepte' }).getByRole('listitem')).toHaveText([exactly(LENTIL_SOUP)])
  })

  // Eine Zeile je Beispiel der Scenario Outline.
  const typicalLines = [
    { name: 'rote Linsen', unit: 'g', line: '125 g rote Linsen', display: '125 g rote Linsen' },
    { name: 'Vanillezucker', unit: 'Pck.', line: '1 Pck. Vanillezucker', display: '1 Pck. Vanillezucker' },
    { name: 'Mehl', unit: 'g', line: '250 G mehl', display: '250 g Mehl' },
    { name: 'schwarzer Pfeffer', unit: 'Prise', line: 'schwarzer pfeffer', display: 'schwarzer Pfeffer' },
  ] as const
  typicalLines.forEach(({ name, unit, line, display }) => {
    // Szenario: Zutatenzeilen in typischer Schreibweise werden erkannt und wie gespeichert angezeigt
    // Beispiel: alle
    test(`US602_EdgeCase_CreateRecipe_IngredientLineInTypicalNotation_ShowsAsStored (${line})`, async ({ page, request }) => {
      // Given: die Zutat <Name> mit Einheit <Einheit> existiert
      await seedIngredientViaApi(request, name, unit)

      // When: "Testrezept" als Titel, <Zeile> als Zutaten, "Alles mischen." als Schritt, dann speichern
      await openCreateForm(page)
      await fillRecipeForm(page, 'Testrezept', ['Alles mischen.'], line)
      await saveForm(page)

      // Then: die Detailansicht zeigt die Zutat <Anzeige> – die einzige Zutat des Rezepts
      await expect(page).toHaveURL(RECIPE_DETAIL_URL)
      await expect(page.getByRole('list', { name: 'Zutaten' }).getByRole('listitem')).toHaveText([exactly(display)])
    })
  })

  // Szenario: Leere Zeilen und Zeilen aus Leerzeichen im Zutatenfeld werden übergangen
  test('US602_EdgeCase_CreateRecipe_BlankIngredientLines_AreSkipped', async ({ page, request }) => {
    // Given: die Zutaten "Mehl" (g) und "Milch" (ml) existieren
    await seedIngredientViaApi(request, 'Mehl', 'g')
    await seedIngredientViaApi(request, 'Milch', 'ml')

    // When: als Zutaten "250 g Mehl", eine leere Zeile, eine Zeile aus Leerzeichen, eine Zeile nur aus Leerzeichen
    //   ohne Breite und "500 ml Milch"
    await openCreateForm(page)
    await fillRecipeForm(page, PANCAKES, [FIRST_STEP], `250 g Mehl\n\n   \n${ONLY_ZERO_WIDTH_SPACES}\n500 ml Milch`)
    await saveForm(page)

    // Then: die Detailansicht zeigt die Zutaten in dieser Reihenfolge: "250 g Mehl", "500 ml Milch"
    await expect(page).toHaveURL(RECIPE_DETAIL_URL)
    await expect(page.getByRole('list', { name: 'Zutaten' }).getByRole('listitem'))
      .toHaveText([exactly('250 g Mehl'), exactly('500 ml Milch')])
  })

  // Szenario: Leere Schrittfelder werden beim Speichern übergangen
  test('US602_EdgeCase_CreateRecipe_BlankStepBetweenSteps_IsSkipped', async ({ page, request }) => {
    // Given: die Zutat "Mehl" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')

    // When: "Pfannkuchen", "250 g Mehl", Schritte "Eier trennen.", "   ", "Eiweiß steif schlagen."
    await openCreateForm(page)
    await fillRecipeForm(page, PANCAKES, ['Eier trennen.', '   ', 'Eiweiß steif schlagen.'])
    await saveForm(page)

    // Then: die Schritte als einzelne Einträge: 1 "Eier trennen.", 2 "Eiweiß steif schlagen."
    await expect(page).toHaveURL(RECIPE_DETAIL_URL)
    await expectDetailSteps(page, ['Eier trennen.', 'Eiweiß steif schlagen.'])
  })

  // Szenario: Ein Schrittfeld nur aus Leerzeichen ohne Breite wird übergangen
  test('US602_EdgeCase_CreateRecipe_StepOfZeroWidthSpacesOnly_IsSkipped', async ({ page, request }) => {
    // Given: die Zutat "Mehl" mit Einheit "g" existiert
    await seedIngredientViaApi(request, 'Mehl', 'g')

    // When: "Pfannkuchen", "250 g Mehl", Schritte "Teig rühren." und eines nur aus Leerzeichen ohne Breite (U+200B)
    await openCreateForm(page)
    await fillRecipeForm(page, PANCAKES, [FIRST_STEP, ONLY_ZERO_WIDTH_SPACES])
    await saveForm(page)

    // Then: Schritt 1 "Teig rühren." als einziger Schritt
    await expect(page).toHaveURL(RECIPE_DETAIL_URL)
    await expectDetailSteps(page, [FIRST_STEP])
  })
})

// Meldungen der Mengenprüfung (ADR-S051-2, Addendum S135) – ohne das Zitat der Zeile davor.
const QUANTITY_NOT_A_NUMBER = 'Menge muss eine Zahl sein (z. B. 1,5).'
const QUANTITY_NOT_POSITIVE = 'Menge muss größer als 0 sein.'
const QUANTITY_TOO_MANY_DECIMALS = 'Menge darf maximal 3 Nachkommastellen haben.'
const QUANTITY_TOO_LARGE = 'Menge darf maximal 9999,999 sein.'

// @US-602-error
test.describe('US602_Error: Ungültige Menge', () => {
  // Eine Zeile je Beispiel der Scenario Outline.
  const invalidQuantities = [
    { line: '0 g Mehl', message: QUANTITY_NOT_POSITIVE },
    { line: '0,0005 g Mehl', message: QUANTITY_TOO_MANY_DECIMALS },
    { line: '10000,0005 g Mehl', message: QUANTITY_TOO_MANY_DECIMALS },
    { line: '1,0000000000000000000000000000001 g Mehl', message: QUANTITY_TOO_MANY_DECIMALS },
    { line: '0,0000000000000000000000000000001 g Mehl', message: QUANTITY_TOO_MANY_DECIMALS },
    { line: '10000 g Mehl', message: QUANTITY_TOO_LARGE },
    { line: '10000,000 g Mehl', message: QUANTITY_TOO_LARGE },
    { line: '100000000000000000000000000000 g Mehl', message: QUANTITY_TOO_LARGE },
    { line: '1.5 g Mehl', message: QUANTITY_NOT_A_NUMBER },
    { line: '1.000 g Mehl', message: QUANTITY_NOT_A_NUMBER },
    { line: '5, g Mehl', message: QUANTITY_NOT_A_NUMBER },
    { line: '1,5,5 g Mehl', message: QUANTITY_NOT_A_NUMBER },
  ] as const
  invalidQuantities.forEach(({ line, message }) => {
    // Szenario: Ungültige Menge in einer Zutatenzeile
    // Beispiel: alle
    test(`US602_Error_CreateRecipe_InvalidQuantity_ShowsMessageQuotingLine (${line})`, async ({ page, request }) => {
      // Given: die Zutat "Mehl" mit Einheit "g" existiert
      await seedIngredientViaApi(request, 'Mehl', 'g')
      const recipesBefore = await fetchRecipeTitlesViaApi(request)

      // When: Formular öffnen, "Pfannkuchen", <Zeile> als Zutaten und den Schritt "Teig rühren." eingeben, speichern
      await openCreateForm(page)
      await fillRecipeForm(page, PANCAKES, [FIRST_STEP], line)
      await saveForm(page)

      // Then: bei den Zutaten genau die Meldung „<Zeile>“: <Meldung> – der Hinweis plus genau diese Meldung
      //   bilden die ganze Beschreibung des Felds, eine weitere Meldung fiele auf
      await expectMessageAtIngredients(page, `„${line}“: ${message}`)
      // Then: der Fokus liegt auf dem Zutatenfeld
      await expect(page.getByLabel('Zutaten')).toBeFocused()
      // Then: weiterhin im Formular mit allen Eingaben
      await expectFormWithInputs(page, PANCAKES, [FIRST_STEP], line)
      // Then: die Rezept-Liste ist unverändert
      expect(await fetchRecipeTitlesViaApi(request)).toEqual(recipesBefore)
    })
  })
})

// @US-602-edge-case
test.describe('US602_EdgeCase: Mengen an den Grenzen', () => {
  // Eine Zeile je Beispiel der Scenario Outline. Nullen am Ende zählen nicht als Nachkommastellen.
  const boundaryQuantities = [
    { line: '0,001 g Mehl', display: '0,001 g Mehl' },
    { line: '9999,999 g Mehl', display: '9999,999 g Mehl' },
    { line: '0,0010 g Mehl', display: '0,001 g Mehl' },
    { line: '9999,9990 g Mehl', display: '9999,999 g Mehl' },
    { line: '1,5 g Mehl', display: '1,5 g Mehl' },
  ] as const
  boundaryQuantities.forEach(({ line, display }) => {
    // Szenario: Mengen an den Grenzen werden gespeichert und angezeigt
    // Beispiel: alle
    test(`US602_EdgeCase_CreateRecipe_QuantityAtBoundary_ShowsAsStored (${line})`, async ({ page, request }) => {
      // Given: die Zutat "Mehl" mit Einheit "g" existiert
      await seedIngredientViaApi(request, 'Mehl', 'g')

      // When: Formular öffnen, "Pfannkuchen", <Zeile> als Zutaten und den Schritt "Teig rühren." eingeben, speichern
      await openCreateForm(page)
      await fillRecipeForm(page, PANCAKES, [FIRST_STEP], line)
      await saveForm(page)

      // Then: die Detailansicht zeigt die Zutat <Anzeige> – die einzige Zutat des Rezepts
      await expect(page).toHaveURL(RECIPE_DETAIL_URL)
      await expect(page.getByRole('list', { name: 'Zutaten' }).getByRole('listitem')).toHaveText([exactly(display)])
    })
  })
})

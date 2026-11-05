import type { Locator, Page } from '@playwright/test'
import { test, expect } from './fixtures'
import { seedIngredientViaApi } from './api/ingredientsApi'
import { exactly } from './exactText'

// Querschnitt @CROSS-text (features/text-input.feature, ADR-S135-1): Texteingaben werden vor Prüfung und
// Speicherung normalisiert. Die Zutaten-Seite steht als Vertreter für jedes Textfeld – garantiert wird die
// Regel über den geteilten Texttyp des Servers (ADR-S112-5), die Rezeptfelder prüft recipes.spec.ts.
//
// Assertion-Technik: lokalisiert per String, geprüft wird der rohe DOM-Text per verankerter Regex (exactText.ts).
//
// Unsichtbare, Leerraum- und kombinierende Zeichen stehen als Codepunkte (fromCodePoints), nie als Literal oder
// \u-Escape im Quelltext: Literale sind unsichtbar und überstehen kein Editor-Normalisieren, \u-Escapes werden
// schon beim Schreiben der Datei durch die Werkzeugkette zu Literalen aufgelöst. Sichtbare
// Buchstaben wie das vorkomponierte „ä" stehen als Literal – ginge es verloren, würde der Test laut rot.
const fromCodePoints = (...codePoints: readonly number[]): string => String.fromCodePoint(...codePoints)

async function openCreateDialog(page: Readonly<Page>): Promise<void> {
  await page.getByRole('button', { name: 'Zutat anlegen' }).click()
}

async function fillAndSave(page: Readonly<Page>, name: string, baseUnit: string): Promise<void> {
  await page.getByLabel('Name').fill(name)
  await page.getByLabel('Einheit').fill(baseUnit)
  await page.getByRole('button', { name: 'Speichern' }).click()
}

const ingredientList = (page: Readonly<Page>): Locator => page.getByTestId('ingredient-list')

test.describe('CROSS_Text: Normalisierung', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ingredients')
  })

  // Szenario: Mehrfacher Leerraum im Inneren wird zu einem Leerzeichen
  test('CROSS_Text_Collapse_CreateIngredient_RepeatedInnerWhitespace_AppearsWithSingleSpace', async ({ page }) => {
    // Given: Zutaten-Seite geöffnet, keine Zutaten (beforeEach, Datenbank-Reset der Fixture)
    // When: Name mit mehrfachen Leerzeichen und Tabulator, Einheit mit mehrfachen Leerzeichen, speichern
    await openCreateDialog(page)
    await fillAndSave(page, `rote   ${fromCodePoints(0x0009)}Linsen`, 'kleine   Dose')

    // Then: Name und Einheit stehen mit je einem Leerzeichen in der Liste (roher Text, s. Kopf)
    const list = ingredientList(page)
    await expect(list.getByText('rote Linsen', { exact: true })).toHaveText(exactly('rote Linsen'))
    await expect(list.getByText('kleine Dose', { exact: true })).toHaveText(exactly('kleine Dose'))
  })

  // Szenario: Die Längengrenze gilt für den normalisierten Wert
  test('CROSS_Text_Length_CreateIngredient_NameAt30CharsWithDoubleInnerSpace_AppearsWithSingleSpace', async ({ page }) => {
    // Given: Zutaten-Seite geöffnet, keine Zutaten (beforeEach, Datenbank-Reset der Fixture)
    // When: Name aus 30 Zeichen (normalisiert), mit doppeltem statt einfachem Leerzeichen eingegeben (31 roh)
    const normalizedName = `${'a'.repeat(14)} ${'b'.repeat(15)}`
    expect(normalizedName).toHaveLength(30)
    await openCreateDialog(page)
    await fillAndSave(page, normalizedName.replace(' ', '  '), 'g')

    // Then: die Zutat steht mit einfachem Leerzeichen in der Liste (roher Text, s. Kopf)
    await expect(ingredientList(page).getByText(normalizedName, { exact: true })).toHaveText(exactly(normalizedName))
  })

  // Szenario: Ein Wert nur aus unsichtbaren Zeichen gilt als leer
  test('CROSS_Text_InvisibleOnly_CreateIngredient_NameOfZeroWidthSpaces_ShowsEmptyNameError', async ({ page }) => {
    // Given: Zutaten-Seite geöffnet, keine Zutaten (beforeEach, Datenbank-Reset der Fixture)
    // When: als Name nur Leerzeichen ohne Breite, Einheit "g", speichern
    await openCreateDialog(page)
    await fillAndSave(page, fromCodePoints(0x200B, 0x200B, 0x200B), 'g')

    // Then: die Leer-Meldung erscheint am Namen
    await expect(page.getByText('Name darf nicht leer sein.')).toBeVisible()
  })

  // Je Zeile ein Vertreter seiner Zeichenmenge; jedes Zeichen einzeln prüft der Backend-Test.
  const characterSetExamples = [
    {
      eingabe: '"rote" und "Linsen" mit zwei gleichen Leerraum-Zeichen dazwischen, je eines der 25 aus White_Space',
      name: `rote${fromCodePoints(0x3000, 0x3000)}Linsen`, // ideographisches Leerzeichen
      then: async (page: Readonly<Page>) => {
        await expect(ingredientList(page).getByText('rote Linsen', { exact: true })).toHaveText(exactly('rote Linsen'))
      },
    },
    {
      eingabe: 'nur ein Leerraum- oder unsichtbares Zeichen, zweimal, je eines der 29',
      name: fromCodePoints(0x2028, 0x2028), // Zeilentrenner
      then: async (page: Readonly<Page>) => {
        await expect(page.getByText('Name darf nicht leer sein.')).toBeVisible()
      },
    },
    {
      eingabe: '"rote" und "Linsen" mit dem Steuerzeichen U+001C dazwischen',
      name: `rote${fromCodePoints(0x001C)}Linsen`,
      then: async (page: Readonly<Page>, name: string) => {
        await expect(ingredientList(page).getByText(name, { exact: true })).toHaveText(exactly(name))
      },
    },
  ] as const
  characterSetExamples.forEach(({ eingabe, name, then }) => {
    // Szenario: Genau die Leerraum- und die unsichtbaren Zeichen werden behandelt
    test(`CROSS_Text_CharacterSet_CreateIngredient_RepresentativeCharacter_IsHandledAsSpecified (${eingabe})`, async ({ page }) => {
      // Given: Zutaten-Seite geöffnet, keine Zutaten (beforeEach, Datenbank-Reset der Fixture)
      // When: Name mit dem Vertreter-Zeichen, Einheit "g", speichern
      await openCreateDialog(page)
      await fillAndSave(page, name, 'g')

      // Then: wie in der Beispielzeile angegeben
      await then(page, name)
    })
  })
})

// Eigener Block ohne beforeEach-Navigation: Die Duplikat-Fälle legen die vorhandene Zutat vor dem Laden an.
test.describe('CROSS_Text: Duplikat nach Normalisierung', () => {
  // Beispiel-Spalte `eingabe` = Zelle „Eingabe" der Beispieltabelle im Feature-File.
  const duplicateExamples = [
    { eingabe: '"rote" und "Linsen" mit zwei Leerzeichen dazwischen', existing: 'rote Linsen', input: 'rote  Linsen', normalized: 'rote Linsen' },
    { eingabe: '"rote" und "Linsen" mit einem geschützten Leerzeichen dazwischen', existing: 'rote Linsen', input: `rote${fromCodePoints(0x00A0)}Linsen`, normalized: 'rote Linsen' },
    { eingabe: '"rote" und "Linsen" mit einem schmalen geschützten Leerzeichen dazwischen', existing: 'rote Linsen', input: `rote${fromCodePoints(0x202F)}Linsen`, normalized: 'rote Linsen' },
    { eingabe: '"Käse" mit einem „ä“ aus „a“ und kombinierendem Trema', existing: 'Käse', input: `Ka${fromCodePoints(0x0308)}se`, normalized: 'Käse' },
    { eingabe: '"Käse" mit einem Leerzeichen ohne Breite nach dem „K“', existing: 'Käse', input: `K${fromCodePoints(0x200B)}äse`, normalized: 'Käse' },
    { eingabe: '"Käse" mit einem weichen Trennzeichen nach dem „K“', existing: 'Käse', input: `K${fromCodePoints(0x00AD)}äse`, normalized: 'Käse' },
    { eingabe: '"Käse" mit einem Wortverbinder nach dem „K“', existing: 'Käse', input: `K${fromCodePoints(0x2060)}äse`, normalized: 'Käse' },
    { eingabe: '"Käse" mit einer Byte-Order-Mark nach dem „K“', existing: 'Käse', input: `K${fromCodePoints(0xFEFF)}äse`, normalized: 'Käse' },
    { eingabe: '"Käse" mit einem Leerzeichen ohne Breite zwischen „a“ und kombinierendem Trema', existing: 'Käse', input: `Ka${fromCodePoints(0x200B, 0x0308)}se`, normalized: 'Käse' },
  ] as const
  duplicateExamples.forEach(({ eingabe, existing, input, normalized }) => {
    // Szenario: Ein nach der Normalisierung gleicher Name gilt als Duplikat
    test(`CROSS_Text_Duplicate_CreateIngredient_NormalizedEqualName_ShowsDuplicateError (${eingabe})`, async ({ page, request }) => {
      // Given: die Zutat existiert (Seed vor dem Laden, damit der initiale GET sie enthält)
      await seedIngredientViaApi(request, existing, 'g')
      await page.goto('/ingredients')
      // includeHidden: Der offene modale Dialog blendet die Liste für die Rollen-Abfrage aus (wie captureIngredientList).
      const listItems = ingredientList(page).getByRole('listitem', { includeHidden: true })
      await expect(listItems).toHaveCount(1)

      // When: denselben Namen in abweichender Kodierung mit Einheit "g" anlegen
      await openCreateDialog(page)
      await fillAndSave(page, input, 'g')

      // Then: die Duplikat-Meldung nennt den normalisierten Namen (roher Text, s. Kopf)
      const message = `Eine Zutat mit dem Namen '${normalized}' existiert bereits.`
      await expect(page.getByRole('dialog').getByText(/existiert bereits/)).toHaveText(exactly(message))
      // Then: die vorhandene Zutat steht genau einmal in der Liste
      await expect(listItems).toHaveCount(1)
      await expect(ingredientList(page).getByText(existing, { exact: true })).toHaveText(exactly(existing))
    })
  })
})

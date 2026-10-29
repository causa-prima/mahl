import { describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router'
import { delay, http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { AppRoutes } from '../App'
import RecipeDetailPage from './RecipeDetailPage'

function createQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

// Die ganze Anwendung ab dem Pfad: Rezept anlegen ist eine Navigation über mehrere Seiten (ADR-S135-4).
function renderApp(initialPath: string) {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[initialPath]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

// API-Vertrag POST /api/recipes: Antwort 201 mit vollem Body (ADR-S068-1); die
// Zutaten kommen zerlegt vom Server (ADR-S135-2), quantity/unit null = ohne Menge (ADR-S020-1).
const createdPancakes = {
  id: '3f2b8c1e-0000-4000-8000-000000000001',
  title: 'Pfannkuchen',
  ingredients: [
    { name: 'Salz', quantity: null, unit: null },
    { name: 'Mehl', quantity: 250, unit: 'g' },
    { name: 'Milch', quantity: 500, unit: 'ml' },
  ],
  steps: [
    { instruction: 'Mehl und Milch verrühren.' },
    { instruction: 'In der Pfanne ausbacken.' },
  ],
} as const

// Given (Szenario): Liste ist leer, der POST legt "Pfannkuchen" an. Liefert den Spion auf den Request
// (Body und Content-Type).
function useCreatePancakesHandlers() {
  const postedRequest = vi.fn()
  server.use(
    http.get('/api/recipes', () => HttpResponse.json([])),
    http.get(`/api/recipes/${createdPancakes.id}`, () => HttpResponse.json(createdPancakes)),
    http.post('/api/recipes', async ({ request }) => {
      postedRequest({ body: await request.json(), contentType: request.headers.get('Content-Type') })
      return HttpResponse.json(createdPancakes, { status: 201 })
    }),
  )
  return postedRequest
}

// Settle: der Submit löst Navigation und Rendern der Detailansicht aus; deren Ende abwarten, damit keine
// Arbeit über das Testende hinausläuft.
async function awaitDetailViewSettled() {
  await screen.findByRole('heading', { name: 'Pfannkuchen' })
}

// When (Szenario): zur Rezepte-Seite, "Rezept anlegen", Formular ausfüllen, "Speichern".
async function fillAndSavePancakes() {
  const user = userEvent.setup()
  renderApp('/recipes')
  fireEvent.click(await screen.findByRole('button', { name: 'Rezept anlegen' }))
  await user.type(await screen.findByLabelText(/^Titel/), 'Pfannkuchen')
  await user.type(screen.getByLabelText(/^Zutaten/), 'Salz\n250 g Mehl\n500 ml Milch')
  await user.type(screen.getByLabelText('Schritt 1'), 'Mehl und Milch verrühren.')
  fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))
  await user.type(await screen.findByLabelText('Schritt 2'), 'In der Pfanne ausbacken.')
  fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))
}

// Zwei Rezepte, damit ein falsch geladenes auffällt: "Brot" liefert "500 g Weizenmehl", "Pfannkuchen" "250 g Mehl".
const pancakes = {
  id: '3f2b8c1e-0000-4000-8000-000000000201',
  title: 'Pfannkuchen',
  ingredients: [{ name: 'Mehl', quantity: 250, unit: 'g' }],
  steps: [{ instruction: 'Teig rühren.' }],
} as const
const bread = {
  id: '3f2b8c1e-0000-4000-8000-000000000202',
  title: 'Brot',
  ingredients: [{ name: 'Weizenmehl', quantity: 500, unit: 'g' }],
  steps: [{ instruction: 'Teig kneten.' }],
} as const

// Given (Szenario): beide Rezepte existieren; Liste und Einzelabruf antworten je Kennung.
function useOpenRecipeHandlers() {
  server.use(
    http.get('/api/recipes', () => HttpResponse.json([pancakes, bread].map(({ id, title }) => ({ id, title })))),
    ...[pancakes, bread].map((recipe) => http.get(`/api/recipes/${recipe.id}`, () => HttpResponse.json(recipe))),
  )
}

// Then (Szenario): die Detailansicht zeigt "Pfannkuchen" mit eigener Zutat, nicht die Zutat von "Brot".
async function expectPancakesDetail() {
  await screen.findByRole('heading', { level: 1, name: 'Pfannkuchen' })
  const ingredients = within(screen.getByRole('list', { name: 'Zutaten' })).getAllByRole('listitem')
  expect(ingredients.map((item) => item.textContent)).toEqual(['250 g Mehl'])
  expect(screen.queryByText(/Weizenmehl/)).not.toBeInTheDocument()
}

// @US-602-happy-path
describe('Rezepte erfassen', () => {
  // Szenario: Rezept-Liste ist leer wenn keine Rezepte vorhanden sind
  it('US602_HappyPath_RecipesPage_EmptyDb_ShowsEmptyListAndCreateButton', async () => {
    // Given: es sind keine Rezepte vorhanden
    const recipesRequested = vi.fn()
    server.use(http.get('/api/recipes', () => {
      recipesRequested()
      return HttpResponse.json([])
    }))

    // When: ich zur Rezepte-Seite navigiere
    renderApp('/recipes')

    // Then: die Liste wurde abgefragt, Hinweis und Button sind sichtbar
    // (Der Leerzustand erscheint auch während des Ladens, TD-S101-1 – deshalb wird belegt, dass der
    // Abruf stattfand.)
    await waitFor(() => { expect(recipesRequested).toHaveBeenCalled() })
    expect(screen.getByText('Noch keine Rezepte angelegt.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rezept anlegen' })).toBeInTheDocument()
  })

  // Szenario: Rezept anlegen (Liste: "Pfannkuchen" steht genau einmal in der Rezept-Liste)
  it('US602_HappyPath_RecipesPage_ExistingRecipe_ShowsTitleInNamedList', async () => {
    // Given: das Rezept "Pfannkuchen" existiert
    server.use(http.get('/api/recipes', () => HttpResponse.json([{ id: createdPancakes.id, title: 'Pfannkuchen' }])))

    // When: ich zur Rezepte-Seite navigiere
    renderApp('/recipes')

    // Then: die Liste "Rezepte" enthält genau den Eintrag "Pfannkuchen"
    const items = await within(await screen.findByRole('list', { name: 'Rezepte' })).findAllByRole('listitem')
    expect(items.map((item) => item.textContent)).toEqual(['Pfannkuchen'])
  })

  // Szenario: Mehrere Rezepte erscheinen alphabetisch sortiert
  // Guard zu ADR-S142-1 (Invariante „Frontend sortiert nicht selbst"), kein Test, der Code treibt: Die
  // Sortierung ist Sache des Servers (DB-Collation); die Seite zeigt die gelieferte Reihenfolge
  // unverändert. Der Server liefert hier bewusst eine nicht-alphabetische Reihenfolge – nur so fällt
  // eine Client-Sortierung auf, die mit der Server-Collation konkurrieren würde.
  it('US602_HappyPath_RecipesPage_MultipleRecipes_RendersServerOrderUnchanged', async () => {
    // Given: der Server liefert vier Rezepte in einer bestimmten Reihenfolge
    const serverRecipes = [
      { id: '3f2b8c1e-0000-4000-8000-000000000101', title: 'Zwiebelkuchen' },
      { id: '3f2b8c1e-0000-4000-8000-000000000102', title: 'Ölkuchen' },
      { id: '3f2b8c1e-0000-4000-8000-000000000103', title: 'apfelstrudel' },
      { id: '3f2b8c1e-0000-4000-8000-000000000104', title: 'Brot' },
    ] as const
    server.use(http.get('/api/recipes', () => HttpResponse.json(serverRecipes)))

    // When: ich zur Rezepte-Seite navigiere
    renderApp('/recipes')

    // Then: die Liste zeigt die Titel in genau der gelieferten Reihenfolge
    const items = await within(await screen.findByRole('list', { name: 'Rezepte' })).findAllByRole('listitem')
    expect(items.map((item) => item.textContent)).toEqual(serverRecipes.map((recipe) => recipe.title))
  })

  // Szenario: Rezept anlegen
  it('US602_HappyPath_CreateRecipe_ValidData_SendsRequestContract', async () => {
    // Given: keine Rezepte, der POST akzeptiert das Rezept
    const postedRequest = useCreatePancakesHandlers()

    // When: Titel, Zutaten und zwei Schritte eingeben, speichern
    await fillAndSavePancakes()

    // Then: der Request trägt den rohen Zutatentext und die Schritte in Feldreihenfolge ohne Nummer;
    // der Server liest den Body nur mit JSON-Content-Type
    await waitFor(() => { expect(postedRequest).toHaveBeenCalledTimes(1) })
    expect(postedRequest).toHaveBeenCalledWith({
      body: {
        title: 'Pfannkuchen',
        ingredients: 'Salz\n250 g Mehl\n500 ml Milch',
        steps: [
          { instruction: 'Mehl und Milch verrühren.' },
          { instruction: 'In der Pfanne ausbacken.' },
        ],
      },
      contentType: 'application/json',
    })

    await awaitDetailViewSettled()
  })

  // Szenario: Rezept anlegen
  // Ohne Unterdrückung des nativen Submits lädt der echte Browser beim Absenden die Seite neu – das
  // Anlegen funktionierte nicht. fireEvent.submit liefert false, wenn preventDefault aufgerufen wurde.
  it('US602_HappyPath_CreateRecipe_Submit_NativeFormSubmitIsPrevented', async () => {
    // Given: das Formular "Rezept anlegen" ist offen
    // (Die Handler sind nur dafür da, dass der durch den Submit ausgelöste POST samt Navigation zur
    // Detailansicht nicht als unhandled request scheitert; ihre Rückgabe wird hier nicht gebraucht.)
    useCreatePancakesHandlers()
    renderApp('/recipes')
    fireEvent.click(await screen.findByRole('button', { name: 'Rezept anlegen' }))
    const form = (await screen.findByLabelText(/^Titel/)).closest('form')
    expect(form).not.toBeNull()

    // When: das Formular abgesendet wird
    const nativeSubmitProceeds = fireEvent.submit(form as HTMLFormElement)

    // Then: der native Submit wurde unterdrückt
    expect(nativeSubmitProceeds).toBe(false)

    await awaitDetailViewSettled()
  })

  // Szenario: Rezept anlegen
  it('US602_HappyPath_CreateRecipe_ValidData_ShowsDetailViewOfCreatedRecipe', async () => {
    // Given: keine Rezepte, der POST akzeptiert das Rezept
    useCreatePancakesHandlers()

    // When: Titel, Zutaten und zwei Schritte eingeben, speichern
    await fillAndSavePancakes()

    // Then: die Detailansicht zeigt Titel, Zutaten und nummerierte Schritte
    // (Sie lädt über die Kennung aus der Adresse; der Handler antwortet nur auf die Kennung des angelegten
    // Rezepts – die Adresse ist damit mitgeprüft.)
    expect(await screen.findByRole('heading', { name: 'Pfannkuchen' })).toBeInTheDocument()
    const ingredients = within(screen.getByRole('list', { name: 'Zutaten' })).getAllByRole('listitem')
    expect(ingredients.map((item) => item.textContent)).toEqual(['Salz', '250 g Mehl', '500 ml Milch'])
    const steps = within(screen.getByRole('list', { name: 'Zubereitung' })).getAllByRole('listitem')
    // Nummer + Anweisung als ein Eintrag; Trennzeichen/Darstellung der Nummer sind nicht Teil des Vertrags
    const stepTexts = steps.map((item) => item.textContent)
    expect(stepTexts).toHaveLength(2)
    expect(stepTexts[0]).toMatch(/^1\D+Mehl und Milch verrühren\.$/)
    expect(stepTexts[1]).toMatch(/^2\D+In der Pfanne ausbacken\.$/)
  })

  // Szenario: Rezept aus der Rezept-Liste öffnen
  // Die Rolle `link` hat ein <a> nur mit href – der Klick sichert damit zugleich einen echten Link (Lesezeichen,
  // neuer Tab, ADR-S135-5); die Adresse prüft der Handler, der nur auf die Kennung des Rezepts antwortet.
  it('US602_HappyPath_OpenRecipe_FromList_ShowsDetailOfClickedRecipe', async () => {
    // Given: zwei Rezepte – ein falsch geladenes Rezept fiele an seinen Zutaten auf
    useOpenRecipeHandlers()

    // When: ich zur Rezepte-Seite navigiere und auf "Pfannkuchen" klicke
    renderApp('/recipes')
    fireEvent.click(await screen.findByRole('link', { name: 'Pfannkuchen' }))

    // Then: die Detailansicht zeigt genau dieses Rezept
    await expectPancakesDetail()
    // Schritt 1 mit Nummer in einer geordneten Liste, damit ein Screenreader die Reihenfolge ansagt (UX-Baseline,
    // „Nummerierte Schritte"); die Rolle `list` gilt für ul und ol gleichermaßen, deshalb bleibt nur das Element.
    const stepList = screen.getByRole('list', { name: 'Zubereitung' })
    expect(stepList.tagName).toBe('OL')
    const steps = within(stepList).getAllByRole('listitem').map((item) => item.textContent)
    expect(steps).toHaveLength(1)
    expect(steps[0]).toMatch(/^1\D+Teig rühren\.$/)
  })

  // Szenario: Rezept per Direktlink aufrufen
  it('US602_HappyPath_OpenRecipe_ByDirectLink_ShowsDetail', async () => {
    // Given: zwei Rezepte
    useOpenRecipeHandlers()

    // When: ich den Direktlink des Rezepts "Pfannkuchen" öffne
    renderApp(`/recipes/${pancakes.id}`)

    // Then: die Detailansicht zeigt genau dieses Rezept
    await expectPancakesDetail()
  })

  // Querschnittsvertrag der Rezeptseiten (features/recipes.feature, ADR-S112-5): während des Ladens erscheint
  // weder der Leerzustand noch "Rezept nicht gefunden.". Kein Szenario treibt den Test, deshalb ohne US-Tag.
  it('RecipeDetailLoading_ResponsePending_ShowsNeitherNotFoundNorRecipe', async () => {
    // Given: der Server antwortet auf das Rezept noch nicht
    const recipeRequested = vi.fn()
    server.use(http.get(`/api/recipes/${pancakes.id}`, async () => {
      recipeRequested()
      await delay('infinite')
    }))

    // When: ich den Direktlink öffne
    renderApp(`/recipes/${pancakes.id}`)

    // Then: der Abruf lief, und es erscheint weder "nicht gefunden" noch ein Rezept
    await waitFor(() => { expect(recipeRequested).toHaveBeenCalled() })
    expect(screen.queryByText('Rezept nicht gefunden.')).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Pfannkuchen' })).not.toBeInTheDocument()
  })
})

const ingredientsHint = 'Eine Zutat je Zeile: Menge, Einheit, Zutat – z. B. „250 g Mehl“ oder „Salz“.'

// Given: die Rezept-Liste ist leer (die Szenarien setzen keine voraus) – When: zur Rezepte-Seite
// navigieren, "Rezept anlegen" klicken.
async function openCreateFormFromEmptyList() {
  server.use(http.get('/api/recipes', () => HttpResponse.json([])))
  renderApp('/recipes')
  fireEvent.click(await screen.findByRole('button', { name: 'Rezept anlegen' }))
  await screen.findByLabelText(/^Titel/)
}

function stepFields() {
  return screen.getAllByLabelText(/^Schritt \d+$/)
}

function expectEmptyForm() {
  expect(screen.getByLabelText(/^Titel/)).toHaveValue('')
  expect(screen.getByLabelText(/^Zutaten/)).toHaveValue('')
  expect(stepFields()).toHaveLength(1)
  expect(screen.getByLabelText('Schritt 1')).toHaveValue('')
}

// @US-602-happy-path
describe('Rezeptformular öffnen', () => {
  // Szenario: Felder sind beim Öffnen des Formulars leer
  it('US602_HappyPath_CreateForm_Opened_FieldsAreEmptyWithOneNumberedStep', async () => {
    // Given: die Rezept-Liste ist leer
    // When: Formular über die Liste öffnen
    await openCreateFormFromEmptyList()

    // Then: Titel und Zutaten leer, genau ein leeres Schrittfeld mit Nummer 1
    expectEmptyForm()
  })

  // Szenario: Pflichtfelder im Formular sind als solche markiert
  it('US602_HappyPath_CreateForm_Opened_RequiredFieldsAndStepsSectionAreMarked', async () => {
    // Given: die Rezept-Liste ist leer
    // When: Formular öffnen
    await openCreateFormFromEmptyList()

    // Then: Titel und Zutaten sind Pflichtfelder, der Abschnitt "Schritte" trägt sichtbar den Asterisk und
    // nennt die Pflichtangabe im zugänglichen Namen (der Asterisk ist aria-hidden)
    expect(screen.getByLabelText(/^Titel/)).toBeRequired()
    expect(screen.getByLabelText(/^Zutaten/)).toBeRequired()
    const group = screen.getByRole('group', { name: 'Schritte (Pflichtangabe)' })
    expect(within(group).getByText(/^Schritte/)).toHaveTextContent(/^Schritte\s*\*$/)
  })

  // Szenario: Das Zutatenfeld erklärt seine Eingabeform
  it('US602_HappyPath_CreateForm_IngredientsField_KeepsHintWhileTyping', async () => {
    // Given: Formular offen
    const user = userEvent.setup()
    await openCreateFormFromEmptyList()

    // Then: der Hinweis ist dem Feld als Beschreibung zugeordnet
    expect(screen.getByLabelText(/^Zutaten/)).toHaveAccessibleDescription(ingredientsHint)

    // When: Zutaten eingeben
    await user.type(screen.getByLabelText(/^Zutaten/), '250 g Mehl')

    // Then: der Hinweis bleibt stehen
    expect(screen.getByLabelText(/^Zutaten/)).toHaveAccessibleDescription(ingredientsHint)
  })

  // Szenario: Beim Öffnen des Formulars liegt der Fokus auf dem Titel
  it('US602_HappyPath_CreateForm_Opened_FocusIsOnTitle', async () => {
    // Given: die Rezept-Liste ist leer
    // When: Formular öffnen
    await openCreateFormFromEmptyList()

    // Then: Fokus auf dem Titel-Feld
    expect(screen.getByLabelText(/^Titel/)).toHaveFocus()
  })

  // Szenario: Jedes Schrittfeld zeigt seine Nummer
  it('US602_HappyPath_CreateForm_AddStepTwice_StepsAreNumbered123', async () => {
    // Given: Formular offen
    await openCreateFormFromEmptyList()

    // When: zweimal "Schritt hinzufügen"
    fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))
    fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))

    // Then: Nummern 1, 2, 3 in Reihenfolge
    const fields = stepFields()
    expect(fields).toHaveLength(3)
    expect(fields[0]).toBe(screen.getByLabelText('Schritt 1'))
    expect(fields[1]).toBe(screen.getByLabelText('Schritt 2'))
    expect(fields[2]).toBe(screen.getByLabelText('Schritt 3'))
  })

  // Szenario: Nach "Schritt hinzufügen" liegt der Fokus im neuen Schrittfeld
  it('US602_HappyPath_CreateForm_AddStep_FocusMovesToNewStepField', async () => {
    // Given: Formular offen, erster Schritt ausgefüllt
    const user = userEvent.setup()
    await openCreateFormFromEmptyList()
    await user.type(screen.getByLabelText('Schritt 1'), 'Teig rühren.')

    // When: "Schritt hinzufügen"
    fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))

    // Then: Fokus auf dem zweiten Schrittfeld
    expect(await screen.findByLabelText('Schritt 2')).toHaveFocus()
  })
})

// @US-602-edge-case
describe('Rezeptformular direkt öffnen', () => {
  // Szenario: Das Formular lässt sich über seine Adresse direkt öffnen und ist leer
  it('US602_EdgeCase_CreateForm_DirectAddress_OpensEmptyForm', () => {
    // Given: die Anwendung ist gestartet
    // When: Adresse des Formulars direkt öffnen
    renderApp('/recipes/new')

    // Then: Felder leer, ein Schrittfeld mit Nummer 1
    expectEmptyForm()
  })
})

type User = ReturnType<typeof userEvent.setup>

// Given/When (Szenario): Leerraum und unsichtbare Zeichen einfügen – sie stammen aus kopiertem Text
// (z. B. von Webseiten), nicht aus Tastenanschlägen. `user.paste` fügt ins fokussierte Element ein; der Klick
// fokussiert das Feld wie ein Nutzer vor dem Einfügen.
async function pasteText(user: User, field: Readonly<HTMLElement>, value: string) {
  await user.click(field)
  await user.paste(value)
}

function clickCancel() {
  fireEvent.click(screen.getByRole('button', { name: 'Abbrechen' }))
}

function discardQuestion() {
  return screen.getByRole('alertdialog', { name: 'Eingaben verwerfen?' })
}

function questionButton(name: 'Weiter bearbeiten' | 'Verwerfen') {
  return within(discardQuestion()).getByRole('button', { name })
}

function clickQuestionButton(name: 'Weiter bearbeiten' | 'Verwerfen') {
  fireEvent.click(questionButton(name))
}

// Given: Formular offen, Titel "Pfannkuchen" getippt, Abbrechen geklickt (Nachfrage offen).
async function openDiscardQuestionWithTitle(user: User) {
  await openCreateFormFromEmptyList()
  await user.type(screen.getByLabelText(/^Titel/), 'Pfannkuchen')
  clickCancel()
}

// Then: die Rezept-Liste ist zu sehen (Formular weg), es gab keine Nachfrage.
async function expectListWithoutQuestion() {
  await screen.findByRole('heading', { level: 1, name: 'Rezepte' })
  expect(screen.queryByLabelText(/^Titel/)).not.toBeInTheDocument()
  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
}

// Then: Nachfrage weg, Formular mit Titel noch da.
async function expectQuestionClosedAndTitleKept(title: string) {
  await waitFor(() => { expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument() })
  expect(screen.getByLabelText(/^Titel/)).toHaveValue(title)
}

// @US-602-happy-path
describe('Rezeptformular abbrechen', () => {
  // Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste
  it('US602_HappyPath_CreateForm_CancelWithoutInput_ShowsListWithoutQuestion', async () => {
    // Given: Formular offen, nichts eingegeben
    await openCreateFormFromEmptyList()

    // When: Abbrechen
    clickCancel()

    // Then: Rezept-Liste, keine Nachfrage
    await expectListWithoutQuestion()
  })

  // Szenario: Abbrechen mit Eingaben fragt nach – Verwerfen führt zur Rezept-Liste
  it.each([
    ['Titel', async (user: User) => { await user.type(screen.getByLabelText(/^Titel/), 'Pfannkuchen') }],
    ['Zutaten', async (user: User) => { await user.type(screen.getByLabelText(/^Zutaten/), 'Salz') }],
    ['Schritt', async (user: User) => { await user.type(screen.getByLabelText('Schritt 1'), 'Teig rühren.') }],
    // ADR-S135-4: ein beliebiges Feld mit Inhalt genügt, auch nur ein späterer Schritt
    ['zweiter Schritt', async (user: User) => {
      fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))
      await user.type(await screen.findByLabelText('Schritt 2'), 'Teig rühren.')
    }],
  ])('US602_HappyPath_CreateForm_CancelWithInput_DiscardShowsList (%s)', async (_feld, fillField) => {
    // Given: Formular offen, ein Feld ausgefüllt
    const user = userEvent.setup()
    await openCreateFormFromEmptyList()
    await fillField(user)

    // When: Abbrechen
    clickCancel()

    // Then: Nachfrage "Eingaben verwerfen?"
    expect(discardQuestion()).toBeInTheDocument()

    // When: Verwerfen
    clickQuestionButton('Verwerfen')

    // Then: Rezept-Liste
    await expectListWithoutQuestion()
  })

  // Szenario: Abbrechen mit Eingaben fragt nach – Weiter bearbeiten behält die Eingaben
  it('US602_HappyPath_CreateForm_CancelWithInput_KeepEditingKeepsInputs', async () => {
    // Given: Titel und Zutaten eingegeben, Abbrechen geklickt
    const user = userEvent.setup()
    await openCreateFormFromEmptyList()
    await user.type(screen.getByLabelText(/^Titel/), 'Pfannkuchen')
    await user.type(screen.getByLabelText(/^Zutaten/), '250 g Mehl')
    clickCancel()

    // When: Weiter bearbeiten
    clickQuestionButton('Weiter bearbeiten')

    // Then: Formular mit beiden Eingaben, keine Nachfrage
    await expectQuestionClosedAndTitleKept('Pfannkuchen')
    expect(screen.getByLabelText(/^Zutaten/)).toHaveValue('250 g Mehl')
  })

  // Szenario: Beim Öffnen der Nachfrage liegt der Fokus auf „Weiter bearbeiten"
  it('US602_HappyPath_CreateForm_DiscardQuestion_Opened_FocusIsOnKeepEditing', async () => {
    // Given: Titel eingegeben
    // When: Abbrechen (beides im Helfer)
    await openDiscardQuestionWithTitle(userEvent.setup())

    // Then: Fokus auf "Weiter bearbeiten" (nach der Öffnen-Transition, ADR-S100-1)
    await waitFor(() => { expect(questionButton('Weiter bearbeiten')).toHaveFocus() })
  })
})

// @US-602-edge-case
describe('Rezeptformular abbrechen – Randfälle', () => {
  // Szenario: Abbrechen fragt nicht nach, wenn nur Leerraum eingegeben wurde
  it('US602_EdgeCase_CreateForm_CancelWithOnlyBlankInput_ShowsListWithoutQuestion', async () => {
    // Given: Titel, Zutaten, Schritt 1 und Schritt 2 enthalten nur Leerraum bzw. unsichtbare Zeichen
    const user = userEvent.setup()
    await openCreateFormFromEmptyList()
    await pasteText(user, screen.getByLabelText(/^Titel/), ' \u{200B} ')
    await pasteText(user, screen.getByLabelText(/^Zutaten/), '\n  \n\u{200B}\n')
    await pasteText(user, screen.getByLabelText('Schritt 1'), '   ')
    fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))
    await pasteText(user, await screen.findByLabelText('Schritt 2'), '\u{200B}')

    // When: Abbrechen
    clickCancel()

    // Then: Rezept-Liste, keine Nachfrage
    await expectListWithoutQuestion()
  })

  // Szenario: Abbrechen fragt nicht nach, wenn der Titel nur Zeichen enthält, die beim Normalisieren wegfallen
  // ADR-S135-1: Jede Zeile ist ein Zeichen der Leer-Definition. U+0085 ist Unicode-Leerraum, den `trim()` nicht kennt.
  it.each([
    ['U+00AD', '\u{00AD}'],
    ['U+2060', '\u{2060}'],
    ['U+FEFF', '\u{FEFF}'],
    ['U+0085', '\u{0085}'],
  ])('US602_EdgeCase_CreateForm_CancelWithTitleOnlyVanishingCharacters_ShowsListWithoutQuestion (%s)', async (_name, text) => {
    // Given: nur ein wegfallendes Zeichen im Titel
    const user = userEvent.setup()
    await openCreateFormFromEmptyList()
    await pasteText(user, screen.getByLabelText(/^Titel/), text)

    // When: Abbrechen
    clickCancel()

    // Then: Rezept-Liste, keine Nachfrage
    await expectListWithoutQuestion()
  })

  // Szenario: Escape oder Klick neben die Nachfrage behält die Eingaben
  it.each([
    ['Escape', async (user: User) => {
      // Escape geht an das fokussierte Element: erst warten, bis der Fokus in der Nachfrage liegt
      await waitFor(() => { expect(questionButton('Weiter bearbeiten')).toHaveFocus() })
      await user.keyboard('{Escape}')
    }],
    // Das Elternelement der Nachfrage ist der MUI-Dialog-Container (der Backdrop-Bereich). MUI erkennt den
    // Klick daneben zweistufig: erst mouseDown auf den Container, dann click – click allein genügt nicht.
    ['Klick neben die Nachfrage', (): void => {
      const container = discardQuestion().parentElement as HTMLElement
      fireEvent.mouseDown(container)
      fireEvent.click(container)
    }],
  ])('US602_EdgeCase_CreateForm_DiscardQuestion_DismissedBy_KeepsInputs (%s)', async (_name, dismiss) => {
    // Given: Titel eingegeben, Nachfrage offen
    const user = userEvent.setup()
    await openDiscardQuestionWithTitle(user)
    expect(discardQuestion()).toBeInTheDocument()

    // When: Escape bzw. Klick neben die Nachfrage
    await dismiss(user)

    // Then: Formular mit Titel, keine Nachfrage
    await expectQuestionClosedAndTitleKept('Pfannkuchen')
  })

  // Szenario: Nach Verwerfen ist das Formular beim erneuten Öffnen leer
  it('US602_EdgeCase_CreateForm_DiscardThenReopen_FormIsEmpty', async () => {
    // Given: Titel, Zutaten und ein zweites Schrittfeld, Abbrechen und Verwerfen
    const user = userEvent.setup()
    await openCreateFormFromEmptyList()
    await user.type(screen.getByLabelText(/^Titel/), 'Pfannkuchen')
    await user.type(screen.getByLabelText(/^Zutaten/), '250 g Mehl')
    fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))
    clickCancel()
    clickQuestionButton('Verwerfen')

    // When: Rezept anlegen
    fireEvent.click(await screen.findByRole('button', { name: 'Rezept anlegen' }))

    // Then: leeres Formular mit genau einem Schrittfeld
    await screen.findByLabelText(/^Titel/)
    expectEmptyForm()
  })
})

// @US-602-error
describe('Rezepte erfassen – Fehlerfälle', () => {
  // Szenario: Direktlink auf ein Rezept, das es nicht gibt – Abgrenzung: nur 404 ist "nicht gefunden". Die
  // Behandlung anderer Fehler ist offen (TD-S083-1); belegt wird nur, dass sie nicht als "Rezept nicht gefunden."
  // erscheinen.
  it('US602_Error_OpenRecipe_NetworkFailure_DoesNotClaimRecipeIsMissing', async () => {
    // Given: der Abruf des Rezepts scheitert auf Netzwerkebene
    const recipeRequested = vi.fn()
    server.use(http.get(`/api/recipes/${pancakes.id}`, () => {
      recipeRequested()
      return HttpResponse.error()
    }))

    // When: ich den Direktlink öffne
    renderApp(`/recipes/${pancakes.id}`)

    // Then: der Abruf lief, und es erscheint nicht "nicht gefunden"
    await waitFor(() => { expect(recipeRequested).toHaveBeenCalled() })
    await expect(screen.findByText('Rezept nicht gefunden.', {}, { timeout: 200 })).rejects.toThrow()
  })

  // Szenario: Direktlink auf ein Rezept, das es nicht gibt (Outline: gültig aufgebaute, unbekannte / ungültige Kennung)
  // Real (ADR-S142-2): eine unbekannte GUID beantwortet der Endpoint mit 404 und ProblemDetails, eine
  // Nicht-GUID schon die Route-Constraint mit 404 ohne Body.
  it.each([
    ['einer gültig aufgebauten, unbekannten Kennung', '3f2b8c1e-0000-4000-8000-0000000009ff',
      () => HttpResponse.json(
        { status: 404, detail: 'Rezept wurde nicht gefunden.', errorCode: 'RECIPE_NOT_FOUND' }, { status: 404 })],
    ['einer ungültigen Kennung', 'keine-guid', () => new HttpResponse(null, { status: 404 })],
  ])('US602_Error_OpenRecipe_UnknownLink_ShowsNotFoundAndWayBack (%s)', async (_kennung, id, notFound) => {
    // Given: der Server kennt die Kennung nicht und liefert die Rezept-Liste
    server.use(
      http.get('/api/recipes', () => HttpResponse.json([{ id: pancakes.id, title: pancakes.title }])),
      http.get('/api/recipes/:id', notFound),
    )

    // When: ich den Rezept-Link öffne
    renderApp(`/recipes/${id}`)

    // Then: der Hinweis erscheint
    expect(await screen.findByRole('heading', { level: 1, name: 'Rezept nicht gefunden.' })).toBeInTheDocument()

    // When: ich auf "Zur Rezept-Liste" klicke
    fireEvent.click(screen.getByRole('link', { name: 'Zur Rezept-Liste' }))

    // Then: die Rezept-Liste ist zu sehen
    const items = await within(await screen.findByRole('list', { name: 'Rezepte' })).findAllByRole('listitem')
    expect(items.map((item) => item.textContent)).toEqual(['Pfannkuchen'])
  })

  // Szenario: Direktlink auf ein Rezept, das es nicht gibt (ungültige Kennung)
  // Eigener Test statt dritter Outline-Zeile: Die Falle liegt nicht in der Antwort auf die Kennung, sondern im
  // Pfad, den der Client daraus baut. React Router dekodiert %2F zu "/"; ohne Kodierung führte
  // /api/recipes/../ingredients zu /api/ingredients, und dessen 200 wäre die Antwort. Das Given muss diese
  // Falle bereitstellen, die Outline-Zeilen antworten auf jede Kennung mit 404.
  it('US602_Error_OpenRecipe_IdWithEncodedSlash_ShowsNotFoundInsteadOfFollowingPath', async () => {
    // Given: unter dem normalisierten Pfad liegt die Zutatenliste; die kodierte Kennung ist dem Server unbekannt
    server.use(
      http.get('/api/ingredients', () => HttpResponse.json([{ id: 'x', name: 'Mehl' }])),
      http.get('/api/recipes/:id', () => new HttpResponse(null, { status: 404 })),
    )

    // When: ich den Rezept-Link mit kodiertem Schrägstrich öffne
    renderApp('/recipes/..%2Fingredients')

    // Then: der Hinweis erscheint
    expect(await screen.findByRole('heading', { level: 1, name: 'Rezept nicht gefunden.' })).toBeInTheDocument()
  })

  // Kein Szenario fordert den Fall, deshalb ohne US-Tag: useParams liefert die Kennung als `string | undefined`,
  // und der Zweig ohne Kennung ersetzt einen Cast. Fachlich gilt ADR-S142-2: fehlende Kennung = nicht gefunden.
  // Die App-Route /recipes/:id liefert die Kennung immer; der Fall ist nur erreichbar, wenn die Seite direkt unter
  // einer Route ohne :id gerendert wird – daher der Import der Seite statt AppRoutes. Es gibt keinen Handler:
  // ein Abruf ließe den Test über onUnhandledRequest scheitern.
  it('RecipeDetailPage_RouteWithoutId_ShowsNotFoundWithoutRequest', async () => {
    // Given: die Seite hängt an einer Route ohne Kennung
    const routeWithoutId = (
      <Routes>
        <Route path="/recipes" element={<RecipeDetailPage />} />
      </Routes>
    )

    // When: ich die Adresse öffne
    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter initialEntries={['/recipes']}>{routeWithoutId}</MemoryRouter>
      </QueryClientProvider>,
    )

    // Then: der Hinweis mit dem Weg zurück erscheint
    expect(await screen.findByRole('heading', { level: 1, name: 'Rezept nicht gefunden.' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Zur Rezept-Liste' })).toHaveAttribute('href', '/recipes')
  })
})

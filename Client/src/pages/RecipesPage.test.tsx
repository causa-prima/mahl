import { describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, useLocation } from 'react-router'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { AppRoutes } from '../App'

function createQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function CurrentPath() {
  return <output data-testid="current-path">{useLocation().pathname}</output>
}

// Die ganze Anwendung ab dem Pfad: Rezept anlegen ist eine Navigation über mehrere Seiten (ADR-S135-4).
function renderApp(initialPath: string) {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[initialPath]}>
        <AppRoutes />
        <CurrentPath />
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
  await user.type(await screen.findByLabelText('Titel'), 'Pfannkuchen')
  await user.type(screen.getByLabelText('Zutaten'), 'Salz\n250 g Mehl\n500 ml Milch')
  await user.type(screen.getByLabelText('Schritt 1'), 'Mehl und Milch verrühren.')
  fireEvent.click(screen.getByRole('button', { name: 'Schritt hinzufügen' }))
  await user.type(await screen.findByLabelText('Schritt 2'), 'In der Pfanne ausbacken.')
  fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))
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
    const form = (await screen.findByLabelText('Titel')).closest('form')
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

    // Then: die Detailansicht unter der Adresse des Rezepts (ADR-S135-5) zeigt Titel, Zutaten und nummerierte Schritte
    expect(await screen.findByRole('heading', { name: 'Pfannkuchen' })).toBeInTheDocument()
    expect(screen.getByTestId('current-path').textContent).toBe(`/recipes/${createdPancakes.id}`)
    const ingredients = within(screen.getByRole('list', { name: 'Zutaten' })).getAllByRole('listitem')
    expect(ingredients.map((item) => item.textContent)).toEqual(['Salz', '250 g Mehl', '500 ml Milch'])
    const steps = within(screen.getByRole('list', { name: 'Zubereitung' })).getAllByRole('listitem')
    // Nummer + Anweisung als ein Eintrag; Trennzeichen/Darstellung der Nummer sind nicht Teil des Vertrags
    const stepTexts = steps.map((item) => item.textContent)
    expect(stepTexts).toHaveLength(2)
    expect(stepTexts[0]).toMatch(/^1\D+Mehl und Milch verrühren\.$/)
    expect(stepTexts[1]).toMatch(/^2\D+In der Pfanne ausbacken\.$/)
  })
})

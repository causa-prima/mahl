import { describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { delay, http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { appRoutes } from '../App'

function renderApp(initialPath: string) {
  const router = createMemoryRouter(appRoutes, { initialEntries: [initialPath] })
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}

const hint = 'Noch keine Rezepte vorgemerkt.'

// @US-803-happy-path
describe('Vorgemerkt-Seite', () => {
  // Szenario: Ohne Vormerkungen zeigt die Vorgemerkt-Seite einen Hinweis
  it('US803_HappyPath_PlannedRecipesPage_NonePlanned_ShowsHintAndLinkToRecipeList', async () => {
    // Given: kein Rezept ist vorgemerkt
    const requested = vi.fn()
    server.use(http.get('/api/planned-recipes', () => {
      requested()
      return HttpResponse.json([])
    }))

    // When: ich zur Vorgemerkt-Seite navigiere
    renderApp('/planned')

    // Then: die Liste wurde abgefragt; Überschrift, Hinweis und Link sind sichtbar
    expect(await screen.findByText(hint)).toBeInTheDocument()
    expect(requested).toHaveBeenCalled()
    expect(screen.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Zur Rezept-Liste' })).toHaveAttribute('href', '/recipes')
  })

  // Szenario: Ohne Vormerkungen zeigt die Vorgemerkt-Seite einen Hinweis
  it('US803_HappyPath_PlannedRecipesPage_NonePlanned_LinkLeadsToRecipeList', async () => {
    // Given: kein Rezept ist vorgemerkt, das Rezept "Pfannkuchen" existiert
    server.use(
      http.get('/api/planned-recipes', () => HttpResponse.json([])),
      http.get('/api/recipes', () => HttpResponse.json([{ id: '3f2b8c1e-0000-4000-8000-000000000301', title: 'Pfannkuchen' }])),
    )
    renderApp('/planned')

    // When: ich auf "Zur Rezept-Liste" klicke
    fireEvent.click(await screen.findByRole('link', { name: 'Zur Rezept-Liste' }))

    // Then: ich sehe die Rezept-Liste mit "Pfannkuchen"
    expect(await screen.findByRole('heading', { level: 1, name: 'Rezepte' })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'Pfannkuchen' })).toBeInTheDocument()
  })

  // Szenario: Die Vorgemerkt-Seite zeigt nur die vorgemerkten Rezepte, alphabetisch
  it('US803_HappyPath_PlannedRecipesPage_SeveralPlanned_ShowsDeliveredOrderUnchanged', async () => {
    // Given: der Server liefert die Vormerkungen. Die Alphabetik liefert der Server (ADR-S142-1); der Client zeigt
    // die gelieferte Reihenfolge unverändert. Die Antwort ist hier bewusst nicht alphabetisch: Ein Sortieren im
    // Client würde die Reihenfolge ändern.
    server.use(http.get('/api/planned-recipes', () => HttpResponse.json([
      { id: '3f2b8c1e-0000-4000-8000-000000000502', title: 'Spaghetti Bolognese' },
      { id: '3f2b8c1e-0000-4000-8000-000000000503', title: 'Kartoffelsuppe' },
      { id: '3f2b8c1e-0000-4000-8000-000000000501', title: 'Pfannkuchen' },
    ])))

    // When: ich zur Vorgemerkt-Seite navigiere
    renderApp('/planned')

    // Then: die Liste "Vorgemerkt" zeigt genau diese Rezepte in der gelieferten Reihenfolge
    const list = await screen.findByRole('list', { name: 'Vorgemerkt' })
    expect(within(list).getAllByRole('listitem').map((item) => item.textContent))
      .toEqual(['Spaghetti Bolognese', 'Kartoffelsuppe', 'Pfannkuchen'])
  })

  // Szenario: Ein vorgemerktes Rezept von der Vorgemerkt-Seite aus öffnen
  it('US803_HappyPath_PlannedRecipesPage_ClickTitle_ShowsDetailWithPlannedToggle', async () => {
    // Given: "Pfannkuchen" (Zutat 250 g Mehl) und "Kartoffelsuppe" sind vorgemerkt; das Detail liefert der Server nach Kennung
    const pancakes = { id: '3f2b8c1e-0000-4000-8000-000000000501', title: 'Pfannkuchen' }
    const potatoSoup = { id: '3f2b8c1e-0000-4000-8000-000000000503', title: 'Kartoffelsuppe' }
    const planned = [potatoSoup, pancakes]
    server.use(
      http.get('/api/planned-recipes', () => HttpResponse.json(planned)),
      http.get('/api/recipes/:id', ({ params }) => {
        const recipe = planned.find((r) => r.id === params.id)
        return HttpResponse.json({ ...recipe, ingredients: [{ name: 'Mehl', quantity: 250, unit: 'g' }], steps: [{ instruction: 'Rühren.' }] })
      }),
    )
    const router = renderApp('/planned')

    // When: ich zur Vorgemerkt-Seite navigiere und auf "Pfannkuchen" klicke
    fireEvent.click(await screen.findByRole('link', { name: 'Pfannkuchen' }))

    // Then: ich sehe die Detailansicht von "Pfannkuchen" mit "250 g Mehl", und der Umschalter zeigt "Vorgemerkt"
    expect(await screen.findByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(`/recipes/${pancakes.id}`)
    const ingredients = within(await screen.findByRole('list', { name: 'Zutaten' }))
    expect(ingredients.getAllByRole('listitem').map((item) => item.textContent)).toEqual(['250 g Mehl'])
    expect(await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })).toHaveTextContent('Vorgemerkt')
  })

  // ADR-S106-3
  // Querschnittsvertrag aus dem Kopf von features/planned-recipes.feature: während des Ladens steht unter
  // der Überschrift nichts – weder Leerzustand noch Spinner. Kein Szenario treibt den Test.
  it('PlannedRecipesLoading_ResponsePending_ShowsOnlyHeading', async () => {
    // Given: der Server antwortet noch nicht
    const requested = vi.fn()
    server.use(http.get('/api/planned-recipes', async () => {
      requested()
      await delay('infinite')
    }))

    // When: ich zur Vorgemerkt-Seite navigiere
    renderApp('/planned')

    // Then: der Abruf lief; nur die Überschrift ist da
    await waitFor(() => { expect(requested).toHaveBeenCalled() })
    expect(screen.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeInTheDocument()
    expect(screen.queryByText(hint)).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Zur Rezept-Liste' })).not.toBeInTheDocument()
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  // ADR-S106-3
  // Querschnittsvertrag aus dem Kopf von features/planned-recipes.feature: ein Ladefehler zeigt nie den
  // Leerzustand (der Fehlerhinweis selbst ist noch nicht gebaut). Kein Szenario treibt den Test.
  it('PlannedRecipesLoading_ServerError_NeverShowsEmptyState', async () => {
    // Given: der Abruf schlägt mit 500 fehl
    const requested = vi.fn()
    server.use(http.get('/api/planned-recipes', () => {
      requested()
      return new HttpResponse(null, { status: 500 })
    }))

    // When: ich zur Vorgemerkt-Seite navigiere
    renderApp('/planned')

    // Then: der Abruf lief; weder Hinweis noch Link erscheinen
    await waitFor(() => { expect(requested).toHaveBeenCalled() })
    expect(screen.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeInTheDocument()
    expect(screen.queryByText(hint)).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Zur Rezept-Liste' })).not.toBeInTheDocument()
  })
})

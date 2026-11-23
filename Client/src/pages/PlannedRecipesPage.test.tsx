import { describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

  // ADR-S112-5
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

  // ADR-S112-5
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

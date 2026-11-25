import { describe, it, expect, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { delay, http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { renderApp } from '../test/renderApp'

const hint = 'Die Einkaufsliste ist leer.'
const linkName = 'Zu den vorgemerkten Rezepten'

// @US-201-happy-path
describe('Einkaufsliste-Seite', () => {
  // Szenario: Eine noch nie gefüllte Einkaufsliste zeigt einen Hinweis
  it('US201_HappyPath_ShoppingListPage_NeverFilled_ShowsHintAndLinkToPlannedRecipes', async () => {
    // Given: die Einkaufsliste ist leer
    const requested = vi.fn()
    server.use(http.get('/api/shopping-list', () => {
      requested()
      return HttpResponse.json([])
    }))

    // When: ich zur Einkaufsliste navigiere
    renderApp('/shopping-list')

    // Then: sehe ich den Hinweis "Die Einkaufsliste ist leer." und den Link "Zu den vorgemerkten Rezepten" – die
    //   Überschrift aus dem freigegebenen UI-Entwurf; der Abruf belegt, dass der Hinweis aus der Antwort des Servers folgt
    expect(await screen.findByText(hint)).toBeInTheDocument()
    expect(requested).toHaveBeenCalled()
    expect(screen.getByRole('heading', { level: 1, name: 'Einkaufsliste' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: linkName })).toHaveAttribute('href', '/planned')
  })

  // Szenario: Eine noch nie gefüllte Einkaufsliste zeigt einen Hinweis
  it('US201_HappyPath_ShoppingListPage_NeverFilled_LinkLeadsToPlannedPage', async () => {
    // Given: das Rezept "Pfannkuchen" ist vorgemerkt, die Einkaufsliste ist leer
    server.use(
      http.get('/api/shopping-list', () => HttpResponse.json([])),
      http.get('/api/planned-recipes', () => HttpResponse.json([{ id: '3f2b8c1e-0000-4000-8000-000000000501', title: 'Pfannkuchen' }])),
    )
    renderApp('/shopping-list')

    // When: ich auf "Zu den vorgemerkten Rezepten" klicke
    fireEvent.click(await screen.findByRole('link', { name: linkName }))

    // Then: die Vorgemerkt-Seite zeigt genau das Rezept "Pfannkuchen"
    expect(await screen.findByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeInTheDocument()
    const items = await within(await screen.findByRole('list', { name: 'Vorgemerkt' })).findAllByRole('listitem')
    expect(items.map((item) => item.textContent)).toEqual(['Pfannkuchen'])
  })

  // ADR-S106-3
  // Ladeverhalten aus dem Kopf von features/shopping-lists.feature: während des Ladens steht unter der
  // Überschrift nichts – kein Leerzustand. Kein Szenario treibt den Test.
  it('ShoppingListLoading_ResponsePending_ShowsOnlyHeading', async () => {
    // Given: der Server antwortet noch nicht
    const requested = vi.fn()
    server.use(http.get('/api/shopping-list', async () => {
      requested()
      await delay('infinite')
    }))

    // When: ich zur Einkaufsliste navigiere
    renderApp('/shopping-list')

    // Then: der Abruf lief; nur die Überschrift ist da
    await waitFor(() => { expect(requested).toHaveBeenCalled() })
    expect(screen.getByRole('heading', { level: 1, name: 'Einkaufsliste' })).toBeInTheDocument()
    expect(screen.queryByText(hint)).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: linkName })).not.toBeInTheDocument()
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  // ADR-S106-3
  // Ladeverhalten aus dem Kopf von features/shopping-lists.feature: ein Ladefehler zeigt nie den Leerzustand
  // (der Fehlerhinweis selbst ist noch nicht gebaut). Kein Szenario treibt den Test. Zum Fehler wird die 500 hier
  // über ihren leeren Body, der sich nicht als JSON lesen lässt – den Statuscode wertet der Abruf noch nicht aus.
  it('ShoppingListLoading_ServerError_NeverShowsEmptyState', async () => {
    // Given: der Abruf schlägt mit 500 fehl
    const requested = vi.fn()
    server.use(http.get('/api/shopping-list', () => {
      requested()
      return new HttpResponse(null, { status: 500 })
    }))

    // When: ich zur Einkaufsliste navigiere
    const { queryClient } = renderApp('/shopping-list')

    // Then: der Abruf lief und ist abgeschlossen; weder Hinweis noch Link erscheinen
    await waitFor(() => { expect(requested).toHaveBeenCalled() })
    await waitFor(() => { expect(queryClient.isFetching()).toBe(0) })
    expect(screen.getByRole('heading', { level: 1, name: 'Einkaufsliste' })).toBeInTheDocument()
    expect(screen.queryByText(hint)).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: linkName })).not.toBeInTheDocument()
  })
})

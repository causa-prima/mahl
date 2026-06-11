import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import IngredientsPage from './IngredientsPage'

function renderWithProviders(ui: Readonly<React.ReactElement>) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('IngredientsPage', () => {
  it('US904_HappyPath_IngredientsPage_EmptyDb_ShowsEmptyList', async () => {
    // Given: keine Zutaten vorhanden
    server.use(
      http.get('/api/ingredients', () => HttpResponse.json([]))
    )

    // When: ich die Zutaten-Seite öffne
    renderWithProviders(<IngredientsPage />)

    // Then: Hinweis und Button sind sichtbar
    await screen.findByText('Noch keine Zutaten angelegt.')
    await screen.findByRole('button', { name: 'Zutat anlegen' })
  })

  it('US904_HappyPath_OpenCreateDialog_FieldsAreEmpty', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    server.use(http.get('/api/ingredients', () => HttpResponse.json([])))
    renderWithProviders(<IngredientsPage />)
    const openButton = await screen.findByRole('button', { name: 'Zutat anlegen' })

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)

    // Then: Name-Feld ist leer
    const nameField = await screen.findByLabelText('Name')
    expect(nameField).toHaveValue('')
    // Then: Einheit-Feld ist leer
    const unitField = screen.getByLabelText('Einheit')
    expect(unitField).toHaveValue('')
  })

  it('US904_HappyPath_OpenCreateDialog_ClosedInitially_FieldsAbsent', async () => {
    // Zweck: killt nach GREEN den Stryker-Mutanten "Dialog initial open={true}" –
    //   ohne diesen Test wäre ein stets offener Dialog faelschlich gruen.
    // Given: leere Zutaten-Seite, vor dem Klick (Vorbedingung der Öffnen-Transition)
    server.use(http.get('/api/ingredients', () => HttpResponse.json([])))
    renderWithProviders(<IngredientsPage />)
    await screen.findByRole('button', { name: 'Zutat anlegen' })

    // Then: Dialog noch nicht geöffnet -> Felder nicht im DOM
    expect(screen.queryByLabelText('Name')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Einheit')).not.toBeInTheDocument()
  })
})

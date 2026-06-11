import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import IngredientsPage from './IngredientsPage'

function renderWithProviders(ui: Readonly<React.ReactElement>) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

// Background (Gherkin): Anwendung gestartet + leere Zutaten-Seite.
// Liefert den stets sichtbaren "Zutat anlegen"-Button zurück.
async function renderEmptyIngredientsPage() {
  server.use(http.get('/api/ingredients', () => HttpResponse.json([])))
  renderWithProviders(<IngredientsPage />)
  return screen.findByRole('button', { name: 'Zutat anlegen' })
}

describe('IngredientsPage', () => {
  it('US904_HappyPath_IngredientsPage_EmptyDb_ShowsEmptyList', async () => {
    // Given + When: keine Zutaten vorhanden, Zutaten-Seite geöffnet
    await renderEmptyIngredientsPage()

    // Then: Hinweis und Button sind sichtbar
    await screen.findByText('Noch keine Zutaten angelegt.')
    await screen.findByRole('button', { name: 'Zutat anlegen' })
  })

  it('US904_HappyPath_OpenCreateDialog_FieldsAreEmpty', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    const openButton = await renderEmptyIngredientsPage()

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)

    // Then: Name-Feld ist leer
    expect(await screen.findByLabelText('Name')).toHaveValue('')
    // Then: Einheit-Feld ist leer
    expect(screen.getByLabelText('Einheit')).toHaveValue('')
  })

  it('US904_HappyPath_OpenCreateDialog_ClosedInitially_FieldsAbsent', async () => {
    // Zweck: killt nach GREEN den Stryker-Mutanten "Dialog initial open={true}" –
    //   ohne diesen Test wäre ein stets offener Dialog faelschlich gruen.
    // Given: leere Zutaten-Seite, vor dem Klick (Vorbedingung der Öffnen-Transition)
    await renderEmptyIngredientsPage()

    // Then: Dialog noch nicht geöffnet -> Felder nicht im DOM
    expect(screen.queryByLabelText('Name')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Einheit')).not.toBeInTheDocument()
  })

  it('US904_HappyPath_ReopenDialogAfterCancel_FieldsAreEmpty', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    const user = userEvent.setup()
    const openButton = await renderEmptyIngredientsPage()

    // When: ich auf "Zutat anlegen" klicke und beide Felder befülle
    fireEvent.click(openButton)
    await user.type(await screen.findByLabelText('Name'), 'Knoblauch')
    await user.type(screen.getByLabelText('Einheit'), 'Zehen')

    // Then (Zwischenzustand): Eingaben sind angekommen
    //   (Voraussetzung dafür, dass "Abbrechen" sie überhaupt verwerfen kann)
    expect(screen.getByLabelText('Name')).toHaveValue('Knoblauch')
    expect(screen.getByLabelText('Einheit')).toHaveValue('Zehen')

    // When: ich auf "Abbrechen" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Abbrechen' }))

    // Then: Dialog ist wirklich geschlossen -> Felder nicht mehr im DOM
    //   (wartet die MUI-Close-Transition ab, statt nur auf den stets sichtbaren Button)
    await waitFor(() => {
      expect(screen.queryByLabelText('Name')).not.toBeInTheDocument()
    })

    // When: ich erneut auf "Zutat anlegen" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Zutat anlegen' }))

    // Then: Name-Feld ist leer
    expect(await screen.findByLabelText('Name')).toHaveValue('')
    // Then: Einheit-Feld ist leer
    expect(screen.getByLabelText('Einheit')).toHaveValue('')
  })
})

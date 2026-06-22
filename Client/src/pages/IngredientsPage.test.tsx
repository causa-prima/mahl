import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import IngredientsPage from './IngredientsPage'

function renderWithProviders(ui: Readonly<React.ReactElement>) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
  return client
}

// Background (Gherkin): Anwendung gestartet + leere Zutaten-Seite.
// Liefert den stets sichtbaren "Zutat anlegen"-Button zurück.
async function renderEmptyIngredientsPage() {
  server.use(http.get('/api/ingredients', () => HttpResponse.json([])))
  renderWithProviders(<IngredientsPage />)
  return screen.findByRole('button', { name: 'Zutat anlegen' })
}

const tomaten = { id: '1', name: 'Tomaten', defaultUnit: 'Stück' } as const

const salz = { id: '7', name: 'Salz', defaultUnit: 'g' } as const

// @US-904-error: Ausgangszustand = eine bestehende Zutat (Salz); der POST eines
// leeren Namens beantwortet das Backend mit 422 + feld-keyed Body (ADR-S090-1):
// { errors: { name: ["Name darf nicht leer sein."] } }. GET liefert unverändert
// [salz] (kein optimistic add), sodass "Liste bleibt unverändert" echt prüfbar ist.
function useEmptyNameRejectingHandlers(): void {
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json([salz])),
    http.post('/api/ingredients', () =>
      HttpResponse.json(
        { status: 422, errors: { name: ['Name darf nicht leer sein.'] } },
        { status: 422 },
      ),
    ),
  )
}

type CapturedPost = {
  body: unknown
  contentType: string | null
}

// Invalidate+Refetch-Modellierung: GET liefert erst [], nach erfolgreichem POST die
// angelegte Zutat (kein optimistic update). Der POST-Request wird in `captured`
// festgehalten und im Then-Block des Tests assertet – feuert der POST nie, bleibt
// `captured` undefined und der Then-Block schlägt sichtbar fehl (statt stiller
// In-Handler-Assertion / unhandled rejection).
function useCreateTomatenHandlers(): { current: CapturedPost | undefined } {
  // eslint-disable-next-line functional/no-let -- MSW-Handler-Umschaltung: GET vor/nach POST
  let created = false
  const capture: { current: CapturedPost | undefined } = { current: undefined }
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json(created ? [tomaten] : [])),
    http.post('/api/ingredients', async ({ request }) => {
      // eslint-disable-next-line functional/immutable-data -- Capture: Request für Then-Block festhalten
      capture.current = {
        body: await request.json(),
        contentType: request.headers.get('Content-Type'),
      }
      created = true
      return HttpResponse.json(tomaten, { status: 201, headers: { Location: '/api/ingredients/1' } })
    }),
  )
  return capture
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
    // Then: ohne Fehler ist das Name-Feld NICHT als ungültig markiert
    //   (killt den Dauer-error={true}-Mutanten am Name-Feld)
    expect(screen.getByLabelText('Name')).toHaveAttribute('aria-invalid', 'false')
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

    // Then: Dialog ist wirklich geschlossen -> Dialog nicht mehr im DOM
    //   (wartet die MUI-Close-Transition ab, statt nur auf den stets sichtbaren Button)
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    // When: ich erneut auf "Zutat anlegen" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Zutat anlegen' }))

    // Then: Name-Feld ist leer
    expect(await screen.findByLabelText('Name')).toHaveValue('')
    // Then: Einheit-Feld ist leer
    expect(screen.getByLabelText('Einheit')).toHaveValue('')
  })

  it('US904_HappyPath_CancelDialog_ClosesDialogAndDiscardsInput', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    const user = userEvent.setup()
    const openButton = await renderEmptyIngredientsPage()

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)
    // When: ich "Oregano" als Name eingebe
    await user.type(await screen.findByLabelText('Name'), 'Oregano')
    // When: ich auf "Abbrechen" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Abbrechen' }))

    // Then: der "Zutat anlegen"-Dialog ist geschlossen -> Dialog nicht mehr im DOM
    //   (wartet die MUI-Close-Transition ab, analog zum Reopen-Test)
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    // Then: "Oregano" nicht als Listentext gerendert (Gherkin "nicht in der Liste").
    //   Im Empty-State redundant zur Dialog-zu-Assertion oben; greift echt erst, sobald
    //   die Liste befüllt rendert (Persistenz-Szenario) – im E2E-Test bereits aussagekräftig.
    expect(screen.queryByText('Oregano')).not.toBeInTheDocument()
  })
})

describe('IngredientsPage – Zutat anlegen', () => {
  it('US904_HappyPath_GetIngredients_SettledEmptyArray_ShowsEmptyState', async () => {
    // Zweck: pinnt den Listen-Branch im SETTLED [] -Zustand (definiertes leeres Array),
    //   nicht im pending-Fenster. Killt die List-Branch-Mutanten (length > 0 → >= 0,
    //   Bedingung → true), die ein pending-Race sonst überleben lässt.
    // Given: GET liefert ein leeres Array
    server.use(http.get('/api/ingredients', () => HttpResponse.json([])))
    const client = renderWithProviders(<IngredientsPage />)

    // When: die Query ist nachweislich settled (nicht mehr pending) -> ingredients === []
    await waitFor(() => {
      expect(client.getQueryState(['ingredients'])?.status).toBe('success')
    })

    // Then: der Empty-State wird angezeigt (definiertes [] rendert NICHT die Liste)
    expect(screen.getByText('Noch keine Zutaten angelegt.')).toBeInTheDocument()
    expect(screen.queryByTestId('ingredient-list')).not.toBeInTheDocument()
  })

  it('US904_HappyPath_CreateIngredient_ValidData_IngredientAppearsInList', async () => {
    // Given: leere Zutaten-Seite; nach erfolgreichem POST liefert GET die angelegte Zutat
    const user = userEvent.setup()
    const captured = useCreateTomatenHandlers()
    renderWithProviders(<IngredientsPage />)
    const openButton = await screen.findByRole('button', { name: 'Zutat anlegen' })

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)
    // When: ich "Tomaten" als Name eingebe
    await user.type(await screen.findByLabelText('Name'), 'Tomaten')
    // When: ich "Stück" als Einheit eingebe
    await user.type(screen.getByLabelText('Einheit'), 'Stück')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: "Tomaten" erscheint in der Zutaten-Liste
    const list = await screen.findByTestId('ingredient-list')
    expect(await within(list).findByText('Tomaten')).toBeInTheDocument()
    // Then: mit Einheit "Stück"
    expect(within(list).getByText('Stück')).toBeInTheDocument()
    // Then: der "Zutat anlegen"-Dialog ist geschlossen
    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Zutat anlegen' })).not.toBeInTheDocument()
    })

    // Then: der POST trug Name + Einheit als { name, defaultUnit } (ADR-S068-1)
    expect(captured.current?.body).toEqual({ name: 'Tomaten', defaultUnit: 'Stück' })
    // Then: der POST sendete JSON (Content-Type), damit das Backend den Body bindet
    expect(captured.current?.contentType).toBe('application/json')
  })
})

describe('IngredientsPage – Zutat anlegen schlägt fehl (leerer Name)', () => {
  // Helper: Dialog öffnen, "g" als Einheit eingeben, "Speichern" klicken.
  // Gemeinsames When für alle Tests dieses Szenarios.
  async function submitEmptyNameWithUnitGramm() {
    const user = userEvent.setup()
    renderWithProviders(<IngredientsPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    // When: ich keinen Namen eingebe (Name-Feld bleibt leer)
    // When: ich "g" als Einheit eingebe
    await user.type(await screen.findByLabelText('Einheit'), 'g')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))
  }

  it('US904_Error_CreateIngredient_EmptyName_ShowsErrorMessage', async () => {
    // Given: bestehende Zutat (Salz); leerer Name -> Backend antwortet 422
    useEmptyNameRejectingHandlers()

    // When: leeren Namen + Einheit "g" speichern
    await submitEmptyNameWithUnitGramm()

    // Then: ich sehe die Fehlermeldung "Name darf nicht leer sein."
    expect(await screen.findByText('Name darf nicht leer sein.')).toBeInTheDocument()
    // Then: das Name-Feld ist als ungültig markiert (a11y-Fehlerzustand, UX-Guideline §4)
    expect(screen.getByLabelText('Name')).toHaveAttribute('aria-invalid', 'true')
  })

  it('US904_Error_CreateIngredient_EmptyName_KeepsDialogOpen', async () => {
    // Given: bestehende Zutat (Salz); leerer Name -> Backend antwortet 422
    useEmptyNameRejectingHandlers()

    // When: leeren Namen + Einheit "g" speichern
    await submitEmptyNameWithUnitGramm()

    // Then: der Dialog bleibt offen (sonst wäre die Meldung nicht korrigierbar)
    //   Auf das Erscheinen der Meldung warten, dann den noch offenen Dialog prüfen.
    await screen.findByText('Name darf nicht leer sein.')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('US904_Error_CreateIngredient_EmptyName_ListUnchanged', async () => {
    // Given: bestehende Zutat (Salz); leerer Name -> Backend antwortet 422
    useEmptyNameRejectingHandlers()

    // When: leeren Namen + Einheit "g" speichern
    await submitEmptyNameWithUnitGramm()

    // Then: die Zutaten-Liste bleibt unverändert (kein optimistisches Hinzufügen)
    //   Auf das Erscheinen der Meldung warten, dann den Listenzustand prüfen.
    //   hidden: true – der (korrekt) offene MUI-Dialog setzt den Hintergrund inkl. Liste
    //   auf aria-hidden; die <li> sind weiter im DOM und exakt unverändert (genau Salz),
    //   die role-Query braucht hidden:true, um sie zu sehen.
    await screen.findByText('Name darf nicht leer sein.')
    const list = screen.getByTestId('ingredient-list')
    expect(within(list).getAllByRole('listitem', { hidden: true })).toHaveLength(1)
    expect(within(list).getByText('Salz')).toBeInTheDocument()
  })
})

// @US-904-error: Ausgangszustand = eine bestehende Zutat (Salz); der POST mit leerer
// Einheit (gültiger Name "Salz") beantwortet das Backend mit 422 + feld-keyed Body
// (ADR-S090-1): { errors: { defaultUnit: ["Einheit darf nicht leer sein."] } }. Der Key
// `defaultUnit` ist die Request-JSON-Property exakt wie das FE im POST sendet. GET liefert
// unverändert [salz] (kein optimistic add), sodass "Liste bleibt unverändert" echt gilt.
function useEmptyUnitRejectingHandlers(): void {
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json([salz])),
    http.post('/api/ingredients', () =>
      HttpResponse.json(
        { status: 422, errors: { defaultUnit: ['Einheit darf nicht leer sein.'] } },
        { status: 422 },
      ),
    ),
  )
}

describe('IngredientsPage – Zutat anlegen schlägt fehl (leere Einheit)', () => {
  // Helper: Dialog öffnen, "Salz" als Name eingeben, Einheit leer lassen, "Speichern".
  // Gemeinsames When für alle Tests dieses Szenarios (spiegelbildlich zum leeren Namen).
  async function submitEmptyUnitWithNameSalz() {
    const user = userEvent.setup()
    renderWithProviders(<IngredientsPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    // When: ich "Salz" als Name eingebe
    await user.type(await screen.findByLabelText('Name'), 'Salz')
    // When: ich keine Einheit eingebe (Einheit-Feld bleibt leer)
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))
  }

  it('US904_Error_CreateIngredient_EmptyUnit_ShowsErrorMessage', async () => {
    // Given: bestehende Zutat (Salz); leere Einheit -> Backend antwortet 422
    useEmptyUnitRejectingHandlers()

    // When: Name "Salz" + leere Einheit speichern
    await submitEmptyUnitWithNameSalz()

    // Then: ich sehe die Fehlermeldung "Einheit darf nicht leer sein."
    expect(await screen.findByText('Einheit darf nicht leer sein.')).toBeInTheDocument()
    // Then: das Einheit-Feld ist als ungültig markiert (a11y-Fehlerzustand, UX-Guideline §4)
    expect(screen.getByLabelText('Einheit')).toHaveAttribute('aria-invalid', 'true')
  })

  it('US904_Error_CreateIngredient_EmptyUnit_MarksOnlyUnitField', async () => {
    // Given: bestehende Zutat (Salz); leere Einheit -> Backend antwortet 422
    useEmptyUnitRejectingHandlers()

    // When: Name "Salz" + leere Einheit speichern
    await submitEmptyUnitWithNameSalz()

    // Then: das Einheit-Feld ist als ungültig markiert (der defaultUnit-Fehler landet dort)
    expect(await screen.findByLabelText('Einheit')).toHaveAttribute('aria-invalid', 'true')
    // Then: das Name-Feld ist NICHT als ungültig markiert (der Fehler betrifft nur die
    //   Einheit) — killt den Mutanten "es wird immer dasselbe Feld markiert" und treibt
    //   den name-absent-Zweig (FieldErrors ohne name-Key).
    expect(screen.getByLabelText('Name')).toHaveAttribute('aria-invalid', 'false')
  })
})

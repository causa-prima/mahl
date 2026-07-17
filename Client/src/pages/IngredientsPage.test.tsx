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

// Der Dialog setzt den Autofokus verzögert (erst nach der Öffnen-Transition, via
// onEntered). Wer unmittelbar nach dem Öffnen tippt, riskiert, dass der Fokus mitten
// im Tippen zurück aufs Name-Feld springt und Zeichen im falschen Feld landen. Daher
// vor dem ersten user.type auf den abgeschlossenen Autofokus warten.
async function awaitDialogAutofocus() {
  await waitFor(() => { expect(screen.getByLabelText(/^Name/)).toHaveFocus() })
}

const tomaten = { id: '1', name: 'Tomaten', defaultUnit: 'Stück' } as const

const salz = { id: '7', name: 'Salz', defaultUnit: 'g' } as const

// > MUI theme.transitions.duration.leavingScreen (225ms, MUI-Default) + Marge. Settle-
// Fenster VOR Assertions, die sich auf "Dialog noch im DOM" verlassen: die Exit-Transition
// hält den Dialog-Knoten kurz im DOM, unabhängig davon ob ein Guard greift – ohne dieses
// Fenster wäre die Assertion ein Transition-Artefakt statt echtes Verhalten (s. Escape-Test).
const DIALOG_EXIT_SETTLE_MS = 300

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
    expect(await screen.findByLabelText(/^Name/)).toHaveValue('')
    // Then: Einheit-Feld ist leer
    expect(screen.getByLabelText(/^Einheit/)).toHaveValue('')
    // Then: ohne Fehler ist das Name-Feld NICHT als ungültig markiert
    //   (killt den Dauer-error={true}-Mutanten am Name-Feld)
    expect(screen.getByLabelText(/^Name/)).toHaveAttribute('aria-invalid', 'false')
  })

  it('US904_HappyPath_OpenCreateDialog_ClosedInitially_FieldsAbsent', async () => {
    // Zweck: killt nach GREEN den Stryker-Mutanten "Dialog initial open={true}" –
    //   ohne diesen Test wäre ein stets offener Dialog faelschlich gruen.
    // Given: leere Zutaten-Seite, vor dem Klick (Vorbedingung der Öffnen-Transition)
    await renderEmptyIngredientsPage()

    // Then: Dialog noch nicht geöffnet -> Felder nicht im DOM
    expect(screen.queryByLabelText(/^Name/)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/^Einheit/)).not.toBeInTheDocument()
  })

  it('US904_HappyPath_ReopenDialogAfterCancel_FieldsAreEmpty', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    const user = userEvent.setup()
    const openButton = await renderEmptyIngredientsPage()

    // When: ich auf "Zutat anlegen" klicke und beide Felder befülle
    fireEvent.click(openButton)
    await awaitDialogAutofocus()
    await user.type(screen.getByLabelText(/^Name/), 'Knoblauch')
    await user.type(screen.getByLabelText(/^Einheit/), 'Zehen')

    // Then (Zwischenzustand): Eingaben sind angekommen
    //   (Voraussetzung dafür, dass "Abbrechen" sie überhaupt verwerfen kann)
    expect(screen.getByLabelText(/^Name/)).toHaveValue('Knoblauch')
    expect(screen.getByLabelText(/^Einheit/)).toHaveValue('Zehen')

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
    expect(await screen.findByLabelText(/^Name/)).toHaveValue('')
    // Then: Einheit-Feld ist leer
    expect(screen.getByLabelText(/^Einheit/)).toHaveValue('')
  })

  // Szenario: Pflichtfelder im Dialog sind als solche markiert
  it('US904_HappyPath_OpenCreateDialog_RequiredFieldsAreMarked', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    const openButton = await renderEmptyIngredientsPage()

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)

    // Then: das Name-Feld ist als Pflichtfeld markiert
    expect(await screen.findByLabelText(/^Name/)).toBeRequired()
    // Then: das Einheit-Feld ist als Pflichtfeld markiert
    expect(screen.getByLabelText(/^Einheit/)).toBeRequired()
  })

  // Szenario: Beim Öffnen des Dialogs liegt der Fokus auf dem ersten Feld
  it('US904_HappyPath_OpenCreateDialog_FocusOnFirstField', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    const openButton = await renderEmptyIngredientsPage()

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)

    // Then: das Name-Feld ist das erste Eingabefeld im Dialog
    const nameField = await screen.findByLabelText(/^Name/)
    const dialogTextboxes = within(screen.getByRole('dialog')).getAllByRole('textbox')
    expect(dialogTextboxes[0]).toBe(nameField)
    // Then: das Name-Feld hat den Fokus
    await waitFor(() => { expect(nameField).toHaveFocus() })
  })

  it('US904_HappyPath_CancelDialog_ClosesDialogAndDiscardsInput', async () => {
    // Given: leere Zutaten-Seite (Background: Anwendung gestartet, Zutaten-Seite)
    const user = userEvent.setup()
    const openButton = await renderEmptyIngredientsPage()

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)
    await awaitDialogAutofocus()
    // When: ich "Oregano" als Name eingebe
    await user.type(screen.getByLabelText(/^Name/), 'Oregano')
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

  // Rule-of-Three: die 3 Pending-Tests unten (Speichern-/Abbrechen-Button disabled, Escape
  // schließt nicht) teilen dieses Setup – hängender POST via externem Resolver, Dialog
  // öffnen/befüllen/Speichern-Klick. Liefert `resolvePost`, damit jeder Test den POST selbst
  // zum gewünschten Zeitpunkt abschließt (Cleanup).
  async function renderWithPendingSave(): Promise<{ resolvePost: () => void }> {
    // eslint-disable-next-line functional/no-let -- Resolver wird im POST-Handler befuellt
    let resolvePost: () => void = () => {}
    const postPending = new Promise<void>((resolve) => { resolvePost = resolve })
    server.use(
      http.get('/api/ingredients', () => HttpResponse.json([])),
      http.post('/api/ingredients', async () => {
        await postPending
        return HttpResponse.json(tomaten, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderWithProviders(<IngredientsPage />)

    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    await user.type(screen.getByLabelText(/^Name/), 'Tomaten')
    await user.type(screen.getByLabelText(/^Einheit/), 'Stück')
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    return { resolvePost }
  }

  it('US904_HappyPath_CreateIngredient_ValidData_IngredientAppearsInList', async () => {
    // Given: leere Zutaten-Seite; nach erfolgreichem POST liefert GET die angelegte Zutat
    const user = userEvent.setup()
    const captured = useCreateTomatenHandlers()
    renderWithProviders(<IngredientsPage />)
    const openButton = await screen.findByRole('button', { name: 'Zutat anlegen' })

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(openButton)
    await awaitDialogAutofocus()
    // When: ich "Tomaten" als Name eingebe
    await user.type(screen.getByLabelText(/^Name/), 'Tomaten')
    // When: ich "Stück" als Einheit eingebe
    await user.type(screen.getByLabelText(/^Einheit/), 'Stück')
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

  // Szenario: Speichern-Button ist während des Speicherns deaktiviert
  it('US904_HappyPath_SaveInFlight_SaveButtonIsDisabled', async () => {
    // Given: der POST bleibt hängen, bis der Test ihn explizit auflöst (Helper) – so ist das
    //   Pending-Fenster deterministisch beobachtbar (kein Timer-Race).
    // When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper)
    const { resolvePost } = await renderWithPendingSave()

    // Then: der "Speichern"-Button ist deaktiviert, solange die Antwort aussteht
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Speichern' })).toBeDisabled()
    })

    // Cleanup (kein Szenario-Assert, reine Test-Infrastruktur): POST auflösen und das
    //   Schließen des Dialogs abwarten, damit kein hängender Handler in den nächsten Test läuft.
    resolvePost()
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  // Szenario: Abbrechen ist während des Speicherns deaktiviert
  it('US904_HappyPath_SaveInFlight_CancelButtonIsDisabled', async () => {
    // Given: der POST bleibt hängen, bis der Test ihn explizit auflöst (Helper)
    // When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper)
    const { resolvePost } = await renderWithPendingSave()

    // Then: der "Abbrechen"-Button ist deaktiviert, solange die Antwort aussteht
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Abbrechen' })).toBeDisabled()
    })

    // Cleanup: POST auflösen und Schließen abwarten (analog zum Save-Button-Test)
    resolvePost()
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  // Szenario: Der Dialog lässt sich während des Speicherns nicht per Escape schließen
  it('US904_HappyPath_SaveInFlight_EscapeDoesNotCloseDialog', async () => {
    // Given: der POST bleibt hängen, bis der Test ihn explizit auflöst (Helper)
    // When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper)
    const { resolvePost } = await renderWithPendingSave()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Speichern' })).toBeDisabled()
    })

    // When: ich Escape drücke – aus dem noch aktiven Name-Feld heraus (Fokus IM Dialog):
    //   sonst fiele der Fokus vom deaktivierten Speichern-Button auf <body> außerhalb des
    //   Modals, und der MUI-Escape-Handler würde gar nicht erst erreicht -> der Test wäre
    //   ohne echten Guard grün (Fokus-Artefakt statt Verhalten).
    const nameField = screen.getByLabelText(/^Name/)
    nameField.focus()
    fireEvent.keyDown(nameField, { key: 'Escape', code: 'Escape' })

    // Then: der "Zutat anlegen"-Dialog ist weiterhin geöffnet, solange die Antwort aussteht.
    //   Settle-Fenster VOR der Assertion: ohne echten Guard triggert Escape ein onClose,
    //   dessen Exit-Transition den Dialog erst NACH der Transition aus dem DOM entfernt –
    //   eine sofortige Assertion sähe ihn fälschlich noch als "im Dokument".
    await new Promise((resolve) => { setTimeout(resolve, DIALOG_EXIT_SETTLE_MS) })
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    // Cleanup: POST auflösen und Schließen abwarten (Erfolgspfad schließt regulär).
    resolvePost()
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  // Szenario: Der Dialog lässt sich während des Speicherns nicht per Backdrop-Klick schließen
  it('US904_HappyPath_SaveInFlight_BackdropClickDoesNotCloseDialog', async () => {
    // Given: der POST bleibt hängen, bis der Test ihn explizit auflöst (Helper)
    // When: Dialog öffnen, gültige Zutat eingeben, "Speichern" klicken (Helper)
    const { resolvePost } = await renderWithPendingSave()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Speichern' })).toBeDisabled()
    })

    // When: ich auf den Backdrop klicke. MUI erkennt "Backdrop" NICHT am Klick-Ziel selbst,
    //   sondern zweistufig: `onMouseDown` auf dem `.MuiDialog-container` merkt sich
    //   target === currentTarget (Klick beginnt/endet auf dem Container, nicht auf einem Kind
    //   wie dem Paper) in einer Ref; der anschließende `onClick` auf dem `.MuiDialog-root`
    //   liest diese Ref und ruft bei true `onClose(reason='backdropClick')`. Ein reines
    //   `fireEvent.click` OHNE vorheriges `mousedown` setzt die Ref nie (bliebe vakuös grün,
    //   unabhängig vom Guard) – daher explizit `mouseDown` vor `click` auf dem Container.
    const dialogContainer = document.querySelector('.MuiDialog-container')
    if (!dialogContainer) throw new Error('MuiDialog-container nicht gefunden')
    fireEvent.mouseDown(dialogContainer)
    fireEvent.click(dialogContainer)

    // Then: der "Zutat anlegen"-Dialog ist weiterhin geöffnet, solange die Antwort aussteht.
    //   Settle-Fenster VOR der Assertion (analog Escape-Test): ohne echten Guard triggert der
    //   Backdrop-Klick ein onClose, dessen Exit-Transition den Dialog erst NACH der Transition
    //   aus dem DOM entfernt – eine sofortige Assertion sähe ihn fälschlich noch als "im Dokument".
    await new Promise((resolve) => { setTimeout(resolve, DIALOG_EXIT_SETTLE_MS) })
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    // Cleanup: POST auflösen und Schließen abwarten (Erfolgspfad schließt regulär).
    resolvePost()
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })
})

describe('IngredientsPage – Zutat anlegen schlägt fehl (leerer Name)', () => {
  // Helper: Dialog öffnen, "g" als Einheit eingeben, "Speichern" klicken.
  // Gemeinsames When für alle Tests dieses Szenarios.
  async function submitEmptyNameWithUnitGramm() {
    const user = userEvent.setup()
    renderWithProviders(<IngredientsPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    // When: ich keinen Namen eingebe (Name-Feld bleibt leer)
    // When: ich "g" als Einheit eingebe
    await user.type(screen.getByLabelText(/^Einheit/), 'g')
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
    expect(screen.getByLabelText(/^Name/)).toHaveAttribute('aria-invalid', 'true')
    // Then: das Name-Feld hat den Fokus (UX-Guideline Prinzip 8 "Fokus aufs erste
    //   fehlerhafte Feld", TD-S094-1 – nicht durch einen eigenen Gherkin-Step getrieben,
    //   sondern durch die Guideline-Baseline; "erstes Feld fehlerhaft" -> Name-Feld).
    //   waitFor, weil der Fokus asynchron via useEffect nach dem Render-Commit gesetzt wird.
    await waitFor(() => { expect(screen.getByLabelText(/^Name/)).toHaveFocus() })
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
    await awaitDialogAutofocus()
    // When: ich "Salz" als Name eingebe
    await user.type(screen.getByLabelText(/^Name/), 'Salz')
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
    expect(screen.getByLabelText(/^Einheit/)).toHaveAttribute('aria-invalid', 'true')
  })

  it('US904_Error_CreateIngredient_EmptyUnit_MarksOnlyUnitField', async () => {
    // Given: bestehende Zutat (Salz); leere Einheit -> Backend antwortet 422
    useEmptyUnitRejectingHandlers()

    // When: Name "Salz" + leere Einheit speichern
    await submitEmptyUnitWithNameSalz()

    // Then: das Einheit-Feld ist als ungültig markiert (der defaultUnit-Fehler landet dort)
    expect(await screen.findByLabelText(/^Einheit/)).toHaveAttribute('aria-invalid', 'true')
    // Then: das Name-Feld ist NICHT als ungültig markiert (der Fehler betrifft nur die
    //   Einheit) — killt den Mutanten "es wird immer dasselbe Feld markiert" und treibt
    //   den name-absent-Zweig (FieldErrors ohne name-Key).
    expect(screen.getByLabelText(/^Name/)).toHaveAttribute('aria-invalid', 'false')
    // Then: das Einheit-Feld hat den Fokus (UX-Guideline Prinzip 8 "Fokus aufs erste
    //   fehlerhafte Feld"; "nur späteres Feld fehlerhaft" -> Einheit-Feld, nicht Name).
    //   waitFor, weil der Fokus asynchron via useEffect nach dem Render-Commit gesetzt wird.
    await waitFor(() => { expect(screen.getByLabelText(/^Einheit/)).toHaveFocus() })
  })
})

describe('IngredientsPage – Reopen nach fehlgeschlagenem Speichern und Abbrechen', () => {
  // Szenario: Nach fehlgeschlagenem Speichern und Abbrechen ist der Dialog beim erneuten Öffnen fehlerfrei
  it('US904_EdgeCase_ReopenDialogAfterFailedSaveAndCancel_IsErrorFree', async () => {
    // Given: bestehende Zutat (Salz); leerer Name -> Backend antwortet 422 (Bug R1: der
    //   Fehlerzustand darf beim Reopen nicht mehr sichtbar sein)
    useEmptyNameRejectingHandlers()
    const user = userEvent.setup()
    renderWithProviders(<IngredientsPage />)

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    // When: ich "g" als Einheit eingebe (Name bleibt leer)
    await user.type(screen.getByLabelText(/^Einheit/), 'g')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // When: die Fehlermeldung "Name darf nicht leer sein." erscheint
    await screen.findByText('Name darf nicht leer sein.')

    // When: ich auf "Abbrechen" klicke -> Dialog schließt (Close-Transition abwarten)
    fireEvent.click(screen.getByRole('button', { name: 'Abbrechen' }))
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    // When: ich erneut auf "Zutat anlegen" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()

    // Then: keine Fehlermeldung sichtbar (der alte Fehlerzustand ist zurückgesetzt)
    expect(screen.queryByText('Name darf nicht leer sein.')).not.toBeInTheDocument()
    // Then: das Name-Feld ist nicht als ungültig markiert (aria-invalid zurückgesetzt)
    expect(screen.getByLabelText(/^Name/)).toHaveAttribute('aria-invalid', 'false')
  })
})

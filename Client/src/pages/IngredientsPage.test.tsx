import { describe, it, expect, vi } from 'vitest'
import { act, render, screen, fireEvent, waitFor, within } from '@testing-library/react'
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

const tomaten = { id: '1', name: 'Tomaten', baseUnit: 'Stück' } as const

const salz = { id: '7', name: 'Salz', baseUnit: 'g' } as const

// run-8: nur "Mehl" (g) existiert. Der per-Zeile-xmin-ETag (ADR-S108-1) reist im GET-Body mit
// und wird von der Komponente als If-Match beim DELETE verwendet. Realistisches Format: lowercase
// hex in Quotes ("{xmin:x8}", ADR-S106-1). Das If-Match-VERHALTEN selbst prüft der Service-Client-
// Test (ingredientsApi.test.ts); hier ist der ETag nur Durchreiche-Wert.
const mehl = { id: '8', name: 'Mehl', baseUnit: 'g', etag: '"0000a1b2"' } as const

// run-8-Nachtrag: zweite Zutat für die Undo-Toast-Verlässlichkeits-Szenarien (zwei
// Löschvorgänge nacheinander). Gleiche ETag-Semantik wie "mehl" – nur als Durchreiche-Wert.
const zucker = { id: '9', name: 'Zucker', baseUnit: 'g', etag: '"0000c3d4"' } as const

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

    // Then: der POST trug Name + Einheit als { name, baseUnit } (ADR-S068-1)
    expect(captured.current?.body).toEqual({ name: 'Tomaten', baseUnit: 'Stück' })
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
// (ADR-S090-1): { errors: { baseUnit: ["Einheit darf nicht leer sein."] } }. Der Key
// `baseUnit` ist die Request-JSON-Property exakt wie das FE im POST sendet. GET liefert
// unverändert [salz] (kein optimistic add), sodass "Liste bleibt unverändert" echt gilt.
function useEmptyUnitRejectingHandlers(): void {
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json([salz])),
    http.post('/api/ingredients', () =>
      HttpResponse.json(
        { status: 422, errors: { baseUnit: ['Einheit darf nicht leer sein.'] } },
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

    // Then: das Einheit-Feld ist als ungültig markiert (der baseUnit-Fehler landet dort)
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

// @US-904-happy-path: run-8 „Löschen·Success". Löschen aus der Liste (DELETE mit dem per-Zeile-
// xmin-ETag als If-Match, ADR-S108-1) + Undo via Toast-„Rückgängig" (Restore ohne If-Match,
// ADR-S108-2). GET-Handler schaltet zwischen [mehl] (aktiv) und [] (gelöscht) um, gesteuert durch
// den DELETE/Restore-Aufruf – so ist die invalidate-getriebene Listen-Umschaltung echt beobachtbar.
// Der DELETE-Handler validiert die id (realer Backend-404 bei falscher id, ADR-S000-5): killt den
// Objekt-Literal-Mutanten am `deleteMutate({ id, etag })`-Aufruf (bei `{}` würde id 'undefined' ->
// 404 -> Liste bliebe befüllt). Restore antwortet ab run-11 200 + Body (ADR-S111-1-Addendum zu
// ADR-S108-2, Pflicht-Body auch für den Undo-Fall) und hält den gesendeten Body fest – Grundlage
// für den Undo-Protokolltest weiter unten (kein eigenes Gherkin-Szenario, strukturell erzwungen).
function useDeleteRestoreMehlHandlers(): { restoreRequestBody: { current: unknown } } {
  // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: GET vor/nach Löschen/Restore
  let isDeleted = false
  const restoreRequestBody: { current: unknown } = { current: undefined }
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json(isDeleted ? [] : [mehl])),
    http.delete('/api/ingredients/:id', ({ params }) => {
      if (params.id !== mehl.id) return new HttpResponse(null, { status: 404 })
      isDeleted = true
      return new HttpResponse(null, { status: 204 })
    }),
    http.post('/api/ingredients/:id/restore', async ({ params, request }) => {
      if (params.id !== mehl.id) return new HttpResponse(null, { status: 404 })
      isDeleted = false
      // eslint-disable-next-line functional/immutable-data -- Capture: Restore-Body für Then-Block festhalten
      restoreRequestBody.current = await request.json()
      return HttpResponse.json(mehl, { status: 200 })
    }),
  )
  return { restoreRequestBody }
}

// run-8-Nachtrag „Undo-Toast-Verlässlichkeit": Mehl UND Zucker aktiv, unabhängig voneinander
// lösch-/wiederherstellbar (zwei Löschvorgänge nacheinander treiben die Szenarien dieses
// Blocks). Gleiches Umschalt-Prinzip wie useDeleteRestoreMehlHandlers, nur über eine Menge
// gelöschter ids statt eines einzelnen Flags.
function useDeleteRestoreMehlAndZuckerHandlers(): void {
  // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: GET vor/nach Löschen/Restore je Zutat
  let deletedIds: readonly string[] = []
  const allIngredients = [mehl, zucker]
  server.use(
    http.get('/api/ingredients', () =>
      HttpResponse.json(allIngredients.filter((i) => !deletedIds.includes(i.id)))),
    http.delete('/api/ingredients/:id', ({ params }) => {
      if (!allIngredients.some((i) => i.id === params.id)) return new HttpResponse(null, { status: 404 })
      deletedIds = [...deletedIds, params.id as string]
      return new HttpResponse(null, { status: 204 })
    }),
    http.post('/api/ingredients/:id/restore', ({ params }) => {
      const found = allIngredients.find((i) => i.id === params.id)
      if (!found) return new HttpResponse(null, { status: 404 })
      deletedIds = deletedIds.filter((id) => id !== params.id)
      // run-11: Restore antwortet 200 + Body statt 204 (ADR-S111-1-Addendum zu ADR-S108-2).
      return HttpResponse.json(found, { status: 200 })
    }),
  )
}

// TD-S108-3: gemeinsames Given der drei Löschen-Tests unten (Mehl aktiv, Seite gerendert,
// Liste da) – Rule-of-Three, analog zum bereits etablierten `renderWithPendingSave`-Muster.
// Nur das Given wandert hierher; der Löschen-Klick (When) bleibt in den Tests: Test 1 hat
// zwischen Given und When eine Vorbedingungs-Assertion ("kein Undo-Toast sichtbar"), die sich
// weder vor den Helper-Aufruf noch danach verschieben lässt, ohne die Given/When-Reihenfolge
// zu verdrehen. Der verbleibende einzeilige Klick ist keine Duplikation, die einen weiteren
// Helper rechtfertigt.
async function renderWithDeletableMehl(): Promise<HTMLElement> {
  // useDeleteRestoreMehlHandlers ist kein React-Hook, sondern reines MSW-Handler-Setup; das
  // "use"-Präfix ist die in dieser Datei etablierte Test-Helper-Konvention (analog
  // useEmptyNameRejectingHandlers etc.). Der Linter kann das nicht unterscheiden und meldet
  // hier einen False Positive.
  // eslint-disable-next-line react-hooks/rules-of-hooks -- s. Begründung oben
  useDeleteRestoreMehlHandlers()
  renderWithProviders(<IngredientsPage />)
  return screen.findByTestId('ingredient-list')
}

describe('IngredientsPage – Zutat löschen', () => {
  it('US904_HappyPath_DeleteIngredient_FromList_ListEmptyAndUndoToastShown', async () => {
    // Given: nur die Zutat "Mehl" (g) existiert
    const list = await renderWithDeletableMehl()
    expect(within(list).getByText('Mehl')).toBeInTheDocument()
    // Given (Vorbedingung): vor dem Löschen ist kein Undo-Toast sichtbar – pinnt "Toast erst nach
    //   der Aktion" und killt den Dauer-offen-Mutanten der Snackbar (open immer true).
    expect(screen.queryByRole('button', { name: 'Rückgängig' })).not.toBeInTheDocument()

    // When: ich bei "Mehl" auf Löschen klicke
    fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))

    // Then: die Zutaten-Liste ist leer -> Empty-State ersetzt die Liste (ingredient-list weg)
    expect(await screen.findByText('Noch keine Zutaten angelegt.')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByTestId('ingredient-list')).not.toBeInTheDocument()
    })
    // Then: Toast "Mehl gelöscht" mit "Rückgängig"-Aktion
    expect(screen.getByText('Mehl gelöscht')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rückgängig' })).toBeInTheDocument()
  })

  it('US904_HappyPath_UndoDelete_ViaToast_IngredientReappearsInList', async () => {
    // Given: nur die Zutat "Mehl" (g) existiert
    const list = await renderWithDeletableMehl()
    expect(within(list).getByText('Mehl')).toBeInTheDocument()

    // When: ich bei "Mehl" auf Löschen klicke
    fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))
    // When: ich im Toast auf "Rückgängig" klicke (findByRole wartet, bis der Toast-Button da ist)
    fireEvent.click(await screen.findByRole('button', { name: 'Rückgängig' }))

    // Then: "Mehl" ist wieder in der Zutaten-Liste mit Einheit "g" (Restore reaktiviert dieselbe
    //   Zeile; auf die Liste gescopt, damit der noch schließende Toast nicht mitzählt).
    const restoredList = await screen.findByTestId('ingredient-list')
    expect(await within(restoredList).findByText('Mehl')).toBeInTheDocument()
    expect(within(restoredList).getByText('g')).toBeInTheDocument()
  })
})

// run-8-Nachtrag „Löschen·Success": Verlässlichkeit des Undo-Wegs – der Toast ist die EINZIGE
// Wiederherstellungsmöglichkeit im UI (UX-Guideline Prinzip 5 Stufe 1), solange die
// Reaktivierung beim Neuanlegen (run-11) fehlt. Drei @US-904-edge-case-Szenarien aus
// features/ingredients.feature.
describe('IngredientsPage – Undo-Toast-Verlässlichkeit', () => {
  // Szenario: Undo-Toast bleibt bei einem Klick daneben erhalten
  it('US904_EdgeCase_UndoToast_ClickBesideToast_ToastRemainsVisible', async () => {
    // UX-Guideline Prinzip 5 ("Destructive Actions schützen"): der Undo-Weg für eine
    //   destruktive Aktion muss die volle autoHideDuration erreichbar bleiben. Ein Klick
    //   irgendwo auf der Seite (clickaway) ist keine bewusste Abbruch-Entscheidung und darf
    //   den Toast NICHT schließen – sonst wäre die großzügige autoHideDuration wertlos.
    //   escapeKeyDown ist eine bewusste Schließen-Geste und schließt weiterhin (deckt den
    //   onClose-Pfad/setDeleted(null) ab, der die Snackbar aus dem DOM nimmt).
    // Given: nur die Zutat "Mehl" (g) existiert
    await renderWithDeletableMehl()

    // When: ich bei "Mehl" auf Löschen klicke -> Toast erscheint
    fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))
    expect(await screen.findByText('Mehl gelöscht')).toBeInTheDocument()

    // When: ich neben den Toast klicke (clickaway). MUIs ClickAwayListener registriert dafür
    //   einen echten 'click'-Listener auf `document` (Snackbar-Default mouseEvent='onClick');
    //   ein reines fireEvent.click(document.body) triggert diesen Mechanismus also tatsächlich
    //   (kein Test-Artefakt, s. node_modules/@mui/material/ClickAwayListener + Snackbar/useSnackbar.js).
    fireEvent.click(document.body)

    // Then: der Toast bleibt offen -> der Undo-Weg ist weiterhin erreichbar
    expect(screen.getByText('Mehl gelöscht')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rückgängig' })).toBeInTheDocument()

    // When: ich Escape drücke. Geht über den Wortlaut des Szenarios (nur "Klick daneben")
    //   hinaus, ist aber KEIN eigenes Szenario: Escape-Dismiss ist MUI-Standardverhalten
    //   (UX-Guideline coding-guideline-ux.md Prinzip 8, Tabelle "Framework-geliefert – KEIN
    //   Szenario, per Review erzwungen") – hier zusätzlich mitgeprüft, um zu belegen, dass der
    //   onClose-Pfad (setDeleted(null)) neben dem clickaway-Guard weiterhin regulär funktioniert.
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' })

    // Then: jetzt schließt der Toast (Meldung + "Rückgängig" aus dem DOM) – belegt, dass der
    //   onClose-Pfad (setDeleted(null)) weiterhin funktioniert.
    await waitFor(() => {
      expect(screen.queryByText('Mehl gelöscht')).not.toBeInTheDocument()
    })
    expect(screen.queryByRole('button', { name: 'Rückgängig' })).not.toBeInTheDocument()
  })

  // Szenario: Zweites Löschen gibt dem neuen Toast die volle Rückgängig-Zeit
  it('US904_EdgeCase_SecondDelete_RestartsUndoWindow', async () => {
    // Given: die Zutaten "Mehl" und "Zucker" existieren
    useDeleteRestoreMehlAndZuckerHandlers()
    renderWithProviders(<IngredientsPage />)
    await screen.findByTestId('ingredient-list')

    // Fake-Timer NUR für den Zeitablauf-Teil dieses Tests: die MUI-autoHideDuration (6s) läuft
    // über echtes setTimeout – ohne Fake-Timer müsste der Test real 7s warten. fireEvent.click
    // bleibt synchron (act-gewrappt) und ist von Fake-Timern unabhängig; requestDelete setzt
    // `deleted` optimistisch synchron (useDeleteIngredientWithUndo.ts), daher reicht eine
    // direkte Assertion nach dem Klick ohne waitFor/findBy. advanceTimersByTimeAsync (statt
    // advanceTimersByTime) IN act(async () => ...): erst so committet React den State-Update,
    // den der abgelaufene MUI-Timer auslöst (handleClose('timeout') -> dismissUndo()) – ohne
    // act() bleibt document.body auf dem Stand vor dem Timer-Feuern (verifiziert: ohne act()
    // blieb der Toast in diesem Test fälschlich sichtbar, obwohl der State bereits genullt war).
    vi.useFakeTimers()
    try {
      // When: ich bei "Mehl" auf Löschen klicke -> Toast "Mehl gelöscht" erscheint,
      //   die 6s-Anzeigezeit startet
      fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))
      expect(screen.getByText('Mehl gelöscht')).toBeInTheDocument()

      // When: ich kurz vor Ablauf der Toast-Anzeigezeit (4,5s < 6s) bei "Zucker" auf Löschen
      //   klicke. advanceTimersByTimeAsync statt advanceTimersByTime: lässt anhängige Promises
      //   (Query-Invalidierung/Refetch aus dem ersten Löschen) zwischen den Ticks abarbeiten.
      await act(async () => { await vi.advanceTimersByTimeAsync(4_500) })
      fireEvent.click(screen.getByRole('button', { name: 'Zucker löschen' }))

      // Then: der neue Toast zeigt "Zucker gelöscht" mit "Rückgängig"
      expect(screen.getByText('Zucker gelöscht')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Rückgängig' })).toBeInTheDocument()

      // Then: "Rückgängig" ist noch verfügbar, nachdem die Anzeigezeit des ERSTEN Toasts
      //   abgelaufen wäre (t≈7s > 6s). Erbt der zweite Toast dessen Restlaufzeit, ist er hier
      //   bereits weg – der Nutzer verlöre die Undo-Möglichkeit für "Zucker" nach 1,5 statt 6s.
      await act(async () => { await vi.advanceTimersByTimeAsync(2_500) })
      expect(screen.getByText('Zucker gelöscht')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Rückgängig' })).toBeInTheDocument()
    } finally {
      vi.useRealTimers()
    }
  })

  // Szenario: Nur der zuletzt gelöschten Zutat lässt sich das Löschen rückgängig machen
  it('US904_EdgeCase_TwoDeletes_UndoRestoresOnlyTheLatest', async () => {
    // ADR-S108-3: der Undo-Zustand hält genau einen Löschvorgang vor (den zuletzt
    //   ausgeführten) – kein Snackbar-Stacking. Pinnt diese bewusste Einschränkung.
    // Given: die Zutaten "Mehl" und "Zucker" existieren
    useDeleteRestoreMehlAndZuckerHandlers()
    renderWithProviders(<IngredientsPage />)
    const list = await screen.findByTestId('ingredient-list')
    expect(within(list).getByText('Mehl')).toBeInTheDocument()

    // When: ich bei "Mehl" und danach bei "Zucker" auf Löschen klicke
    fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))
    fireEvent.click(screen.getByRole('button', { name: 'Zucker löschen' }))
    // When: ich im Toast auf "Rückgängig" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Rückgängig' }))

    // Then: "Zucker" kehrt in die Zutaten-Liste zurück – "Mehl" bleibt gelöscht
    const restoredList = await screen.findByTestId('ingredient-list')
    expect(await within(restoredList).findByText('Zucker')).toBeInTheDocument()
    expect(within(restoredList).queryByText('Mehl')).not.toBeInTheDocument()
  })
})

// run-9 „Löschen·Pending": das DELETE bleibt hängen, bis der Test es per `resolveDelete`
// auflöst – analog zu `renderWithPendingSave` (deterministisches Pending-Fenster ohne
// Timer-Race). GET ist zustandsbehaftet (analog `useDeleteRestoreMehlHandlers`), damit der
// Refetch nach dem aufgelösten DELETE echt auf die leere Liste umschaltet – sonst könnte das
// Cleanup unten (Warten auf verschwundene Liste) nie zutreffen.
async function renderWithPendingDelete(): Promise<{ resolveDelete: () => void }> {
  // eslint-disable-next-line functional/no-let -- Resolver wird im DELETE-Handler befuellt
  let resolveDelete: () => void = () => {}
  const deletePending = new Promise<void>((resolve) => { resolveDelete = resolve })
  // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: GET vor/nach dem DELETE
  let isDeleted = false
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json(isDeleted ? [] : [mehl])),
    http.delete('/api/ingredients/:id', async () => {
      await deletePending
      isDeleted = true
      return new HttpResponse(null, { status: 204 })
    }),
  )
  renderWithProviders(<IngredientsPage />)
  await screen.findByTestId('ingredient-list')
  return { resolveDelete }
}

describe('IngredientsPage – Löschen·Pending', () => {
  // Szenario: Löschen-Button ist während des Löschens deaktiviert
  it('US904_HappyPath_DeleteInFlight_DeleteButtonIsDisabled', async () => {
    // Given: nur die Zutat "Mehl" (g) existiert; der DELETE bleibt hängen, bis der Test
    //   ihn auflöst (Helper)
    const { resolveDelete } = await renderWithPendingDelete()
    // Given (Vorbedingung): vor dem Klick ist der Löschen-Button aktiv. "deaktiviert solange
    //   die Antwort aussteht" ist ein Übergang – ohne diese Hälfte wäre die Then-Assertion
    //   vakuös erfüllbar: wäre der Button schon beim Rendern deaktiviert, feuerte der Klick
    //   nativ kein onClick, und `toBeDisabled()` träfe zu, ohne dass je ein DELETE lief.
    expect(screen.getByRole('button', { name: 'Mehl löschen' })).not.toBeDisabled()

    // When: ich bei "Mehl" auf Löschen klicke
    fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))

    // Then: der Löschen-Button für "Mehl" ist deaktiviert, solange die Antwort aussteht
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Mehl löschen' })).toBeDisabled()
    })

    // Cleanup (kein Szenario-Assert, reine Test-Infrastruktur): DELETE auflösen, damit kein
    //   hängender Handler in den nächsten Test läuft.
    resolveDelete()
    await waitFor(() => {
      expect(screen.queryByTestId('ingredient-list')).not.toBeInTheDocument()
    })
  })
})

// run-11 „Reaktivierung": Der Name existiert bereits soft-deleted -> POST antwortet 409
// { code: 'ingredient_soft_deleted', id } (ADR-S004-1), der Client ruft daraufhin transparent
// den Restore mit den EIGENEN Eingaben auf (ADR-S051-4) – ohne Zutun des Nutzers. Der Restore-
// Mock ECHOT ausschließlich, was der Client im Body sendet (wie der reale Server bei fehlendem
// Konflikt), nicht die (dem Client unbekannten) alten Werte der gelöschten Zeile – so pinnt jeder
// Test hier, dass die EIGENE Eingabe reist, nicht ein Zufallswert. GET liefert erst [] (Zeile ist
// für den Client "nicht da"), nach dem Restore die reaktivierte Zutat.
function useReactivateSoftDeletedHandlers(
  id: string,
): { restoreRequestBody: { current: unknown }; restoreContentType: { current: string | null } } {
  const restoreRequestBody: { current: unknown } = { current: undefined }
  const restoreContentType: { current: string | null } = { current: null }
  server.use(
    http.get('/api/ingredients', () =>
      HttpResponse.json(
        restoreRequestBody.current
          ? [{ id, ...(restoreRequestBody.current as { name: string; baseUnit: string }), etag: '"00000001"' }]
          : [],
      )),
    http.post('/api/ingredients', () =>
      HttpResponse.json({ code: 'ingredient_soft_deleted', id }, { status: 409 })),
    http.post(`/api/ingredients/${id}/restore`, async ({ request }) => {
      // eslint-disable-next-line functional/immutable-data -- Capture: Restore-Body/-Header für Then-Block/GET-Echo festhalten
      restoreRequestBody.current = await request.json()
      // eslint-disable-next-line functional/immutable-data -- Capture: s.o.
      restoreContentType.current = request.headers.get('Content-Type')
      return HttpResponse.json(
        { id, ...(restoreRequestBody.current as { name: string; baseUnit: string }), etag: '"00000001"' },
        { status: 200 },
      )
    }),
  )
  return { restoreRequestBody, restoreContentType }
}

describe('IngredientsPage – Zutat reaktivieren', () => {
  // Szenario: Gelöschte Zutat mit gleichem Namen anlegen reaktiviert diese
  it('US904_EdgeCase_CreateIngredient_SoftDeletedSameName_ReactivatesIngredient', async () => {
    // Given: die Zutat "Butter" (g) existiert soft-deleted
    const user = userEvent.setup()
    const { restoreRequestBody, restoreContentType } = useReactivateSoftDeletedHandlers('butter-id')
    renderWithProviders(<IngredientsPage />)

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    // When: ich "Butter" als Name eingebe
    await user.type(screen.getByLabelText(/^Name/), 'Butter')
    // When: ich "g" als Einheit eingebe
    await user.type(screen.getByLabelText(/^Einheit/), 'g')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: ich sehe "Butter" in der Zutaten-Liste mit Einheit "g"
    const list = await screen.findByTestId('ingredient-list')
    expect(await within(list).findByText('Butter')).toBeInTheDocument()
    expect(within(list).getByText('g')).toBeInTheDocument()
    // Then: der "Zutat anlegen"-Dialog ist geschlossen – der Nutzer merkt von der Reaktivierung
    //   nichts (der 409/Restore-Umweg ist rein client-intern)
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
    // Then: der Client rief den Restore transparent mit den EIGENEN Eingaben auf
    expect(restoreRequestBody.current).toEqual({ name: 'Butter', baseUnit: 'g' })
    // Then: der Restore-Request sendete JSON (Content-Type), damit das Backend den Pflicht-Body
    //   bindet (ADR-S111-1)
    expect(restoreContentType.current).toBe('application/json')
    // Then: kein Reaktivierungs-Konflikt-Hinweis – der Nutzer merkt von der Reaktivierung
    //   wirklich nichts, es gibt keinen fremden Stand zu melden (Abgrenzung zu
    //   US904_Error_ReactivateIngredient_ParallelRestoreDifferentData_ShowsConflictHint)
    expect(screen.queryByText(/wurde zwischenzeitlich an anderer Stelle wiederhergestellt/)).not.toBeInTheDocument()
  })

  // Szenario: Reaktivierung übernimmt neue Einheit
  it('US904_EdgeCase_ReactivateIngredient_NewUnit_ListShowsNewUnit', async () => {
    // Given: die Zutat "Butter" existiert soft-deleted (frühere Einheit "Würfel" ist dem Client
    //   unbekannt – der Restore-Mock kennt sie gar nicht, er echot nur den gesendeten Body)
    const user = userEvent.setup()
    useReactivateSoftDeletedHandlers('butter-id')
    renderWithProviders(<IngredientsPage />)

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    // When: ich "Butter" als Name eingebe
    await user.type(screen.getByLabelText(/^Name/), 'Butter')
    // When: ich "g" als NEUE Einheit eingebe (weicht von der alten, gelöschten Einheit ab)
    await user.type(screen.getByLabelText(/^Einheit/), 'g')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: ich sehe "Butter" in der Zutaten-Liste mit der NEUEN Einheit "g"
    //   (der Mock echot ausschließlich die gesendeten Werte – "Würfel" kann in keinem
    //   Ausführungspfad ins DOM gelangen, eine Negativ-Assertion darauf wäre unfähig zu
    //   scheitern; der reale "alte Wert existiert noch"-Fall ist im E2E-Test gegen das
    //   echte Backend abgesichert)
    const list = await screen.findByTestId('ingredient-list')
    expect(await within(list).findByText('Butter')).toBeInTheDocument()
    expect(within(list).getByText('g')).toBeInTheDocument()
  })

  // Szenario: Reaktivierung übernimmt neuen Namen bei abweichender Schreibweise
  it('US904_EdgeCase_ReactivateIngredient_DifferentCasing_ListShowsNewSpelling', async () => {
    // Given: die Zutat "mehl" (kleingeschrieben) existiert soft-deleted
    const user = userEvent.setup()
    useReactivateSoftDeletedHandlers('mehl-id')
    renderWithProviders(<IngredientsPage />)

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    // When: ich "Mehl" (großgeschrieben) als Name eingebe – case-insensitiv dieselbe Zutat
    //   (ADR-S051-3), aber eine abweichende Schreibweise
    await user.type(screen.getByLabelText(/^Name/), 'Mehl')
    // When: ich "g" als Einheit eingebe
    await user.type(screen.getByLabelText(/^Einheit/), 'g')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: ich sehe "Mehl" (neue Schreibweise) in der Zutaten-Liste mit Einheit "g"
    //   (der Mock echot ausschließlich die gesendeten Werte – "mehl" kleingeschrieben kann in
    //   keinem Ausführungspfad ins DOM gelangen, eine Negativ-Assertion darauf wäre unfähig zu
    //   scheitern; der reale "alte Schreibweise existiert noch"-Fall ist im E2E-Test gegen das
    //   echte Backend abgesichert)
    const list = await screen.findByTestId('ingredient-list')
    expect(await within(list).findByText('Mehl')).toBeInTheDocument()
  })

  // Protokolltest nach ADR-S106-3 Kategorie 1 (kein US-Tag, kein treibendes Gherkin-Szenario):
  // strukturell erzwungen durch den gemeinsamen Restore-Codepfad. Tragende Entscheidung
  // ADR-S111-1 – der Restore-Body ist ab run-11 Pflichtbestandteil des Contracts, auch für den
  // Undo-Fall (fachlich ein No-op: unveränderte Werte). Ohne diesen Test bliebe die Verdrahtung
  // der Werte im Undo-Pfad (useDeleteIngredientWithUndo) ungetestet und ein Stryker-Survivor.
  it('UndoDelete_RestoreRequestCarriesOriginalNameAndUnit', async () => {
    // Given: nur die Zutat "Mehl" (g) existiert
    const { restoreRequestBody } = useDeleteRestoreMehlHandlers()
    renderWithProviders(<IngredientsPage />)
    await screen.findByTestId('ingredient-list')

    // When: ich bei "Mehl" auf Löschen klicke und danach im Toast auf "Rückgängig"
    fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Rückgängig' }))

    // Then: der Restore-Request trug Name und Einheit der gelöschten Zutat unverändert mit
    await waitFor(() => {
      expect(restoreRequestBody.current).toEqual({ name: 'Mehl', baseUnit: 'g' })
    })
  })

  // run-11-Nachbesserung F1: Löschen + sofortiges Neuanlegen unter demselben Namen reaktiviert die
  // Zeile über den transparenten 409-soft-deleted-Restore-Umweg (ADR-S051-4) – kombiniert GET/DELETE
  // mit dem für diesen Fall bislang fehlenden POST-/api/ingredients-Pfad (409) + Restore (200).
  function useDeleteThenRecreateMehlHandlers(): void {
    // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: GET/POST vor/nach Löschen/Restore
    let isDeleted = false
    server.use(
      http.get('/api/ingredients', () => HttpResponse.json(isDeleted ? [] : [mehl])),
      http.delete('/api/ingredients/:id', ({ params }) => {
        if (params.id !== mehl.id) return new HttpResponse(null, { status: 404 })
        isDeleted = true
        return new HttpResponse(null, { status: 204 })
      }),
      http.post('/api/ingredients', () =>
        HttpResponse.json({ code: 'ingredient_soft_deleted', id: mehl.id }, { status: 409 })),
      http.post(`/api/ingredients/${mehl.id}/restore`, () => {
        isDeleted = false
        return HttpResponse.json(mehl, { status: 200 })
      }),
    )
  }

  // Protokolltest nach ADR-S106-3 Kategorie 1 (kein US-Tag, kein eigenes Gherkin-Szenario):
  // tragende Entscheidung ADR-S111-1 – der transparente Reaktivierungs-Umweg (409 soft-deleted ->
  // Restore) macht eine zuvor gelöschte Zeile wieder aktiv, ohne dass der Nutzer den Undo-Weg
  // benutzt. Der noch sichtbare Undo-Toast der vorangegangenen Löschung muss dabei verworfen
  // werden – sonst behauptet er weiterhin "gelöscht", obwohl die Zeile längst wieder aktiv ist,
  // und ein Klick auf "Rückgängig" liefe ins Leere (409 ingredient_already_active, ADR-S111-1).
  it('UndoToast_ReactivateSameIngredientViaCreate_DismissesUndoToast', async () => {
    // Given: nur die Zutat "Mehl" (g) existiert
    const user = userEvent.setup()
    useDeleteThenRecreateMehlHandlers()
    renderWithProviders(<IngredientsPage />)
    await screen.findByTestId('ingredient-list')

    // When: ich "Mehl" lösche -> Undo-Toast erscheint
    fireEvent.click(screen.getByRole('button', { name: 'Mehl löschen' }))
    expect(await screen.findByText('Mehl gelöscht')).toBeInTheDocument()

    // When: ich innerhalb der Undo-Frist "Mehl" (g) erneut anlege
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    await user.type(screen.getByLabelText(/^Name/), 'Mehl')
    await user.type(screen.getByLabelText(/^Einheit/), 'g')
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: der Undo-Toast für die alte Löschung ist verschwunden (die Zeile ist bereits aktiv)
    await waitFor(() => {
      expect(screen.queryByText('Mehl gelöscht')).not.toBeInTheDocument()
    })
    expect(screen.queryByRole('button', { name: 'Rückgängig' })).not.toBeInTheDocument()
  })
})

// run-11 „Reaktivierung", Konfliktfall (ADR-S111-1/-3): Trägt die parallel wiederhergestellte
// Zeile ABWEICHENDE Daten, antwortet der Restore 409 { code: 'ingredient_already_active',
// ingredient }. GET liefert erst [] (die Zeile ist für den Client "noch nicht da"), nach dem
// Restore-Aufruf den bereits aktiven FREMDEN Stand ("Koriander"/"Töpfchen") – unabhängig von der
// eigenen Eingabe ("Bund"), weil der Client den fremden Schreibvorgang nicht überschreiben darf.
function useReactivationConflictHandlers(id: string): void {
  // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: GET vor/nach dem Restore-Konflikt
  let isResolved = false
  const activeIngredient = { id, name: 'Koriander', baseUnit: 'Töpfchen', etag: '"00000002"' } as const
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json(isResolved ? [activeIngredient] : [])),
    http.post('/api/ingredients', () =>
      HttpResponse.json({ code: 'ingredient_soft_deleted', id }, { status: 409 })),
    http.post(`/api/ingredients/${id}/restore`, () => {
      isResolved = true
      return HttpResponse.json({ code: 'ingredient_already_active', ingredient: activeIngredient }, { status: 409 })
    }),
  )
}

describe('IngredientsPage – Reaktivierungs-Konflikt', () => {
  // Szenario: Reaktivierung meldet Konflikt wenn die Zutat parallel mit anderen Daten
  // wiederhergestellt wurde
  it('US904_Error_ReactivateIngredient_ParallelRestoreDifferentData_ShowsConflictHint', async () => {
    // Given: die Zutat "Koriander" (Bund) existiert soft-deleted; parallel wurde sie bereits mit
    //   Einheit "Töpfchen" wiederhergestellt
    const user = userEvent.setup()
    useReactivationConflictHandlers('koriander-id')
    renderWithProviders(<IngredientsPage />)

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    // When: ich "Koriander" als Name eingebe
    await user.type(screen.getByLabelText(/^Name/), 'Koriander')
    // When: ich "Bund" als Einheit eingebe
    await user.type(screen.getByLabelText(/^Einheit/), 'Bund')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: ich sehe den Hinweis, der die eigene Eingabe UND den tatsächlich gespeicherten
    //   Stand nennt (Wortlaut run-11-Nachbesserung F2, ADR-S111-3)
    expect(await screen.findByText(
      "'Koriander' wurde zwischenzeitlich an anderer Stelle wiederhergestellt (z. B. auf einem anderen Gerät). Gespeichert ist 'Koriander' mit der Einheit 'Töpfchen'.",
    )).toBeInTheDocument()
    // Then: der Dialog ist geschlossen – es gibt nichts zu korrigieren (ADR-S111-3)
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
    // Then: ich sehe "Koriander" in der Zutaten-Liste mit Einheit "Töpfchen"
    const list = await screen.findByTestId('ingredient-list')
    expect(await within(list).findByText('Töpfchen')).toBeInTheDocument()
    // Then: die eigene Eingabe "Bund" erscheint nicht – sie wurde nicht gespeichert
    expect(within(list).queryByText('Bund')).not.toBeInTheDocument()
  })

  // Protokolltest nach ADR-S106-3 Kategorie 1 (kein US-Tag, kein treibendes Gherkin-Szenario):
  // tragende Entscheidung ADR-S111-3 ("Auto-Hide 10000 ms, bewusst länger als der Undo-Toast") –
  // ohne einen funktionierenden Dismiss-Callback bliebe die Konflikt-Snackbar nach Ablauf der
  // Anzeigezeit dauerhaft sichtbar, weil MUI selbst nichts unmountet. Geprüft wird ausschließlich,
  // dass der Hinweis nach einem Schließen-Grund (hier: Escape, trifft denselben onClose-Callback
  // wie der Auto-Hide-Timer) wieder verschwindet – keine Timing-Zusicherung, kein Fehlerpfad.
  it('ReactivationConflictToast_Escape_HidesToast', async () => {
    // Given: der Reaktivierungs-Konflikt-Hinweis ist sichtbar
    const user = userEvent.setup()
    useReactivationConflictHandlers('koriander-id')
    renderWithProviders(<IngredientsPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    await user.type(screen.getByLabelText(/^Name/), 'Koriander')
    await user.type(screen.getByLabelText(/^Einheit/), 'Bund')
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))
    await screen.findByText(/wurde zwischenzeitlich an anderer Stelle wiederhergestellt/)

    // When: ich Escape drücke
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' })

    // Then: der Hinweis verschwindet
    await waitFor(() => {
      expect(screen.queryByText(/wurde zwischenzeitlich an anderer Stelle wiederhergestellt/)).not.toBeInTheDocument()
    })
  })

  // Protokolltest nach ADR-S106-3 Kategorie 1 (kein US-Tag, kein eigenes Gherkin-Szenario):
  // tragende Entscheidung ADR-S051-1/-2 ("jede nutzersichtbare Wiedergabe einer Eingabe ist
  // getrimmt") angewandt auf den Reaktivierungs-Konflikt-Hinweis (ADR-S111-3). Ohne Trimmen
  // stünde die Eingabe mit sichtbaren Leerzeichen im Hinweis, obwohl jede andere nutzersichtbare
  // Wiedergabe einer Eingabe im UI getrimmt ist (analog zur Duplikat-Fehlermeldung).
  it('ReactivationConflictToast_WhitespacePaddedInput_ShowsTrimmedNameInHint', async () => {
    // Given: die Zutat "Koriander" (Bund) existiert soft-deleted; parallel wurde sie bereits mit
    //   Einheit "Töpfchen" wiederhergestellt
    const user = userEvent.setup()
    useReactivationConflictHandlers('koriander-id')
    renderWithProviders(<IngredientsPage />)

    // When: ich auf "Zutat anlegen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    // When: ich "  Koriander  " (mit umgebenden Leerzeichen) als Name eingebe
    await user.type(screen.getByLabelText(/^Name/), '  Koriander  ')
    // When: ich "Bund" als Einheit eingebe
    await user.type(screen.getByLabelText(/^Einheit/), 'Bund')
    // When: ich auf "Speichern" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: der Hinweis nennt die eigene Eingabe GETRIMMT, nicht mit Leerzeichen
    expect(await screen.findByText(
      "'Koriander' wurde zwischenzeitlich an anderer Stelle wiederhergestellt (z. B. auf einem anderen Gerät). Gespeichert ist 'Koriander' mit der Einheit 'Töpfchen'.",
    )).toBeInTheDocument()
  })

  // run-11-Nachbesserung F5: Konflikt-Hinweis für "Koriander", gefolgt von einer normal
  // erfolgreichen Anlage einer ANDEREN Zutat – deckt den null-Zweig von toConflictNotice
  // (Code-Kommentar dort, tragende Entscheidung ADR-S111-3): räumt einen noch sichtbaren
  // Hinweis weg, wenn danach ein normales Anlegen gelingt.
  function useReactivationConflictThenPlainCreateHandlers(id: string): void {
    // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: GET vor/nach Konflikt/Erfolg
    let isResolved = false
    // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: s.o.
    let created = false
    const activeIngredient = { id, name: 'Koriander', baseUnit: 'Töpfchen', etag: '"00000002"' } as const
    const zwiebel = { id: 'zwiebel-id', name: 'Zwiebel', baseUnit: 'Stück', etag: '"00000003"' } as const
    server.use(
      http.get('/api/ingredients', () =>
        HttpResponse.json([...(isResolved ? [activeIngredient] : []), ...(created ? [zwiebel] : [])])),
      http.post('/api/ingredients', async ({ request }) => {
        const body = await request.json() as { name: string }
        if (body.name === 'Koriander') return HttpResponse.json({ code: 'ingredient_soft_deleted', id }, { status: 409 })
        created = true
        return HttpResponse.json(zwiebel, { status: 201 })
      }),
      http.post(`/api/ingredients/${id}/restore`, () => {
        isResolved = true
        return HttpResponse.json({ code: 'ingredient_already_active', ingredient: activeIngredient }, { status: 409 })
      }),
    )
  }

  // Protokolltest nach ADR-S106-3 Kategorie 1 (kein US-Tag, kein eigenes Gherkin-Szenario):
  // pinnt den null-Zweig von toConflictNotice – ohne ihn bliebe ein Refactoring zu
  // `if (kind === 'ReactivationConflict') setConflictNotice(...)` unentdeckt, und ein veralteter
  // Konflikt-Hinweis stünde fälschlich weiter, obwohl danach ein normales Anlegen gelingt.
  it('ReactivationConflictToast_SucceedingCreateAfterConflict_HidesToast', async () => {
    // Given: der Reaktivierungs-Konflikt-Hinweis für "Koriander" ist sichtbar
    const user = userEvent.setup()
    useReactivationConflictThenPlainCreateHandlers('koriander-id')
    renderWithProviders(<IngredientsPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    await user.type(screen.getByLabelText(/^Name/), 'Koriander')
    await user.type(screen.getByLabelText(/^Einheit/), 'Bund')
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))
    await screen.findByText(/wurde zwischenzeitlich an anderer Stelle wiederhergestellt/)

    // When: ich danach eine ANDERE Zutat erfolgreich anlege
    fireEvent.click(await screen.findByRole('button', { name: 'Zutat anlegen' }))
    await awaitDialogAutofocus()
    await user.type(screen.getByLabelText(/^Name/), 'Zwiebel')
    await user.type(screen.getByLabelText(/^Einheit/), 'Stück')
    fireEvent.click(screen.getByRole('button', { name: 'Speichern' }))

    // Then: der Konflikt-Hinweis für "Koriander" ist verschwunden
    await waitFor(() => {
      expect(screen.queryByText(/wurde zwischenzeitlich an anderer Stelle wiederhergestellt/)).not.toBeInTheDocument()
    })
  })
})

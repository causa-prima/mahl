import { describe, it, expect, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { delay, http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { renderApp } from '../test/renderApp'

const hint = 'Noch keine Rezepte vorgemerkt.'
const potatoSoup = { id: '3f2b8c1e-0000-4000-8000-000000000503', title: 'Kartoffelsuppe' }
const pancakes = { id: '3f2b8c1e-0000-4000-8000-000000000501', title: 'Pfannkuchen' }

// Zustandsbehafteter Server (ADR-S153-1: idempotentes PUT/DELETE auf die Rezept-ID, 204). GET liefert
// wie der echte Server alphabetisch (ADR-S142-1). `planned` hält die IDs der Vormerkungen; die
// Schreibaufrufe werden als Rezept-ID in `deleted` bzw. `put` mitgezählt. `putDeleteFinished` erhält
// bei jedem PUT zusätzlich, ob das DELETE desselben Rezepts zu diesem Zeitpunkt schon abgeschlossen war.
// `deleteGate`: Das DELETE antwortet (und ändert den Serverzustand) erst, wenn das Tor aufgeht.
function plannedServer(initial: readonly { id: string; title: string }[], deleteGate: Promise<void> = Promise.resolve()) {
  const all = [potatoSoup, pancakes]
  // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: GET vor/nach Entfernen/Vormerken
  let planned: readonly string[] = initial.map((r) => r.id)
  // eslint-disable-next-line functional/no-let -- MSW-Handler-Zustand: IDs, deren DELETE abgeschlossen ist
  let finishedDeletes: readonly string[] = []
  const deleted = vi.fn<(id: string) => void>()
  const put = vi.fn<(id: string) => void>()
  const putDeleteFinished = vi.fn<(id: string, deleteFinished: boolean) => void>()
  server.use(
    http.get('/api/planned-recipes', () => HttpResponse.json(
      all.filter((r) => planned.includes(r.id)).sort((a, b) => a.title.localeCompare(b.title, 'de')),
    )),
    http.delete('/api/planned-recipes/:id', async ({ params }) => {
      deleted(String(params.id))
      await deleteGate
      planned = planned.filter((id) => id !== params.id)
      finishedDeletes = [...finishedDeletes, String(params.id)]
      return new HttpResponse(null, { status: 204 })
    }),
    http.put('/api/planned-recipes/:id', ({ params }) => {
      put(String(params.id))
      putDeleteFinished(String(params.id), finishedDeletes.includes(String(params.id)))
      planned = [...planned.filter((id) => id !== params.id), String(params.id)]
      return new HttpResponse(null, { status: 204 })
    }),
  )
  return { deleted, put, putDeleteFinished }
}

const titlesShown = () => within(screen.getByRole('list', { name: 'Vorgemerkt' }))
  .getAllByRole('listitem').map((item) => item.textContent)

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
    const { router } = renderApp('/planned')

    // When: ich zur Vorgemerkt-Seite navigiere und auf "Pfannkuchen" klicke
    fireEvent.click(await screen.findByRole('link', { name: 'Pfannkuchen' }))

    // Then: ich sehe die Detailansicht von "Pfannkuchen" mit "250 g Mehl", und der Umschalter zeigt "Vorgemerkt"
    expect(await screen.findByRole('heading', { level: 1, name: 'Pfannkuchen' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(`/recipes/${pancakes.id}`)
    const ingredients = within(await screen.findByRole('list', { name: 'Zutaten' }))
    expect(ingredients.getAllByRole('listitem').map((item) => item.textContent)).toEqual(['250 g Mehl'])
    expect(await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })).toHaveTextContent('Vorgemerkt')
  })

  // Szenario: Eine Vormerkung auf der Vorgemerkt-Seite entfernen
  it('US803_HappyPath_PlannedRecipesPage_RemoveClicked_DeletesAndShowsRestAndUndoToast', async () => {
    // Given: "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt; der Server hält den Zustand
    const writes = plannedServer([potatoSoup, pancakes])
    renderApp('/planned')

    // When: ich bei "Pfannkuchen" auf "Entfernen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Pfannkuchen entfernen' }))

    // Then: der Server wurde mit DELETE auf die Rezept-ID gerufen, die Seite zeigt genau "Kartoffelsuppe",
    // und der Toast "Pfannkuchen entfernt" bietet "Rückgängig" an
    await waitFor(() => { expect(titlesShown()).toEqual(['Kartoffelsuppe']) })
    expect(writes.deleted).toHaveBeenCalledExactlyOnceWith(pancakes.id)
    expect(screen.getByText('Pfannkuchen entfernt')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rückgängig' })).toBeInTheDocument()
  })

  // Szenario: Löschen-Button ist während des Löschens deaktiviert
  // (features/interaction.feature, Querschnitt: auf dieser Seite heißt die Aktion „Entfernen")
  it('CROSS_Interaction_Pending_PlannedRecipesPage_RemoveRunning_DisablesOnlyThatRowsButton', async () => {
    // Given: beide Rezepte sind vorgemerkt; das DELETE für "Pfannkuchen" antwortet noch nicht
    server.use(
      http.get('/api/planned-recipes', () => HttpResponse.json([potatoSoup, pancakes])),
      http.delete('/api/planned-recipes/:id', async () => { await delay('infinite') }),
    )
    renderApp('/planned')

    // When: ich bei "Pfannkuchen" auf "Entfernen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Pfannkuchen entfernen' }))

    // Then: nur dieser Entfernen-Button ist gesperrt
    expect(screen.getByRole('button', { name: 'Pfannkuchen entfernen' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Kartoffelsuppe entfernen' })).toBeEnabled()
  })

  // Szenario: Das Entfernen einer Vormerkung rückgängig machen
  it('US803_HappyPath_PlannedRecipesPage_UndoClicked_RestoresRowInServerOrderAndHidesToast', async () => {
    // Given: beide Rezepte sind vorgemerkt; der Server liefert alphabetisch
    const writes = plannedServer([potatoSoup, pancakes])
    renderApp('/planned')

    // When: ich bei "Kartoffelsuppe" auf "Entfernen" und im Toast auf "Rückgängig" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Kartoffelsuppe entfernen' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Rückgängig' }))

    // Then: PUT auf die Rezept-ID, beide Rezepte in dieser Reihenfolge, der Toast ist weg
    await waitFor(() => { expect(titlesShown()).toEqual(['Kartoffelsuppe', 'Pfannkuchen']) })
    expect(writes.put).toHaveBeenCalledExactlyOnceWith(potatoSoup.id)
    await waitFor(() => { expect(screen.queryByText('Kartoffelsuppe entfernt')).not.toBeInTheDocument() })
  })

  // Szenario: Rückgängig während das Löschen noch läuft stellt die Zutat dauerhaft wieder her
  // (features/interaction.feature, Querschnitt: auf dieser Seite heißt die Aktion „Entfernen")
  it('CROSS_Interaction_Undo_PlannedRecipesPage_UndoWhileRemoveRunning_RestoresOnlyAfterRemoveFinished', async () => {
    // Given: beide Rezepte sind vorgemerkt; das DELETE für "Kartoffelsuppe" antwortet erst, wenn das Tor aufgeht
    // eslint-disable-next-line functional/no-let -- Tor: Auflöser der Promise nach außen reichen
    let openGate: () => void = () => undefined
    const gate = new Promise<void>((resolve) => { openGate = resolve })
    const writes = plannedServer([potatoSoup, pancakes], gate)
    renderApp('/planned')

    // When: ich bei "Kartoffelsuppe" auf "Entfernen" klicke und im Toast auf "Rückgängig", noch bevor das Entfernen fertig ist
    fireEvent.click(await screen.findByRole('button', { name: 'Kartoffelsuppe entfernen' }))
    await waitFor(() => { expect(writes.deleted).toHaveBeenCalledExactlyOnceWith(potatoSoup.id) })
    fireEvent.click(screen.getByRole('button', { name: 'Rückgängig' }))

    // (ein Event-Loop-Durchlauf, damit ein vorschnell gesendetes PUT den Server vor dem Öffnen des Tors erreicht – kein Zeitfenster)
    await new Promise((resolve) => { setTimeout(resolve, 0) })

    // When: das Entfernen ist abgeschlossen
    openGate()

    // Then: genau ein PUT folgt, und zwar nach abgeschlossenem DELETE; danach zeigt die Liste wieder beide Rezepte
    await waitFor(() => { expect(titlesShown()).toEqual(['Kartoffelsuppe', 'Pfannkuchen']) })
    expect(writes.putDeleteFinished).toHaveBeenCalledExactlyOnceWith(potatoSoup.id, true)
  })

  // Szenario: Die letzte Vormerkung entfernen und zurückholen
  it('US803_EdgeCase_PlannedRecipesPage_RemoveLast_ShowsHintAndUndoBringsItBack', async () => {
    // Given: nur "Pfannkuchen" ist vorgemerkt
    plannedServer([pancakes])
    renderApp('/planned')

    // When: ich bei "Pfannkuchen" auf "Entfernen" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Pfannkuchen entfernen' }))

    // Then: Hinweis und Link erscheinen, der Toast "Pfannkuchen entfernt" bietet "Rückgängig" an
    expect(await screen.findByText(hint)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Zur Rezept-Liste' })).toBeInTheDocument()
    expect(screen.getByText('Pfannkuchen entfernt')).toBeInTheDocument()

    // When: ich im Toast auf "Rückgängig" klicke
    fireEvent.click(screen.getByRole('button', { name: 'Rückgängig' }))

    // Then: die Seite zeigt genau "Pfannkuchen", der Hinweis ist weg
    await waitFor(() => { expect(titlesShown()).toEqual(['Pfannkuchen']) })
    expect(screen.queryByText(hint)).not.toBeInTheDocument()
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

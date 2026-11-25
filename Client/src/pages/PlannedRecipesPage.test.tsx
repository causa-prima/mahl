import { describe, it, expect, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { delay, http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { renderApp } from '../test/renderApp'
import { listedItems } from '../test/shoppingListItems'
import { nbsp } from '../test/nbsp'

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

const generateName = 'Zutaten aller vorgemerkten Rezepte auf die Einkaufsliste'

// Tor: `opened` löst auf, sobald `open` gerufen wird (kein Promise.withResolvers: lib ES2022). Das Lauschen
// beginnt beim Anlegen – `open` vor dem Warten geht nicht verloren.
const gate = () => {
  const target = new EventTarget()
  return {
    opened: new Promise<void>((resolve) => { target.addEventListener('open', () => { resolve() }, { once: true }) }),
    open: () => { target.dispatchEvent(new Event('open')) },
  }
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
    expect(ingredients.getAllByRole('listitem').map((item) => item.textContent)).toEqual([`250${nbsp}g Mehl`])
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
    const deleteGate = gate()
    const writes = plannedServer([potatoSoup, pancakes], deleteGate.opened)
    renderApp('/planned')

    // When: ich bei "Kartoffelsuppe" auf "Entfernen" klicke und im Toast auf "Rückgängig", noch bevor das Entfernen fertig ist
    fireEvent.click(await screen.findByRole('button', { name: 'Kartoffelsuppe entfernen' }))
    await waitFor(() => { expect(writes.deleted).toHaveBeenCalledExactlyOnceWith(potatoSoup.id) })
    fireEvent.click(screen.getByRole('button', { name: 'Rückgängig' }))

    // (ein Event-Loop-Durchlauf, damit ein vorschnell gesendetes PUT den Server vor dem Öffnen des Tors erreicht – kein Zeitfenster)
    await new Promise((resolve) => { setTimeout(resolve, 0) })

    // When: das Entfernen ist abgeschlossen
    deleteGate.open()

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

// @US-201-happy-path
describe('Vorgemerkt-Seite: Auf die Einkaufsliste', () => {
  // Szenario: Die Zutaten der vorgemerkten Rezepte alphabetisch auf die Einkaufsliste übernehmen
  it('US201_HappyPath_PlannedRecipesPage_Generate_PostsAndShowsShoppingList', async () => {
    // Given: Pfannkuchen und Kartoffelsuppe sind vorgemerkt, die Einkaufsliste ist leer; POST füllt sie
    const posted = vi.fn<(body: string) => void>()
    server.use(
      http.get('/api/planned-recipes', () => HttpResponse.json([potatoSoup, pancakes])),
      http.get('/api/shopping-list', () => HttpResponse.json(posted.mock.calls.length > 0 ? [
        { name: 'Eier', quantity: 3, unit: 'Stück' },
        { name: 'Kartoffeln', quantity: 1000, unit: 'g' },
        { name: 'Mehl', quantity: 250, unit: 'g' },
        { name: 'Milch', quantity: 0.5, unit: 'l' },
        { name: 'Salz', quantity: null, unit: null },
      ] : [])),
      http.post('/api/shopping-list/generate', async ({ request }) => {
        posted(await request.text())
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { router } = renderApp('/planned')

    // When: ich auf "Auf die Einkaufsliste" klicke
    await screen.findByRole('list', { name: 'Vorgemerkt' })
    const generateButton = screen.getByRole('button', { name: generateName })
    expect(generateButton).toHaveTextContent('Auf die Einkaufsliste')
    fireEvent.click(generateButton)

    // Then: sehe ich die Einkaufsliste mit genau diesen Einträgen in dieser Reihenfolge; der POST hatte keinen Body
    expect(await screen.findByRole('list', { name: 'Einkaufsliste' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/shopping-list')
    expect(screen.getByRole('heading', { level: 1, name: 'Einkaufsliste' })).toBeInTheDocument()
    expect(listedItems()).toEqual([['Eier', `3${nbsp}Stück`], ['Kartoffeln', `1000${nbsp}g`], ['Mehl', `250${nbsp}g`], ['Milch', `0,5${nbsp}l`], ['Salz']])
    // ADR-S154-2: der Client schickt keine Rezept-IDs
    expect(posted).toHaveBeenCalledWith('')
  })

  // Szenario: Die Einkaufsliste bleibt bis zum erneuten Übernehmen unverändert, das sie dann ersetzt
  it('US201_HappyPath_PlannedRecipesPage_GenerateAgain_ReplacesListWithoutShowingOldOne', async () => {
    // Given: die Einkaufsliste ist übernommen (Kartoffeln, Mehl, Milch, Salz) und auf dieser Seite geladen;
    //   "Kartoffelsuppe" ist nicht mehr, "Linsensalat" vorgemerkt. Der Abruf nach dem Übernehmen antwortet erst auf Zuruf.
    const lentilSalad = { id: '3f2b8c1e-0000-4000-8000-000000000504', title: 'Linsensalat' }
    const generatePosted = vi.fn()
    const afterGenerateGate = gate()
    server.use(
      http.get('/api/planned-recipes', () => HttpResponse.json([lentilSalad, pancakes])),
      http.get('/api/shopping-list', async () => {
        if (generatePosted.mock.calls.length === 0) {
          return HttpResponse.json([
            { name: 'Kartoffeln', quantity: 1000, unit: 'g' },
            { name: 'Mehl', quantity: 250, unit: 'g' },
            { name: 'Milch', quantity: 0.5, unit: 'l' },
            { name: 'Salz', quantity: null, unit: null },
          ])
        }
        await afterGenerateGate.opened
        return HttpResponse.json([
          { name: 'Linsen', quantity: 200, unit: 'g' },
          { name: 'Mehl', quantity: 250, unit: 'g' },
          { name: 'Milch', quantity: 0.5, unit: 'l' },
        ])
      }),
      http.post('/api/shopping-list/generate', () => {
        generatePosted()
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { router } = renderApp('/shopping-list')

    // Vorbedingung (erster Then-Schritt des Szenarios): bis zum erneuten Übernehmen steht die bisherige Liste da
    await screen.findByRole('list', { name: 'Einkaufsliste' })
    expect(listedItems()).toEqual([['Kartoffeln', `1000${nbsp}g`], ['Mehl', `250${nbsp}g`], ['Milch', `0,5${nbsp}l`], ['Salz']])

    // When: ich in der Navigationsleiste auf "Vorgemerkt" und auf "Auf die Einkaufsliste" klicke
    fireEvent.click(within(screen.getByRole('navigation', { name: 'Hauptnavigation' })).getByRole('link', { name: 'Vorgemerkt' }))
    await screen.findByRole('list', { name: 'Vorgemerkt' })
    fireEvent.click(screen.getByRole('button', { name: generateName }))

    // Then: die Einkaufsliste öffnet sich, ohne die alte Liste zu zeigen; mit der Antwort steht dort genau die neue.
    //   „ohne die alte Liste“: Regel im Kopf von features/shopping-lists.feature, Abschnitt „Regeln“ – „Nach dem
    //   Übernehmen zeigt die Einkaufsliste nie, auch nicht kurz, die bisherige Liste.“
    await waitFor(() => { expect(router.state.location.pathname).toBe('/shopping-list') })
    expect(screen.queryByRole('list', { name: 'Einkaufsliste' })).not.toBeInTheDocument()
    afterGenerateGate.open()
    expect(await screen.findByText('Linsen')).toBeInTheDocument()
    expect(listedItems()).toEqual([['Linsen', `200${nbsp}g`], ['Mehl', `250${nbsp}g`], ['Milch', `0,5${nbsp}l`]])
  })

  // ADR-S106-3
  // Vertrag aus dem Kopf von features/shopping-lists.feature, Abschnitt „Regeln“: „Übernehmen lässt die anderen Seiten
  // unberührt: Zurück auf der Vorgemerkt-Seite stehen die Vormerkungen sofort da, ohne Ladezustand.“ Kein Szenario
  // treibt den Test.
  it('Generate_ThenBackToPlannedPage_ShowsPlannedRecipesWithoutLoading', async () => {
    // Given: Pfannkuchen ist vorgemerkt und auf der Vorgemerkt-Seite geladen; der POST gelingt. Ein erneuter Abruf der
    //   Vormerkungen nach dem POST antwortet erst auf Zuruf: Er darf die Anzeige nicht erst herstellen müssen.
    const generatePosted = vi.fn()
    const plannedRefetchGate = gate()
    server.use(
      http.get('/api/planned-recipes', async () => {
        await (generatePosted.mock.calls.length > 0 ? plannedRefetchGate.opened : Promise.resolve())
        return HttpResponse.json([pancakes])
      }),
      http.get('/api/shopping-list', () => HttpResponse.json([{ name: 'Mehl', quantity: 250, unit: 'g' }])),
      http.post('/api/shopping-list/generate', () => {
        generatePosted()
        return new HttpResponse(null, { status: 204 })
      }),
    )
    renderApp('/planned')
    await screen.findByRole('list', { name: 'Vorgemerkt' })
    fireEvent.click(screen.getByRole('button', { name: generateName }))
    await screen.findByRole('list', { name: 'Einkaufsliste' })

    // When: ich in der Navigationsleiste auf "Vorgemerkt" klicke
    fireEvent.click(within(screen.getByRole('navigation', { name: 'Hauptnavigation' })).getByRole('link', { name: 'Vorgemerkt' }))

    // Then: die Vormerkungen stehen sofort da (ohne zu warten), ohne Ladezustand
    expect(within(screen.getByRole('list', { name: 'Vorgemerkt' })).getAllByRole('listitem')).toHaveLength(1)
    expect(screen.getByRole('link', { name: 'Pfannkuchen' })).toBeInTheDocument()
    plannedRefetchGate.open()
  })

  // ADR-S106-3
  // Vertrag aus dem Kopf von features/shopping-lists.feature, Abschnitt „Bekannte Grenzen (SKELETON, vom User so
  // entschieden)“: Schlägt Übernehmen fehl, bleibt man ohne Meldung auf der Vorgemerkt-Seite. Kein Szenario treibt den
  // Test. Die Regel fällt mit einer Fehlermeldung (Fehler-Toast nach ADR-S056-1, noch nicht gebaut); dann wird dieser
  // Test rot.
  it('Generate_PostFails_StaysOnPlannedPageWithoutMessage', async () => {
    // Given: Pfannkuchen ist vorgemerkt, der POST schlägt mit 500 fehl
    const posted = vi.fn()
    server.use(
      http.get('/api/planned-recipes', () => HttpResponse.json([pancakes])),
      http.post('/api/shopping-list/generate', () => {
        posted()
        return new HttpResponse(null, { status: 500 })
      }),
    )
    const { router, queryClient } = renderApp('/planned')

    // When: ich auf "Auf die Einkaufsliste" klicke
    await screen.findByRole('list', { name: 'Vorgemerkt' })
    fireEvent.click(screen.getByRole('button', { name: generateName }))

    // Then: der POST ist abgeschlossen; die Seite bleibt, ohne Meldung
    await waitFor(() => { expect(posted).toHaveBeenCalled() })
    // Bis run-3 gibt es kein sichtbares Signal für „abgeschlossen“. Ohne dieses Warten liefe die Pfadprüfung vor einer
    // möglichen Navigation und prüfte nichts.
    await waitFor(() => { expect(queryClient.isMutating()).toBe(0) })
    expect(router.state.location.pathname).toBe('/planned')
    expect(screen.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

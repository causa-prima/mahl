import { describe, it, expect, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { delay, http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { appRoutes } from '../App'
import type { RecipeId } from '../domain/recipe'

function renderApp(initialPath: string) {
  const router = createMemoryRouter(appRoutes, { initialEntries: [initialPath] })
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}

type Summary = { readonly id: RecipeId; readonly title: string }

const pancakes: Summary = { id: '3f2b8c1e-0000-4000-8000-000000000401' as RecipeId, title: 'Pfannkuchen' }
const potatoSoup: Summary = { id: '3f2b8c1e-0000-4000-8000-000000000402' as RecipeId, title: 'Kartoffelsuppe' }

// Given (Szenario): die Rezepte existieren; der Server hält die Vormerkungen, anfangs `planned` (sonst keine). Gibt den
// Spion auf die schreibenden Requests zurück (ruft mit "PUT" bzw. "DELETE" auf). `planElsewhere` merkt vor, ohne dass
// der Client es erfährt (anderes Gerät). `writeGate` hält die Antwort auf Vormerken und Aufheben offen, bis der Test es freigibt.
function givenServer(options: Readonly<{ writeGate?: Promise<void>; recipes?: readonly Summary[]; planned?: readonly Summary[] }> = {}) {
  const recipes = options.recipes ?? [potatoSoup, pancakes]
  const state: { planned: Summary[] } = { planned: [...(options.planned ?? [])] }
  const writes = vi.fn()
  server.use(
    http.get('/api/recipes', () => HttpResponse.json(recipes)),
    http.get('/api/recipes/:id', ({ params }) => {
      const recipe = recipes.find((r) => r.id === params.id)
      return HttpResponse.json({ ...recipe, ingredients: [{ name: 'Mehl', quantity: 250, unit: 'g' }], steps: [{ instruction: 'Rühren.' }] })
    }),
    http.get('/api/planned-recipes', () => HttpResponse.json(state.planned)),
    http.put('/api/planned-recipes/:id', async ({ params }) => {
      writes('PUT')
      await options.writeGate
      const recipe = recipes.find((r) => r.id === params.id)
      // eslint-disable-next-line functional/immutable-data, functional/no-conditional-statements -- Server-Zustand des Tests
      if (recipe && !state.planned.some((p) => p.id === recipe.id)) state.planned.push(recipe)
      return new HttpResponse(null, { status: 204 })
    }),
    http.delete('/api/planned-recipes/:id', async ({ params }) => {
      writes('DELETE')
      await options.writeGate
      // eslint-disable-next-line functional/immutable-data -- Server-Zustand des Tests
      state.planned = state.planned.filter((p) => p.id !== params.id)
      return new HttpResponse(null, { status: 204 })
    }),
  )
  return {
    writes,
    planElsewhere: (recipe: Summary) => {
      // eslint-disable-next-line functional/immutable-data -- anderes Gerät ändert den Server-Zustand
      state.planned.push(recipe)
    },
  }
}

function expectNoToast() {
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
}

// Then (Szenario): die Rezept-Liste zeigt bei "Pfannkuchen" "Vorgemerkt" und bei "Kartoffelsuppe" "Vormerken".
async function expectListShowsPancakesPlanned() {
  expect(await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })).toHaveTextContent('Vorgemerkt')
  expect(screen.getByRole('button', { name: 'Kartoffelsuppe vormerken' })).toHaveTextContent('Vormerken')
  expect(screen.queryByRole('button', { name: 'Pfannkuchen vormerken' })).not.toBeInTheDocument()
}

// Then (Szenario): die Vorgemerkt-Seite zeigt genau das Rezept <title>.
async function expectPlannedPageShowsOnly(title: string) {
  const list = await screen.findByRole('list', { name: 'Vorgemerkt' })
  expect(within(list).getAllByRole('listitem').map((item) => item.textContent)).toEqual([title])
  expect(screen.queryByText('Noch keine Rezepte vorgemerkt.')).not.toBeInTheDocument()
}

// Then (Szenario): die Rezept-Liste zeigt bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt".
async function expectListShowsPancakesUnplanned() {
  expect(await screen.findByRole('button', { name: 'Pfannkuchen vormerken' })).toHaveTextContent('Vormerken')
  expect(screen.getByRole('button', { name: 'Kartoffelsuppe vorgemerkt' })).toHaveTextContent('Vorgemerkt')
  expect(screen.queryByRole('button', { name: 'Pfannkuchen vorgemerkt' })).not.toBeInTheDocument()
}

const cases = [
  {
    ort: 'die Rezept-Liste',
    path: '/recipes',
    loadedProbe: { role: 'link', name: 'Pfannkuchen' },
    expectPlanned: expectListShowsPancakesPlanned,
    expectUnplanned: expectListShowsPancakesUnplanned,
  },
  {
    ort: 'die Detailansicht des Rezepts "Pfannkuchen"',
    path: `/recipes/${String(pancakes.id)}`,
    loadedProbe: { role: 'heading', name: 'Pfannkuchen' },
    expectPlanned: async () => { expect(await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })).toHaveTextContent('Vorgemerkt') },
    expectUnplanned: async () => { expect(await screen.findByRole('button', { name: 'Pfannkuchen vormerken' })).toHaveTextContent('Vormerken') },
  },
] as const

// @US-803-happy-path
describe('Rezepte vormerken', () => {
  // Szenario: Ein Rezept vormerken
  // Beispiel: alle
  it.each(cases)('US803_HappyPath_PlanRecipe_ClickToggle_ShowsPlannedEverywhere ($ort)', async ({ path, expectPlanned }) => {
    // Given: die Rezepte existieren, kein Rezept ist vorgemerkt
    givenServer()
    const router = renderApp(path)

    // When: ich bei "Pfannkuchen" auf "Vormerken" klicke
    const toggle = await screen.findByRole('button', { name: 'Pfannkuchen vormerken' })
    expect(toggle).toHaveTextContent('Vormerken')
    fireEvent.click(toggle)

    // Then: der Umschalter zeigt den Zustand, ich bleibe am Ort, kein Toast
    await expectPlanned()
    expect(router.state.location.pathname).toBe(path)
    expectNoToast()

    // When/Then: Vorgemerkt-Seite zeigt genau "Pfannkuchen"
    fireEvent.click(screen.getByRole('link', { name: 'Vorgemerkt' }))
    await expectPlannedPageShowsOnly('Pfannkuchen')

    // When/Then: zurück zur Rezept-Liste
    fireEvent.click(screen.getByRole('link', { name: 'Rezepte' }))
    await expectListShowsPancakesPlanned()

    // When/Then: Seite neu laden
    cleanup()
    renderApp('/recipes')
    await expectListShowsPancakesPlanned()
  })

  // Szenario: Ein inzwischen anderswo vorgemerktes Rezept vormerken
  it('US803_EdgeCase_PlanRecipe_AlreadyPlannedElsewhere_ShowsPlannedOnce', async () => {
    // Given: das Rezept "Pfannkuchen" existiert, die Liste ist geöffnet, danach wird es auf einem anderen Gerät vorgemerkt
    const { planElsewhere } = givenServer({ recipes: [pancakes] })
    renderApp('/recipes')
    const toggle = await screen.findByRole('button', { name: 'Pfannkuchen vormerken' })
    planElsewhere(pancakes)

    // When: ich bei "Pfannkuchen" auf "Vormerken" klicke
    fireEvent.click(toggle)

    // Then: die Liste zeigt "Vorgemerkt"; die Vorgemerkt-Seite nach Neuladen genau das Rezept einmal
    expect(await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })).toHaveTextContent('Vorgemerkt')
    cleanup()
    renderApp('/planned')
    await expectPlannedPageShowsOnly('Pfannkuchen')
  })

  // Szenario: Eine Vormerkung per Umschalter aufheben
  // Beispiel: alle
  it.each(cases)('US803_HappyPath_UnplanRecipe_ClickToggle_ShowsUnplannedEverywhere ($ort)', async ({ path, expectUnplanned }) => {
    // Given: die Rezepte "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt
    givenServer({ planned: [potatoSoup, pancakes] })
    const router = renderApp(path)

    // When: ich bei "Pfannkuchen" auf "Vorgemerkt" klicke
    const toggle = await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })
    expect(toggle).toHaveTextContent('Vorgemerkt')
    fireEvent.click(toggle)

    // Then: der Umschalter zeigt den Zustand, ich bleibe am Ort, kein Toast
    await expectUnplanned()
    expect(router.state.location.pathname).toBe(path)
    expectNoToast()

    // When/Then: Vorgemerkt-Seite zeigt genau "Kartoffelsuppe"
    fireEvent.click(screen.getByRole('link', { name: 'Vorgemerkt' }))
    await expectPlannedPageShowsOnly('Kartoffelsuppe')

    // When/Then: zurück zur Rezept-Liste
    fireEvent.click(screen.getByRole('link', { name: 'Rezepte' }))
    await expectListShowsPancakesUnplanned()

    // When/Then: Seite neu laden
    cleanup()
    renderApp('/recipes')
    await expectListShowsPancakesUnplanned()
  })

  // ADR-S106-3
  // Vertrag aus dem Kopf von features/planned-recipes.feature: der Umschalter zeigt den neuen Zustand erst mit der
  // Antwort des Servers, nicht vorab. Kein Szenario treibt den Test.
  it.each([
    { richtung: 'Vormerken', method: 'PUT', planned: [], before: { name: 'Pfannkuchen vormerken', text: 'Vormerken' }, after: { name: 'Pfannkuchen vorgemerkt', text: 'Vorgemerkt' } },
    { richtung: 'Aufheben', method: 'DELETE', planned: [pancakes], before: { name: 'Pfannkuchen vorgemerkt', text: 'Vorgemerkt' }, after: { name: 'Pfannkuchen vormerken', text: 'Vormerken' } },
  ] as const)('PlanningToggle_ResponsePending_ShowsOldStateUntilServerAnswers ($richtung)', async ({ method, planned, before, after }) => {
    // Given: der Server hält die Antwort auf das Vormerken bzw. Aufheben offen, bis der Test sie freigibt
    const gate: { release: () => void } = { release: () => undefined }
    // eslint-disable-next-line functional/immutable-data -- Deferred: der Test gibt die Antwort frei
    const writeGate = new Promise<void>((resolve) => { gate.release = resolve })
    const { writes } = givenServer({ writeGate, planned })
    renderApp('/recipes')

    // When: ich bei "Pfannkuchen" auf den Umschalter klicke
    fireEvent.click(await screen.findByRole('button', { name: before.name }))
    await waitFor(() => { expect(writes).toHaveBeenCalledExactlyOnceWith(method) })

    // Then: bis zur Antwort steht dort weiter der alte Zustand (kein optimistisches Update), danach der neue
    expect(screen.getByRole('button', { name: before.name })).toHaveTextContent(before.text)
    gate.release()
    expect(await screen.findByRole('button', { name: after.name })).toHaveTextContent(after.text)
  })

  // ADR-S106-3
  // Querschnittsvertrag aus dem Kopf von features/planned-recipes.feature: solange die Vormerkungen laden,
  // zeigen Rezept-Liste und Detailansicht keinen Umschalter. Kein Szenario treibt den Test.
  it.each(cases)('PlanningToggle_PlannedRecipesPending_ShowsNoToggle ($ort)', async ({ path, loadedProbe }) => {
    // Given: die Vormerkungen laden noch, die Rezepte sind da
    const requested = vi.fn()
    givenServer()
    server.use(http.get('/api/planned-recipes', async () => {
      requested()
      await delay('infinite')
    }))

    // When: ich den Ort öffne
    renderApp(path)

    // Then: nachdem Rezepte und Abruf da sind, gibt es keinen Umschalter
    await screen.findByRole(loadedProbe.role, { name: loadedProbe.name })
    await waitFor(() => { expect(requested).toHaveBeenCalled() })
    expect(screen.queryByRole('button', { name: /vormerken|vorgemerkt/ })).not.toBeInTheDocument()
  })
})

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

// Given (Szenario): die Rezepte existieren; der Server hält die Vormerkungen. Gibt den Spion auf die PUT-Requests
// zurück. `planElsewhere` merkt vor, ohne dass der Client es erfährt (anderes Gerät). `putGate` hält die Antwort auf
// das Vormerken offen, bis der Test es freigibt.
function givenServer(options: Readonly<{ putGate?: Promise<void>; recipes?: readonly Summary[] }> = {}) {
  const recipes = options.recipes ?? [potatoSoup, pancakes]
  const state: { planned: Summary[] } = { planned: [] }
  const puts = vi.fn()
  server.use(
    http.get('/api/recipes', () => HttpResponse.json(recipes)),
    http.get('/api/recipes/:id', ({ params }) => {
      const recipe = recipes.find((r) => r.id === params.id)
      return HttpResponse.json({ ...recipe, ingredients: [{ name: 'Mehl', quantity: 250, unit: 'g' }], steps: [{ instruction: 'Rühren.' }] })
    }),
    http.get('/api/planned-recipes', () => HttpResponse.json(state.planned)),
    http.put('/api/planned-recipes/:id', async ({ params }) => {
      puts(params.id)
      await options.putGate
      const recipe = recipes.find((r) => r.id === params.id)
      // eslint-disable-next-line functional/immutable-data, functional/no-conditional-statements -- Server-Zustand des Tests
      if (recipe && !state.planned.some((p) => p.id === recipe.id)) state.planned.push(recipe)
      return new HttpResponse(null, { status: 204 })
    }),
  )
  return {
    puts,
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

// Then (Szenario): die Vorgemerkt-Seite zeigt genau das Rezept "Pfannkuchen".
async function expectPlannedPageShowsOnlyPancakes() {
  const list = await screen.findByRole('list', { name: 'Vorgemerkt' })
  expect(within(list).getAllByRole('listitem').map((item) => item.textContent)).toEqual(['Pfannkuchen'])
  expect(screen.queryByText('Noch keine Rezepte vorgemerkt.')).not.toBeInTheDocument()
}

const cases = [
  {
    ort: 'die Rezept-Liste',
    path: '/recipes',
    loadedProbe: { role: 'link', name: 'Pfannkuchen' },
    expectAnzeige: expectListShowsPancakesPlanned,
  },
  {
    ort: 'die Detailansicht des Rezepts "Pfannkuchen"',
    path: `/recipes/${String(pancakes.id)}`,
    loadedProbe: { role: 'heading', name: 'Pfannkuchen' },
    expectAnzeige: async () => { expect(await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })).toHaveTextContent('Vorgemerkt') },
  },
] as const

// @US-803-happy-path
describe('Rezepte vormerken', () => {
  // Szenario: Ein Rezept vormerken
  // Beispiel: alle
  it.each(cases)('US803_HappyPath_PlanRecipe_ClickToggle_ShowsPlannedEverywhere ($ort)', async ({ path, expectAnzeige }) => {
    // Given: die Rezepte existieren, kein Rezept ist vorgemerkt
    const { puts } = givenServer()
    const router = renderApp(path)

    // When: ich bei "Pfannkuchen" auf "Vormerken" klicke
    const toggle = await screen.findByRole('button', { name: 'Pfannkuchen vormerken' })
    expect(toggle).toHaveTextContent('Vormerken')
    fireEvent.click(toggle)

    // Then: der Umschalter zeigt den Zustand, ich bleibe am Ort, kein Toast, genau ein Request für dieses Rezept
    await expectAnzeige()
    expect(router.state.location.pathname).toBe(path)
    expectNoToast()
    expect(puts).toHaveBeenCalledExactlyOnceWith(pancakes.id)

    // When/Then: Vorgemerkt-Seite zeigt genau "Pfannkuchen"
    fireEvent.click(screen.getByRole('link', { name: 'Vorgemerkt' }))
    await expectPlannedPageShowsOnlyPancakes()

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
    await expectPlannedPageShowsOnlyPancakes()
  })

  // ADR-S106-3
  // Vertrag aus dem Kopf von features/planned-recipes.feature: der Umschalter zeigt den neuen Zustand erst mit der
  // Antwort des Servers, nicht vorab. Kein Szenario treibt den Test.
  it('PlanningToggle_ResponsePending_ShowsOldStateUntilServerAnswers', async () => {
    // Given: der Server hält die Antwort auf das Vormerken offen, bis der Test sie freigibt
    const gate: { release: () => void } = { release: () => undefined }
    // eslint-disable-next-line functional/immutable-data -- Deferred: der Test gibt die Antwort frei
    const putGate = new Promise<void>((resolve) => { gate.release = resolve })
    const { puts } = givenServer({ putGate })
    renderApp('/recipes')

    // When: ich bei "Pfannkuchen" auf "Vormerken" klicke
    fireEvent.click(await screen.findByRole('button', { name: 'Pfannkuchen vormerken' }))
    await waitFor(() => { expect(puts).toHaveBeenCalledOnce() })

    // Then: bis zur Antwort steht dort weiter "Vormerken" (kein optimistisches Update), danach "Vorgemerkt"
    expect(screen.getByRole('button', { name: 'Pfannkuchen vormerken' })).toHaveTextContent('Vormerken')
    gate.release()
    expect(await screen.findByRole('button', { name: 'Pfannkuchen vorgemerkt' })).toHaveTextContent('Vorgemerkt')
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

import { describe, it, expect } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { http, HttpResponse } from 'msw'
import { server } from './mocks/server'
import { appRoutes } from './App'

type PageName = 'Zutaten' | 'Rezepte'

// Given (Background): die Anwendung ist gestartet, beide Listen sind leer.
function renderAppAt(initialPath: string) {
  server.use(
    http.get('/api/ingredients', () => HttpResponse.json([])),
    http.get('/api/recipes', () => HttpResponse.json([])),
  )
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={createMemoryRouter(appRoutes, { initialEntries: [initialPath] })} />
    </QueryClientProvider>,
  )
}

const navEntry = (name: PageName) =>
  within(screen.getByRole('navigation', { name: 'Hauptnavigation' })).getByRole('link', { name })

// Then „sehe ich die <Ziel>-Seite": Seitentitel und markierter Eintrag der Leiste, der andere Eintrag (`other`)
// nicht markiert (die Adresse prüft der E2E-Test).
async function expectPageShown(name: PageName, other: PageName) {
  expect(await screen.findByRole('heading', { level: 1, name })).toBeInTheDocument()
  expect(navEntry(name)).toHaveAttribute('aria-current', 'page')
  expect(navEntry(other)).not.toHaveAttribute('aria-current')
}

describe('CROSS_Navigation: Navigationsleiste', () => {
  // Szenario: Von der Zutaten-Seite zur Rezepte-Seite navigieren
  it('CROSS_Navigation_IngredientsToRecipes_ClickNavigationEntry_ShowsRecipesPage', async () => {
    // Given: ich navigiere zur Zutaten-Seite
    renderAppAt('/ingredients')
    await screen.findByRole('heading', { level: 1, name: 'Zutaten' })

    // When: ich in der Navigationsleiste auf "Rezepte" klicke
    fireEvent.click(navEntry('Rezepte'))

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown('Rezepte', 'Zutaten')
  })

  // Szenario: Von der Rezepte-Seite zur Zutaten-Seite navigieren
  it('CROSS_Navigation_RecipesToIngredients_ClickNavigationEntry_ShowsIngredientsPage', async () => {
    // Given: ich navigiere zur Rezepte-Seite
    renderAppAt('/recipes')
    await screen.findByRole('heading', { level: 1, name: 'Rezepte' })

    // When: ich in der Navigationsleiste auf "Zutaten" klicke
    fireEvent.click(navEntry('Zutaten'))

    // Then: sehe ich die Zutaten-Seite
    await expectPageShown('Zutaten', 'Rezepte')
  })

  // Szenario: Von der Zutaten-Seite zur Rezepte-Seite navigieren
  // Survivor-Test: sichert die sichtbare Markierung des aktiven Eintrags (fett und unterstrichen, freigegebener
  // UI-Entwurf und Visuelle Baseline „Navigationsleiste") – die Szenario-Tests prüfen nur aria-current.
  it('CROSS_Navigation_IngredientsToRecipes_OpenIngredientsPage_MarksActiveEntryBoldAndUnderlined', async () => {
    // Given: die Anwendung ist gestartet (renderAppAt)
    // When: ich navigiere zur Zutaten-Seite – die Ausgangslage des Szenarios
    renderAppAt('/ingredients')
    await screen.findByRole('heading', { level: 1, name: 'Zutaten' })

    // Then: der Eintrag der geöffneten Seite ist sichtbar markiert, der andere nicht
    expect(navEntry('Zutaten')).toHaveStyle({ fontWeight: 700, textDecoration: 'underline' })
    expect(navEntry('Rezepte')).not.toHaveStyle({ fontWeight: 700 })
    expect(navEntry('Rezepte')).not.toHaveStyle({ textDecoration: 'underline' })
  })
})

describe('CROSS_Navigation: Einstieg', () => {
  // Szenario: Ohne Adresse öffnet die Anwendung die Rezepte-Seite
  it('CROSS_Navigation_StartPage_OpenWithoutPath_ShowsRecipesPage', async () => {
    // Given: die Anwendung ist gestartet (renderAppAt)
    // When: ich die Anwendung ohne Pfad öffne
    renderAppAt('/')

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown('Rezepte', 'Zutaten')
  })

  // Szenario: Eine unbekannte Adresse zeigt „Seite nicht gefunden.“ mit Navigationsleiste
  it('CROSS_Navigation_UnknownAddress_OpenUnknownPath_ShowsNotFoundWithNavigationBar', async () => {
    // Given: die Anwendung ist gestartet (renderAppAt)
    // When: ich die Adresse "/zutatn" öffne
    renderAppAt('/zutatn')

    // Then: sehe ich die Meldung "Seite nicht gefunden."
    expect(await screen.findByRole('heading', { level: 1, name: 'Seite nicht gefunden.' })).toBeInTheDocument()

    // When: ich in der Navigationsleiste auf "Rezepte" klicke
    fireEvent.click(navEntry('Rezepte'))

    // Then: sehe ich die Rezepte-Seite
    await expectPageShown('Rezepte', 'Zutaten')
  })
})

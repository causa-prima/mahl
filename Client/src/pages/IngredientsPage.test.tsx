import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import IngredientsPage from './IngredientsPage'

function renderWithProviders(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('IngredientsPage', () => {
  it('US904_HappyPath_IngredientsPage_EmptyDb_ShowsEmptyList', async () => {
    server.use(
      http.get('/api/ingredients', () => HttpResponse.json([]))
    )

    renderWithProviders(<IngredientsPage />)

    await screen.findByText('Noch keine Zutaten angelegt.')
    await screen.findByRole('button', { name: 'Zutat anlegen' })
  })
})

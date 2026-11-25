import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { appRoutes } from '../App'

// Die ganze Anwendung ab dem Pfad. Gibt den Router (Adresse, Browser-Zurück; ADR-S151-1) und den QueryClient
// (z.B. `isFetching()`) zurück, die nur darüber erreichbar sind.
export function renderApp(initialPath: string) {
  const router = createMemoryRouter(appRoutes, { initialEntries: [initialPath] })
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { router, queryClient }
}

import { Navigate } from 'react-router'
import type { RouteObject } from 'react-router'
import NotFoundPage from './pages/NotFoundPage'
import IngredientsPage from './pages/IngredientsPage'
import RecipesPage from './pages/RecipesPage'
import CreateRecipePage from './pages/CreateRecipePage'
import RecipeDetailPage from './pages/RecipeDetailPage'
import AppLayout from './components/AppLayout'

// ADR-S151-1: die Routentabelle für den Data-Router; main.tsx baut daraus den Browser-Router, Tests den Memory-Router.
export const appRoutes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      // Übergangsregel: bis zur Startseite (US-001) öffnet die Anwendung die Rezept-Liste.
      { index: true, element: <Navigate to="/recipes" replace /> },
      { path: '/ingredients', element: <IngredientsPage /> },
      { path: '/recipes', element: <RecipesPage /> },
      { path: '/recipes/new', element: <CreateRecipePage /> },
      { path: '/recipes/:id', element: <RecipeDetailPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]

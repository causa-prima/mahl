import { BrowserRouter, Routes, Route, Navigate } from 'react-router'
import NotFoundPage from './pages/NotFoundPage'
import IngredientsPage from './pages/IngredientsPage'
import RecipesPage from './pages/RecipesPage'
import CreateRecipePage from './pages/CreateRecipePage'
import RecipeDetailPage from './pages/RecipeDetailPage'
import AppLayout from './components/AppLayout'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* Übergangsregel: bis zur Startseite (US-001) öffnet die Anwendung die Rezept-Liste. */}
        <Route index element={<Navigate to="/recipes" replace />} />
        <Route path="/ingredients" element={<IngredientsPage />} />
        <Route path="/recipes" element={<RecipesPage />} />
        <Route path="/recipes/new" element={<CreateRecipePage />} />
        <Route path="/recipes/:id" element={<RecipeDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

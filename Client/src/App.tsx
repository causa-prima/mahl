import { BrowserRouter, Routes, Route } from 'react-router'
import IngredientsPage from './pages/IngredientsPage'
import RecipesPage from './pages/RecipesPage'
import CreateRecipePage from './pages/CreateRecipePage'
import RecipeDetailPage from './pages/RecipeDetailPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/ingredients" element={<IngredientsPage />} />
      <Route path="/recipes" element={<RecipesPage />} />
      <Route path="/recipes/new" element={<CreateRecipePage />} />
      <Route path="/recipes/:id" element={<RecipeDetailPage />} />
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

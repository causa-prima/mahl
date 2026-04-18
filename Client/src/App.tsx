import { BrowserRouter, Routes, Route } from 'react-router'
import IngredientsPage from './pages/IngredientsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/ingredients" element={<IngredientsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

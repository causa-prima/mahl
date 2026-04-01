import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme';
import Layout from './components/Layout';
import IngredientsPage from './pages/IngredientsPage';
import RecipesPage from './pages/RecipesPage';
import WeeklyPoolPage from './pages/WeeklyPoolPage';
import ShoppingListPage from './pages/ShoppingListPage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/ingredients" replace />} />
              <Route path="ingredients" element={<IngredientsPage />} />
              <Route path="recipes" element={<RecipesPage />} />
              <Route path="weekly-pool" element={<WeeklyPoolPage />} />
              <Route path="shopping-list" element={<ShoppingListPage />} />
            </Route>
          </Routes>
        </ThemeProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
}

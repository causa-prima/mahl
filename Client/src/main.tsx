import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { appRoutes } from './App.tsx'
import { MIN_TOUCH_TARGET } from './touchTarget.ts'

const queryClient = new QueryClient()
// ADR-S151-1: Data-Router (useBlocker für die Nachfrage beim Verlassen des Rezeptformulars).
const router = createBrowserRouter(appRoutes)

// Touch-Targets ≥ 44×44px (touchTarget.ts) als Komponenten-Default statt je Element, damit ein neuer Button
// nicht durchfällt (MUI-Defaults: Button 36,5px, IconButton 40px).
const theme = createTheme({
  components: {
    // Seitenrumpf: MUIs Container polstert nur seitlich – ohne das klebt die Überschrift am oberen Rand.
    MuiContainer: { styleOverrides: { root: ({ theme }) => ({ paddingBlock: theme.spacing(2) }) } },
    // Meldungsliste unter einem Feld (<ul>): kleiner Einzug statt Browser-Default 40px, sonst kosten die Umbrüche am Handy Platz.
    // Listensemantik bleibt (kein list-style: none).
    MuiFormHelperText: { styleOverrides: { root: { '&:is(ul)': { paddingInlineStart: '1.25em' } } } },
    MuiButton: { styleOverrides: { root: { minHeight: MIN_TOUCH_TARGET } } },
    MuiIconButton: { styleOverrides: { root: { minWidth: MIN_TOUCH_TARGET, minHeight: MIN_TOUCH_TARGET } } },
  },
})

// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>
)

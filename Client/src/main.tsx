import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import App from './App.tsx'

const queryClient = new QueryClient()

// docs/process/nfr.md (Accessibility): Touch-Targets ≥ 44×44px. Als Komponenten-Default statt je
// Element, damit ein neuer Button nicht durchfällt (MUI-Defaults: Button 36,5px, IconButton 40px).
const MIN_TOUCH_TARGET = 44
const theme = createTheme({
  components: {
    // Seitenrumpf: MUIs Container polstert nur seitlich – ohne das klebt die Überschrift am oberen Rand.
    MuiContainer: { styleOverrides: { root: ({ theme }) => ({ paddingBlock: theme.spacing(2) }) } },
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
        <App />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>
)

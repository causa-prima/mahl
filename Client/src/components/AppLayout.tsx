import { AppBar, Box, Button, Toolbar } from '@mui/material'
import { NavLink, Outlet } from 'react-router'

// ADR-S103-1, ADR-S112-5: eine geteilte Layout-Komponente um alle Routen statt einer Leiste je Seite.
// NavLink setzt aria-current="page" am aktiven Eintrag (Default end=false: /recipes/new und /recipes/:id
// markieren „Rezepte"); die sichtbare Markierung hängt am selben Attribut.
const entries = [
  { label: 'Zutaten', to: '/ingredients' },
  { label: 'Rezepte', to: '/recipes' },
  { label: 'Vorgemerkt', to: '/planned' },
  { label: 'Einkaufsliste', to: '/shopping-list' },
] as const

export default function AppLayout() {
  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Box component="nav" aria-label="Hauptnavigation">
            {entries.map(({ label, to }) => (
              <Button
                key={to}
                component={NavLink}
                to={to}
                color="inherit"
                sx={{ '&[aria-current="page"]': { fontWeight: 'bold', textDecoration: 'underline' } }}
              >
                {label}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </AppBar>
      <Outlet />
    </>
  )
}

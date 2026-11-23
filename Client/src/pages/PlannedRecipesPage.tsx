import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { Link as RouterLink } from 'react-router'
import { useResultQuery } from '../hooks/useResultQuery'
import { fetchPlannedRecipes } from '../services/plannedRecipesApi'

export default function PlannedRecipesPage() {
  // Solange die Antwort fehlt (Laden oder Fehler), steht unter der Überschrift nichts: kein Leerzustand, kein Spinner.
  // Jede Antwort zeigt den Leerzustand: Noch liefert der Server keine Einträge, ihre Darstellung ist nicht gebaut.
  const planned = useResultQuery(['planned-recipes'], fetchPlannedRecipes)

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" gutterBottom>Vorgemerkt</Typography>
      {planned !== undefined && (
        <Stack spacing={2}>
          <Typography>Noch keine Rezepte vorgemerkt.</Typography>
          <Box>
            <Button component={RouterLink} to="/recipes" variant="contained">Zur Rezept-Liste</Button>
          </Box>
        </Stack>
      )}
    </Container>
  )
}

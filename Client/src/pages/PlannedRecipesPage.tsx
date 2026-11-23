import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { Link as RouterLink } from 'react-router'
import { usePlannedRecipes } from '../hooks/usePlannedRecipes'

export default function PlannedRecipesPage() {
  // Solange die Antwort fehlt (Laden oder Fehler), steht unter der Überschrift nichts: kein Leerzustand, kein Spinner.
  const planned = usePlannedRecipes()

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" id="planned-heading" gutterBottom>Vorgemerkt</Typography>
      {planned === undefined ? null : planned.length === 0 ? (
        <Stack spacing={2}>
          <Typography>Noch keine Rezepte vorgemerkt.</Typography>
          <Box>
            <Button component={RouterLink} to="/recipes" variant="contained">Zur Rezept-Liste</Button>
          </Box>
        </Stack>
      ) : (
        <List aria-labelledby="planned-heading" disablePadding>
          {planned.map((recipe) => (
            <ListItem key={recipe.id} disableGutters disablePadding>
              <ListItemButton component={RouterLink} to={`/recipes/${recipe.id}`} disableGutters>
                <ListItemText primary={recipe.title} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      )}
    </Container>
  )
}

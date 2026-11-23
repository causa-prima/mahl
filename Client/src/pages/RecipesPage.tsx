import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { Link as RouterLink, useNavigate } from 'react-router'
import PlanningToggle from '../components/PlanningToggle'
import { useResultQuery } from '../hooks/useResultQuery'
import { fetchRecipes } from '../services/recipesApi'

const recipesKey = ['recipes'] as const

export default function RecipesPage() {
  const navigate = useNavigate()
  // Solange keine Antwort da ist (Laden oder Fehler), steht weder Leerzustand noch Liste (Querschnittsvertrag im Kopf von features/recipes.feature).
  const recipes = useResultQuery(recipesKey, fetchRecipes)

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" id="recipes-heading" gutterBottom>Rezepte</Typography>
      <Stack spacing={2}>
        {/* Über der Liste, damit man für "Rezept anlegen" nicht durch die ganze Liste scrollt. */}
        <Box>
          <Button variant="contained" onClick={() => { void navigate('/recipes/new') }}>Rezept anlegen</Button>
        </Box>
        {recipes === undefined ? null : recipes.length === 0 ? (
          <Typography>Noch keine Rezepte angelegt.</Typography>
        ) : (
          <List aria-labelledby="recipes-heading" disablePadding>
            {recipes.map((recipe) => (
              // Umschalter neben dem Link statt als secondaryAction: UX-Guideline, Visuelle Baseline
              // „Listeneinträge mit eigener Aktion" (CGU-visuelle-baseline).
              // Stryker disable next-line ObjectLiteral,StringLiteral: Layout-Wert, in jsdom nicht beobachtbar (ADR-S136-2)
              <ListItem key={recipe.id} disableGutters disablePadding sx={{ gap: 1 }}>
                <ListItemButton component={RouterLink} to={`/recipes/${recipe.id}`} disableGutters>
                  <ListItemText primary={recipe.title} />
                </ListItemButton>
                <PlanningToggle recipe={recipe} />
              </ListItem>
            ))}
          </List>
        )}
      </Stack>
    </Container>
  )
}

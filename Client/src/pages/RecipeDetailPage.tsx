import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import PlanningToggle from '../components/PlanningToggle'
import { Link as RouterLink, useParams } from 'react-router'
import { formatIngredient } from '../domain/recipe'
import type { Recipe } from '../domain/recipe'
import { useResultQuery } from '../hooks/useResultQuery'
import { fetchRecipe } from '../services/recipesApi'
import { MIN_TOUCH_TARGET } from '../touchTarget'

// ADR-S142-2: Die Seite lädt das Rezept immer über die Kennung aus der Adresse – auch direkt nach dem Anlegen.
export default function RecipeDetailPage() {
  // useParams liefert `string | undefined`; die App-Route /recipes/:id liefert die Kennung immer. Fehlt sie, gibt es
  // dazu kein Rezept: nicht gefunden, ohne Abruf.
  const { id } = useParams()
  return id === undefined ? <RecipeNotFound /> : <LoadedRecipe id={id} />
}

function LoadedRecipe({ id }: Readonly<{ id: string }>) {
  // Während des Ladens bleibt die Seite leer: weder Hinweis noch Spinner.
  // Stryker disable next-line StringLiteral: Query-Key-Präfix, äquivalent solange nichts per Präfix invalidiert (ADR-S153-2)
  const lookup = useResultQuery(['recipes', id], () => fetchRecipe(id))

  if (lookup === undefined) return null
  return lookup.kind === 'Found' ? <RecipeDetail recipe={lookup.recipe} /> : <RecipeNotFound />
}

function RecipeNotFound() {
  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" gutterBottom>Rezept nicht gefunden.</Typography>
      <Button component={RouterLink} to="/recipes" variant="contained">Zur Rezept-Liste</Button>
    </Container>
  )
}

function RecipeDetail({ recipe }: Readonly<{ recipe: Recipe }>) {
  return (
    <Container component="main" maxWidth="sm">
      {/* Titelzeile mit Umschalter: UX-Guideline, Visuelle Baseline „Seitentitel mit Aktion" (CGU-visuelle-baseline). */}
      <Stack
        direction="row"
        spacing={2}
        // Stryker disable next-line ObjectLiteral,StringLiteral: Layout-Wert, in jsdom nicht beobachtbar (ADR-S136-2)
        sx={{ alignItems: 'center', justifyContent: 'space-between', minHeight: MIN_TOUCH_TARGET, mb: 1 }}
      >
        <Typography variant="h5" component="h1">{recipe.title}</Typography>
        <PlanningToggle recipe={recipe} />
      </Stack>
      <Typography variant="h6" component="h2" id="recipe-ingredients-heading" gutterBottom>Zutaten</Typography>
      <List aria-labelledby="recipe-ingredients-heading">
        {recipe.ingredients.map((ingredient, index) => (
          // Zutaten haben keine Identität außer ihrer Position; die Liste wird nur angezeigt.
          <ListItem key={index} disableGutters>
            <ListItemText primary={formatIngredient(ingredient)} />
          </ListItem>
        ))}
      </List>
      <Typography variant="h6" component="h2" id="recipe-steps-heading" gutterBottom>Zubereitung</Typography>
      {/* Geordnete Liste: ein Screenreader sagt die Reihenfolge an; die Nummer steht als eigenes Element
          im Eintrag, damit eine mehrzeilige Anweisung unter dem Text und nicht unter der Nummer läuft. */}
      <List component="ol" aria-labelledby="recipe-steps-heading">
        {recipe.steps.map((step, index) => (
          <ListItem key={index} disableGutters alignItems="flex-start">
            <ListItemIcon>{`${String(index + 1)}.`}</ListItemIcon>
            <ListItemText primary={step.instruction} />
          </ListItem>
        ))}
      </List>
    </Container>
  )
}

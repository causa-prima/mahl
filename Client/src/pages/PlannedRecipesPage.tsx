import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import IconButton from '@mui/material/IconButton'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import Close from '@mui/icons-material/Close'
import { Link as RouterLink } from 'react-router'
import UndoToast from '../components/UndoToast'
import { useDeleteWithUndo } from '../hooks/useDeleteWithUndo'
import { useInvalidatePlannedRecipes, usePlannedRecipes } from '../hooks/usePlannedRecipes'
import { planRecipe, unplanRecipe } from '../services/plannedRecipesApi'
import type { RecipeSummary } from '../domain/recipe'

type PlannedRecipeRowProps = {
  readonly recipe: RecipeSummary
  readonly removing: boolean
  readonly onRemove: (recipe: Readonly<RecipeSummary>) => void
}

// Wie bei den Zutaten: die destruktive Aktion steht am Zeilenende; das aria-label nennt das Rezept.
// Kein sichtbarer Text, damit der Zeilentext der Titel bleibt. Nur die Zeile mit laufendem DELETE ist gesperrt.
function PlannedRecipeRow({ recipe, removing, onRemove }: Readonly<PlannedRecipeRowProps>) {
  return (
    <ListItem
      disableGutters
      disablePadding
      secondaryAction={
        <IconButton aria-label={`${recipe.title} entfernen`} disabled={removing} onClick={() => { onRemove(recipe) }}>
          <Close />
        </IconButton>
      }
    >
      <ListItemButton component={RouterLink} to={`/recipes/${recipe.id}`} disableGutters>
        <ListItemText primary={recipe.title} />
      </ListItemButton>
    </ListItem>
  )
}

type PlannedRecipeListProps = {
  readonly planned: readonly RecipeSummary[] | undefined
  readonly deletingId: RecipeSummary['id'] | null
  readonly onRemove: (recipe: Readonly<RecipeSummary>) => void
}

// Solange die Antwort fehlt (Laden oder Fehler), steht unter der Überschrift nichts: kein Leerzustand, kein Spinner.
// Leerzustand hier statt als Ternary in der Seite – Muster wie IngredientList.
function PlannedRecipeList({ planned, deletingId, onRemove }: Readonly<PlannedRecipeListProps>) {
  if (planned === undefined) return null
  if (planned.length === 0) {
    return (
      <Stack spacing={2}>
        <Typography>Noch keine Rezepte vorgemerkt.</Typography>
        <Box>
          <Button component={RouterLink} to="/recipes" variant="contained">Zur Rezept-Liste</Button>
        </Box>
      </Stack>
    )
  }
  return (
    <List aria-labelledby="planned-heading" disablePadding>
      {planned.map((recipe) => (
        <PlannedRecipeRow key={recipe.id} recipe={recipe} removing={recipe.id === deletingId} onRemove={onRemove} />
      ))}
    </List>
  )
}

export default function PlannedRecipesPage() {
  const planned = usePlannedRecipes()
  const invalidatePlannedRecipes = useInvalidatePlannedRecipes()
  // ADR-S112-5: geteilte Umsetzung; ADR-S153-1: DELETE/PUT sind idempotent, ohne If-Match und Body.
  const { deleted, deletingId, requestDelete, undoDelete, dismissUndo } = useDeleteWithUndo<RecipeSummary>({
    remove: (recipe) => unplanRecipe(recipe.id),
    restore: (recipe) => planRecipe(recipe.id),
    onChanged: invalidatePlannedRecipes,
  })

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" id="planned-heading" gutterBottom>Vorgemerkt</Typography>
      <PlannedRecipeList planned={planned} deletingId={deletingId} onRemove={requestDelete} />
      <UndoToast
        deleted={deleted}
        message={(recipe) => `${recipe.title} entfernt`}
        onUndo={undoDelete}
        onDismiss={dismissUndo}
      />
    </Container>
  )
}

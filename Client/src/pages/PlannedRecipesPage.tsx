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
import { Link as RouterLink, useNavigate } from 'react-router'
import UndoToast from '../components/UndoToast'
import { useDeleteWithUndo } from '../hooks/useDeleteWithUndo'
import { useInvalidatePlannedRecipes, usePlannedRecipes } from '../hooks/usePlannedRecipes'
import { useGenerateShoppingList } from '../hooks/useShoppingList'
import { planRecipe, unplanRecipe } from '../services/plannedRecipesApi'
import type { RecipeSummary } from '../domain/recipe'
import { shoppingListPath } from '../routes'

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

type PlannedRecipeActions = {
  readonly deletingId: RecipeSummary['id'] | null
  readonly onRemove: (recipe: Readonly<RecipeSummary>) => void
  readonly onGenerate: () => void
}

type PlannedRecipeListProps = PlannedRecipeActions & {
  readonly planned: readonly RecipeSummary[] | undefined
}

type PlannedRecipesWithGenerateProps = PlannedRecipeActions & {
  readonly planned: readonly RecipeSummary[]
}

// Die Liste der Vormerkungen mit der Hauptaktion darunter (CGU-visuelle-baseline: Stack spacing={2}).
function PlannedRecipesWithGenerate({ planned, deletingId, onRemove, onGenerate }: Readonly<PlannedRecipesWithGenerateProps>) {
  return (
    <Stack spacing={2}>
      <List aria-labelledby="planned-heading" disablePadding>
        {planned.map((recipe) => (
          <PlannedRecipeRow key={recipe.id} recipe={recipe} removing={recipe.id === deletingId} onRemove={onRemove} />
        ))}
      </List>
      <Button
        variant="contained"
        fullWidth
        aria-label="Zutaten aller vorgemerkten Rezepte auf die Einkaufsliste"
        onClick={onGenerate}
      >
        Auf die Einkaufsliste
      </Button>
    </Stack>
  )
}

// Solange die Antwort fehlt (Laden oder Fehler), steht unter der Überschrift nichts: kein Leerzustand, kein Spinner.
// Leerzustand hier statt als Ternary in der Seite – Muster wie IngredientList.
function PlannedRecipeList({ planned, deletingId, onRemove, onGenerate }: Readonly<PlannedRecipeListProps>) {
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
  return <PlannedRecipesWithGenerate planned={planned} deletingId={deletingId} onRemove={onRemove} onGenerate={onGenerate} />
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

  const navigate = useNavigate()
  // ADR-S154-3: POST /generate, danach öffnet sich die Einkaufsliste. Schlägt es fehl, bleibt die Seite ohne Meldung.
  const generate = useGenerateShoppingList(() => { void navigate(shoppingListPath) })

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" id="planned-heading" gutterBottom>Vorgemerkt</Typography>
      <PlannedRecipeList planned={planned} deletingId={deletingId} onRemove={requestDelete} onGenerate={generate} />
      <UndoToast
        deleted={deleted}
        message={(recipe) => `${recipe.title} entfernt`}
        onUndo={undoDelete}
        onDismiss={dismissUndo}
      />
    </Container>
  )
}

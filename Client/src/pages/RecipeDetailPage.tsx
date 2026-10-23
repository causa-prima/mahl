import Container from '@mui/material/Container'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import { useLocation } from 'react-router'
import { formatIngredient } from '../domain/recipe'
import type { Recipe } from '../domain/recipe'

// Zeigt in diesem Lauf das Rezept aus der 201-Antwort des POST (Router-State); Nachladen per
// GET /api/recipes/{id} folgt mit dem Direktlink (run-4).
export default function RecipeDetailPage() {
  const recipe = useLocation().state as Recipe

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" gutterBottom>{recipe.title}</Typography>
      <Typography variant="h6" component="h2" id="recipe-ingredients-heading">Zutaten</Typography>
      <List aria-labelledby="recipe-ingredients-heading">
        {recipe.ingredients.map((ingredient, index) => (
          // Zutaten haben keine Identität außer ihrer Position; die Liste wird nur angezeigt.
          <ListItem key={index} disableGutters>
            <ListItemText primary={formatIngredient(ingredient)} />
          </ListItem>
        ))}
      </List>
      <Typography variant="h6" component="h2" id="recipe-steps-heading">Zubereitung</Typography>
      <List aria-labelledby="recipe-steps-heading">
        {recipe.steps.map((step, index) => (
          <ListItem key={index} disableGutters>
            <ListItemText primary={`${String(index + 1)}. ${step.instruction}`} />
          </ListItem>
        ))}
      </List>
    </Container>
  )
}

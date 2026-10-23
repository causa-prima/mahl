import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import { useNavigate } from 'react-router'
import { useResultQuery } from '../hooks/useResultQuery'
import { fetchRecipes } from '../services/recipesApi'

const recipesKey = ['recipes'] as const

export default function RecipesPage() {
  const navigate = useNavigate()
  // Während des Ladens erscheint der Leerzustand (TD-S101-1).
  const recipes = useResultQuery(recipesKey, fetchRecipes) ?? []

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" id="recipes-heading" gutterBottom>Rezepte</Typography>
      {recipes.length === 0 ? (
        <Typography gutterBottom>Noch keine Rezepte angelegt.</Typography>
      ) : (
        <List aria-labelledby="recipes-heading">
          {recipes.map((recipe) => (
            <ListItem key={recipe.id} disableGutters>
              <ListItemText primary={recipe.title} />
            </ListItem>
          ))}
        </List>
      )}
      <Button variant="contained" onClick={() => { void navigate('/recipes/new') }}>Rezept anlegen</Button>
    </Container>
  )
}

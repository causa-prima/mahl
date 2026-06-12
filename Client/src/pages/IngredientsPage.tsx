import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import TextField from '@mui/material/TextField'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import { useResultQuery } from '../hooks/useResultQuery'
import { useResultMutation } from '../hooks/useResultMutation'
import { fetchIngredients, createIngredient } from '../services/ingredientsApi'

const ingredientsKey = ['ingredients'] as const

export default function IngredientsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [name, setName] = useState('')
  const [unit, setUnit] = useState('')
  const queryClient = useQueryClient()
  const ingredients = useResultQuery(ingredientsKey, fetchIngredients)

  const closeDialog = () => {
    setIsDialogOpen(false)
    setName('')
    setUnit('')
  }

  const save = useResultMutation(createIngredient, () => {
    closeDialog()
    void queryClient.invalidateQueries({ queryKey: ingredientsKey })
  })

  return (
    <div>
      {ingredients && ingredients.length > 0
        ? (
          <List data-testid="ingredient-list">
            {ingredients.map((ingredient) => (
              <ListItem key={ingredient.id}>
                <ListItemText primary={ingredient.name} secondary={ingredient.defaultUnit} />
              </ListItem>
            ))}
          </List>
        )
        : <p>Noch keine Zutaten angelegt.</p>}
      <Button variant="contained" onClick={() => { setIsDialogOpen(true) }}>Zutat anlegen</Button>
      <Dialog open={isDialogOpen} aria-labelledby="create-ingredient-title">
        <DialogTitle id="create-ingredient-title">Zutat anlegen</DialogTitle>
        <DialogContent>
          <TextField label="Name" value={name} onChange={(e) => { setName(e.target.value) }} />
          <TextField label="Einheit" value={unit} onChange={(e) => { setUnit(e.target.value) }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>Abbrechen</Button>
          <Button variant="contained" onClick={() => { save({ name, defaultUnit: unit }) }}>Speichern</Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}

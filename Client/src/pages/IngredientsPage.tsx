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

  const [save, saveError] = useResultMutation(createIngredient, () => {
    closeDialog()
    // Äquivalenter Mutant: Die App hat nur eine Query-Art (['ingredients']), daher ist
    // invalidateQueries({}) (alle) ≡ invalidateQueries({ queryKey: ingredientsKey }).
    // Deterministisch tötbar erst mit einer zweiten Query-Art.
    // Stryker disable next-line ObjectLiteral: aequivalent, nur eine Query-Art (s. o.)
    void queryClient.invalidateQueries({ queryKey: ingredientsKey })
  })

  // Direkter kind-Check statt matchKind (ADR-S056-1) ist hier bewusst aufgeschoben:
  // ADR-S056-1's kanonisches Muster trennt Netzwerk/5xx (werfen -> QueryCache.onError/
  // Toast) von Domain-Fehlern (matchKind). onError existiert noch nicht (resilience-
  // Szenario). Bis dahin trägt ApiError den Unexpected-kind und die Komponente liest
  // FieldErrors geguarded direkt; matchKind wird im resilience-Szenario adoptiert, wenn
  // die Komponenten-Fehler-Union auf Domain-Fehler-only kollabiert. Tracking: docs/tech-debt.md.
  // ADR-S090-1: feld-keyed 422-Fehler -> Meldung am Name-Feld (UX-Guideline §4: nah am
  // betroffenen Element). Nur der FieldErrors-kind trägt feldbezogene Meldungen.
  // name?.[0]: Guard gegen Render-Crash, falls ein FieldErrors OHNE name-Key ankommt
  // (contractlich möglich nach ADR-S090-1, z.B. nur defaultUnit-Fehler beim 'leere
  // Einheit'-Szenario; der fields-Typ ist Partial -> Lookup ehrlich `... | undefined`).
  // Der name-absent-Zweig ist von DIESEM Szenario nicht test-getrieben -> Stryker-
  // Suppression; ein echter Test ersetzt sie mit dem 'leere Einheit'-Szenario.
  // Stryker disable next-line OptionalChaining: name-absent-Zweig erst im 'leere Einheit'-Szenario test-getrieben (s. o.)
  const nameError = saveError?.kind === 'FieldErrors' ? saveError.fields.name?.[0] : undefined

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
          <TextField
            label="Name"
            value={name}
            onChange={(e) => { setName(e.target.value) }}
            error={Boolean(nameError)}
            helperText={nameError}
          />
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

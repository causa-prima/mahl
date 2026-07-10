import { useRef, useState } from 'react'
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

type CreateIngredientDialogProps = {
  readonly open: boolean
  readonly name: string
  readonly unit: string
  readonly nameError: string | undefined
  readonly unitError: string | undefined
  readonly isPending: boolean
  readonly onNameChange: (value: string) => void
  readonly onUnitChange: (value: string) => void
  readonly onClose: () => void
  readonly onSubmit: () => void
}

// Ausgelagert aus IngredientsPage (Refactor, keine eigenes Szenario/Test – die
// Komponenten-Tests decken diesen Dialog weiterhin über die IngredientsPage-API ab).
function CreateIngredientDialog(props: Readonly<CreateIngredientDialogProps>) {
  const { open, name, unit, nameError, unitError, isPending, onNameChange, onUnitChange, onClose, onSubmit } = props
  const nameInputRef = useRef<HTMLInputElement>(null)

  // UX-Guideline Prinzip 3 ("Sperren während Pending"): MUI ruft `onClose` für BEIDE
  // Schließ-Pfade (Escape UND Backdrop-Klick) auf – während `isPending` beide sperren,
  // ohne den Erfolgspfad zu berühren (der ruft `closeDialog` direkt über `onSuccess`).
  const handleClose = () => {
    if (isPending) return
    onClose()
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      aria-labelledby="create-ingredient-title"
      // Framework-geliefert (Prinzip 8, "Enter sendet ab"): echtes <form> via
      // Dialog-Paper-Slot statt onClick. `formNoValidate` am Speichern-Button, weil
      // die Validierung server-only ist (ADR-S090-1) – sonst blockiert der native
      // `required`-Check die @US-904-error-Szenarien (leerer Name/leere Einheit) stumm.
      slotProps={{
        paper: {
          component: 'form',
          // Typ HTMLDivElement, nicht HTMLFormElement: Paper-Slot ist auf Paper<div>
          // typisiert; component="form" ändert nur das gerenderte Element zur Laufzeit.
          onSubmit: (e: Readonly<React.SyntheticEvent<HTMLDivElement>>) => {
            e.preventDefault()
            onSubmit()
          },
        },
        // Framework-geliefert (Prinzip 8, "Autofokus beim Öffnen"): `autoFocus` auf dem
        // TextField reicht NICHT – der Dialog öffnet mit einer Fade-Transition, die das
        // Paper anfangs auf `visibility: hidden` setzt; ein `.focus()`-Aufruf auf ein zu
        // dem Zeitpunkt unsichtbares Element wird von echten Browsern (nicht von
        // jsdom/happy-dom) stillschweigend ignoriert. Fokus daher erst nach Abschluss der
        // Enter-Transition (`onEntered`) setzen, wenn das Feld tatsächlich sichtbar ist.
        transition: { onEntered: () => { nameInputRef.current?.focus() } },
      }}
    >
      <DialogTitle id="create-ingredient-title">Zutat anlegen</DialogTitle>
      <DialogContent>
        <TextField
          label="Name"
          value={name}
          onChange={(e) => { onNameChange(e.target.value) }}
          error={Boolean(nameError)}
          helperText={nameError}
          required
          inputRef={nameInputRef}
        />
        <TextField
          label="Einheit"
          value={unit}
          onChange={(e) => { onUnitChange(e.target.value) }}
          error={Boolean(unitError)}
          helperText={unitError}
          required
        />
      </DialogContent>
      <DialogActions>
        <Button type="button" onClick={handleClose} disabled={isPending}>Abbrechen</Button>
        <Button type="submit" formNoValidate variant="contained" disabled={isPending}>Speichern</Button>
      </DialogActions>
    </Dialog>
  )
}

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

  const [save, saveError, isPending, resetSaveError] = useResultMutation(createIngredient, () => {
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
  // ADR-S090-1: feld-keyed 422-Fehler -> Meldung am betroffenen Feld (UX-Guideline §4: nah
  // am betroffenen Element). Nur der FieldErrors-kind trägt feldbezogene Meldungen. Der Key
  // (name / defaultUnit) ist die Request-JSON-Property; ein FieldErrors kann einen Key
  // weglassen (z.B. nur defaultUnit beim 'leere Einheit'-Szenario), daher liefert der Lookup
  // dank noUncheckedIndexedAccess (tsconfig.app.json) ehrlich `... | undefined` -> der
  // `?.`-Guard schützt vor einem Render-Crash bei fehlendem Key.
  const fieldErrors = saveError?.kind === 'FieldErrors' ? saveError.fields : undefined
  const nameError = fieldErrors?.name?.[0]
  const unitError = fieldErrors?.defaultUnit?.[0]

  const handleCancel = () => {
    resetSaveError()
    closeDialog()
  }

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
      <CreateIngredientDialog
        open={isDialogOpen}
        name={name}
        unit={unit}
        nameError={nameError}
        unitError={unitError}
        isPending={isPending}
        onNameChange={setName}
        onUnitChange={setUnit}
        onClose={handleCancel}
        onSubmit={() => { save({ name, defaultUnit: unit }) }}
      />
    </div>
  )
}

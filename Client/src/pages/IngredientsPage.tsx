import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import TextField from '@mui/material/TextField'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import IconButton from '@mui/material/IconButton'
import DeleteIcon from '@mui/icons-material/Delete'
import UndoToast from '../components/UndoToast'
import ReactivationConflictToast from '../components/ReactivationConflictToast'
import { useResultQuery } from '../hooks/useResultQuery'
import { useDeleteWithUndo } from '../hooks/useDeleteWithUndo'
import { useCreateIngredientWithReactivation } from '../hooks/useCreateIngredientWithReactivation'
import { fetchIngredients, deleteIngredient, restoreIngredient } from '../services/ingredientsApi'
import { asIngredientName, asUnit } from '../domain/ingredient'
import type { Ingredient, IngredientId, NewIngredient } from '../domain/ingredient'

const ingredientsKey = ['ingredients'] as const

const emptyNewIngredient: NewIngredient = { name: asIngredientName(''), baseUnit: asUnit('') }

type CreateIngredientDialogProps = {
  // null = Dialog geschlossen. Ein Wert statt open-Flag plus Feld-Slices: "offen ohne Eingabe" und
  // "geschlossen mit Resteingabe" sind so nicht darstellbar, und Schließen verwirft alle Felder auf
  // einmal – auch künftige, ohne dass der Schließen-Pfad sie kennen muss.
  readonly newIngredient: NewIngredient | null
  readonly nameError: string | undefined
  readonly unitError: string | undefined
  readonly isPending: boolean
  readonly onChange: (newIngredient: NewIngredient) => void
  readonly onClose: () => void
  readonly onSubmit: (newIngredient: NewIngredient) => void
}

type NewIngredientFieldsProps = {
  readonly value: NewIngredient
  readonly nameError: string | undefined
  readonly unitError: string | undefined
  readonly nameInputRef: React.RefObject<HTMLInputElement | null>
  readonly unitInputRef: React.RefObject<HTMLInputElement | null>
  readonly onChange: (newIngredient: NewIngredient) => void
}

function NewIngredientFields(props: Readonly<NewIngredientFieldsProps>) {
  const { value, nameError, unitError, nameInputRef, unitInputRef, onChange } = props
  return (
    <>
      <TextField
        label="Name"
        fullWidth
        margin="dense"
        value={value.name}
        onChange={(e) => { onChange({ ...value, name: asIngredientName(e.target.value) }) }}
        error={Boolean(nameError)}
        helperText={nameError}
        required
        inputRef={nameInputRef}
      />
      <TextField
        label="Einheit"
        fullWidth
        margin="dense"
        value={value.baseUnit}
        onChange={(e) => { onChange({ ...value, baseUnit: asUnit(e.target.value) }) }}
        error={Boolean(unitError)}
        helperText={unitError}
        required
        inputRef={unitInputRef}
      />
    </>
  )
}

// UX-Guideline „Formular-/Dialog-Baseline" ("Fokus aufs erste fehlerhafte Feld", TD-S094-1): nach einem
// Validierungsfehler springt der Fokus auf das erste fehlerhafte Feld in DOM-Reihenfolge
// (Name vor Einheit). Kein Transition-Race wie beim Autofokus (ADR-S100-1): der Dialog ist
// beim Fehler bereits offen/sichtbar, `.focus()` greift deterministisch. Als eigene Funktion
// ausgelagert, weil das Fokus-Management nach Validierungsfehler ein eigenständiges,
// testbares Verhalten ist (losgelöst vom reinen Rendering); dass CreateIngredientDialog
// dadurch unter dem Zeilen-Richtwert bleibt, ist ein Nebeneffekt.
function useFocusFirstInvalidField(
  nameInputRef: Readonly<React.RefObject<HTMLInputElement | null>>,
  unitInputRef: Readonly<React.RefObject<HTMLInputElement | null>>,
  nameError: string | undefined,
  unitError: string | undefined,
): void {
  useEffect(() => {
    const firstInvalidFieldRef = nameError ? nameInputRef : unitError ? unitInputRef : undefined
    firstInvalidFieldRef?.current?.focus()
  }, [nameError, unitError, nameInputRef, unitInputRef])
}

// Ausgelagert aus IngredientsPage (Refactor, keine eigenes Szenario/Test – die
// Komponenten-Tests decken diesen Dialog weiterhin über die IngredientsPage-API ab).
function CreateIngredientDialog(props: Readonly<CreateIngredientDialogProps>) {
  const { newIngredient, nameError, unitError, isPending, onChange, onClose, onSubmit } = props
  // Während der Schließ-Transition ist newIngredient schon null, die Felder sind aber noch zu sehen.
  const value = newIngredient ?? emptyNewIngredient
  const nameInputRef = useRef<HTMLInputElement>(null)
  const unitInputRef = useRef<HTMLInputElement>(null)
  useFocusFirstInvalidField(nameInputRef, unitInputRef, nameError, unitError)

  // UX-Guideline „Sichtbares Feedback" ("Sperren während Pending"): MUI ruft `onClose` für BEIDE
  // Schließ-Pfade (Escape UND Backdrop-Klick) auf – während `isPending` beide sperren,
  // ohne den Erfolgspfad zu berühren (der ruft `closeDialog` direkt über `onSuccess`).
  const handleClose = () => {
    if (isPending) return
    onClose()
  }

  return (
    <Dialog
      open={newIngredient !== null}
      onClose={handleClose}
      aria-labelledby="create-ingredient-title"
      // Framework-geliefert (Formular-/Dialog-Baseline,"Enter sendet ab"): echtes <form> via
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
            onSubmit(value)
          },
        },
        // Framework-geliefert (Formular-/Dialog-Baseline,"Autofokus beim Öffnen"): `autoFocus` auf dem
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
        <NewIngredientFields
          value={value}
          nameError={nameError}
          unitError={unitError}
          nameInputRef={nameInputRef}
          unitInputRef={unitInputRef}
          onChange={onChange}
        />
      </DialogContent>
      <DialogActions>
        <Button type="button" onClick={handleClose} disabled={isPending}>Abbrechen</Button>
        <Button type="submit" formNoValidate variant="contained" disabled={isPending}>Speichern</Button>
      </DialogActions>
    </Dialog>
  )
}

type IngredientListProps = {
  // undefined, solange die Liste nicht geladen ist – dann steht wie bei leerer Liste der Leerzustand.
  readonly ingredients: readonly Ingredient[] | undefined
  readonly deletingId: IngredientId | null
  readonly onDelete: (ingredient: Readonly<Ingredient>) => void
}

// UX-Prinzip „Least Surprise": die destruktive Aktion steht am Zeilenende (secondaryAction). Das aria-label
// nennt die Zutat, damit die Aktion auch ohne visuellen Kontext eindeutig ist ("Mehl löschen").
// Nur die Zeile, deren DELETE gerade läuft, ist deaktiviert (deletingId) – kein globales Sperren der
// übrigen Zeilen (CROSS-interaction run-3 „Löschen·Pending").
// Leerzustand hier statt als Ternary in IngredientsPage – Muster wie ReactivationConflictToast.
function IngredientList({ ingredients, deletingId, onDelete }: Readonly<IngredientListProps>) {
  if (!ingredients || ingredients.length === 0) return <Typography gutterBottom>Noch keine Zutaten angelegt.</Typography>
  return (
    <List data-testid="ingredient-list">
      {ingredients.map((ingredient) => (
        <ListItem
          key={ingredient.id}
          // Bündig mit Überschrift und Anlegen-Button: der Container polstert bereits seitlich.
          disableGutters
          secondaryAction={
            <IconButton
              aria-label={`${ingredient.name} löschen`}
              disabled={ingredient.id === deletingId}
              onClick={() => { onDelete(ingredient) }}
            >
              <DeleteIcon />
            </IconButton>
          }
        >
          <ListItemText primary={ingredient.name} secondary={ingredient.baseUnit} />
        </ListItem>
      ))}
    </List>
  )
}

export default function IngredientsPage() {
  const [newIngredient, setNewIngredient] = useState<NewIngredient | null>(null)
  const queryClient = useQueryClient()
  const ingredients = useResultQuery(ingredientsKey, fetchIngredients)

  const invalidateIngredients = () => {
    // Äquivalenter Mutant: Die App hat nur eine Query-Art (['ingredients']), daher ist
    // invalidateQueries({}) (alle) ≡ invalidateQueries({ queryKey: ingredientsKey }).
    // Deterministisch tötbar erst mit einer zweiten Query-Art.
    // Stryker disable next-line ObjectLiteral: aequivalent, nur eine Query-Art (s. o.; Einzelfall, vom User freigegeben S136)
    void queryClient.invalidateQueries({ queryKey: ingredientsKey })
  }

  const closeDialog = () => { setNewIngredient(null) }

  // ADR-S108-1/-2: DELETE mit dem per-Zeile-xmin-ETag als If-Match; Undo = Restore ohne If-Match,
  // aber mit Name und Einheit im Body (ADR-S111-1-Addendum).
  const { deleted, deletingId, requestDelete, undoDelete, dismissUndo } = useDeleteWithUndo<Ingredient>({
    remove: (ingredient) => deleteIngredient(ingredient.id, ingredient.etag),
    restore: (ingredient) => restoreIngredient(ingredient.id, ingredient.name, ingredient.baseUnit),
    onChanged: invalidateIngredients,
  })

  // run-11-Nachbesserung F1: `dismissUndo()` verwirft einen noch sichtbaren Undo-Toast einer
  // vorangegangenen Löschung. Ohne das kann eine Reaktivierung (409 soft-deleted -> transparenter
  // Restore, ADR-S051-4) dieselbe Zeile wieder aktivieren, während ihr Undo-Toast noch "gelöscht"
  // behauptet – ein Klick auf "Rückgängig" liefe dann ins Leere (409 ingredient_already_active,
  // ADR-S111-1).
  const { save, isPending, nameError, unitError, resetSaveError, conflictNotice, dismissConflictNotice } =
    useCreateIngredientWithReactivation(() => {
      closeDialog()
      invalidateIngredients()
      dismissUndo()
    })

  const handleCancel = () => {
    resetSaveError()
    closeDialog()
  }

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" gutterBottom>Zutaten</Typography>
      <IngredientList ingredients={ingredients} deletingId={deletingId} onDelete={requestDelete} />
      <Button variant="contained" onClick={() => { setNewIngredient(emptyNewIngredient) }}>Zutat anlegen</Button>
      <CreateIngredientDialog
        newIngredient={newIngredient}
        nameError={nameError}
        unitError={unitError}
        isPending={isPending}
        onChange={setNewIngredient}
        onClose={handleCancel}
        onSubmit={save}
      />
      <UndoToast
        deleted={deleted}
        message={(ingredient) => `${ingredient.name} gelöscht`}
        onUndo={undoDelete}
        onDismiss={dismissUndo}
      />
      <ReactivationConflictToast
        conflict={conflictNotice}
        onDismiss={dismissConflictNotice}
      />
    </Container>
  )
}

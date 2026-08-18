import { useEffect, useRef, useState } from 'react'
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
import IconButton from '@mui/material/IconButton'
import Snackbar from '@mui/material/Snackbar'
import type { SnackbarCloseReason } from '@mui/material/Snackbar'
import DeleteIcon from '@mui/icons-material/Delete'
import { useResultQuery } from '../hooks/useResultQuery'
import { useDeleteIngredientWithUndo } from '../hooks/useDeleteIngredientWithUndo'
import type { DeletedIngredient } from '../hooks/useDeleteIngredientWithUndo'
import { useCreateIngredientWithReactivation } from '../hooks/useCreateIngredientWithReactivation'
import type { ReactivationConflictNotice } from '../hooks/useCreateIngredientWithReactivation'
import { fetchIngredients } from '../services/ingredientsApi'
import type { Ingredient } from '../services/ingredientsApi'

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

// UX-Guideline Prinzip 8 ("Fokus aufs erste fehlerhafte Feld", TD-S094-1): nach einem
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
  const { open, name, unit, nameError, unitError, isPending, onNameChange, onUnitChange, onClose, onSubmit } = props
  const nameInputRef = useRef<HTMLInputElement>(null)
  const unitInputRef = useRef<HTMLInputElement>(null)
  useFocusFirstInvalidField(nameInputRef, unitInputRef, nameError, unitError)

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
          inputRef={unitInputRef}
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
  readonly ingredients: readonly Ingredient[]
  readonly deletingId: string | null
  readonly onDelete: (ingredient: Readonly<Ingredient>) => void
}

// UX-Prinzip 1: die destruktive Aktion steht am Zeilenende (secondaryAction). Das aria-label
// nennt die Zutat, damit die Aktion auch ohne visuellen Kontext eindeutig ist ("Mehl löschen").
// run-9: nur die Zeile, deren DELETE gerade läuft, ist deaktiviert (deletingId) – kein globales
// Sperren der übrigen Zeilen (Scope-Grenze run-9).
function IngredientList({ ingredients, deletingId, onDelete }: Readonly<IngredientListProps>) {
  return (
    <List data-testid="ingredient-list">
      {ingredients.map((ingredient) => (
        <ListItem
          key={ingredient.id}
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

type ReactivationConflictToastProps = {
  readonly conflict: ReactivationConflictNotice | null
  readonly onDismiss: () => void
}

// ADR-S111-3: Reaktivierungs-Konflikt (Restore antwortet 409 "bereits aktiv", abweichende
// Werte). Der Anlege-Dialog ist zu diesem Zeitpunkt bereits geschlossen (der Vorgang gilt als
// abgeschlossen) – diese Snackbar informiert nur noch. Anders als UndoToast ohne Aktions-Button
// und ohne clickaway-Schutz: kein Szenario verlangt hier einen "Rückgängig"-Pfad, der MUI-
// Default (jeder Schließen-Grund dismisst) genügt. Der Null-Check liegt hier (statt als `&&` in
// IngredientsPage), damit dieser Zweig nicht in deren Komplexität einzahlt.
// run-11-Nachbesserung F2: autoHideDuration 10000ms – bewusst EIGENES Literal, nicht dieselbe
// Konstante wie UndoToast (6000ms): der Text ist rund zehnmal so lang, besteht aus zwei Sätzen
// und MUIs Pause-bei-Hover greift auf Touch nicht (ADR-S111-3).
// run-11-Nachbesserung F4: `key` aus den drei ANGEZEIGTEN Feldern (nicht aus einer id) – erzwingt
// genau dann einen Remount (und damit einen frischen Auto-Hide-Timer, s. UndoToast-Kommentar
// unten für den Mechanismus), wenn sich der sichtbare Text ändert. Eine id-basierte Alternative
// (z.B. savedIngredient.id) würde zwei aufeinanderfolgende Konflikte zur SELBEN Zutat mit
// UNTERSCHIEDLICHEM gespeichertem Stand fälschlich als identisch behandeln – kein Remount, obwohl
// der Nutzer einen neuen Text sieht und der Timer neu laufen müsste. Sind alle drei Felder
// zwischen zwei Konflikten identisch, ist auch der Text identisch – ein ausbleibender Remount ist
// dann folgenlos.
function ReactivationConflictToast({ conflict, onDismiss }: Readonly<ReactivationConflictToastProps>) {
  if (!conflict) return null
  return (
    <Snackbar
      // Kein Test erzwingt den konkreten Aufbau des Remount-`key` (Team-Lead-Review, F4):
      // die Race-Condition, die einen fehlenden/falschen Remount sichtbar machen würde
      // (zwei Konflikte direkt hintereinander, zweiter erbt Restlaufzeit des ersten), ist
      // im Komponenten-Test praktisch nicht mit vertretbarem Aufwand deterministisch
      // herstellbar (kein Fake-Timer-Muster wie bei UndoToast, weil der zweite Konflikt
      // selbst einen Restore-Roundtrip braucht statt eines einzelnen Klicks). Analog zum
      // bereits etablierten `key={deleted.id}` bei UndoToast, dort mit Test.
      // Stryker disable next-line StringLiteral: kein Test für den Remount-key (s. o.)
      key={`${conflict.requestedName}|${conflict.savedName}|${conflict.savedUnit}`}
      open
      autoHideDuration={10000}
      onClose={onDismiss}
      message={
        `'${conflict.requestedName}' wurde zwischenzeitlich an anderer Stelle wiederhergestellt `
        + `(z. B. auf einem anderen Gerät). Gespeichert ist '${conflict.savedName}' mit der Einheit `
        + `'${conflict.savedUnit}'.`
      }
    />
  )
}

type UndoToastProps = {
  readonly deleted: DeletedIngredient
  readonly onUndo: () => void
  readonly onDismiss: () => void
}

// UX-Guideline Prinzip 5 ("Destructive Actions schützen"): Soft-Delete + Undo-Toast ersetzt
// den Bestätigungsdialog. Nicht-blockierende Snackbar; autoHideDuration großzügig, damit
// "Rückgängig" klickbar bleibt.
function UndoToast({ deleted, onUndo, onDismiss }: Readonly<UndoToastProps>) {
  // clickaway (Klick irgendwo auf der Seite) darf den Toast NICHT schließen: sonst wäre die
  // bewusst großzügige autoHideDuration wertlos, sobald der Nutzer nach dem Löschen woanders
  // hinklickt – der Undo-Weg für eine destruktive Aktion muss die volle Dauer erreichbar
  // bleiben (UX-Guideline Prinzip 5). timeout/escapeKeyDown sind bewusste Schließen-Gesten
  // und schließen weiterhin regulär.
  const handleClose = (_event: unknown, reason: SnackbarCloseReason) => {
    if (reason === 'clickaway') return
    onDismiss()
  }

  // `key={deleted.id}`: erzwingt einen Remount pro Löschvorgang. Ohne key behält React beim
  // Wechsel von einer gelöschten Zutat zur nächsten (deleted-Objekt ändert sich, open/
  // autoHideDuration bleiben literal unverändert) dieselbe Snackbar-Instanz bei – MUIs
  // Auto-Hide-Timer-Effect (useSnackbar.js, deps [open, autoHideDuration, setAutoHideTimer,
  // timerAutoHide]) läuft dann NICHT erneut, weil keine dieser Deps sich ändert (open/
  // autoHideDuration sind Literale, die beiden Callbacks referenzstabil via useEventCallback).
  // Der neue Toast erbt so die Restlaufzeit des alten statt der vollen autoHideDuration
  // (US904_EdgeCase_SecondDelete_RestartsUndoWindow). Der Remount startet den Timer frisch.
  return (
    <Snackbar
      key={deleted.id}
      open
      autoHideDuration={6000}
      onClose={handleClose}
      message={`${deleted.name} gelöscht`}
      action={<Button onClick={onUndo}>Rückgängig</Button>}
    />
  )
}

export default function IngredientsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [name, setName] = useState('')
  const [unit, setUnit] = useState('')
  const queryClient = useQueryClient()
  const ingredients = useResultQuery(ingredientsKey, fetchIngredients)

  const invalidateIngredients = () => {
    // Äquivalenter Mutant: Die App hat nur eine Query-Art (['ingredients']), daher ist
    // invalidateQueries({}) (alle) ≡ invalidateQueries({ queryKey: ingredientsKey }).
    // Deterministisch tötbar erst mit einer zweiten Query-Art.
    // Stryker disable next-line ObjectLiteral: aequivalent, nur eine Query-Art (s. o.)
    void queryClient.invalidateQueries({ queryKey: ingredientsKey })
  }

  const closeDialog = () => {
    setIsDialogOpen(false)
    setName('')
    setUnit('')
  }

  const { deleted, deletingId, requestDelete, undoDelete, dismissUndo } = useDeleteIngredientWithUndo(invalidateIngredients)

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
    <div>
      {ingredients && ingredients.length > 0
        ? <IngredientList ingredients={ingredients} deletingId={deletingId} onDelete={requestDelete} />
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
        onSubmit={() => { save({ name, baseUnit: unit }) }}
      />
      {deleted && (
        <UndoToast
          deleted={deleted}
          onUndo={() => { undoDelete(deleted) }}
          onDismiss={dismissUndo}
        />
      )}
      <ReactivationConflictToast
        conflict={conflictNotice}
        onDismiss={dismissConflictNotice}
      />
    </div>
  )
}

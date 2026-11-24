import Button from '@mui/material/Button'
import Snackbar from '@mui/material/Snackbar'
import type { SnackbarCloseReason } from '@mui/material/Snackbar'
import type { WithId } from '../types/withId'

// Großzügig, damit „Rückgängig" klickbar bleibt
const autoHideMs = 6000

type UndoToastProps<T extends WithId> = {
  readonly deleted: T | null
  // Text samt Verb baut die Seite („<Name> gelöscht", „<Titel> entfernt")
  readonly message: (deleted: T) => string
  readonly onUndo: (deleted: T) => void
  readonly onDismiss: () => void
}

// ADR-S112-5: einzige erlaubte Stelle für den Undo-Toast (Import-Guard auf @mui/material/Snackbar).
// UX-Guideline „Destructive Actions schützen": Soft-Delete + Undo-Toast ersetzt den
// Bestätigungsdialog; die Snackbar blockiert nicht. Null-Check hier statt in der Seite –
// Muster wie ReactivationConflictToast.
export default function UndoToast<T extends WithId>(
  { deleted, message, onUndo, onDismiss }: Readonly<UndoToastProps<T>>,
) {
  // clickaway darf den Toast NICHT schließen: der Undo-Weg bleibt die volle Dauer erreichbar,
  // auch wenn der Nutzer nach dem Löschen woanders hinklickt. timeout/escapeKeyDown schließen regulär.
  const handleClose = (_event: unknown, reason: SnackbarCloseReason) => {
    if (reason === 'clickaway') return
    onDismiss()
  }
  if (!deleted) return null

  // `key` erzwingt pro Löschvorgang einen Remount und startet so den Auto-Hide-Timer neu
  // (CROSS_Interaction_Undo_SecondDelete_RestartsUndoWindow). Er liegt hier, damit er nicht
  // bei der Seite vergessen werden kann.
  return (
    <Snackbar
      key={deleted.id}
      open
      autoHideDuration={autoHideMs}
      onClose={handleClose}
      message={message(deleted)}
      // color="inherit": Primärblau auf dem dunklen Snackbar-Grund ist zu kontrastarm (nfr.md, Accessibility).
      action={<Button color="inherit" onClick={() => { onUndo(deleted) }}>Rückgängig</Button>}
    />
  )
}

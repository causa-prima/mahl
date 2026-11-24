import Snackbar from '@mui/material/Snackbar'
import type { ReactivationConflictNotice } from '../hooks/useCreateIngredientWithReactivation'

// Bewusst länger als beim UndoToast (6000 ms): Der Text ist rund zehnmal so lang, besteht aus zwei
// Sätzen, und MUIs Pause-bei-Hover greift auf Touch nicht (ADR-S111-3).
const autoHideMs = 10000

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
// `key` aus den drei ANGEZEIGTEN Feldern, nicht aus einer id: Er erzwingt genau dann einen Remount und
// damit einen frischen Auto-Hide-Timer (MUI startet ihn sonst nur bei geändertem open/autoHideDuration
// neu), wenn sich der sichtbare Text ändert. Eine id-basierte Variante behandelte zwei Konflikte zur
// selben Zutat mit unterschiedlichem gespeichertem Stand fälschlich als identisch.
export default function ReactivationConflictToast({ conflict, onDismiss }: Readonly<ReactivationConflictToastProps>) {
  if (!conflict) return null
  return (
    <Snackbar
      // Kein Test pinnt den Aufbau des `key`: Zwei Konflikte direkt hintereinander brauchen je einen
      // Restore-Roundtrip und sind im Komponententest nicht deterministisch herstellbar. Dasselbe
      // Muster beim UndoToast (`key={deleted.id}`) ist getestet.
      // Stryker disable next-line StringLiteral: kein Test für den Remount-key (s. o.; Einzelfall, vom User freigegeben S136)
      key={`${conflict.requestedName}|${conflict.savedName}|${conflict.savedUnit}`}
      open
      autoHideDuration={autoHideMs}
      onClose={onDismiss}
      message={
        `'${conflict.requestedName}' wurde zwischenzeitlich an anderer Stelle wiederhergestellt `
        + `(z. B. auf einem anderen Gerät). Gespeichert ist '${conflict.savedName}' mit der Einheit `
        + `'${conflict.savedUnit}'.`
      }
    />
  )
}

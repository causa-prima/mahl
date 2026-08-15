import { useState } from 'react'
import { useResultMutation } from './useResultMutation'
import { createIngredient } from '../services/ingredientsApi'
import type { NewIngredient, CreateIngredientResult } from '../services/ingredientsApi'

export type ReactivationConflictNotice = {
  readonly requestedName: string
  readonly savedName: string
  readonly savedUnit: string
}

// Direkter kind-Check statt matchKind, konsistent mit dem bereits bestehenden
// FieldErrors-Zugriff unten (matchKind-Adoption ist auf die volle MutationState-Union
// aufgeschoben – TD-S101-1). ADR-S111-3: der Konflikt ist fachlich erfolgreich (Ok-Pfad) – nur dieser
// eine Zweig liefert einen Hinweis mit dem tatsächlich gespeicherten Stand; sonst `null` (setzt
// einen evtl. noch sichtbaren alten Hinweis zurück).
// run-11-Nachbesserung F2: `requestedName` GETRIMMT – jede andere nutzersichtbare Wiedergabe
// einer Eingabe ist es auch (ADR-S051-1/-2). `result.requestedName` reist ungetrimmt vom
// Dialog-State bis hierher (Anzeige-Aufbereitung, nicht Transport-Anliegen).
function toConflictNotice(result: Readonly<CreateIngredientResult>): ReactivationConflictNotice | null {
  return result.kind === 'ReactivationConflict'
    ? {
        requestedName: result.requestedName.trim(),
        savedName: result.savedIngredient.name,
        savedUnit: result.savedIngredient.defaultUnit,
      }
    : null
}

type CreateIngredientWithReactivation = {
  readonly save: (ingredient: NewIngredient) => void
  readonly isPending: boolean
  readonly nameError: string | undefined
  readonly unitError: string | undefined
  readonly resetSaveError: () => void
  readonly conflictNotice: ReactivationConflictNotice | null
  readonly dismissConflictNotice: () => void
}

// run-11-Nachbesserung F6 (Refactor, keine Verhaltensänderung): ausgelagert aus IngredientsPage,
// analog zu useDeleteIngredientWithUndo. Bündelt Anlegen inkl. transparenter Reaktivierung
// (ADR-S004-1/S051-4) und Reaktivierungs-Konflikt-Hinweis (ADR-S111-1/-3) samt der davon
// abgeleiteten Feldfehler (ADR-S090-1). Ein einziger `onSuccess`-Callback (statt mehrerer
// Einzel-Callbacks) hält die Schnittstelle deckungsgleich mit useDeleteIngredientWithUndo(onChanged)
// – alle Seiteneffekte der Page (Dialog schließen, Liste neu laden, Undo-Toast verwerfen) feuern
// ohnehin gemeinsam im Erfolgsfall; der Hook selbst kennt nur "danach passiert etwas", nicht was.
export function useCreateIngredientWithReactivation(onSuccess: () => void): CreateIngredientWithReactivation {
  const [conflictNotice, setConflictNotice] = useState<ReactivationConflictNotice | null>(null)

  const [save, saveError, isPending, resetSaveError] = useResultMutation(createIngredient, (result) => {
    onSuccess()
    setConflictNotice(toConflictNotice(result))
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

  return {
    save,
    isPending,
    nameError,
    unitError,
    resetSaveError,
    conflictNotice,
    dismissConflictNotice: () => { setConflictNotice(null) },
  }
}

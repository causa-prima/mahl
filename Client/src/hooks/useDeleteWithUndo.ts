import { useState } from 'react'
import { ResultAsync } from 'neverthrow'
import { useResultMutation } from './useResultMutation'
import type { WithId } from '../types/withId'

type DeleteWithUndo<T extends WithId> = {
  readonly deleted: T | null
  readonly deletingId: T['id'] | null
  readonly requestDelete: (item: Readonly<T>) => void
  readonly undoDelete: (deleted: T) => void
  readonly dismissUndo: () => void
}

type RemoveAndRestore<T extends WithId> = {
  // Wie die Seite entfernt bzw. wiederherstellt (Zutaten: DELETE mit If-Match / POST …/restore
  // mit Body; Vorgemerkt: DELETE / idempotentes PUT ohne Zusatzdaten) – der Rest ist geteilt.
  readonly remove: (item: T) => ResultAsync<unknown, unknown>
  readonly restore: (item: T) => ResultAsync<unknown, unknown>
}

type DeleteWithUndoConfig<T extends WithId> = RemoveAndRestore<T> & {
  // lädt die Daten der Seite neu, sodass sie nach Entfernen bzw. Wiederherstellen den Serverzustand zeigt
  readonly onChanged: () => void
}

// ADR-S112-5: geteilte Umsetzung von „Löschen mit Rückgängig-Toast". Grundlage: ADR-S108-1/-2
// (Zutaten). `deleted` trägt das soeben entfernte Element und steuert damit zugleich die
// Sichtbarkeit des Undo-Toasts – ein State statt zusätzlichem open-Flag, damit es keinen
// Zustand "Toast offen ohne Element" geben kann.
export function useDeleteWithUndo<T extends WithId>(
  { remove, restore, onChanged }: Readonly<DeleteWithUndoConfig<T>>,
): DeleteWithUndo<T> {
  const [deleted, setDeleted] = useState<T | null>(null)
  // Sperrt nur die Zeile, deren Entfernen gerade läuft. Wie beim Toast (ADR-S108-3: genau ein
  // Löschvorgang) gilt hier nur der letzte: ein zweites Löschen überschreibt deletingId.
  // Zurückgesetzt wird nur im Erfolgsfall; nach einem Fehler bleibt der Button gesperrt
  // (bekannte Lücke, TD-S108-1, hier nicht behoben).
  const [deletingId, setDeletingId] = useState<T['id'] | null>(null)
  const { trackedRemove, restoreAfterRemove } = useRestoreAfterRemove({ remove, restore })

  const [deleteMutate] = useResultMutation(trackedRemove, () => {
    setDeletingId(null)
    onChanged()
  })
  const [restoreMutate] = useResultMutation(restoreAfterRemove, () => {
    setDeleted(null)
    onChanged()
  })

  const requestDelete = (item: Readonly<T>) => {
    setDeleted(item)
    setDeletingId(item.id)
    deleteMutate(item)
  }

  return {
    deleted,
    deletingId,
    requestDelete,
    undoDelete: (target) => { restoreMutate(target) },
    dismissUndo: () => { setDeleted(null) },
  }
}

// „Rückgängig" während des Entfernens sendet das Wiederherstellen erst danach – sonst könnte das DELETE
// zuletzt eintreffen und das Element trotz Rückgängig löschen (features/interaction.feature, „Rückgängig
// während das Löschen noch läuft …"). Dafür merkt sich der Hook je Element-ID das laufende Entfernen.
// Läuft nichts (kein Eintrag) oder ist es schon fertig, geht das Wiederherstellen sofort los; abgeschlossene
// Einträge bleiben deshalb stehen, bis das nächste Entfernen derselben ID sie ersetzt. Auch ein
// fehlgeschlagenes Entfernen gibt das Wiederherstellen frei: `Promise.resolve` entpackt das ResultAsync zu
// Ok oder Err, ohne abzulehnen – den Fehlerpfad behandelt der Hook nicht (TD-S108-1).
function useRestoreAfterRemove<T extends WithId>({ remove, restore }: Readonly<RemoveAndRestore<T>>) {
  // Einmal je Hook-Instanz angelegt (Initialisierer statt Argument); kein Render hängt am Inhalt.
  const [running] = useState(() => new Map<T['id'], ResultAsync<unknown, unknown>>())
  const trackedRemove = (item: T) => {
    const result = remove(item)
    // eslint-disable-next-line functional/immutable-data -- nur der Undo-Klick liest die Map, kein Render
    running.set(item.id, result)
    return result
  }
  const restoreAfterRemove = (item: T) => ResultAsync
    .fromSafePromise(Promise.resolve(running.get(item.id)))
    .andThen(() => restore(item))
  return { trackedRemove, restoreAfterRemove }
}

import { useState } from 'react'
import { useResultMutation } from './useResultMutation'
import { deleteIngredient, restoreIngredient } from '../services/ingredientsApi'
import type { Ingredient } from '../services/ingredientsApi'

// run-11: `baseUnit` ergänzt, weil der Restore-Body ab jetzt Pflicht ist (ADR-S111-1-Addendum
// zu ADR-S108-2) – der Undo-Aufruf muss Name UND Einheit der gelöschten Zeile mitschicken.
export type DeletedIngredient = { readonly id: string; readonly name: string; readonly baseUnit: string }

type DeleteIngredientWithUndo = {
  readonly deleted: DeletedIngredient | null
  readonly deletingId: string | null
  readonly requestDelete: (ingredient: Readonly<Ingredient>) => void
  readonly undoDelete: (deleted: DeletedIngredient) => void
  readonly dismissUndo: () => void
}

// ADR-S108-1/-2: Löschen einer Zutat (DELETE mit dem per-Zeile-xmin-ETag als If-Match) samt Undo
// (Restore ohne If-Match). `deleted` trägt die soeben gelöschte Zutat und steuert damit zugleich
// die Sichtbarkeit des Undo-Toasts – ein State statt zusätzlichem open-Flag, damit es keinen
// Zustand "Toast offen ohne Zutat" geben kann. `onChanged` lädt die Zutaten-Query neu, sodass die
// Liste nach Löschen bzw. Wiederherstellen den Serverzustand zeigt.
export function useDeleteIngredientWithUndo(onChanged: () => void): DeleteIngredientWithUndo {
  const [deleted, setDeleted] = useState<DeletedIngredient | null>(null)
  // run-9: sperrt gezielt die Zeile, deren DELETE gerade läuft (nicht global, ADR-S108-3-
  // Nachbar-Entscheidung "kein Snackbar-Stacking" gilt sinngemäß auch hier: ein zweites Löschen
  // während des ersten überschreibt deletingId, statt beide Zeilen zu sperren). Reset hängt
  // bewusst am Erfolgspfad (onSuccess feuert nur bei Ok) – ein Netzwerkfehler (Err) lässt den
  // Button dauerhaft deaktiviert. Bekannte Lücke, gehört zu TD-S108-1 (fehlender Status-Check
  // in deleteIngredient), hier bewusst nicht behoben.
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const [deleteMutate] = useResultMutation(
    (vars: { readonly id: string; readonly etag: string }) => deleteIngredient(vars.id, vars.etag),
    () => {
      setDeletingId(null)
      onChanged()
    },
  )
  // ADR-S111-1-Addendum zu ADR-S108-2: der Restore-Body ist ab run-11 Pflicht, auch für den
  // Undo – fachlich ein No-op (dieselben Werte reisen unverändert mit), aber ein einziger
  // Codepfad im Endpoint. Der Wrapper bündelt die drei Werte zum vars-Objekt, das
  // restoreIngredient als Positionsparameter erwartet.
  const [restoreMutate] = useResultMutation(
    (vars: { readonly id: string; readonly name: string; readonly baseUnit: string }) =>
      restoreIngredient(vars.id, vars.name, vars.baseUnit),
    () => {
      setDeleted(null)
      onChanged()
    },
  )

  const requestDelete = (ingredient: Readonly<Ingredient>) => {
    setDeleted({ id: ingredient.id, name: ingredient.name, baseUnit: ingredient.baseUnit })
    setDeletingId(ingredient.id)
    deleteMutate({ id: ingredient.id, etag: ingredient.etag })
  }

  return {
    deleted,
    deletingId,
    requestDelete,
    undoDelete: (target) => { restoreMutate({ id: target.id, name: target.name, baseUnit: target.baseUnit }) },
    dismissUndo: () => { setDeleted(null) },
  }
}

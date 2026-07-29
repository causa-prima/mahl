import { useState } from 'react'
import { useResultMutation } from './useResultMutation'
import { deleteIngredient, restoreIngredient } from '../services/ingredientsApi'
import type { Ingredient } from '../services/ingredientsApi'

export type DeletedIngredient = { readonly id: string; readonly name: string }

type DeleteIngredientWithUndo = {
  readonly deleted: DeletedIngredient | null
  readonly deletingId: string | null
  readonly requestDelete: (ingredient: Readonly<Ingredient>) => void
  readonly undoDelete: (id: string) => void
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
  const [restoreMutate] = useResultMutation(restoreIngredient, () => {
    setDeleted(null)
    onChanged()
  })

  const requestDelete = (ingredient: Readonly<Ingredient>) => {
    setDeleted({ id: ingredient.id, name: ingredient.name })
    setDeletingId(ingredient.id)
    deleteMutate({ id: ingredient.id, etag: ingredient.etag })
  }

  return {
    deleted,
    deletingId,
    requestDelete,
    undoDelete: restoreMutate,
    dismissUndo: () => { setDeleted(null) },
  }
}

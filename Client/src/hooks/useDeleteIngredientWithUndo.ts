import { useState } from 'react'
import { useResultMutation } from './useResultMutation'
import { deleteIngredient, restoreIngredient } from '../services/ingredientsApi'
import type { Ingredient } from '../services/ingredientsApi'

export type DeletedIngredient = { readonly id: string; readonly name: string }

type DeleteIngredientWithUndo = {
  readonly deleted: DeletedIngredient | null
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

  const [deleteMutate] = useResultMutation(
    (vars: { readonly id: string; readonly etag: string }) => deleteIngredient(vars.id, vars.etag),
    onChanged,
  )
  const [restoreMutate] = useResultMutation(restoreIngredient, () => {
    setDeleted(null)
    onChanged()
  })

  const requestDelete = (ingredient: Readonly<Ingredient>) => {
    setDeleted({ id: ingredient.id, name: ingredient.name })
    deleteMutate({ id: ingredient.id, etag: ingredient.etag })
  }

  return {
    deleted,
    requestDelete,
    undoDelete: restoreMutate,
    dismissUndo: () => { setDeleted(null) },
  }
}

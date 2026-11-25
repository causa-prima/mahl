import { useQueryClient } from '@tanstack/react-query'
import { fetchShoppingList, generateShoppingList } from '../services/shoppingListApi'
import { useResultMutation } from './useResultMutation'
import { useResultQuery } from './useResultQuery'

const shoppingListKey = ['shopping-list'] as const

export const useShoppingList = () => useResultQuery(shoppingListKey, fetchShoppingList)

// Nach dem Übernehmen steht die alte Liste im Cache. Sie wird entfernt statt nur als veraltet markiert:
// Sonst zeigte die Einkaufsliste beim Öffnen erst die alte Liste und tauschte sie dann aus.
export function useGenerateShoppingList(onGenerated: () => void) {
  const queryClient = useQueryClient()
  const [mutate] = useResultMutation(generateShoppingList, () => {
    queryClient.removeQueries({ queryKey: shoppingListKey })
    onGenerated()
  })
  // Das Übernehmen hat keine Eingabe; die Mutation (TVariables = unknown) bekommt sie hier.
  return () => { mutate(undefined) }
}

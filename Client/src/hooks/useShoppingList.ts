import { fetchShoppingList } from '../services/shoppingListApi'
import { useResultQuery } from './useResultQuery'

const shoppingListKey = ['shopping-list'] as const

export const useShoppingList = () => useResultQuery(shoppingListKey, fetchShoppingList)

export function fetchIngredients(): Promise<unknown[]> {
  return fetch('/api/ingredients').then(r => r.json())
}

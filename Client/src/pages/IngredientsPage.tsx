import { useQuery } from '@tanstack/react-query'
import { fetchIngredients } from '../services/ingredientsApi'

export default function IngredientsPage() {
  // Stryker disable next-line ArrayDeclaration -- Default [] nie getestet: data ist während Tests nie undefined (MSW liefert immer []). Entfällt wenn Loading-State-Szenario implementiert ist.
  const { data: ingredients = [] } = useQuery({
    // Stryker disable next-line StringLiteral,ArrayDeclaration -- queryKey ist ein Cache-Bezeichner, kein Verhalten
    queryKey: ['ingredients'],
    queryFn: fetchIngredients,
  })

  if (ingredients.length === 0) {
    return (
      <div>
        <p>Noch keine Zutaten angelegt.</p>
        <button>Zutat anlegen</button>
      </div>
    )
  }

  return (
    <ul data-testid="ingredient-list">
      {ingredients.map((_, i) => <li key={i} />)}
    </ul>
  )
}

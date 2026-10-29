import { useState } from 'react'
import { hasRecipeInput } from '../domain/recipe'
import type { RecipeFormValues } from '../domain/recipe'

// Formularzustand von "Rezept anlegen": Titel, Zutaten und die Schritte (es wird nur angehängt).
export function useRecipeForm() {
  const [title, setTitle] = useState('')
  const [ingredients, setIngredients] = useState('')
  const [steps, setSteps] = useState<readonly string[]>([''])
  const values: RecipeFormValues = { title, ingredients, steps }

  return {
    values,
    hasInput: hasRecipeInput(values),
    setTitle,
    setIngredients,
    changeStep: (index: number, instruction: string) => {
      setSteps((previous) => previous.map((step, i) => (i === index ? instruction : step)))
    },
    addStep: () => { setSteps((previous) => [...previous, '']) },
  }
}

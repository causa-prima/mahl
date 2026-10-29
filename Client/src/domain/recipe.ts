// Domänentypen des Rezepts. Nominale Brands wie bei der Zutat (ADR-S112-4): sie unterscheiden
// gleichartige Strings und prüfen keine Regeln; die setzt das Backend durch.
import type { IngredientName, Unit } from './ingredient'
import { isBlank } from './text'

export type RecipeId = string & { readonly __brand: 'RecipeId' }
export type RecipeTitle = string & { readonly __brand: 'RecipeTitle' }
// Roher Text des Zutatenfelds, eine Zutat je Zeile – zerlegt wird auf dem Server (ADR-S135-2).
export type IngredientsText = string & { readonly __brand: 'IngredientsText' }
export type StepInstruction = string & { readonly __brand: 'StepInstruction' }

export const asRecipeTitle = (value: string): RecipeTitle => value as RecipeTitle
export const asIngredientsText = (value: string): IngredientsText => value as IngredientsText
export const asStepInstruction = (value: string): StepInstruction => value as StepInstruction

// Die rohen Eingaben des Formulars "Rezept anlegen".
export type RecipeFormValues = {
  readonly title: string
  readonly ingredients: string
  readonly steps: readonly string[]
}

// ADR-S135-4: Mit Eingaben (ein Feld ist nach ADR-S135-1 nicht leer) fragt Abbrechen nach.
export const hasRecipeInput = ({ title, ingredients, steps }: RecipeFormValues): boolean =>
  [title, ingredients, ...steps].some((text) => !isBlank(text))

export type RecipeSummary = {
  readonly id: RecipeId
  readonly title: RecipeTitle
}

// ADR-S020-1: quantity und unit sind beide null (ohne Menge) oder beide gesetzt.
export type RecipeIngredient =
  | { readonly name: IngredientName; readonly quantity: null; readonly unit: null }
  | { readonly name: IngredientName; readonly quantity: number; readonly unit: Unit }

// ADR-S027-1: Die Schrittnummer ergibt sich aus der Listenposition und ist nicht Teil des Schritts.
export type RecipeStep = {
  readonly instruction: StepInstruction
}

export type Recipe = RecipeSummary & {
  readonly ingredients: readonly RecipeIngredient[]
  readonly steps: readonly RecipeStep[]
}

// "<Menge> <Einheit> <Name>" bzw. nur "<Name>" ohne Menge (ADR-S020-1).
export function formatIngredient(ingredient: RecipeIngredient): string {
  return ingredient.quantity === null
    ? ingredient.name
    : `${String(ingredient.quantity)} ${ingredient.unit} ${ingredient.name}`
}

export type NewRecipe = {
  readonly title: RecipeTitle
  readonly ingredients: IngredientsText
  readonly steps: readonly RecipeStep[]
}

export const toNewRecipe = ({ title, ingredients, steps }: RecipeFormValues): NewRecipe => ({
  title: asRecipeTitle(title),
  ingredients: asIngredientsText(ingredients),
  steps: steps.map((instruction) => ({ instruction: asStepInstruction(instruction) })),
})

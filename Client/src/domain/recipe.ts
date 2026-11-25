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

// Deutsche Schreibweise: Dezimalkomma, keine Tausendergruppierung, höchstens 3 Nachkommastellen (Server-Grenze),
// keine Nullen am Ende.
const quantityFormat = new Intl.NumberFormat('de-DE', { useGrouping: false, maximumFractionDigits: 3 })

// Geschütztes Leerzeichen (U+00A0): Zahl und Einheit brechen nicht auseinander. Als Codepunkt-Ausdruck, weil ein
// Literal vom normalen Leerzeichen nicht zu unterscheiden ist.
const noBreakSpace = String.fromCodePoint(0xa0)

// "<Menge>␣<Einheit>" mit geschütztem Leerzeichen, z.B. "0,5 l"; geteilt von Rezept-Detailansicht und Einkaufsliste.
export const formatQuantity = (quantity: number, unit: Unit): string => `${quantityFormat.format(quantity)}${noBreakSpace}${unit}`

// "<Menge> <Einheit> <Name>" bzw. nur "<Name>" ohne Menge (ADR-S020-1).
export function formatIngredient(ingredient: RecipeIngredient): string {
  return ingredient.quantity === null
    ? ingredient.name
    : `${formatQuantity(ingredient.quantity, ingredient.unit)} ${ingredient.name}`
}

export type NewRecipe = {
  readonly title: RecipeTitle
  readonly ingredients: IngredientsText
  readonly steps: readonly RecipeStep[]
}

// ADR-S135-3: Leere Schrittfelder werden nicht mitgeschickt (Normalisierung wie der Server, ADR-S135-1).
const isSentStep = (instruction: string): boolean => !isBlank(instruction)

// ADR-S135-3: Meldungen zu Schritten keyen auf den Index in der gesendeten Liste. Das Ergebnis nennt je
// gesendetem Schritt den Index seines Formularfeldes.
export const sentStepFieldIndexes = (steps: readonly string[]): readonly number[] =>
  steps.flatMap((instruction, fieldIndex) => (isSentStep(instruction) ? [fieldIndex] : []))

// ADR-S144-1: Ordnet die Meldung je gesendetem Schritt (Index in der gesendeten Liste) dem Formularfeld zu, aus
// dem der Schritt stammt. Das Ergebnis enthält nur Felder mit Meldung, in Formularreihenfolge.
export const messagesByFieldIndex = (
  sentFieldIndexes: readonly number[],
  messageAtSentIndex: (sentIndex: number) => string | undefined,
): ReadonlyMap<number, string> =>
  new Map(sentFieldIndexes.flatMap((fieldIndex, sentIndex) => {
    const message = messageAtSentIndex(sentIndex)
    return message === undefined ? [] : [[fieldIndex, message] as const]
  }))

export const toNewRecipe = ({ title, ingredients, steps }: RecipeFormValues): NewRecipe => ({
  title: asRecipeTitle(title),
  ingredients: asIngredientsText(ingredients),
  steps: steps
    .filter(isSentStep)
    .map((instruction) => ({ instruction: asStepInstruction(instruction) })),
})

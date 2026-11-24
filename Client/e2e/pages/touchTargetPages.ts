import type { TouchTargetPageDefinition } from './touchTargetPage'
import { ingredientsTouchTargets } from './ingredientsPage'
import { plannedRecipesTouchTargets } from './plannedRecipesPage'
import { recipesTouchTargets } from './recipesPage'

// Alle Seiten der Touch-Target-Suite (ADR-S112-5, Geltungsbereich). Jede Seite trägt sich hier ein –
// anders als bei den Registries in interactionPages.ts ohne Vorbedingung, denn Bedienelemente hat jede Seite.
export const TOUCH_TARGET_PAGES: readonly TouchTargetPageDefinition[] = [
  ingredientsTouchTargets,
  recipesTouchTargets,
  plannedRecipesTouchTargets,
]

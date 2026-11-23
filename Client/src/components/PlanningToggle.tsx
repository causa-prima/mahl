import Button from '@mui/material/Button'
import PlaylistAdd from '@mui/icons-material/PlaylistAdd'
import PlaylistAddCheck from '@mui/icons-material/PlaylistAddCheck'
import type { RecipeSummary } from '../domain/recipe'
import { usePlannedRecipes, usePlanRecipe } from '../hooks/usePlannedRecipes'

// Stryker disable next-line ObjectLiteral: Layout-Wert, in jsdom nicht beobachtbar (ADR-S136-2)
const keepWidth = { flexShrink: 0 }

// Umschalter "vormerken": in Rezept-Liste und Detailansicht gleich. Solange die Vormerkungen laden, gibt es ihn nicht.
// Sichtbarer Text und Symbol tragen den Zustand; Rahmen und Füllung: UX-Guideline, Visuelle Baseline „Farbe"
// (CGU-visuelle-baseline). Der aria-label enthält den sichtbaren Text
// (Label-in-Name) und nennt das Rezept. Der vorgemerkte Zustand hat bewusst keinen Klick-Handler (Ausschalten folgt in run-4).
export default function PlanningToggle({ recipe }: Readonly<{ recipe: RecipeSummary }>) {
  const planned = usePlannedRecipes()
  const [plan] = usePlanRecipe()

  if (planned === undefined) return null
  return planned.some((p) => p.id === recipe.id) ? (
    <Button startIcon={<PlaylistAddCheck />} aria-label={`${recipe.title} vorgemerkt`} sx={keepWidth}>
      Vorgemerkt
    </Button>
  ) : (
    <Button
      variant="outlined"
      startIcon={<PlaylistAdd />}
      aria-label={`${recipe.title} vormerken`}
      onClick={() => { plan(recipe.id) }}
      sx={keepWidth}
    >
      Vormerken
    </Button>
  )
}

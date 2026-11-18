import { useNavigate } from 'react-router'
import { sentStepFieldIndexes, toNewRecipe } from '../domain/recipe'
import type { Recipe, RecipeFormValues } from '../domain/recipe'
import { createRecipe } from '../services/recipesApi'
import { useDiscardQuestion, useLeaveRelease } from './useDiscardQuestion'
import { useRecipeFieldMessages } from './useRecipeFieldMessages'
import type { SaveRejection } from './useRecipeFieldMessages'
import { useResultMutation } from './useResultMutation'

// Speichern, Verlassen-Nachfrage und Feldmeldungen des Formulars „Rezept anlegen" (ADR-S135-4, ADR-S135-6).
export function useRecipeCreation(hasInput: boolean) {
  const navigate = useNavigate()
  // `release`: Die Weiterleitung nach dem Speichern darf nicht vom Blocker aufgehalten werden. Die Zuordnung der
  // Schritte (ADR-S144-1) fährt im Fehler mit: Sie gehört zur Antwort und wechselt erst mit ihr.
  const release = useLeaveRelease()
  const [save, rejection, saving] = useResultMutation(
    (form: RecipeFormValues) => createRecipe(toNewRecipe(form)).mapErr(
      (error): SaveRejection => ({ error, sentFieldIndexes: sentStepFieldIndexes(form.steps) }),
    ),
    (created: Recipe) => {
      // Die Detailansicht lädt das Rezept selbst über die Adresse (ADR-S142-2).
      release.leaveWithoutQuestion(() => { void navigate(`/recipes/${created.id}`) })
    },
  )
  const discardQuestion = useDiscardQuestion({ hasInput, saving }, release)
  const field = useRecipeFieldMessages(rejection)
  return { save, discardQuestion, field }
}

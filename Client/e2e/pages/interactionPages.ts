import type { CreateDialogPageDefinition, DeleteWithUndoPageDefinition } from './interactionPage'
import { ingredientsCreateDialog, ingredientsDeleteWithUndo } from './ingredientsPage'
import { plannedRecipesDeleteWithUndo } from './plannedRecipesPage'

// Registries der Querschnitts-Suite (ADR-S112-5, Geltungsbereich): je Fähigkeit die Seiten, für die sie
// gilt. Eine neue Seite trägt sich in jede Registry ein, deren Vertrag (interactionPage.ts) sie erfüllt –
// interaction.spec.ts läuft dann auch gegen sie, statt nachgebaut zu werden. Die Touch-Target-Suite hat
// eine eigene Registry (touchTargetPages.ts).

// Die Vorgemerkt-Seite hat keinen Anlege-Dialog: Vorgemerkt wird über den Umschalter in Rezept-Liste und
// Detailansicht (features/planned-recipes.feature, Querschnitts-Verträge).
export const CREATE_DIALOG_PAGES: readonly CreateDialogPageDefinition[] = [ingredientsCreateDialog]

export const DELETE_WITH_UNDO_PAGES: readonly DeleteWithUndoPageDefinition[] = [
  ingredientsDeleteWithUndo,
  plannedRecipesDeleteWithUndo,
]

// Was geteiltes Listenverhalten („Löschen mit Rückgängig", UndoToast) von einem Element braucht: eine
// Kennung. Bewusst ein ungebrandeter Obertyp – IngredientId und RecipeId sind beide Strings und passen hinein.
export type WithId = { readonly id: string }

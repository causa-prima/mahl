// Domänentypen der Zutat – getrennt vom HTTP-Service, damit Hooks und Seiten für reine Typen nicht am
// Transportmodul hängen. Die Transporttypen (Antwort-Bodies, CreateIngredientResult) bleiben in
// services/ingredientsApi.ts.

// Nominale Brands (ADR-S112-4): Sie machen gleichartige Strings unverwechselbar – etwa in
// restoreIngredient(id, name, baseUnit) – und prüfen keine Regeln; die setzt das Backend durch.
// Vergeben werden sie an der API-Grenze: für Antworten durch den JSON-Cast im Service, für
// Eingaben durch die as…-Funktionen.
export type IngredientId = string & { readonly __brand: 'IngredientId' }
export type IngredientName = string & { readonly __brand: 'IngredientName' }
export type Unit = string & { readonly __brand: 'Unit' }
export type ETag = string & { readonly __brand: 'ETag' }

export const asIngredientId = (value: string): IngredientId => value as IngredientId
export const asIngredientName = (value: string): IngredientName => value as IngredientName
export const asUnit = (value: string): Unit => value as Unit
export const asETag = (value: string): ETag => value as ETag

export type Ingredient = {
  readonly id: IngredientId
  readonly name: IngredientName
  readonly baseUnit: Unit
  // ADR-S108-1: per-Zeile xmin-ETag (hex, "{xmin:x8}") aus dem GET-Body – die If-Match-Quelle
  // fürs Löschen einer aus der Liste geladenen Zutat. Eigentlich ein Protokollwert, gehört aber zur
  // Listenzeile, die gelöscht wird – deshalb hier und nicht im Service.
  readonly etag: ETag
}

export type NewIngredient = {
  readonly name: IngredientName
  readonly baseUnit: Unit
}

// ADR-S056-1: Domain-Fehler reisen als kind-getaggte Discriminated Union durch den
// Result-Erfolgspfad und werden in der Komponente via match auf das Feld abgebildet.
export type ApiError =
  // ADR-S090-1: 422-Validierungsfehler sind feld-keyed (Feld -> Meldungen), RFC 9457.
  // Partial: ein beliebiges Feld kann fehlen (z.B. nur defaultUnit-Fehler) -> der
  // Lookup eines abwesenden Keys ist zur Laufzeit ehrlich undefined.
  | { readonly kind: 'FieldErrors'; readonly fields: Partial<Readonly<Record<string, readonly string[]>>> }
  // Netzwerk/sonstige Fehler (GET-Pfad, POST-catch) tragen eine technische Meldung.
  | { readonly kind: 'Unexpected'; readonly message: string }

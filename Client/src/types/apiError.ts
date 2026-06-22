// ADR-S056-1: Domain-Fehler reisen als kind-getaggte Discriminated Union durch den
// Result-Erfolgspfad und werden in der Komponente via match auf das Feld abgebildet.
export type ApiError =
  // ADR-S090-1: 422-Validierungsfehler sind feld-keyed (Feld -> Meldungen), RFC 9457.
  // Ein beliebiges Feld kann fehlen (z.B. nur defaultUnit-Fehler); dank
  // noUncheckedIndexedAccess (tsconfig.app.json) ist der Lookup eines abwesenden
  // Keys zur Laufzeit ehrlich `… | undefined` -> der `?.`-Guard an der Zugriffsstelle
  // ist echt nötig (kein eslint-disable).
  | { readonly kind: 'FieldErrors'; readonly fields: Readonly<Record<string, readonly string[]>> }
  // Netzwerk/sonstige Fehler (GET-Pfad, POST-catch) tragen eine technische Meldung.
  | { readonly kind: 'Unexpected'; readonly message: string }

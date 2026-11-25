// Prüfung des rohen Textes eines Elements. Playwrights String-Matcher (getByText, toHaveText('x'))
// normalisieren Leerraum und entfernen Leerzeichen ohne Breite – sie könnten "rote  Linsen" nicht von
// "rote Linsen" unterscheiden. Lokalisiert wird deshalb per String, geprüft wird per verankerter Regex.
export const escapeRegExp = (text: string): string => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

// Ein Leerzeichen der Erwartung trifft auch ein geschütztes (U+00A0, zwischen Zahl und Einheit einer Menge): Beide
// sehen gleich aus, und die Szenarien schreiben „250 g“. Ob es geschützt ist, prüfen die Komponententests.
const spaceOrNoBreakSpace = `[ ${String.fromCodePoint(0xa0)}]`

export const exactly = (text: string): RegExp =>
  new RegExp(`^${escapeRegExp(text).replaceAll(' ', spaceOrNoBreakSpace)}$`)

// Prüfung des rohen Textes eines Elements. Playwrights String-Matcher (getByText, toHaveText('x'))
// normalisieren Leerraum und entfernen Leerzeichen ohne Breite – sie könnten "rote  Linsen" nicht von
// "rote Linsen" unterscheiden. Lokalisiert wird deshalb per String, geprüft wird per verankerter Regex.
export const escapeRegExp = (text: string): string => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

export const exactly = (text: string): RegExp => new RegExp(`^${escapeRegExp(text)}$`)

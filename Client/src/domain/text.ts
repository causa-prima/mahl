// Was beim Normalisieren wegfällt (ADR-S135-1): jedes Unicode-Leerzeichen sowie die unsichtbaren Zeichen
// Leerzeichen ohne Breite (U+200B), weiches Trennzeichen (U+00AD), Wortverbinder (U+2060) und Byte-Order-Mark
// (U+FEFF). Ändert die ADR die Liste, ändert sie sich hier und auf dem Server.
const vanishingCharacters = /[\p{White_Space}\u{200B}\u{00AD}\u{2060}\u{FEFF}]/gu

// ADR-S135-1: Ein Text ohne sichtbaren Inhalt gilt als leer – der Client entscheidet so gleich wie der Server.
export const isBlank = (text: string): boolean => text.replace(vanishingCharacters, '') === ''

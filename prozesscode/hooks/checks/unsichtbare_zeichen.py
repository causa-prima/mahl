"""Unsichtbare Zeichen als Literal in C#-/TypeScript-Tests (blockierend).

Warum (CM-S047-1, Hotspot unsichtbare Zeichen): CGG-naming verlangt für Leerraum außer dem
ASCII-Leerzeichen, unsichtbare und kombinierende Zeichen den Codepunkt-Ausdruck. Die Regel war
bekannt und wurde trotzdem gebrochen: Ein `'\\u200B'` im Tool-Aufruf kommt schon im Hook-Input
als echtes Zeichen an (Gegenprobe S149; vermutlich beim JSON-Dekodieren aufgelöst, ungeprüft). Ein Editor, der es entfernt, verwandelt den Test still in
einen Leer-String-Test, der die Normalisierung nicht mehr prüft. Deshalb prüft der Check genau
das, was der Hook-Input trägt: das Literal.

Geltungsbereich: Test- und Spec-Dateien in C# und TypeScript – dort entstehen solche Zeichen als
Testeingaben. Produktcode und Python-Tests (deren Meldungstexte „⚠️" tragen) nicht.

Bewusst ohne Ausnahme für Emoji-Bestandteile (Variationsselektor, ZWJ, Keycap, Tag-Zeichen): Ein
Nullbreiten-Verbinder ist außerhalb eines Emojis genau die gefährliche Testeingabe, und eine
Ausnahme „nur innerhalb einer Emoji-Sequenz" wäre mehr Regel als Bedarf – die C#/TS-Tests
enthalten kein Emoji (S149 geprüft). Ein Emoji im Test steht deshalb wie jedes andere unsichtbare
Zeichen als Codepunkt-Ausdruck.
"""
import unicodedata

from .common import HookInput

# Unicode-Kategorien ohne sichtbares Glyph: Leerraum, Format- und Steuerzeichen, kombinierende Zeichen.
_UNSICHTBARE_KATEGORIEN = {"Zs", "Zl", "Zp", "Cf", "Cc", "Mn", "Me"}
_ERLAUBT = {" ", "\t", "\n", "\r"}


def _unsichtbar(zeichen: str) -> bool:
    return zeichen not in _ERLAUBT and unicodedata.category(zeichen) in _UNSICHTBARE_KATEGORIEN


def _beschreibung(zeichen: str) -> str:
    name = unicodedata.name(zeichen, "(Steuerzeichen)")
    return f"U+{ord(zeichen):04X} {name}"


def _funde(text: str) -> list[str]:
    """Je Zeile jedes unsichtbare Zeichen einmal, in Reihenfolge des Auftretens.

    `split("\\n")` statt `splitlines()`: Letzteres trennt auch an U+0085, U+2028/2029 und
    `\\v`/`\\f` – genau die Zeichen, die hier gefunden werden sollen, verschwänden als Zeilenende.
    """
    funde = []
    for nummer, zeile in enumerate(text.split("\n"), start=1):
        gesehen = dict.fromkeys(z for z in zeile if _unsichtbar(z))
        funde += [f"  - Zeile {nummer}: {_beschreibung(z)}" for z in gesehen]
    return funde


def check(inp: HookInput) -> list[str]:
    if not (inp.is_test and (inp.is_cs or inp.is_ts)):
        return []
    funde = _funde(inp.new_content)
    return [MELDUNG.format(funde="\n".join(funde))] if funde else []


MELDUNG = (
    "⛔ Unsichtbares Zeichen als Literal im Test (blockierend):\n{funde}\n"
    "Als Codepunkt-Ausdruck schreiben: `String.fromCodePoint(0x200B)` (TypeScript) bzw. "
    "`char.ConvertFromUtf32(0x200B)` (C#) – nicht als Literal und nicht als `\\u`-Escape, den die "
    "Werkzeugkette beim Schreiben zum Literal auflöst. Zeile = Zeile im neuen Text dieses "
    "Edits. Regel: docs/guidelines/coding-guideline-general.md#CGG-naming"
)

"""Testnamen samt Zeilenbereich aus Test-Dateien ziehen (C# xunit, TypeScript vitest, Python pytest).

Zweck: Wer einen Test ergänzt, will meist nur wissen, *was schon da ist* und *wo* – und liest
dafür heute die ganze Datei. Gemessen sind rund zwei Drittel des Lesens auf Code- und
Testdateien reine Orientierung, nicht der vom Harness erzwungene Read-vor-Edit. Eine Inventur
beantwortet dieselbe Frage für einen Bruchteil, und der **Zeilenbereich** macht den Folge-Read
gezielt (`Read` mit `offset`/`limit`) statt vollständig.

Gegenüber LSP `documentSymbol`: Das liefert nur Startzeilen und listet zusätzlich jede
Property/Konstante mit auf – für eine große Testdatei ein Vielfaches dieser Ausgabe. Für
C# steht ohnehin kein Language-Server bereit.

Blockende per Klammerzählung: TypeScript zählt `{}` und `()`, eine C#-Methode nur ihren Rumpf in
`{}` – oder sie endet am `;` eines Ausdrucks ohne Rumpf. Zeichenketten und Zeilenkommentare werden vorher
ausgeblendet, damit eine Klammer in einem Text-Literal die Zählung nicht verschiebt. Python hat
keine Blockklammern – dort ergibt sich das Ende aus der Einrückung.
"""
import re
from dataclasses import dataclass
from pathlib import Path

# C#: xunit-Testmethode = Attribut, dann (ggf. nach weiteren Attributen) die Signatur.
CS_ATTRIBUTE = re.compile(r"^\s*\[\s*(Fact|Theory)\b")
CS_METHOD = re.compile(r"^\s*(?:public|private|internal|protected)[\w\s<>,\[\]]*?\s(\w+)\s*\(")

# TypeScript/JS: describe/it/test, ggf. mit Modifikatoren (`.only`, `.skip`, `.each`).
# Die Modifikatoren werden mitgefangen, weil Playwright Suiten als `test.describe(…)` schreibt –
# dort steht die Art im Modifikator, nicht im ersten Wort.
# Die optionale Gruppe fängt die zweistufige Form `it.each([…])('name', …)` ab, bei der der
# Name erst in der ZWEITEN Argumentliste steht.
TS_BLOCK = re.compile(
    r"""^(\s*)(describe|it|test)\b((?:\.\w+)*)\s*\((?:.*\)\s*\(\s*)?\s*(['"`])(.+?)\4"""
)
# Dieselbe Form mit mehrzeiliger Tabelle: `it.each([` öffnet, der Name steht erst in der Zeile,
# die die Tabelle schließt (`])('name', …)`).
TS_EACH_OPEN = re.compile(r"^(\s*)(it|test)((?:\.\w+)*\.each)\s*\(")
TS_EACH_NAME = re.compile(r"""^\s*\]\s*\)\s*\(\s*(['"`])(.+?)\1""")

# Python/pytest: Testfunktion = `def test_…`. Async-Tests eingeschlossen.
PY_TEST = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w*)\s*\(")

_LINE_COMMENT = re.compile(r"//.*$")
_LITERAL = re.compile(r"'[^']*'|\"[^\"]*\"|`[^`]*`")


@dataclass
class Eintrag:
    """Ein Test oder eine Suite mit ihrem Zeilenbereich (1-basiert, beide inklusive)."""
    name: str
    start: int
    end: int
    tiefe: int
    ist_suite: bool

    @property
    def zeilen(self) -> int:
        return self.end - self.start + 1


def _ohne_literale(line: str) -> str:
    """Blendet Zeichenketten und Zeilenkommentare aus, damit nur echte Klammern zählen."""
    return _LINE_COMMENT.sub("", _LITERAL.sub("''", line))


# Klammerpaare, die die Blockzählung berücksichtigt. TypeScript braucht beide: `it('…', () => {…})`
# öffnet mit `(`. Ein C#-Methodenrumpf dagegen ist allein durch `{}` begrenzt – mit `()` endete der
# Block bei einer mehrzeiligen Parameterliste schon an deren `)`, vor dem Rumpf.
ALLE_KLAMMERN = ("{}", "()")
NUR_GESCHWEIFTE = ("{}",)
# Was in einer C#-Methode ab der Signatur zuerst kommt: `{` öffnet den Rumpf, `;` beendet einen Ausdruck.
_RUMPF_ODER_ENDE = re.compile(r"[{;]")


def block_ende(lines: list[str], start_idx: int, paare: tuple[str, ...] = ALLE_KLAMMERN) -> int:
    """Letzte Zeile (0-basiert) des bei `start_idx` beginnenden Blocks, per Klammerzählung über `paare`.

    Öffnet der Block nie eine Klammer, reicht er bis zum Dateiende – wer das nicht will, grenzt
    vorher selbst ab (wie `_cs_methoden_ende` für Methoden ohne Rumpf).
    """
    tiefe = 0
    geoeffnet = False
    for idx in range(start_idx, len(lines)):
        sauber = _ohne_literale(lines[idx])
        tiefe += sum(sauber.count(auf) - sauber.count(zu) for auf, zu in paare)
        if tiefe > 0:
            geoeffnet = True
        elif geoeffnet:
            return idx
    return len(lines) - 1


def _cs_methoden_ende(lines: list[str], signatur_idx: int) -> int:
    """Letzte Zeile (0-basiert) einer C#-Methode ab ihrer Signatur.

    Steht vor der ersten `{` ein `;`, ist es ein Ausdruck ohne Rumpf (`=> …;`), der dort endet –
    auch über mehrere Zeilen. Sonst begrenzt der Rumpf in `{}` die Methode.
    """
    for idx in range(signatur_idx, len(lines)):
        erstes = _RUMPF_ODER_ENDE.search(_ohne_literale(lines[idx]))
        if erstes:
            return idx if erstes.group() == ";" else block_ende(lines, idx, NUR_GESCHWEIFTE)
    return len(lines) - 1


def parse_csharp(lines: list[str]) -> list[Eintrag]:
    """xunit-Testmethoden: `[Fact]`/`[Theory]`, dann die nächste Signatur."""
    eintraege = []
    for idx, line in enumerate(lines):
        if not CS_ATTRIBUTE.match(line):
            continue
        for folge in range(idx + 1, min(idx + 6, len(lines))):
            treffer = CS_METHOD.match(lines[folge])
            if treffer:
                eintraege.append(Eintrag(treffer.group(1), idx + 1,
                                         _cs_methoden_ende(lines, folge) + 1, 0, False))
                break
    return eintraege


def parse_typescript(lines: list[str]) -> list[Eintrag]:
    """`describe`/`test.describe` als Suite, `it`/`test` als Test; Verschachtelung über die Einrückung."""
    eintraege = []
    for idx, line in enumerate(lines):
        treffer = TS_BLOCK.match(line)
        if treffer:
            einrueckung, art, modifikatoren, _, name = treffer.groups()
            ist_suite = art == "describe" or ".describe" in modifikatoren
            eintraege.append(Eintrag(name, idx + 1, block_ende(lines, idx) + 1,
                                     len(einrueckung) // 2, ist_suite))
            continue
        offen = TS_EACH_OPEN.match(line)
        if offen:
            ende = block_ende(lines, idx)
            name = next((m.group(2) for folge in lines[idx + 1:ende + 1]
                         if (m := TS_EACH_NAME.match(folge))), None)
            if name is not None:
                eintraege.append(Eintrag(name, idx + 1, ende + 1, len(offen.group(1)) // 2, False))
    return eintraege


def _einrueckung(line: str) -> int:
    return len(line) - len(line.lstrip())


def _python_block_ende(lines: list[str], start_idx: int, tiefe: int) -> int:
    """Letzte Zeile (0-basiert) einer Python-Definition, bestimmt über die Einrückung.

    Der Block endet vor der nächsten nicht-leeren Zeile, die höchstens so weit eingerückt ist
    wie das `def` selbst. Leerzeilen zählen nicht als Ende – sie stehen regelmäßig *innerhalb*
    eines Tests; deshalb wird bis zur letzten inhaltlichen Zeile zurückgegangen.
    """
    letzte_inhaltliche = start_idx
    for idx in range(start_idx + 1, len(lines)):
        if not lines[idx].strip():
            continue
        if _einrueckung(lines[idx]) <= tiefe:
            return letzte_inhaltliche
        letzte_inhaltliche = idx
    return letzte_inhaltliche


def parse_python(lines: list[str]) -> list[Eintrag]:
    """pytest-Tests: `def test_…` auf Modulebene, Dekoratoren eingeschlossen.

    Nur `test_`-Präfixe – Hilfsfunktionen und Fixtures sind kein Inventar-Gegenstand (dieselbe
    Auswahl, die pytest selbst trifft). Testklassen kommen im Bestand nicht vor und werden
    deshalb nicht erkannt; sie fielen als `def test_…` in ihrem Rumpf trotzdem auf.
    """
    eintraege = []
    for idx, line in enumerate(lines):
        treffer = PY_TEST.match(line)
        if not treffer:
            continue
        tiefe = _einrueckung(line)
        start = idx
        # Dekoratoren gehören zum Test – ohne sie schnitte ein Folge-Read sie ab.
        while start > 0 and lines[start - 1].lstrip().startswith("@"):
            start -= 1
        eintraege.append(Eintrag(treffer.group(1), start + 1,
                                 _python_block_ende(lines, idx, tiefe) + 1, 0, False))
    return eintraege


def inventar(path: Path) -> list[Eintrag]:
    """Einträge der Datei, nach Startzeile sortiert. Unbekannte Endung → leer."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if path.suffix == ".cs":
        eintraege = parse_csharp(lines)
    elif path.suffix in (".ts", ".tsx", ".js", ".jsx"):
        eintraege = parse_typescript(lines)
    elif path.suffix == ".py":
        eintraege = parse_python(lines)
    else:
        return []
    return sorted(eintraege, key=lambda e: e.start)


def zeilenzahl(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())

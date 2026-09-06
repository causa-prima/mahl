"""Testnamen samt Zeilenbereich aus Test-Dateien ziehen (C# xunit, TypeScript vitest).

Zweck: Wer einen Test ergänzt, will meist nur wissen, *was schon da ist* und *wo* – und liest
dafür heute die ganze Datei. Gemessen sind rund zwei Drittel des Lesens auf Code- und
Testdateien reine Orientierung, nicht der vom Harness erzwungene Read-vor-Edit. Eine Inventur
beantwortet dieselbe Frage für einen Bruchteil, und der **Zeilenbereich** macht den Folge-Read
gezielt (`Read` mit `offset`/`limit`) statt vollständig.

Gegenüber LSP `documentSymbol`: Das liefert nur Startzeilen und listet zusätzlich jede
Property/Konstante mit auf – für eine große Testdatei ein Vielfaches dieser Ausgabe. Für
C# steht ohnehin kein Language-Server bereit.

Blockende per Klammerzählung. Zeichenketten und Zeilenkommentare werden vorher ausgeblendet,
damit eine Klammer in einem Text-Literal die Zählung nicht verschiebt.
"""
import re
from dataclasses import dataclass
from pathlib import Path

# C#: xunit-Testmethode = Attribut, dann (ggf. nach weiteren Attributen) die Signatur.
CS_ATTRIBUTE = re.compile(r"^\s*\[\s*(Fact|Theory)\b")
CS_METHOD = re.compile(r"^\s*(?:public|private|internal|protected)[\w\s<>,\[\]]*?\s(\w+)\s*\(")

# TypeScript/JS: describe/it/test, ggf. mit Modifikatoren (`.only`, `.skip`, `.each`).
# Die optionale Gruppe fängt die zweistufige Form `it.each([…])('name', …)` ab, bei der der
# Name erst in der ZWEITEN Argumentliste steht.
TS_BLOCK = re.compile(
    r"""^(\s*)(describe|it|test)\b(?:\.\w+)*\s*\((?:.*\)\s*\(\s*)?\s*(['"`])(.+?)\3"""
)

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


def block_ende(lines: list[str], start_idx: int) -> int:
    """Letzte Zeile (0-basiert) des bei `start_idx` beginnenden Blocks, per Klammerzählung.

    Öffnet der Block nie eine Klammer (etwa eine abstrakte Deklaration), ist er einzeilig.
    """
    tiefe = 0
    geoeffnet = False
    for idx in range(start_idx, len(lines)):
        sauber = _ohne_literale(lines[idx])
        tiefe += sauber.count("{") + sauber.count("(")
        tiefe -= sauber.count("}") + sauber.count(")")
        if tiefe > 0:
            geoeffnet = True
        elif geoeffnet:
            return idx
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
                                         block_ende(lines, folge) + 1, 0, False))
                break
    return eintraege


def parse_typescript(lines: list[str]) -> list[Eintrag]:
    """`describe` als Suite, `it`/`test` als Test; Verschachtelung über die Einrückung."""
    eintraege = []
    for idx, line in enumerate(lines):
        treffer = TS_BLOCK.match(line)
        if not treffer:
            continue
        einrueckung, art, _, name = treffer.groups()
        eintraege.append(Eintrag(name, idx + 1, block_ende(lines, idx) + 1,
                                 len(einrueckung) // 2, art == "describe"))
    return eintraege


def inventar(path: Path) -> list[Eintrag]:
    """Einträge der Datei, nach Startzeile sortiert. Unbekannte Endung → leer."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if path.suffix == ".cs":
        eintraege = parse_csharp(lines)
    elif path.suffix in (".ts", ".tsx", ".js", ".jsx"):
        eintraege = parse_typescript(lines)
    else:
        return []
    return sorted(eintraege, key=lambda e: e.start)


def zeilenzahl(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())

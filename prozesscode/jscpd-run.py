#!/usr/bin/env python3
"""
jscpd (Duplikat-Analyse, nativ über npm) – gemessen gegen eine Baseline, kein Gate.

Verwendung:
  python3 -m prozesscode.jscpd-run           # nur der Zuwachs gegenüber BEKANNTE_KLONE
  python3 -m prozesscode.jscpd-run --verbose # vollständiger Output inkl. Statistik-Tabelle

**Warum eine Baseline:** Der Bestand trägt Klone, die sich nicht auflösen lassen (unten je
einzeln begründet). Meldete der Wrapper sie bei jedem Lauf als ✗, wäre er dauerhaft rot – und
ein dauerhaft rotes Werkzeug wird ignoriert, dann auch bei einem echten Fund. Die Politik steht
in `coding-guideline-python.md`, „Duplikate: gemessen, nicht als Gate"; hier steht ihre
Durchsetzung. Neu ist ein Klon, wenn sein Dateipaar unbekannt ist oder häufiger auftritt als
in der Baseline vermerkt.

Pflege: Löst sich ein Klon auf, verschwindet sein Eintrag hier – der Lauf sagt es an. Ein neuer
Eintrag gehört nur dann hierher, wenn der Klon **nachweislich** nicht extrahierbar ist; sonst
ist der Fund selbst die Aufgabe.
"""
import argparse
import re
import sys
from collections import Counter

from ._util import run_npm
from ._wrapper_output import emit, strip_noise

# Klone, die der Bestand kennt: Dateipaar (sortiert) → Grund, warum er stehen bleiben darf.
# Ein Eintrag deckt genau einen Klon zwischen diesen beiden Dateien ab.
#
# Bis S129 standen hier fünf weitere Einträge: derselbe `sys.path.insert`-Bootstrap in der
# ganzen Hook-Familie. Er war nicht auslagerbar, solange die Hooks unter `.claude/hooks/`
# lagen – ein Bootstrap muss dem ersten Import vorausgehen und kann deshalb nicht aus einem
# Modul kommen, das er selbst erst auffindbar macht. Im Paket findet der relative Import sein
# Ziel ohne Eingriff; die fünf Klone sind damit ersatzlos entfallen, nicht unterdrückt.
BEKANNTE_KLONE: dict[tuple[str, str], str] = {
    ("prozesscode/dotnet-stryker.py", "prozesscode/stryker-frontend.py"):
        "vier Zeilen Kommentar über drei Zeilen Code, mit der beide Wrapper ihren Rohoutput "
        "nach derselben Regel zeigen – ein Helfer für drei Zeilen wäre teurer als die Kopie",
}

# Ausnahme von „ein Eintrag deckt einen Klon": Liegen zwischen zwei Dateien mehrere getrennte
# Fundstellen, steht hier die erwartete Anzahl. Derzeit leer – der zweite Fund im
# Stryker-Paar (der gemeinsame Importblock) entfiel mit dem Paket-Umzug (S129).
_MEHRFACH: dict[tuple[str, str], int] = {}

# Statistik-Tabelle (Rahmen + Zellen), Laufzeit und die Spenden-/Werbezeilen am Ende:
# alles ohne Aussagewert für „gibt es Duplikate?".
_JSCPD_CHROME = re.compile(r"^[\x1b\[\d;m]*[┌├└│]|^\x1b\[90mtime:|💡|🎩|💖")
_CLONE_COUNT = re.compile(r"Found (\d+) clones?\.")
_ANSI = re.compile(r"\x1b\[[\d;]*m")
# Eine Fundstelle: Pfad, dann der Zeilenbereich in eckigen Klammern. Der Pfad steht relativ
# zu Client/ (dort läuft npm), also mit führendem `../`.
_FUNDSTELLE = re.compile(r"^\s*(?:- )?(\S+) \[\d+:\d+ - \d+:\d+\]")

_PARSER_HINWEIS = ("✗ jscpd meldet {gemeldet} Klon(e), erkannt wurden {erkannt} – das "
                   "Ausgabeformat hat sich geändert.\n"
                   "  Parser `_FUNDSTELLE` in prozesscode/jscpd-run.py nachziehen; bis "
                   "dahin trägt kein Verdikt.")


def _fundstellen(ausgabe: str) -> list[str]:
    """Alle genannten Dateien in Reihenfolge – je zwei bilden einen Klon."""
    return [m.group(1).removeprefix("../") for zeile in _ANSI.sub("", ausgabe).splitlines()
            if (m := _FUNDSTELLE.match(zeile))]


def klon_paare(fundstellen: list[str]) -> list[tuple[str, str]]:
    """Die Dateipaare der Klone, jedes Paar sortiert – die Nennungsreihenfolge innerhalb eines
    Klons ist beliebig und bezeichnet denselben Fund."""
    return [tuple(sorted(fundstellen[i:i + 2])) for i in range(0, len(fundstellen) - 1, 2)]


def neue_klone(paare: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Paare über die Baseline hinaus – unbekannte, und bekannte in Überzahl."""
    offen = {paar: _MEHRFACH.get(paar, 1) for paar in BEKANNTE_KLONE}
    neu = []
    for paar in paare:
        if offen.get(paar):
            offen[paar] -= 1
        else:
            neu.append(paar)
    return neu


def entfallene_klone(paare: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Bekannte Paare, die seltener auftreten als der Bestand erwartet.

    Die Unterzahl zählt mit, nicht nur das vollständige Fehlen: Ein `_MEHRFACH`-Eintrag,
    dessen zweiter Fund verschwunden ist, bliebe sonst als zu hohe Erwartung stehen – und
    deckte künftig einen echten neuen Klon, ohne dass irgendetwas anschlüge.
    """
    gezaehlt = Counter(paare)
    return [paar for paar in BEKANNTE_KLONE if gezaehlt[paar] < _MEHRFACH.get(paar, 1)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output inkl. Statistik-Tabelle und npm-Header")
    args = parser.parse_args(argv)

    output, exit_code = run_npm(["run", "lint:duplicates"])

    gemeldet = _CLONE_COUNT.search(output)
    if not gemeldet:
        # Ohne Abschlusszeile hat jscpd nicht zu Ende gearbeitet – dann trägt nur das Original.
        print(output.rstrip())
        return exit_code or 1

    # Gezählt werden die Fundstellen, nicht die Paare: Lieferte ein geändertes Format drei
    # Zeilen je Klon, käme die Paarzahl zufällig hin und der Fehlgriff bliebe stumm.
    fundstellen = _fundstellen(output)
    if len(fundstellen) != 2 * int(gemeldet.group(1)):
        print(_PARSER_HINWEIS.format(gemeldet=gemeldet.group(1), erkannt=len(fundstellen) // 2))
        return 1

    paare = klon_paare(fundstellen)
    neu = neue_klone(paare)
    if neu:
        # Die Fundstellen selbst sind die Analyse-Information – Tabelle und Werbung nicht.
        zeilen = [z for z in strip_noise(output, _JSCPD_CHROME) if z.strip()]
        emit(verbose=args.verbose, output=output, details=zeilen,
             verdict=f"✗ jscpd: {len(neu)} neue(s) Duplikat(e) – "
                     + ", ".join(f"{a} ↔ {b}" for a, b in neu))
        return 1

    verdikt = f"✓ jscpd: keine neuen Duplikate ({len(paare)} bekannte im Bestand)"
    entfallen = entfallene_klone(paare)
    if entfallen:
        verdikt += (f"; {len(entfallen)} davon aufgelöst – Baseline in jscpd-run.py kürzen: "
                    + ", ".join(f"{a} ↔ {b}" for a, b in entfallen))
    emit(verbose=args.verbose, output=output, verdict=verdikt)
    return 0


if __name__ == "__main__":
    sys.exit(main())

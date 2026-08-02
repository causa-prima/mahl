#!/usr/bin/env python3
"""Welche Tests stehen in einer Testdatei – und in welchen Zeilen?

Statt eine gewachsene Testdatei vollständig zu lesen, um zu sehen was es schon gibt: die
Inventur lesen, dann gezielt die interessante Stelle mit `Read` (`offset`/`limit`) nachladen.

Beispiele:
  python3 .claude/scripts/test-inventory.py Client/src/pages/IngredientsPage.test.tsx
  python3 .claude/scripts/test-inventory.py Server.Tests/IngredientsEndpointsTests.cs
  python3 .claude/scripts/test-inventory.py Client/e2e/*.spec.ts --names
  python3 .claude/scripts/test-inventory.py <datei> --grep Reaktivierung
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _test_inventory import inventar, zeilenzahl  # noqa: E402


def zeige(path: Path, nur_namen: bool, muster: str | None) -> int:
    """Gibt die Inventur einer Datei aus. Liefert die Zahl der gefundenen Tests."""
    eintraege = inventar(path)
    if not eintraege:
        print(f"{path}: keine Tests erkannt (unterstützt: .cs, .ts/.tsx/.js/.jsx)")
        return 0

    if muster:
        gesucht = muster.lower()
        eintraege = [e for e in eintraege if gesucht in e.name.lower()]

    tests = [e for e in eintraege if not e.ist_suite]
    suiten = [e for e in eintraege if e.ist_suite]
    kopf = f"{path}  ({zeilenzahl(path)} Zeilen, {len(tests)} Tests"
    print(f"{kopf}{f', {len(suiten)} Suiten' if suiten else ''})")

    for eintrag in eintraege:
        einzug = "  " + "  " * eintrag.tiefe
        if nur_namen:
            print(f"{einzug}{eintrag.name}")
            continue
        bereich = f"{eintrag.start}-{eintrag.end}"
        markierung = "▸" if eintrag.ist_suite else " "
        print(f"{einzug}{markierung} {bereich:<12} {eintrag.zeilen:>4} Z.  {eintrag.name}")

    return len(tests)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Testnamen samt Zeilenbereich – als Ersatz für das Lesen der ganzen Datei.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("dateien", nargs="+", help="Test-Dateien (.cs, .ts, .tsx, .js, .jsx)")
    parser.add_argument("--names", action="store_true",
                        help="nur Namen, ohne Zeilenbereiche (noch kompakter)")
    parser.add_argument("--grep", metavar="TEXT",
                        help="nur Einträge, deren Name TEXT enthält (Groß-/Kleinschreibung egal)")
    args = parser.parse_args()

    fehlend = [d for d in args.dateien if not Path(d).is_file()]
    if fehlend:
        print(f"Nicht gefunden: {', '.join(fehlend)}", file=sys.stderr)
        sys.exit(1)

    for i, datei in enumerate(args.dateien):
        if i:
            print()
        zeige(Path(datei), args.names, args.grep)


if __name__ == "__main__":
    main()

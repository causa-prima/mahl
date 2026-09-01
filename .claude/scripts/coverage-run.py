#!/usr/bin/env python3
"""
Testabdeckung des Prozess-Codes unter `.claude/**` – als Metrik, nicht als Gate.

Verwendung:
  python3 .claude/scripts/coverage-run.py            # Gesamtwert + die schwächsten Module
  python3 .claude/scripts/coverage-run.py --verbose  # vollständige Tabelle

**Warum kein Gate:** siehe `coding-guideline-python.md`, „Was nicht gilt".

**Wofür die Zahl dann gut ist:** als Suchhilfe. Beim ersten Lauf (S128, 73 % über 11.735
Statements) zeigte sie, dass die Kernmodule bei 90–99 % liegen, sämtliche Wrapper-Scripts aber
bei 0 % – eine Information, die kein anderes Werkzeug liefert.

Der Lauf dauert rund 75 s (gegen 43 s ohne Coverage) und gehört deshalb in die Retro oder in
eine gezielte Sichtung, nicht in einen Hook.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _wrapper_output import emit

ROOT = Path(__file__).resolve().parent.parent.parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
TESTS = ".claude/hooks/tests/"
MESSPFADE = (".claude/scripts", ".claude/hooks")

# Ab hier lohnt der Blick. Keine Schwelle im Sinne eines Gates – eine Anzeigegrenze, damit die
# 90-%-Module den Bericht nicht zuschütten und das Wesentliche verdecken.
ZEIGEN_UNTER = 60

_ZEILE = re.compile(r"^(\S+\.py)\s+(\d+)\s+(\d+)\s+(\d+)%")
_TOTAL = re.compile(r"^TOTAL\s+\d+\s+\d+\s+(\d+)%", re.M)

_FEHLT = (
    "✗ Werkzeug-Umgebung fehlt ({pfad}).\n"
    "  Herstellen:\n"
    "    python3 -m venv .venv\n"
    "    .venv/bin/pip install -r requirements-dev.txt"
)


def _venv_vorhanden() -> bool:
    return VENV_PY.is_file()


def _laufe(*befehl: str) -> subprocess.CompletedProcess:
    return subprocess.run(befehl, capture_output=True, text=True, cwd=ROOT)


def module_unter(ausgabe: str, grenze: int) -> list[tuple[str, int]]:
    """(Modul, Prozent) unter der Anzeigegrenze – ungetestete zuerst, dann aufsteigend."""
    treffer = [(m.group(1), int(m.group(4))) for m in
               (_ZEILE.match(z) for z in ausgabe.splitlines()) if m]
    return sorted([t for t in treffer if t[1] < grenze], key=lambda t: t[1])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="Vollständige Tabelle")
    args = parser.parse_args(argv)

    if not _venv_vorhanden():
        print(_FEHLT.format(pfad=VENV_PY))
        return 2

    ergebnis = _laufe(str(VENV_PY), "-m", "pytest", TESTS, "-q",
                      *[f"--cov={p}" for p in MESSPFADE], "--cov-report=term")
    ausgabe = ergebnis.stdout + ergebnis.stderr

    # Bei roten Tests ist die Zahl bedeutungslos: Nicht gelaufene Tests decken nichts ab, und
    # der Wert läse sich wie ein Befund über den Code statt über den kaputten Lauf.
    if ergebnis.returncode != 0:
        emit(verbose=args.verbose, output=ausgabe,
             verdict="✗ Testlauf rot – die Coverage-Zahl sagt nichts, bis die Tests grün sind")
        return 1

    gesamt = _TOTAL.search(ausgabe)
    schwach = module_unter(ausgabe, ZEIGEN_UNTER)
    ungetestet = [m for m, p in schwach if p == 0]

    zeilen = [f"  {p:3}%  {m}" for m, p in schwach]
    kopf = f"✓ Coverage Prozess-Code: {gesamt.group(1) if gesamt else '?'} %"
    if ungetestet:
        kopf += f" – {len(ungetestet)} Modul(e) ohne jeden Test"
    emit(verbose=args.verbose, output=ausgabe, verdict=kopf, details=zeilen or None)
    return 0


if __name__ == "__main__":
    sys.exit(main())

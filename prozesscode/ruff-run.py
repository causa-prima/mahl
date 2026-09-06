#!/usr/bin/env python3
"""
Ruff über den Prozess-Code unter .claude/** (Regelauswahl: `ruff.toml` im Root).

Verwendung:
  python3 -m prozesscode.ruff-run            # Verdikt, im Fehlerfall die Fundstellen
  python3 -m prozesscode.ruff-run --verbose  # vollständiger Output

Warum es das gibt (S128): Für den Prozess-Code galt keine einzige Qualitätsmaßgabe außer den
Tests – kein Linter, kein Coverage-Wert, kein Mutations-Backstop –, während Produktcode 100 %
Branch-Coverage und 100 % Mutation Score erfüllen muss. Ruff schließt die billigste dieser
Lücken; die teureren (Review, Mutation) folgen getrennt.

Ruff läuft aus dem venv (`.venv/bin/ruff`), nicht aus dem System-Python: Das ist
Debian-verwaltet und weist Installationen nach PEP 668 ab.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from ._wrapper_output import emit

ROOT = Path(__file__).resolve().parent.parent
RUFF = ROOT / ".venv" / "bin" / "ruff"
# Der Prozess-Code. Beide Verzeichnisse, weil `checks/` unter `hooks/` mitzählt und die
# Werkzeuge im Paket genauso Fehler tragen können wie die Hooks selbst.
PFADE = ("prozesscode", "tests")

_FEHLT = (
    "✗ ruff nicht gefunden ({pfad}).\n"
    "  Werkzeug-Umgebung herstellen:\n"
    "    python3 -m venv .venv\n"
    "    .venv/bin/pip install -r requirements-dev.txt\n"
    "  (Braucht das Systempaket python3.12-venv.)"
)


def _ruff_vorhanden() -> bool:
    return RUFF.is_file()


def _laufe(*befehl: str) -> subprocess.CompletedProcess:
    return subprocess.run(befehl, capture_output=True, text=True, cwd=ROOT)


_VERBLEIBEND = re.compile(r"\((?:\d+ fixed, )?(\d+) remaining\)")


def _anzahl(ausgabe: str) -> str:
    """Die Zahl, die den ZUSTAND beschreibt – nicht die, die zuerst dasteht.

    Nach `--fix` schreibt Ruff `Found 25 errors (14 fixed, 11 remaining).` Wer daraus die 25
    zieht, berichtet den Stand VOR der eigenen Änderung als aktuelles Ergebnis. Die 11 ist die
    Größe, um die es geht.
    """
    for zeile in ausgabe.splitlines():
        if zeile.startswith("Found ") and " error" in zeile:
            if (rest := _VERBLEIBEND.search(zeile)):
                return rest.group(1)
            return zeile.split()[1]
    return "?"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="Vollständiger Output")
    # Nur die als `safe` markierten Fixes: Ruffs `--unsafe-fixes` ändern Semantik (etwa
    # Vergleiche umschreiben) und gehören unter Augenschein, nicht in einen Wrapper-Schalter.
    parser.add_argument("--fix", action="store_true",
                        help="Sichere Fixes anwenden (ändert Dateien)")
    args = parser.parse_args(argv)

    # Zuerst, und mit dem herstellenden Befehl: Ein Werkzeug, das unverständlich scheitert,
    # wird abgeschaltet statt repariert – und der Linter fiele danach lautlos aus.
    if not _ruff_vorhanden():
        print(_FEHLT.format(pfad=RUFF))
        return 2

    befehl = [str(RUFF), "check", *PFADE, "--output-format", "concise"]
    if args.fix:
        befehl.append("--fix")
    ergebnis = _laufe(*befehl)
    ausgabe = ergebnis.stdout + ergebnis.stderr

    if ergebnis.returncode == 0:
        nachsatz = " (nach --fix)" if args.fix else ""
        emit(verbose=args.verbose, output=ausgabe,
             verdict=f"✓ ruff: keine Probleme{nachsatz} ({len(PFADE)} Pfade)")
        return 0

    fundstellen = [z for z in ausgabe.splitlines() if z.strip() and not z.startswith("Found ")]
    emit(verbose=args.verbose, output=ausgabe,
         verdict=f"✗ ruff: {_anzahl(ausgabe)} Problem(e) – oben aufgelistet",
         details=fundstellen)
    return 1


if __name__ == "__main__":
    sys.exit(main())

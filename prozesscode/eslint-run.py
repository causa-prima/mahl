#!/usr/bin/env python3
"""
ESLint run (nativ über npm).

Verwendung:
  python3 -m prozesscode.eslint-run           # ESLint über src/
  python3 -m prozesscode.eslint-run --verbose # vollständiger Output inkl. npm-Header
"""
import argparse
import re
import sys

from ._util import run_npm
from ._wrapper_output import emit, strip_noise

# ESLints Abschlusszeile, z.B. "✖ 2 problems (0 errors, 2 warnings)".
_PROBLEM_SUMMARY = re.compile(r"✖\s*(\d+)\s+problems?\s*\((\d+)\s+errors?,\s*(\d+)\s+warnings?\)")


def verdikt(output: str, lines: list[str]) -> str:
    """Das Verdikt richtet sich nach der FEHLERZAHL, nicht nach der Ausgabemenge (S130).

    `Client/eslint.config.js` stuft `max-params` und `max-lines-per-function` mit
    ausbuchstabierter Begründung als `warn` ein – das ist die Aussage der Konfiguration,
    dass diese Befunde tolerabel sind. Bis S130 machte der Wrapper daraus ein ✗, sobald
    überhaupt etwas ausgegeben wurde, und meldete damit auf unverändertem `main` dauerhaft
    Fehlschlag bei null Errors. Ein Verdikt, das immer ✗ zeigt, wird überlesen.

    Die Warnungen bleiben vollständig sichtbar – sie stehen in `details`, nur das Urteil
    darüber ändert sich. Ist die Zusammenfassung nicht lesbar (ESLint ändert sein Format),
    bleibt es bei ✗: Es gibt Meldungen, und wie viele davon Fehler sind, ist dann unbekannt.
    """
    if not lines:
        return "✓ ESLint: keine Probleme"

    treffer = _PROBLEM_SUMMARY.search(output)
    if not treffer:
        return "✗ ESLint: Meldungen vorhanden, Zusammenfassung nicht lesbar – oben aufgelistet"

    fehler, warnungen = int(treffer.group(2)), int(treffer.group(3))
    if fehler:
        return f"✗ ESLint: {fehler} Fehler, {warnungen} Warnung(en) – oben aufgelistet"
    return f"✓ ESLint: keine Fehler ({warnungen} Warnung(en) – oben aufgelistet)"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output inkl. npm-Header")
    args = parser.parse_args()

    output, exit_code = run_npm(["run", "lint"])

    # ESLint schreibt bei sauberem Lauf gar nichts – nach dem Noise-Strip bleibt nichts übrig.
    lines = strip_noise(output)
    emit(verbose=args.verbose, output=output, verdict=verdikt(output, lines),
         details=lines or None)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

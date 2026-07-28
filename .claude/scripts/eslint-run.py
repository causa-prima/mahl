#!/usr/bin/env python3
"""
ESLint run (nativ über npm).

Verwendung:
  python3 .claude/scripts/eslint-run.py           # ESLint über src/
  python3 .claude/scripts/eslint-run.py --verbose # vollständiger Output inkl. npm-Header
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _util import run_npm
from _wrapper_output import emit, strip_noise

# ESLints Abschlusszeile, z.B. "✖ 2 problems (0 errors, 2 warnings)".
_PROBLEM_SUMMARY = re.compile(r"✖\s*(\d+)\s+problems?")


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
    # Alles andere (Fehler UND Warnungen, die exit 0 liefern) ist analyse-relevant und bleibt.
    lines = strip_noise(output)
    if not lines:
        emit(verbose=args.verbose, output=output, verdict="✓ ESLint: keine Probleme")
    else:
        summary = _PROBLEM_SUMMARY.search(output)
        count = summary.group(1) if summary else "?"
        emit(verbose=args.verbose, output=output,
             verdict=f"✗ ESLint: {count} Problem(e) – oben aufgelistet", details=lines)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

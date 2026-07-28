#!/usr/bin/env python3
"""
Playwright E2E-Tests (nativ über npm).

Verwendung:
  python3 .claude/scripts/playwright-test.py                        # alle E2E-Tests
  python3 .claude/scripts/playwright-test.py --filter ingredients   # nach Datei/Testname filtern
  python3 .claude/scripts/playwright-test.py --verbose              # vollständiger Output
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _util import run_npm
from _wrapper_output import emit, strip_noise

# Playwrights Abschlusszeilen, z.B. "  12 passed (34.5s)" / "  2 failed".
_PASSED = re.compile(r"^\s*(\d+)\s+passed\b", re.MULTILINE)
_FAILED = re.compile(r"^\s*(\d+)\s+(?:failed|flaky)\b", re.MULTILINE)
_DURATION = re.compile(r"passed\s+\(([^)]+)\)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--filter", dest="filter_name", metavar="PATTERN",
                        help="Dateiname oder Testname-Filter (Substring-Match)")
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output ohne Filterung")
    args = parser.parse_args()

    npm_args = ["run", "test:e2e", "--"]
    if args.filter_name:
        npm_args.extend(["--grep", args.filter_name])

    output, exit_code = run_npm(npm_args)

    passed = _PASSED.search(output)
    # Nur zusammenfassen, wenn der Lauf grün war UND die Abschlusszeile erkannt wurde –
    # sonst bleibt es beim vollständigen Output (fail-open, s. _wrapper_output).
    if exit_code == 0 and passed and not _FAILED.search(output):
        duration = _DURATION.search(output)
        took = f", {duration.group(1)}" if duration else ""
        emit(verbose=args.verbose, output=output,
             verdict=f"✓ {passed.group(1)} E2E-Tests grün{took}")
    else:
        # Rot: Playwrights Fehlerblock (Erwartung/Ist, Locator, Screenshot-Pfad) IST die
        # Analyse-Information und bleibt vollständig erhalten.
        failed = _FAILED.search(output)
        count = failed.group(1) if failed else "?"
        emit(verbose=args.verbose, output=output,
             verdict=f"✗ {count} E2E-Test(s) rot – Details oben",
             details=strip_noise(output))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

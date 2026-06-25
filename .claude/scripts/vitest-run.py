#!/usr/bin/env python3
"""
vitest run (nativ über npm).

Verwendung:
  python3 .claude/scripts/vitest-run.py                   # alle Tests (einmalig, kein Watch)
  python3 .claude/scripts/vitest-run.py --filter Pattern  # nach TESTname filtern (vitest -t)
  python3 .claude/scripts/vitest-run.py --file Pattern    # nach DATEIname filtern (vitest positional)
  python3 .claude/scripts/vitest-run.py --verbose         # vollständiger Output inkl. npm-Header

--filter und --file sind jeweils unabhängig optional und beliebig kombinierbar.

--filter matcht als Substring gegen den voll-qualifizierten Testnamen (inkl. describe-Block);
nicht-passende Tests werden übersprungen. Matcht das Pattern nichts, würde vitest grün durchlaufen –
der Wrapper meldet das als FEHLER (Exit 1) und weist ausgeführte/übersprungene Tests aus.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _util import run_npm

# npm-interne Zeilen die keinen Informationswert für den Aufrufer haben
_NPM_NOISE = re.compile(r"^> mahl-client@|^npm (warn|error notice)")

# vitest-Zusammenfassung: "  Tests  3 passed | 13 skipped (16)" (nicht "Test Files …").
_TESTS_SUMMARY = re.compile(r"^\s*Tests\s+(?P<body>.+?)\s+\((?P<total>\d+)\)\s*$", re.MULTILINE)


def _parse_counts(output: str) -> dict[str, int] | None:
    """Liest passed/failed/skipped/total aus der vitest-'Tests'-Zeile (None, wenn keine da)."""
    match = _TESTS_SUMMARY.search(output)
    if not match:
        return None

    def count(status: str) -> int:
        found = re.search(rf"(\d+)\s+{status}", match.group("body"))
        return int(found.group(1)) if found else 0

    return {
        "passed":  count("passed"),
        "failed":  count("failed"),
        "skipped": count("skipped"),
        "total":   int(match.group("total")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--filter", dest="filter_name", metavar="PATTERN",
                        help="Testname-Filter via vitest -t (Substring/Regex gegen Testnamen)")
    parser.add_argument("--file", dest="file_name", metavar="PATTERN",
                        help="Dateiname-Filter (vitest positional) – grenzt auf Testdateien mit passendem Pfad ein")
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output ohne Filterung")
    args = parser.parse_args()

    # "run" als erstes Argument → einmaliger Lauf, kein Watch-Mode
    npm_args = ["run", "test", "--", "run"]
    # Positional (Datei) muss vor den Optionen stehen
    if args.file_name:
        npm_args.append(args.file_name)
    if args.filter_name:
        npm_args.extend(["-t", args.filter_name])

    output, exit_code = run_npm(npm_args)

    if args.verbose or not output.strip():
        print(output)
    else:
        lines = [l for l in output.splitlines() if not _NPM_NOISE.match(l)]
        print("\n".join(lines))

    # --filter (vitest -t) matcht als Substring gegen den voll-qualifizierten Testnamen.
    # Nicht-passende Tests werden ÜBERSPRUNGEN, nicht gefiltert – matcht das Pattern nichts,
    # läuft vitest grün durch (0 ausgeführt). Das machen wir explizit und fail-closed.
    if args.filter_name:
        counts = _parse_counts(output)
        print(
            f"\n[filter] --filter '{args.filter_name}' matcht als Substring gegen den "
            f"voll-qualifizierten Testnamen (inkl. describe-Block).",
            file=sys.stderr,
        )
        if counts is not None:
            matched = counts["passed"] + counts["failed"]
            print(
                f"[filter] {matched} ausgeführt, {counts['skipped']} übersprungen "
                f"(von {counts['total']}).",
                file=sys.stderr,
            )
            if matched == 0:
                print(
                    "[filter] ⚠️  0 Tests gematcht – alle übersprungen. Tippfehler im Pattern "
                    "oder Test existiert (noch) nicht? → als FEHLER gewertet.",
                    file=sys.stderr,
                )
                exit_code = exit_code or 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

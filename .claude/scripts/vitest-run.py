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
from _wrapper_output import emit, strip_noise

# vitest-Banner und Zeitstempel – kein Aussagewert für „sind die Tests grün?".
_VITEST_CHROME = re.compile(r"^\s*RUN\s+v[\d.]|^\s*Start at\s|^\s*Duration\s")

# vitest-Zusammenfassung: "  Tests  3 passed | 13 skipped (16)" (nicht "Test Files …").
_TESTS_SUMMARY = re.compile(r"^\s*Tests\s+(?P<body>.+?)\s+\((?P<total>\d+)\)\s*$", re.MULTILINE)
_FILES_SUMMARY = re.compile(r"^\s*Test Files\s+.+?\((?P<total>\d+)\)\s*$", re.MULTILINE)
_DURATION = re.compile(r"^\s*Duration\s+(?P<value>[\d.]+m?s)", re.MULTILINE)


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

    counts = _parse_counts(output)
    files = _FILES_SUMMARY.search(output)
    duration = _DURATION.search(output)
    if exit_code == 0 and counts and counts["failed"] == 0:
        skipped = f", {counts['skipped']} übersprungen" if counts["skipped"] else ""
        scope = f", {files.group('total')} Dateien" if files else ""
        took = f", {duration.group('value')}" if duration else ""
        verdict = f"✓ {counts['passed']} Tests grün{skipped}{scope}{took}"
        emit(verbose=args.verbose, output=output, verdict=verdict)
    else:
        # Rot: der vitest-Fehlerblock (Diff, Stack, Datei/Zeile) IST die Analyse-Information –
        # nur Banner und Zeitstempel fallen weg.
        failed = counts["failed"] if counts else "?"
        emit(verbose=args.verbose, output=output,
             verdict=f"✗ {failed} Test(s) rot – Details oben",
             details=strip_noise(output, _VITEST_CHROME))

    # --filter (vitest -t) matcht als Substring gegen den voll-qualifizierten Testnamen.
    # Nicht-passende Tests werden ÜBERSPRUNGEN, nicht gefiltert – matcht das Pattern nichts,
    # läuft vitest grün durch (0 ausgeführt). Das machen wir explizit und fail-closed.
    if args.filter_name:
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

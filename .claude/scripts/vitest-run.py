#!/usr/bin/env python3
"""
vitest run via cmd.exe (WSL-Wrapper).

Verwendung:
  python3 .claude/scripts/vitest-run.py                   # alle Tests (einmalig, kein Watch)
  python3 .claude/scripts/vitest-run.py --filter Pattern  # nach TESTname filtern (vitest -t)
  python3 .claude/scripts/vitest-run.py --file Pattern    # nach DATEIname filtern (vitest positional)
  python3 .claude/scripts/vitest-run.py --verbose         # vollständiger Output inkl. npm-Header

--filter und --file sind jeweils unabhängig optional und beliebig kombinierbar.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _util import run_npm

# npm-interne Zeilen die keinen Informationswert für den Aufrufer haben
_NPM_NOISE = re.compile(r"^> mahl-client@|^npm (warn|error notice)")


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

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

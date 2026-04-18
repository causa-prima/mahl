#!/usr/bin/env python3
"""
Playwright E2E-Tests via cmd.exe (WSL-Wrapper).

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

_NPM_NOISE = re.compile(r"^> mahl-client@|^npm (warn|error notice)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Playwright E2E-Tests via cmd.exe (WSL)")
    parser.add_argument("--filter", dest="filter_name", metavar="PATTERN",
                        help="Dateiname oder Testname-Filter (Substring-Match)")
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output ohne Filterung")
    args = parser.parse_args()

    npm_args = ["run", "test:e2e", "--"]
    if args.filter_name:
        npm_args.extend(["--grep", args.filter_name])

    output, exit_code = run_npm(npm_args)

    if args.verbose or not output.strip():
        print(output)
    else:
        lines = [l for l in output.splitlines() if not _NPM_NOISE.match(l)]
        print("\n".join(lines))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

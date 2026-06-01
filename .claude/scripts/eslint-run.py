#!/usr/bin/env python3
"""
ESLint run via cmd.exe (WSL-Wrapper).

Verwendung:
  python3 .claude/scripts/eslint-run.py           # ESLint über src/
  python3 .claude/scripts/eslint-run.py --verbose # vollständiger Output inkl. npm-Header
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _util import run_npm

_NPM_NOISE = re.compile(r"^> mahl-client@|^npm (warn|error notice)")


def main() -> None:
    verbose = "--verbose" in sys.argv

    output, exit_code = run_npm(["run", "lint"])

    if verbose or not output.strip():
        print(output)
    else:
        lines = [l for l in output.splitlines() if not _NPM_NOISE.match(l)]
        print("\n".join(lines))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

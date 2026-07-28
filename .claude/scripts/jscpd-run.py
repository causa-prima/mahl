#!/usr/bin/env python3
"""
jscpd (Duplikat-Analyse, nativ über npm).

Verwendung:
  python3 .claude/scripts/jscpd-run.py           # jscpd über src/
  python3 .claude/scripts/jscpd-run.py --verbose # vollständiger Output inkl. npm-Header
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _util import run_npm
from _wrapper_output import emit, strip_noise

# Statistik-Tabelle (Rahmen + Zellen), Laufzeit und die Spenden-/Werbezeilen am Ende:
# alles ohne Aussagewert für „gibt es Duplikate?".
_JSCPD_CHROME = re.compile(r"^[\x1b\[\d;m]*[┌├└│]|^\x1b\[90mtime:|💡|🎩|💖")
_CLONE_COUNT = re.compile(r"Found (\d+) clones?\.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output inkl. Statistik-Tabelle und npm-Header")
    args = parser.parse_args()

    output, exit_code = run_npm(["run", "lint:duplicates"])

    found = _CLONE_COUNT.search(output)
    if found and found.group(1) == "0":
        emit(verbose=args.verbose, output=output, verdict="✓ jscpd: keine Duplikate")
    else:
        # Die Fundstellen selbst sind die Analyse-Information – Tabelle und Werbung nicht.
        lines = [l for l in strip_noise(output, _JSCPD_CHROME) if l.strip()]
        count = found.group(1) if found else "?"
        emit(verbose=args.verbose, output=output,
             verdict=f"✗ jscpd: {count} Duplikat(e) – Fundstellen oben", details=lines)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

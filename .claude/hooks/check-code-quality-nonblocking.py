#!/usr/bin/env python3
"""PostToolUse-Dispatcher (nicht-blockierend): Heuristische Hinweise und Test-Pattern-Checks."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from checks.common import parse_input
from checks import constructors, test_patterns
from checks.primitives import check_nonblocking as primitives_nonblocking

CHECKS = [constructors.check, test_patterns.check, primitives_nonblocking]


def main() -> None:
    inp = parse_input()
    if inp is None:
        sys.exit(0)

    warnings: list[str] = []
    for check_fn in CHECKS:
        try:
            warnings.extend(check_fn(inp))
        except Exception as e:
            print(f"check-code-quality-nonblocking: Fehler in {check_fn.__module__}: {e}", file=sys.stderr)

    if warnings:
        separator = "\n" + "─" * 60 + "\n"
        print(separator.join(warnings), file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()

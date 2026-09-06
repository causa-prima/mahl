#!/usr/bin/env python3
"""PostToolUse-Dispatcher (nicht-blockierend): Heuristische Hinweise und Test-Pattern-Checks."""
import sys

from .checks.common import parse_input
from .checks import constructors, guard_log, ruff_lint, test_patterns
from .checks import tooling_tests
from .checks.primitives import check_nonblocking as primitives_nonblocking

CHECKS = [constructors.check, test_patterns.check, primitives_nonblocking,
          tooling_tests.check, ruff_lint.check]


def main() -> None:
    inp = parse_input()
    if inp is None:
        sys.exit(0)

    warnings: list[str] = []
    for check_fn in CHECKS:
        try:
            treffer = check_fn(inp)
        except Exception as e:
            print(f"check-code-quality-nonblocking: Fehler in {check_fn.__module__}: {e}", file=sys.stderr)
            continue
        if treffer:
            # Wer gefeuert hat, wird protokolliert – ein Guard ohne jede Auslösung ist
            # entweder kaputt oder überflüssig, und ohne Protokoll fiele beides nie auf.
            guard_log.protokolliere(check_fn.__module__.rsplit(".", 1)[-1])
        warnings.extend(treffer)

    if warnings:
        separator = "\n" + "─" * 60 + "\n"
        print(separator.join(warnings), file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()

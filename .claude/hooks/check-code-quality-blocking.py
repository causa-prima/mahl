#!/usr/bin/env python3
"""PostToolUse-Dispatcher (blockierend): Eindeutige Guideline-Verletzungen."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from checks.common import parse_input, BLOCKING_DISCUSSION_NOTE
from checks import rop, throw_check, immutability_strict, constructors, tdd_one_test, domain_visibility

CHECKS = [rop.check, throw_check.check, immutability_strict.check, constructors.check, tdd_one_test.check, domain_visibility.check]


def main() -> None:
    inp = parse_input()
    if inp is None:
        sys.exit(0)

    violations: list[str] = []
    for check_fn in CHECKS:
        try:
            violations.extend(check_fn(inp))
        except Exception as e:
            print(f"check-code-quality-blocking: Fehler in {check_fn.__module__}: {e}", file=sys.stderr)

    if violations:
        separator = "\n" + "─" * 60 + "\n"
        msg = separator.join(violations) + "\n" + BLOCKING_DISCUSSION_NOTE
        print(msg, file=sys.stderr)
        sys.exit(2)  # exit 2 = Claude soll Aktion überdenken/korrigieren

    sys.exit(0)


if __name__ == "__main__":
    main()

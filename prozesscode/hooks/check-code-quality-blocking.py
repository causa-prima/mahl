#!/usr/bin/env python3
"""PostToolUse-Dispatcher (blockierend): Eindeutige Guideline-Verletzungen."""
import sys

from .checks.common import parse_input, BLOCKING_DISCUSSION_NOTE
from .checks import rop, throw_check, immutability_strict, immutability, constructors
from .checks.primitives import check_blocking as primitives_blocking

CHECKS = [
    rop.check,
    throw_check.check,
    immutability_strict.check,
    immutability.check,
    constructors.check,
    primitives_blocking,
]

_TRENNER = "\n" + "─" * 60 + "\n"


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    inp = parse_input(data)
    if inp is None:
        return None

    violations: list[str] = []
    for check_fn in CHECKS:
        try:
            violations.extend(check_fn(inp))
        except Exception as e:
            print(f"check-code-quality-blocking: Fehler in {check_fn.__module__}: {e}", file=sys.stderr)

    if not violations:
        return None

    return _TRENNER.join(violations) + "\n" + BLOCKING_DISCUSSION_NOTE

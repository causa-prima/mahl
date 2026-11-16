#!/usr/bin/env python3
"""PostToolUse-Dispatcher (blockierend): Eindeutige Guideline-Verletzungen."""
import sys

from .checks.common import parse_input, BLOCKING_DISCUSSION_NOTE
from .checks import guard_log, rop, throw_check, immutability_strict, immutability, constructors
from .checks import unsichtbare_zeichen
from .checks.primitives import check_blocking as primitives_blocking

CHECKS = [
    rop.check,
    throw_check.check,
    immutability_strict.check,
    immutability.check,
    constructors.check,
    primitives_blocking,
    unsichtbare_zeichen.check,
]

_TRENNER = "\n" + "─" * 60 + "\n"
_PRAEFIX = "blockierend:"


def teilcheck_name(check_fn) -> str:
    """Name im Guard-Protokoll. Der Präfix trennt ihn von gleichnamigen Modulen des
    nicht-blockierenden Dispatchers (`primitives` steht in beiden)."""
    return _PRAEFIX + check_fn.__module__.rpartition(".")[2]


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    inp = parse_input(data)
    if inp is None:
        return None

    violations: list[str] = []
    for check_fn in CHECKS:
        try:
            treffer = check_fn(inp)
        except Exception as e:
            print(f"check-code-quality-blocking: Fehler in {check_fn.__module__}: {e}", file=sys.stderr)
            continue
        if treffer:
            # Der Dispatcher protokolliert nur diesen Hook als Ganzes; welcher Teilcheck
            # anschlug, wäre sonst unsichtbar – und ein kaputter Teilcheck fiele nie auf.
            guard_log.protokolliere(teilcheck_name(check_fn))
            violations.extend(treffer)

    if not violations:
        return None

    return _TRENNER.join(violations) + "\n" + BLOCKING_DISCUSSION_NOTE

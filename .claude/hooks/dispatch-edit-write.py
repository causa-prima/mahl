#!/usr/bin/env python3
"""PreToolUse-Dispatcher für den Matcher `Edit|Write` (OBS-S088-1).

Warum: Bis S113 stand jeder Check einzeln in `settings.json`. Einen Check
hinzuzufügen oder zu entfernen erforderte damit eine `settings.json`-Änderung –
und die greift erst nach einem Claude-Code-Reload. Über diesen Dispatcher ändert
sich nur noch die `CHECKS`-Liste unten: sofort wirksam, ohne Reload.

Vertrag je Check-Modul: eine Funktion `check(data: dict) -> str | None`.
`data` ist der rohe, bereits geparste Hook-Input (stdin wird hier EINMAL gelesen
und ist danach konsumiert – deshalb bekommt jeder Check das Dict übergeben,
statt selbst zu lesen). Rückgabe `None` = kein Einwand, ein String = Blockier-Grund.
Die Module behalten daneben ihr eigenes `main()` und bleiben standalone lauffähig
(nützlich für manuelles Testen); der Dispatcher nutzt es nicht.

Fail-open: Wirft ein Check, wird sein Fehler nach stderr gemeldet und der Check
übersprungen – ein defekter Check darf nie einen Edit blockieren. Das gilt je
Check einzeln, damit ein Fehler nicht die übrigen mitreißt.

Alle Checks laufen immer; ihre Gründe werden gesammelt ausgegeben statt beim
ersten Treffer abzubrechen (sonst sieht man Verletzung 2 erst, nachdem man 1
behoben hat).
"""
import json
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Reihenfolge = Ausgabe-Reihenfolge der Gründe. Hinzufügen/Entfernen wirkt sofort,
# ohne settings.json-Änderung und ohne Reload.
CHECKS = [
    "check-dependency-allowlist",
    "check-code-quality-blocking",
    "check-index-length",
    "check-e2e-scenario-ref",
    "check-ref-direction",
    "check-obs-capture",
]


def collect_reasons(data: dict) -> list[str]:
    """Führt alle Checks aus und sammelt ihre Blockier-Gründe (fail-open je Check)."""
    reasons: list[str] = []
    for name in CHECKS:
        try:
            reason = import_module(name).check(data)
        except Exception as exc:  # noqa: BLE001 – defekter Check darf nie blockieren
            print(f"dispatch-edit-write: Fehler in {name} ({exc}) – Check übersprungen.",
                  file=sys.stderr)
            continue
        if reason:
            reasons.append(reason)
    return reasons


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # kein parsbarer Input → nichts blocken

    if data.get("tool_name", "") not in ("Edit", "Write"):
        sys.exit(0)

    reasons = collect_reasons(data)
    if reasons:
        separator = "\n" + "─" * 60 + "\n"
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": separator.join(reasons),
            }
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()

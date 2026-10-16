#!/usr/bin/env python3
"""Auditoren starten ohne `name` – sonst verliert der Bash-Hook ihre Nur-Lese-Sperre.

Der Bash-Hook erkennt Auditoren am Feld `agent_type` seiner Eingabe (AUDITOREN in
`check-bash-permission.py`). Bei einem Agenten, der mit `name` gestartet wurde, steht dort aber
der Name statt des Typs – live gemessen: ein `code-quality-auditor` namens `cq-probe`
kam als `agent_type: "cq-probe"` an und durfte `touch` ausführen. Den Typ nennt nur der Aufruf
selbst, und den sieht dieser PreToolUse-Hook.

Verworfen: den Namen über eine Startliste zum Typ auflösen. Der Start-Hook läuft erst, nachdem
das Agent-Werkzeug zurückkehrt; der Agent arbeitet da schon, sein erster Befehl kann vor dem
Eintrag beim Bash-Hook ankommen. Ohne Namen gibt es diese Lücke nicht, und er fehlt nicht:
Auch ein unbenannter Agent ist per `SendMessage` an seine `agent_id` erreichbar.
"""
import json
import sys
from importlib import import_module

from .checks import guard_log

AUDITOREN = import_module("prozesscode.hooks.check-bash-permission").AUDITOREN


def grund(daten: dict) -> str | None:
    """Der Deny-Grund – oder None, wenn der Start in Ordnung ist."""
    if daten.get("tool_name") != "Agent":
        return None
    eingabe = daten.get("tool_input") or {}
    typ = eingabe.get("subagent_type")
    if typ not in AUDITOREN or not eingabe.get("name"):
        return None
    return (f"Auditoren ohne `name` starten: Mit `name: \"{eingabe['name']}\"` sieht der Bash-Hook "
            f"den Namen statt des Typs `{typ}` und hebt die Nur-Lese-Sperre auf. Denselben Aufruf "
            "ohne `name` wiederholen – erreichbar bleibt der Agent per SendMessage an seine "
            "agent_id.")


def main() -> None:
    try:
        text = grund(json.load(sys.stdin))
    except Exception as fehler:  # noqa: BLE001 – fail-open: ein Hook-Fehler blockt keinen Start
        print(f"check-agent-start: unlesbare Eingabe ({type(fehler).__name__}: {fehler})",
              file=sys.stderr)
        sys.exit(0)
    if text:
        guard_log.protokolliere("check-agent-start")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": text}}))
    sys.exit(0)


if __name__ == "__main__":
    main()

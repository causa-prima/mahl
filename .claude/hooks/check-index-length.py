#!/usr/bin/env python3
"""PreToolUse-Hook: blockiert Edit/Write, das eine zu lange Kurzfassung nach
docs/history/sessions/index.md schreibt (OBS-S085-9 – Verbosity-Ratchet).

Cap-Werte + Parsing: Single source in `.claude/scripts/_index_length.py`.
Grandfathering: Zeilen, die bereits unverändert in der Datei stehen, werden
übersprungen (History ist read-only) – geprüft werden nur neue/geänderte Zeilen.

Einschränkung: Der Hook sieht nur den geschriebenen Inhalt (new_string/content).
Ein Fragment-Edit, der eine bestehende Kurzfassung ohne '| NN |'-Präfix verlängert,
wird nicht erkannt. Neue Einträge werden als volle Zeile angehängt → abgedeckt.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from _index_length import HARD_CAP, SOFT_TARGET, table_rows  # noqa: E402

_REL_INDEX = "docs/history/sessions/index.md"


def main() -> None:
    try:
        inp = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = inp.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    tool_input = inp.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    rel = file_path
    if project_dir and file_path.startswith(project_dir):
        rel = file_path[len(project_dir):].lstrip("/\\")
    if not rel.replace("\\", "/").endswith(_REL_INDEX):
        sys.exit(0)

    content = tool_input.get("new_string") if tool_name == "Edit" else tool_input.get("content")
    if not content:
        sys.exit(0)

    # Grandfathering: bereits vorhandene Zeilen (unverändert) sind ausgenommen.
    existing: set[str] = set()
    index_abs = os.path.join(project_dir, _REL_INDEX) if project_dir else file_path
    try:
        with open(index_abs, encoding="utf-8") as f:
            existing = {line.strip() for line in f}
    except OSError:
        pass

    violations = [(s, n) for raw, s, n in table_rows(content)
                  if raw not in existing and n > HARD_CAP]
    if violations:
        lst = "; ".join(f"S{s}: {n} Zeichen" for s, n in violations)
        reason = (
            f"Index-Kurzfassung über dem harten Cap ({HARD_CAP} Zeichen): {lst}.\n"
            "Regel: ein Satz – was sich änderte, kein Warum (das gehört in die Session-Datei); "
            f"auf ADR-/Session-IDs verweisen statt Prosa. Soft-Ziel {SOFT_TARGET}. "
            "Details: closing-session SKILL Schritt 6."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()

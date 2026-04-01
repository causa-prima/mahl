#!/usr/bin/env python3
"""PreToolUse-Hook: Dependency-Dateien vor unkontrollierten Änderungen schützen.

Blockiert Edit/Write auf:
- Client/package.json
- **/*.csproj
- docs/DEPENDENCIES.md

Grund: Externe Abhängigkeiten erfordern explizite Freigabe durch den User.
Prozess: docs/DEPENDENCIES.md (Sektion "Prozess: Neues Paket hinzufügen")
"""
import json
import os
import re
import sys


PROTECTED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'(^|[/\\])package\.json$'), 'package.json'),
    (re.compile(r'\.csproj$'), '.csproj'),
    (re.compile(r'(^|[/\\])DEPENDENCIES\.md$'), 'DEPENDENCIES.md'),
]

DENY_MESSAGE = """\
Dependency-Datei ({filename}) darf nicht direkt vom Agenten bearbeitet werden.

Prozess (docs/DEPENDENCIES.md):
1. Agent bereitet 5-Punkte-Anfrage vor
2. User gibt explizit frei
3. User trägt das Paket manuell in DEPENDENCIES.md ein
4. User installiert das Paket und aktualisiert {filename} selbst"""


def get_denial_reason(file_path: str) -> str | None:
    """Gibt die Deny-Meldung zurück wenn file_path geschützt ist, sonst None."""
    for pattern, filename in PROTECTED_PATTERNS:
        if pattern.search(file_path):
            return DENY_MESSAGE.format(filename=filename)
    return None


def main() -> None:
    try:
        inp = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if inp.get("tool_name", "") not in ("Edit", "Write"):
        sys.exit(0)

    file_path = inp.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir and file_path.startswith(project_dir):
        file_path = file_path[len(project_dir):].lstrip("/\\")

    reason = get_denial_reason(file_path)
    if reason:
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

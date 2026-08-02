#!/usr/bin/env python3
"""PreToolUse-Hook: Dependency-Dateien vor unkontrollierten Änderungen schützen.

Blockiert Edit/Write auf:
- Client/package.json
- **/*.csproj
- docs/reference/dependencies.md

Grund: Externe Abhängigkeiten erfordern explizite Freigabe durch den User.
Prozess: docs/reference/dependencies.md (Sektion "Prozess: Neues Paket hinzufügen")
"""
import json
import os
import re
import sys


PROTECTED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'(^|[/\\])package\.json$'), 'package.json'),
    (re.compile(r'\.csproj$'), '.csproj'),
    (re.compile(r'(^|[/\\])dependencies\.md$'), 'dependencies.md'),
]

DENY_MESSAGE = """\
Dependency-Datei ({filename}) darf nicht direkt vom Agenten bearbeitet werden.

Prozess (docs/reference/dependencies.md):
1. Agent bereitet 5-Punkte-Anfrage vor
2. User gibt explizit frei
3. User trägt das Paket manuell in docs/reference/dependencies.md ein
4. User installiert das Paket und aktualisiert {filename} selbst"""


def get_denial_reason(file_path: str) -> str | None:
    """Gibt die Deny-Meldung zurück wenn file_path geschützt ist, sonst None."""
    for pattern, filename in PROTECTED_PATTERNS:
        if pattern.search(file_path):
            return DENY_MESSAGE.format(filename=filename)
    return None


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    if data.get("tool_name", "") not in ("Edit", "Write"):
        return None

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return None

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir and file_path.startswith(project_dir):
        file_path = file_path[len(project_dir):].lstrip("/\\")

    return get_denial_reason(file_path)


def main() -> None:
    try:
        inp = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    reason = check(inp)
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

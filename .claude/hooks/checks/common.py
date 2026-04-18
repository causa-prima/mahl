"""Gemeinsame Hilfsfunktionen für alle Code-Quality-Checks."""
import json
import re
import sys
from dataclasses import dataclass

BLOCKING_DISCUSSION_NOTE = (
    "Falls eine der blockierten Änderungen nach den Guidelines korrekt sein sollte, "
    "bitte Rücksprache mit dem Aufrufer halten."
)

CS_FILE = re.compile(r'\.cs$')
TS_FILE = re.compile(r'\.(ts|tsx)$')

TEST_FILE = re.compile(
    r'[/\\](?:Tests?|test|__tests__)[/\\]'
    r'|\.Tests[/\\]'          # e.g. Server.Tests/foo.cs
    r'|Tests\.cs$'
    r'|\.Tests\.'
    r'|\.test\.(ts|tsx)$'
    r'|\.spec\.(ts|tsx)$'
)

# Pfade, die von Domain-Checks ausgenommen sind
DOMAIN_EXCLUDED = re.compile(
    r'[/\\](?:Migrations|DatabaseTypes)[/\\]'
    r'|[/\\]Dtos[/\\]'
    r'|(?:Dto|Options|Settings)\.cs$'
    r'|[/\\](?:Tests?|test)[/\\]'
    r'|\.Tests[/\\]'          # e.g. Server.Tests/foo.cs
    r'|Tests\.cs$'
    r'|\.Tests\.'
)


# Pfade, die von Immutability-Checks ausgenommen sind (DTOs bewusst NICHT ausgenommen)
IMMUTABILITY_EXCLUDED = re.compile(
    r'[/\\](?:Migrations|DatabaseTypes)[/\\]'
    r'|DbContext\.cs$'            # EF DbContext muss class sein – kein record
    r'|(?:^|[/\\])Program\.cs$'  # public partial class Program für WebApplicationFactory
    r'|(?:Options|Settings)\.cs$'
    r'|[/\\](?:Tests?|test)[/\\]'
    r'|\.Tests[/\\]'          # e.g. Server.Tests/foo.cs
    r'|Tests\.cs$'
    r'|\.Tests\.'
)


@dataclass
class HookInput:
    tool: str
    file_path: str
    new_content: str
    old_content: str  # nur bei Edit befüllt, sonst ""
    is_cs: bool
    is_ts: bool
    is_test: bool
    is_domain_excluded: bool


def parse_input() -> HookInput | None:
    """Liest und parsed den Hook-Input von stdin. Gibt None zurück bei Fehler."""
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        print(f"check-code-quality: JSON-Parsing fehlgeschlagen: {e}", file=sys.stderr)
        return None

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool == "Edit":
        new_content = tool_input.get("new_string", "")
        old_content = tool_input.get("old_string", "")
    elif tool == "Write":
        new_content = tool_input.get("content", "")
        old_content = ""
    else:
        return None  # kein Edit/Write – nichts zu prüfen

    return HookInput(
        tool=tool,
        file_path=file_path,
        new_content=new_content,
        old_content=old_content,
        is_cs=bool(CS_FILE.search(file_path)),
        is_ts=bool(TS_FILE.search(file_path)),
        is_test=bool(TEST_FILE.search(file_path)),
        is_domain_excluded=bool(DOMAIN_EXCLUDED.search(file_path)),
    )

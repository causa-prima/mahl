"""
TDD-Enforcement-Check (blockierend): Maximal 1 neuer Test pro Edit/Write-Zyklus.
Verhindert, dass mehrere Tests auf einmal geschrieben werden (TDD-Verstoß).
"""
import re
from .common import HookInput

_CS_TEST = re.compile(r'^\s*\[Test(?:Case)?\b', re.MULTILINE)
_TS_TEST = re.compile(r'^\s*(it|test)\s*\(', re.MULTILINE)

_IS_TEST_FILE = re.compile(r'\.Tests\b.*\.cs$|\.(test|spec)\.(ts|tsx)$')


def check(inp: HookInput) -> list[str]:
    if not _IS_TEST_FILE.search(inp.file_path):
        return []

    counter = _CS_TEST if inp.is_cs else _TS_TEST

    if inp.tool == "Edit":
        added = len(counter.findall(inp.new_content)) - len(counter.findall(inp.old_content))
    else:  # Write
        try:
            with open(inp.file_path, encoding="utf-8") as f:
                existing = f.read()
        except OSError:
            existing = ""
        added = len(counter.findall(inp.new_content)) - len(counter.findall(existing))

    if added > 1:
        return [
            f"⛔ TDD-Verletzung (blockierend): Maximal 1 neuer Test pro Zyklus erlaubt "
            f"(gefunden: {added}). Teile die Änderung auf."
        ]
    return []

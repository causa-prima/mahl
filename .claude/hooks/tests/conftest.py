"""Gemeinsame Hilfsfunktionen für Hook-Tests."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from checks.common import HookInput, CS_FILE, TS_FILE, TEST_FILE, DOMAIN_EXCLUDED


def make_input(
    file_path: str,
    new_content: str,
    old_content: str = "",
    tool: str = "Edit",
) -> HookInput:
    """Erstellt ein HookInput-Objekt mit automatisch abgeleiteten Flags."""
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

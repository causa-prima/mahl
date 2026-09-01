"""Gemeinsame Hilfsfunktionen für Hook-Tests."""
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from checks import guard_log
from checks.common import HookInput, CS_FILE, TS_FILE, TEST_FILE, DOMAIN_EXCLUDED


@pytest.fixture(autouse=True)
def _guard_log_ins_leere(tmp_path, monkeypatch):
    """Kein Test schreibt je ins echte Auslöse-Protokoll.

    Die Dispatcher-Tests rufen `collect_reasons` mit Fixture-Daten auf; seit die Dispatcher
    protokollieren, landete jeder Lauf im Produktionslog. In S128 direkt beobachtet: Der
    Report wies `a`, `c` und `working` als Guards mit je fünf Auslösungen aus. Ein
    Messinstrument, das die eigenen Tests mitzählt, misst sich selbst.
    """
    monkeypatch.setattr(guard_log, "LOG", tmp_path / "guard-triggers.jsonl")


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

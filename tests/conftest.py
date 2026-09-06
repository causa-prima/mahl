"""Gemeinsame Hilfsfunktionen für die Tests des Prozess-Codes.

Die Tests liegen bewusst NEBEN dem Paket, nicht darin: mutmut mutiert `paths_to_mutate`,
und läge `tests/` unter `prozesscode/`, mutierte es die Tests gleich mit – ein Mutant im
Test, der den Test grün lässt, wäre als „überlebt" gezählt und sähe aus wie eine Lücke im
Produktivcode.
"""
import sys
import os

import pytest

# Repo-Root, damit `prozesscode` als Paket importierbar ist. Zentral hier statt in jeder
# Testdatei: conftest.py lädt pytest vor jedem Testmodul, und 58 Kopien derselben Zeile
# wären genau die Bootstrap-Duplikation, die jscpd im Produktivcode bereits anmahnt.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prozesscode._mutmut_ausnahmen import UNTER_MUTMUT_UEBERSPRUNGEN
from prozesscode.hooks.checks import guard_log
from prozesscode.hooks.checks.common import HookInput, CS_FILE, TS_FILE, TEST_FILE, DOMAIN_EXCLUDED


def pytest_collection_modifyitems(config, items):
    """Überspringt die gelisteten Tests, sobald der Lauf von mutmut kommt.

    `MUTANT_UNDER_TEST` setzt mutmut in jeder seiner Phasen (Stats, Generierung, Bewertung);
    ein gewöhnlicher pytest-Lauf kennt sie nicht.
    """
    del config  # von pytest übergeben, hier ohne Belang
    if "MUTANT_UNDER_TEST" not in os.environ:
        return
    for item in items:
        grund = UNTER_MUTMUT_UEBERSPRUNGEN.get(item.nodeid)
        if grund:
            item.add_marker(pytest.mark.skip(reason=f"unter mutmut: {grund}"))


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

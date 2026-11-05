"""Der nicht blockierende Dispatcher: was `main()` mit den Ergebnissen seiner Checks macht.

Die Checks selbst haben eigene Tests. Hier stehen Attrappen an ihrer Stelle, damit sichtbar
wird, was der Dispatcher entscheidet: ob nach einem werfenden Check die übrigen noch laufen,
unter welchem Namen eine Auslösung ins Guard-Protokoll geht und wie die Hinweise bei Claude
Code ankommen (Exit 2, stderr).
"""
import io
import json
import sys
from importlib import import_module

import pytest

from prozesscode.hooks.checks import guard_log

dispatcher = import_module("prozesscode.hooks.check-code-quality-nonblocking")

EINGABE = {"tool_name": "Write", "tool_input": {"file_path": "docs/probe.md", "content": "x"}}


def _check(modul: str, *, meldet=(), wirft: str | None = None):
    def check(_inp):
        if wirft:
            raise RuntimeError(wirft)
        return list(meldet)
    check.__module__ = modul
    return check


def _lauf(monkeypatch, checks, stdin: str = json.dumps(EINGABE)) -> int:
    monkeypatch.setattr(dispatcher, "CHECKS", checks)
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    try:
        dispatcher.main()
    except SystemExit as ende:
        return ende.code
    return 0


def test_nach_einem_werfenden_check_laufen_die_uebrigen_weiter(monkeypatch, capsys):
    """Sonst fiele mit einem kaputten Check jeder spätere aus – darunter die Werkzeug-Suite."""
    code = _lauf(monkeypatch, [_check("prozesscode.hooks.checks.kaputt", wirft="kein Zugriff"),
                               _check("prozesscode.hooks.checks.spaeter", meldet=["Hinweis"])])
    fehler = capsys.readouterr().err
    assert code == 2
    assert "check-code-quality-nonblocking: Fehler in prozesscode.hooks.checks.kaputt: " \
           "kein Zugriff" in fehler
    assert "Hinweis" in fehler


def test_protokolliert_eine_ausloesung_unter_dem_letzten_namensteil(monkeypatch):
    """guard-stats ordnet nach diesem Namen zu – `checks.spaeter` wäre ein anderer Guard."""
    _lauf(monkeypatch, [_check("prozesscode.hooks.checks.still"),
                        _check("prozesscode.hooks.checks.spaeter", meldet=["Hinweis"])])
    assert guard_log.zaehlstand() == {"spaeter": 1}


def test_trennt_hinweise_durch_eine_linie(monkeypatch, capsys):
    _lauf(monkeypatch, [_check("prozesscode.hooks.checks.a", meldet=["erster", "zweiter"])])
    assert capsys.readouterr().err == "erster\n" + "─" * 60 + "\nzweiter\n"


@pytest.mark.parametrize("stdin", [json.dumps(EINGABE), "kein JSON"])
def test_ohne_hinweis_endet_er_mit_exit_0(monkeypatch, stdin):
    """Exit 2 hieße für Claude Code: Hinweis da. Ohne Eingabe gibt es auch keinen."""
    assert _lauf(monkeypatch, [_check("prozesscode.hooks.checks.still")], stdin) == 0

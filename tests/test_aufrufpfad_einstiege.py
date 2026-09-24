"""Aufrufpfad der direkt registrierten Einstiege: stdin/argv → `main()` → Entscheidung.

So ruft Claude Code sie auf (`settings.json`) bzw. git den commit-msg-Hook. Die Prüflogik
dahinter hat eigene Tests; hier steht, dass der Einstieg sie erreicht und die Entscheidung im
Format ausgibt, das der Aufrufer liest. Jeder Test lenkt Laufzeit-Logs nach `tmp_path` – das
Deny-Log ist Retro-Datenquelle und darf von Tests nicht verfälscht werden.
"""
import io
import json
import sys
from importlib import import_module

import pytest

from prozesscode.hooks.checks import mengenangaben


def _mit_stdin(monkeypatch, modul, daten: dict, *argv) -> int:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(daten)))
    monkeypatch.setattr(sys, "argv", [modul.__name__, *argv])
    try:
        modul.main()
    except SystemExit as ende:
        return ende.code or 0
    return 0


@pytest.mark.aufrufpfad("check-bash-permission")
def test_bash_hook_gibt_deny_als_json_aus(tmp_path, monkeypatch, capsys):
    hook = import_module("prozesscode.hooks.check-bash-permission")
    monkeypatch.setattr(hook, "_LOG_FILE", str(tmp_path / "denied.log"))
    monkeypatch.setattr(hook, "_ALLOWED_LOG_FILE", str(tmp_path / "allowed.log"))
    code = _mit_stdin(monkeypatch, hook,
                      {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}})
    entscheidung = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert code == 0
    assert entscheidung["permissionDecision"] == "deny"
    assert (tmp_path / "denied.log").exists()


def test_bash_hook_laesst_erlaubten_befehl_durch(tmp_path, monkeypatch, capsys):
    """Gegenprobe: Das Deny oben liegt am Befehl, nicht am Einstieg."""
    hook = import_module("prozesscode.hooks.check-bash-permission")
    monkeypatch.setattr(hook, "_LOG_FILE", str(tmp_path / "denied.log"))
    monkeypatch.setattr(hook, "_ALLOWED_LOG_FILE", str(tmp_path / "allowed.log"))
    _mit_stdin(monkeypatch, hook, {"tool_name": "Bash", "tool_input": {"command": "git status"}})
    assert json.loads(capsys.readouterr().out)["hookSpecificOutput"].get(
        "permissionDecision", "allow") == "allow"


@pytest.mark.aufrufpfad("dispatch-edit-write")
def test_dispatcher_gibt_den_grund_eines_checks_als_deny_aus(tmp_path, monkeypatch, capsys):
    # Leeres Repo für check-anchors: Geprüft wird die Weitergabe des Grunds, nicht der
    # Bestand – der echte kostete hier 0,8 s Lesezeit (S133).
    monkeypatch.setattr(import_module("prozesscode.anchors"), "REPO_ROOT", tmp_path)
    daten = {"tool_name": "Write", "tool_input": {
        "file_path": "docs/guidelines/aufrufpfad-probe.md", "content": "Siehe TD-S999-1.\n"}}
    _mit_stdin(monkeypatch, import_module("prozesscode.hooks.dispatch-edit-write"), daten)
    entscheidung = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert entscheidung["permissionDecision"] == "deny"
    assert "TD-S999-1" in entscheidung["permissionDecisionReason"]


@pytest.mark.aufrufpfad("check-code-quality-nonblocking")
def test_nicht_blockierender_hook_meldet_per_exit_2_auf_stderr(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mengenangaben, "LOG", tmp_path / "mengen.log")
    daten = {"tool_name": "Write", "tool_input": {
        "file_path": "docs/aufrufpfad-probe.md", "content": "Das gilt für alle vier Agenten.\n"}}
    code = _mit_stdin(monkeypatch, import_module("prozesscode.hooks.check-code-quality-nonblocking"),
                      daten)
    assert code == 2  # Exit 2 ist der Kanal, über den Claude Code den Hinweis zeigt
    assert "alle vier Agenten" in capsys.readouterr().err


@pytest.mark.aufrufpfad("commit_msg")
def test_commit_msg_weist_nachricht_ohne_betreff_ab(tmp_path, monkeypatch, capsys):
    nachricht = tmp_path / "COMMIT_EDITMSG"
    nachricht.write_text("\nNur ein Rumpf.\n", encoding="utf-8")
    modul = import_module("prozesscode.commit_msg")
    monkeypatch.setattr(sys, "argv", ["commit_msg.py", str(nachricht)])
    assert modul.main() == 1
    assert "Betreff fehlt" in capsys.readouterr().err

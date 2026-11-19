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


@pytest.mark.parametrize("agent_type, erwartet", [
    ("code-quality-auditor", "deny"),
    # Gegenprobe: Implementer schreiben, und ohne `agent_type` läuft die Hauptsession.
    ("backend-layer-implementer", "allow"),
    (None, "allow"),
])
def test_bash_hook_sperrt_auditoren_auf_lesen(tmp_path, monkeypatch, capsys, agent_type, erwartet):
    """Claude Code nennt den Subagenten im Feld `agent_type` – daran hängt die Weiche."""
    hook = import_module("prozesscode.hooks.check-bash-permission")
    monkeypatch.setattr(hook, "_LOG_FILE", str(tmp_path / "denied.log"))
    monkeypatch.setattr(hook, "_ALLOWED_LOG_FILE", str(tmp_path / "allowed.log"))
    daten = {"tool_name": "Bash", "tool_input": {"command": "touch notiz.md"}}
    if agent_type:
        daten["agent_type"] = agent_type
    _mit_stdin(monkeypatch, hook, daten)
    entscheidung = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert entscheidung["permissionDecision"] == erwartet



def _bash_hook_mit_cwd(tmp_path, monkeypatch, capsys, befehl: str, cwd: str | None) -> dict:
    hook = import_module("prozesscode.hooks.check-bash-permission")
    monkeypatch.setattr(hook, "_LOG_FILE", str(tmp_path / "denied.log"))
    monkeypatch.setattr(hook, "_ALLOWED_LOG_FILE", str(tmp_path / "allowed.log"))
    daten = {"tool_name": "Bash", "tool_input": {"command": befehl}}
    if cwd is not None:
        daten["cwd"] = cwd
    _mit_stdin(monkeypatch, hook, daten)
    return json.loads(capsys.readouterr().out)["hookSpecificOutput"]


def _repo_root() -> str:
    return import_module("prozesscode.hooks.check-bash-permission")._NORMALIZE_ROOT


def test_bash_hook_kuerzt_absoluten_repo_pfad_nur_vom_repo_root_aus(tmp_path, monkeypatch, capsys):
    """Gegenprobe zu den beiden folgenden: Im Repo-Root wird relativ ausgeführt."""
    root = _repo_root()
    entscheidung = _bash_hook_mit_cwd(tmp_path, monkeypatch, capsys,
                                      f"python3 {root}/tests/test-bash-permission.py", root)
    assert entscheidung["permissionDecision"] == "allow"
    assert entscheidung["updatedInput"] == {"command": "python3 tests/test-bash-permission.py"}


@pytest.mark.parametrize("cwd_relativ", ["Client", None])
def test_bash_hook_fuehrt_absoluten_pfad_ausserhalb_des_repo_roots_unveraendert_aus(
        tmp_path, monkeypatch, capsys, cwd_relativ):
    """Ein `cd` bleibt in der Hauptsession bestehen (gemessen 2.1.318). Der relative Pfad stimmt
    dann nicht mehr, der absolute schon: aus `cd <root>/Client/src` würde in `Client/` ein
    scheiterndes `cd Client/src`. Ohne `cwd` im Input ist der Standort unbekannt – der absolute
    Pfad ist dann der einzige, der sicher stimmt."""
    root = _repo_root()
    cwd = f"{root}/{cwd_relativ}" if cwd_relativ else None
    entscheidung = _bash_hook_mit_cwd(tmp_path, monkeypatch, capsys,
                                      f"python3 {root}/tests/test-bash-permission.py", cwd)
    assert entscheidung["permissionDecision"] == "allow"
    assert "updatedInput" not in entscheidung
    # Kein Hinweis auf eine Pfad-Kürzung. In `Client/` steht stattdessen der Hinweis auf das
    # verrutschte Arbeitsverzeichnis (OBS-S139-1), ohne `cwd` gar keiner.
    hook = import_module("prozesscode.hooks.check-bash-permission")
    erwartet = hook._CWD_HINWEIS.format(verzeichnis="Client", root=root) if cwd_relativ else None
    assert entscheidung.get("additionalContext") == erwartet


def test_bash_hook_entfernt_filter_auch_ausserhalb_des_repo_roots(tmp_path, monkeypatch, capsys):
    """Der Filter-Strip hängt nicht am Standort – nur die Pfad-Kürzung tut es."""
    root = _repo_root()
    befehl = f"python3 -m prozesscode.vitest-run --file {root}/Client/src/a.test.tsx | tail -5"
    entscheidung = _bash_hook_mit_cwd(tmp_path, monkeypatch, capsys, befehl, f"{root}/Client")
    assert entscheidung["updatedInput"] == {
        "command": f"python3 -m prozesscode.vitest-run --file {root}/Client/src/a.test.tsx"}


@pytest.mark.parametrize("befehl", [
    "touch notiz.md",        # Allow-Muster, für Auditoren gesperrt
    "rm -rf notiz",          # destruktiv: der Grund nennt ein Beispiel mit Marker
    "dotnet test",           # falscher Weg: der Grund verweist auf einen gesperrten Wrapper
    "python3 - <<'EOF'\nprint(1)\nEOF",  # Smart-Hint: empfiehlt Scratchpad plus Marker
])
def test_bash_hook_bietet_auditoren_keinen_marker_an(tmp_path, monkeypatch, capsys, befehl):
    """Den Ausweg über `--allow-once` gibt es für Auditoren nicht – die Meldung darf ihn
    nicht anbieten, auch nicht über den Grund des ursprünglichen Denys."""
    hook = import_module("prozesscode.hooks.check-bash-permission")
    monkeypatch.setattr(hook, "_LOG_FILE", str(tmp_path / "denied.log"))
    monkeypatch.setattr(hook, "_ALLOWED_LOG_FILE", str(tmp_path / "allowed.log"))
    _mit_stdin(monkeypatch, hook, {"tool_name": "Bash", "tool_input": {"command": befehl},
                                   "agent_type": "code-quality-auditor"})
    entscheidung = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert entscheidung["permissionDecision"] == "deny"
    assert "--allow-once" not in entscheidung["permissionDecisionReason"]


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

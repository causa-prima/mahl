"""Tests für checks/tooling_tests.py – PostToolUse-Check, der die Werkzeug-Suite fährt.

`check()` wird ausschließlich mit gemocktem subprocess getestet: ein echter Lauf würde
pytest aus pytest heraus starten.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from checks import tooling_tests as tt
from conftest import make_input


# --- Relevanz: welche Datei löst einen Lauf aus? -----------------------------
def test_watches_scripts_and_hooks():
    assert tt._is_watched(".claude/scripts/qa-check.py")
    assert tt._is_watched(".claude/hooks/check-ref-direction.py")
    assert tt._is_watched("/home/x/repo/.claude/hooks/checks/rop.py")


def test_ignores_non_python_and_unrelated_paths():
    assert not tt._is_watched(".claude/skills/kaizen/SKILL.md")
    assert not tt._is_watched(".claude/settings.json")
    assert not tt._is_watched("Server/Program.cs")
    assert not tt._is_watched("Client/src/main.tsx")


def test_ignores_python_outside_watched_dirs():
    # Ein Python-Script anderswo im Repo bricht diese Suite nicht.
    assert not tt._is_watched("tools/irgendwas.py")


# --- Formatierung: kurz, mit Assertion, gedeckelt ----------------------------
_STDOUT = """\
/home/x/repo/.claude/hooks/tests/test_qa_check.py:37: assert None == 100.0
/home/x/repo/.claude/hooks/tests/test_obs_drain.py:12: assert 3 == 4
2 failed, 285 passed in 0.38s
"""


def test_format_keeps_location_and_assertion():
    msg = tt._format_failures(_STDOUT)
    assert "test_qa_check.py:37: assert None == 100.0" in msg
    assert "test_obs_drain.py:12: assert 3 == 4" in msg
    assert "2 failed, 285 passed in 0.38s" in msg


def test_format_strips_absolute_path_prefix():
    assert "/home/x/repo" not in tt._format_failures(_STDOUT)


def test_format_caps_long_failure_lists():
    lines = "\n".join(
        f"/repo/.claude/hooks/tests/test_x.py:{i}: assert {i} == 0" for i in range(25)
    )
    msg = tt._format_failures(lines + "\n25 failed, 0 passed in 1.0s\n")
    assert "… und 15 weitere" in msg
    # Deckel wirkt: die 11. Detailzeile darf nicht mehr einzeln erscheinen.
    assert "test_x.py:11:" not in msg


# --- check(): Auslösung und fail-open ----------------------------------------
class _Proc:
    def __init__(self, returncode, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


def test_no_run_for_unwatched_file(monkeypatch):
    def fail(*a, **k):
        raise AssertionError("subprocess darf für irrelevante Dateien nicht starten")

    monkeypatch.setattr(tt.subprocess, "run", fail)
    assert tt.check(make_input("Server/Program.cs", "x")) == []


def test_silent_when_suite_is_green(monkeypatch):
    monkeypatch.setattr(tt.subprocess, "run", lambda *a, **k: _Proc(0, "287 passed"))
    assert tt.check(make_input(".claude/scripts/qa-check.py", "x")) == []


def test_reports_when_suite_is_red(monkeypatch):
    monkeypatch.setattr(tt.subprocess, "run", lambda *a, **k: _Proc(1, _STDOUT))
    result = tt.check(make_input(".claude/scripts/qa-check.py", "x"))
    assert len(result) == 1
    assert "Tooling-Tests rot" in result[0]


def test_timeout_is_fail_open(monkeypatch):
    def timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=120)

    monkeypatch.setattr(tt.subprocess, "run", timeout)
    # Ein hängender Testlauf darf keinen Befund erzeugen.
    assert tt.check(make_input(".claude/scripts/qa-check.py", "x")) == []


def test_missing_interpreter_is_fail_open(monkeypatch):
    def oserror(*a, **k):
        raise OSError("kein python")

    monkeypatch.setattr(tt.subprocess, "run", oserror)
    assert tt.check(make_input(".claude/scripts/qa-check.py", "x")) == []

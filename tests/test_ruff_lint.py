"""Tests für checks/ruff_lint.py – PostToolUse-Linter über den Prozess-Code.

Drei Zusagen: Der Check greift nur bei Python des Prozess-Codes, er lintet die GEÄNDERTE
Datei (nicht den Bestand), und er meldet sich, wenn ruff fehlt oder abstürzt, statt still
zu verschwinden. Warum es den Check neben `ruff-run.py` gibt: im Modul-Docstring.
"""

from prozesscode.hooks.checks import ruff_lint as rl
from conftest import make_input


class _Lauf:
    def __init__(self, stdout: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


# --- Relevanz ----------------------------------------------------------------
def test_prueft_python_unter_prozesscode_und_tests():
    assert rl._is_watched("prozesscode/qa-check.py")
    assert rl._is_watched("prozesscode/hooks/checks/rop.py")
    assert rl._is_watched("tests/test_ruff_lint.py")


def test_ignoriert_nicht_python_und_fremde_pfade():
    assert not rl._is_watched(".claude/skills/kaizen/SKILL.md")
    assert not rl._is_watched("Server/Program.cs")
    assert not rl._is_watched("tools/irgendwas.py")


# --- Verhalten ---------------------------------------------------------------
def test_saubere_datei_erzeugt_keine_warnung(monkeypatch):
    monkeypatch.setattr(rl, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(rl, "_laufe", lambda *_a: _Lauf("All checks passed!\n", 0))
    assert rl.check(make_input("prozesscode/qa-check.py", "x = 1\n")) == []


def test_fundstellen_erscheinen_in_der_warnung(monkeypatch):
    monkeypatch.setattr(rl, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(rl, "_laufe", lambda *_a: _Lauf(
        "prozesscode/qa-check.py:12:5: F401 `os` imported but unused\n"
        "Found 1 error.\n", 1))
    warnungen = rl.check(make_input("prozesscode/qa-check.py", "x = 1\n"))
    assert len(warnungen) == 1
    assert "F401" in warnungen[0]
    assert "prozesscode.ruff-run" in warnungen[0], "der Weg zum vollen Lauf fehlt"


def test_geprueft_wird_die_geaenderte_datei(monkeypatch):
    """Gegenprobe: Ein Linter, der eine andere Datei liest, ist grün und wertlos."""
    gesehen = {}

    def _merke(*befehl: str) -> _Lauf:
        gesehen["befehl"] = befehl
        return _Lauf("All checks passed!\n", 0)

    monkeypatch.setattr(rl, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(rl, "_laufe", _merke)
    rl.check(make_input("prozesscode/doc.py", "x = 1\n"))
    assert any(teil.endswith("doc.py") for teil in gesehen["befehl"])


def test_fehlendes_venv_meldet_sich_statt_stumm_auszufallen(monkeypatch):
    """Ohne .venv gäbe es sonst nie wieder eine Lint-Meldung – und niemand erführe davon."""
    monkeypatch.setattr(rl, "_ruff_vorhanden", lambda: False)
    warnungen = rl.check(make_input("prozesscode/qa-check.py", "x = 1\n"))
    assert len(warnungen) == 1
    assert "requirements-dev.txt" in warnungen[0]


def test_ein_ruff_absturz_reisst_den_hook_nicht_mit(monkeypatch):
    """Der Linter ist Beiwerk; sein Ausfall darf das Schreiben nicht blockieren."""
    def kracht(*_a):
        raise OSError("ruff kaputt")

    monkeypatch.setattr(rl, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(rl, "_laufe", kracht)
    warnungen = rl.check(make_input("prozesscode/qa-check.py", "x = 1\n"))
    assert len(warnungen) == 1
    assert "ruff kaputt" in warnungen[0]

"""Zwei Wurzeln, zwei Begriffe: wo der Code liegt und wo Claude Code läuft.

In einem git-Worktree fallen beide auseinander. Ein Werkzeug, das Repo-Dateien liest oder
`dotnet`/`npm` startet, muss im Repo seines eigenen Codes arbeiten – sonst prüfte es im Worktree
still das Hauptrepo. Nur der Ordner der Session-Logs ist nach dem Startverzeichnis von Claude
Code benannt.
"""
import importlib
from pathlib import Path

import pytest

from prozesscode import _util

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def util_neu_geladen(monkeypatch):
    """Lädt `_util` unter der gesetzten Umgebung neu – REPO_ROOT entsteht beim Import."""
    def laden():
        return importlib.reload(_util)
    yield laden
    monkeypatch.undo()
    importlib.reload(_util)


def test_repo_root_folgt_dem_dateipfad_auch_bei_anderem_projektverzeichnis(
        monkeypatch, tmp_path, util_neu_geladen):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert util_neu_geladen().REPO_ROOT == REPO


def test_projektverzeichnis_kommt_von_claude_code(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert _util.projekt_verzeichnis() == tmp_path


def test_projektverzeichnis_ohne_claude_code_ist_das_repo(monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert _util.projekt_verzeichnis() == REPO

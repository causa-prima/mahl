"""Tests für check-anchors.py – der PreToolUse-Hook um anchors.py herum.

Die Prüflogik (tote Verweise, falsche Pfade, verwaiste Anker) steht in test_anchors.py. Hier
steht der Hook-Vertrag über den Weg, den der Dispatcher nimmt: `check(payload)`.
"""
from importlib import import_module

import pytest

hook = import_module("prozesscode.hooks.check-anchors")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(hook.anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ziel.md").write_text(
        '# Ziel\n\n<a id="ZIE-da"></a>\n## Da\n\nText.\n', encoding="utf-8")
    return tmp_path


def _write(pfad, inhalt):
    return {"tool_name": "Write", "tool_input": {"file_path": str(pfad), "content": inhalt}}


@pytest.mark.aufrufpfad("check-anchors")
def test_verweis_ohne_ziel_blockt(repo):
    grund = hook.check(_write(repo / "docs" / "neu.md", "Siehe [tot](ziel.md#ZIE-weg).\n"))
    assert grund and "ZIE-weg" in grund


def test_verweis_mit_ziel_passiert(repo):
    """Gegenprobe: Der Block oben liegt am fehlenden Ziel, nicht am Verweis an sich."""
    assert hook.check(_write(repo / "docs" / "neu.md", "Siehe [da](ziel.md#ZIE-da).\n")) is None

"""Tests für obs_parse.running_session – welche Session läuft gerade?

Der Fall, der die naive Rechnung „höchste Session-Datei + 1" bricht: `closing-session` legt
`session_NNN.md` mitten in der Session an (Schritt 4) und schreibt danach noch Learnings
(Schritt 5). Ab Schritt 4 lieferte „+1" die Nummer der FOLGE-Session, neue Einträge bekämen
also eine falsche ID. Unterscheidungsmerkmal ist der Commit-Zustand der Datei.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

import obs_parse


def _repo(tmp_path, sessions: list[int], committen: bool = True):
    """Minimales git-Repo mit Session-Dateien; optional alle committet."""
    (tmp_path / "docs" / "history" / "sessions").mkdir(parents=True)
    for nummer in sessions:
        (tmp_path / "docs" / "history" / "sessions" / f"session_{nummer}.md").write_text(
            f"# Session {nummer}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    if committen:
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-qm", "sessions"], cwd=tmp_path, check=True)
    return tmp_path


# --- latest_session_file -----------------------------------------------------
def test_finds_the_highest_session_number(tmp_path):
    root = _repo(tmp_path, [38, 112, 113])
    nummer, pfad = obs_parse.latest_session_file(root)
    assert nummer == 113
    assert pfad.name == "session_113.md"


def test_none_without_a_sessions_directory(tmp_path):
    assert obs_parse.latest_session_file(tmp_path) is None


# --- running_session ---------------------------------------------------------
def test_committed_session_file_means_the_next_session_is_running(tmp_path):
    """Normalfall: Die letzte Session ist abgeschlossen und committet."""
    root = _repo(tmp_path, [112, 113])
    assert obs_parse.running_session(root) == 114


def test_uncommitted_session_file_is_the_running_session(tmp_path):
    """Der kritische Fall: `closing-session` hat die Datei gerade erst angelegt."""
    root = _repo(tmp_path, [112, 113])
    (root / "docs" / "history" / "sessions" / "session_114.md").write_text(
        "# Session 114\n", encoding="utf-8")
    assert obs_parse.running_session(root) == 114


def test_modified_but_tracked_session_file_also_counts_as_running(tmp_path):
    root = _repo(tmp_path, [112, 113])
    (root / "docs" / "history" / "sessions" / "session_113.md").write_text(
        "# Session 113 – ergänzt\n", encoding="utf-8")
    assert obs_parse.running_session(root) == 113


def test_falls_back_to_plus_one_without_git(tmp_path):
    """Ohne git-Repo bleibt es beim alten Verhalten – nie schlechter als vorher."""
    (tmp_path / "docs" / "history" / "sessions").mkdir(parents=True)
    (tmp_path / "docs" / "history" / "sessions" / "session_50.md").write_text("x", encoding="utf-8")
    assert obs_parse.running_session(tmp_path) == 51


def test_none_without_any_session_file(tmp_path):
    assert obs_parse.running_session(tmp_path) is None


def test_current_session_keeps_its_naive_behaviour(tmp_path):
    """`current_session` bleibt unverändert – `obs-drain.py` nutzt es nur für die Altersanzeige,
    wo ein Off-by-one folgenlos ist."""
    root = _repo(tmp_path, [112, 113])
    (root / "docs" / "history" / "sessions" / "session_114.md").write_text("x", encoding="utf-8")
    assert obs_parse.current_session(root) == 115
    assert obs_parse.running_session(root) == 114

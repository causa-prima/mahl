"""Tests für repo_kontext – welche Session läuft gerade?

Die Nummer kommt aus der Git-Historie: Abgeschlossen ist eine Session mit ihrem
Abschluss-Commit, und der trägt den Trailer `Session-Ende: <NNN>`. Der Fall, der eine
Ableitung über die Betreffzeile bricht: Eine Session darf mehrfach committen, aber nur einer
dieser Commits beendet sie – „Betreff + 1" nennt ab dem ersten Zwischen-Commit die
FOLGE-Session, und jeder neue Tracker-Eintrag bekäme eine falsche ID.
"""
import subprocess


import pytest
from prozesscode import repo_kontext


@pytest.fixture(autouse=True)
def _warnung_zuruecksetzen():
    """Der Rückfall warnt nur einmal je Prozess – für den Test je Testfall neu."""
    repo_kontext._betreff_gewarnt = False


def _repo(tmp_path, nachrichten: list[str]):
    """Minimales git-Repo mit je einem Commit pro Nachricht."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    for i, nachricht in enumerate(nachrichten):
        (tmp_path / f"datei_{i}.txt").write_text(str(i), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-q", "-m", nachricht], cwd=tmp_path, check=True)
    return tmp_path


def _abschluss(nummer: int, titel: str = "Titel") -> str:
    return f"Session {nummer}: {titel}\n\nRumpf.\n\nSession-Ende: {nummer}\n"


# --- Regelfall: der Trailer des Abschluss-Commits -----------------------------
def test_running_session_is_the_last_closed_one_plus_one(tmp_path):
    root = _repo(tmp_path, [_abschluss(112), _abschluss(113)])
    assert repo_kontext.current_session(root) == 114


def test_intermediate_commits_do_not_advance_the_number(tmp_path):
    """Zwischen-Commits tragen die Session-Nummer im Betreff, aber keinen Trailer –
    die Session läuft weiter (Bestandsbeleg: zwei Commits „Session 124: …")."""
    root = _repo(tmp_path, [_abschluss(123), "Session 124: Zwischenstand\n\nRumpf.\n"])
    assert repo_kontext.current_session(root) == 124


def test_highest_trailer_wins_regardless_of_commit_order(tmp_path):
    """Ein Nachtrag (Doku-Fix, Revert) hinter dem Abschluss darf die Nummer nicht senken."""
    root = _repo(tmp_path, [_abschluss(113), "Tippfehler\n"])
    assert repo_kontext.current_session(root) == 114


def test_trailer_must_stand_on_its_own_line(tmp_path):
    """Prosa über den Trailer ist kein Abschluss – sonst verschiebt jede Erwähnung die Nummer."""
    root = _repo(tmp_path, [_abschluss(113), "Session 114: x\n\nsiehe Session-Ende: 114 oben\n"])
    assert repo_kontext.current_session(root) == 114


# --- Rückfall auf die Betreff-Konvention --------------------------------------
def test_falls_back_to_the_subject_line_and_warns(tmp_path, capsys):
    """Ohne jeden Trailer (Alt-Historie, oder ein Abschluss ohne closing-session) trägt
    die Betreff-Konvention – hörbar, weil sie den Zwischen-Commit-Fall nicht kennt."""
    root = _repo(tmp_path, ["Session 124: Umbau\n", "Session 125: Umbau\n"])
    assert repo_kontext.current_session(root) == 126
    assert "WARNUNG" in capsys.readouterr().err


def test_subject_fallback_ignores_the_body(tmp_path, capsys):
    """Der Rückfall liest nur Betreffzeilen – ein zitierter Betreff im Rumpf zählt nicht."""
    root = _repo(tmp_path, ["Session 124: Umbau\n\nWie in Session 200: dort beschrieben.\n"])
    assert repo_kontext.current_session(root) == 125
    capsys.readouterr()


def test_the_fallback_warns_once_per_process(tmp_path, capsys):
    """`session-agenda.py` fragt die Nummer mehrfach an – viermal dieselbe Zeile liest sich
    wie vier Befunde."""
    root = _repo(tmp_path, ["Session 125: Umbau\n"])
    repo_kontext.current_session(root)
    capsys.readouterr()
    repo_kontext.current_session(root)
    assert capsys.readouterr().err == ""


def test_none_without_any_session_commit(tmp_path, capsys):
    """Kein Session-Commit -> Nummer unbestimmbar (None), kein 0-Sentinel."""
    root = _repo(tmp_path, ["init\n"])
    assert repo_kontext.current_session(root) is None
    capsys.readouterr()


def test_none_outside_a_git_repository(tmp_path, capsys):
    """git-Aufruf schlägt fehl -> None statt Absturz."""
    assert repo_kontext.current_session(tmp_path / "kein-repo") is None
    capsys.readouterr()

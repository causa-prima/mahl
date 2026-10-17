"""Tests für tracker_preview.py – was der User im Freigabedialog zu einem Tracker-Befehl liest.

Die Änderung selbst zeigt der Mod `tracker-diff` im Pane neben dem Prompt (`tracker_diff.py`).
Der Dialog trägt nur noch eine Kopfzeile – sie bleibt, damit ohne Pane (Mod aus, Terminal zu
schmal, andere Oberfläche) wenigstens zu sehen ist, was angefasst wird.

Vier Zusagen:
  1. Eine Kopfzeile: Werkzeug, Unterbefehl, Eintrag, Datei – mit Wortgrenzen.
  2. `remove` warnt: Der Eintrag geht ersatzlos verloren.
  3. Shell-Metazeichen werden gemeldet, wo die Shell sie auswertet: Dann weicht der
     geschriebene Text vom Befehl ab, ohne dass Script oder Aufrufer es bemerken (S117).
  4. Nichts davon darf den Permission-Hook stören: Unparsbares ergibt None, kein
     Terminal-Escape im Text (der Dialog zeigt ihn sonst als Bytes).
"""
from importlib import import_module

import pytest

tp = import_module("prozesscode.tracker_preview")


# --- Kopfzeile ----------------------------------------------------------------
@pytest.mark.parametrize("befehl, kopf", [
    ('python3 -m prozesscode.obs set OBS-S110-1 --status "UMGESETZT (S124)"',
     "obs set OBS-S110-1 → docs/kaizen/observations.md"),
    # Beim Paket-Umzug (S129) fiel das Leerzeichen zwischen Werkzeug und Unterbefehl weg
    # („obsadd") – im Dialog las sich das wie ein anderer Befehl.
    ('python3 -m prozesscode.obs add --titel "Neu" --bezug LL-S1-1',
     "obs add → docs/kaizen/observations.md"),
    ("python3 -m prozesscode.td set TD-S080-1 --titel X", "td set TD-S080-1 → docs/tech-debt.md"),
    ("python3 -m prozesscode.oq remove OQ-S094-1", "oq remove OQ-S094-1 → docs/open-questions.md"),
    ("python3 -m prozesscode.lessons add --titel X",
     "lessons add → docs/kaizen/lessons_learned.md"),
])
def test_die_kopfzeile_nennt_werkzeug_eintrag_und_datei(befehl, kopf):
    assert tp.vorschau(befehl).splitlines()[0].startswith(kopf)


def test_die_kopfzeile_verweist_auf_das_pane():
    assert "Pane" in tp.vorschau("python3 -m prozesscode.td set TD-S080-1 --titel X")


def test_feldwerte_stehen_nicht_mehr_im_dialog():
    """Gegenprobe zur Verkürzung: Die Werte zeigt das Pane, nicht der Prompt."""
    out = tp.vorschau('python3 -m prozesscode.obs set OBS-S110-1 --status "UMGESETZT (S124)"')
    assert "UMGESETZT" not in out


# --- Löschen ------------------------------------------------------------------
def test_remove_warnt_vor_dem_ersatzlosen_loeschen():
    assert "ersatzlos" in tp.vorschau("python3 -m prozesscode.oq remove OQ-S094-1")


def test_set_warnt_nicht_vor_dem_loeschen():
    assert "ersatzlos" not in tp.vorschau("python3 -m prozesscode.oq set OQ-S094-1 --frage X")


# --- Shell-Metazeichen -------------------------------------------------------
def test_metazeichen_werden_gemeldet():
    out = tp.vorschau('python3 -m prozesscode.obs set OBS-S110-1 --entscheidung "siehe `foo.py`"')
    assert "Shell" in out


def test_ohne_metazeichen_keine_warnung():
    """Gegenprobe – sonst stünde die Warnung immer da und hätte keine Aussage."""
    out = tp.vorschau('python3 -m prozesscode.obs set OBS-S110-1 --entscheidung "siehe foo.py"')
    assert "Shell" not in out


@pytest.mark.parametrize("befehl, wertet_aus", [
    ("x --a 'siehe `foo.py` und $(date)'", False),   # einfache Anführungszeichen: alles wörtlich
    ('x --a "siehe `foo.py`"', True),                 # doppelte: Backticks laufen
    ('x --a "heute $(date)"', True),
    ("x --a ungequotet`id`", True),
    ("x --a 'erst wörtlich' \"dann $(date)\"", True),
    ("x --a 'it'\\''s `ok`'", False),                 # Quote-Wechsel innerhalb eines Worts
])
def test_metazeichen_zaehlen_nur_wo_die_shell_sie_auswertet(befehl, wertet_aus):
    assert tp.metazeichen(befehl) is wertet_aus


# --- Robustheit: der Hook darf nie fallen ------------------------------------
def test_die_vorschau_enthaelt_keine_terminal_escapes():
    """Der Freigabedialog rendert ANSI nicht (seit S129, undokumentiert) – er zeigt die Bytes."""
    for befehl in ('python3 -m prozesscode.obs set OBS-S110-1 --status "X `y`"',
                   "python3 -m prozesscode.oq remove OQ-S094-1"):
        assert "\x1b" not in tp.vorschau(befehl)


@pytest.mark.parametrize("befehl", [
    "python3 -m prozesscode.obs get OBS-S110-1",
    'python3 -m prozesscode.obs set OBS-S110-1 --status "offen',
    "ls -la",
])
def test_kein_tracker_schreibbefehl_ergibt_none(befehl):
    assert tp.vorschau(befehl) is None

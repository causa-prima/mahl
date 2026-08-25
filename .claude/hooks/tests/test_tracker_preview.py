"""Tests für tracker_preview.py – was der User im Freigabedialog sieht.

Hintergrund (OBS-S116-1): Seit die Tracker über Scripte geschrieben werden, zeigt der
Freigabedialog eine lange Kommandozeile statt eines Diffs. Der User kann den Inhalt so vor
der Freigabe nicht prüfen – bei `Edit` konnte er es. Empirisch (S124) trägt
`permissionDecisionReason` mehrzeiligen Text, Einrückung, Unicode-Rahmen und ANSI, aber kein
Markdown; die Darstellung nutzt daher ANSI.

Vier Zusagen:
  1. Beim ANLEGEN eine leserliche Auflistung der Felder – kein Diff, es gibt kein Vorher.
  2. Beim ÄNDERN Vorher und Nachher je betroffenem Feld, Vorher aus der Datei gelesen.
  3. Shell-Metazeichen werden gemeldet: Sie verändern den geschriebenen Text, ohne dass
     Script oder Aufrufer es bemerken (Schadensfall S117) – dann weicht auch diese Vorschau
     von dem ab, was wirklich ankommt.
  4. Nichts davon darf den Permission-Hook zum Absturz bringen: Unparsbares ergibt None.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
tp = import_module("tracker_preview")

BESTAND = """# Observations

## OBS-S110-1 – Erster
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: irgendwas
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
"""


def repo(tmp_path):
    ziel = tmp_path / "docs" / "kaizen"
    ziel.mkdir(parents=True)
    (ziel / "observations.md").write_text(BESTAND, encoding="utf-8")
    return tmp_path


def klartext(s: str) -> str:
    """ANSI-Sequenzen raus – die Tests prüfen Inhalt, nicht Farbe."""
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s or "")


# --- Ändern: Vorher/Nachher --------------------------------------------------
def test_set_zeigt_alten_und_neuen_wert(tmp_path):
    out = klartext(tp.vorschau(
        'python3 .claude/scripts/obs.py set OBS-S110-1 --status "UMGESETZT (S124)"',
        root=repo(tmp_path)))
    assert "OBS-S110-1" in out
    assert "NEU" in out                    # Vorher, aus der Datei
    assert "UMGESETZT (S124)" in out       # Nachher, aus dem Befehl


def test_set_zeigt_nur_betroffene_felder(tmp_path):
    """Gegenprobe: Ein Feld, das der Befehl nicht anfasst, gehört nicht in den Diff."""
    out = klartext(tp.vorschau(
        'python3 .claude/scripts/obs.py set OBS-S110-1 --status "UMGESETZT (S124)"',
        root=repo(tmp_path)))
    assert "Quelle" not in out
    assert "Kategorie" not in out


def test_set_uebersetzt_argument_in_feldnamen(tmp_path):
    out = klartext(tp.vorschau(
        'python3 .claude/scripts/obs.py set OBS-S110-1 --entscheidung "fertig"',
        root=repo(tmp_path)))
    assert "Entscheidung/Maßnahme" in out
    assert "offen - beim Drain" in out
    assert "fertig" in out


# --- Anlegen: nur Klartext ---------------------------------------------------
def test_add_listet_felder_ohne_diff(tmp_path):
    out = klartext(tp.vorschau(
        'python3 .claude/scripts/obs.py add --titel "Neuer Punkt" --impact MITTEL '
        '--kontext Doku --beobachtung "etwas faellt auf"',
        root=repo(tmp_path)))
    assert "Neuer Punkt" in out
    assert "etwas faellt auf" in out
    assert "Doku" in out


# --- Shell-Metazeichen -------------------------------------------------------
def test_metazeichen_werden_gemeldet(tmp_path):
    out = klartext(tp.vorschau(
        'python3 .claude/scripts/obs.py set OBS-S110-1 --entscheidung "siehe `foo.py`"',
        root=repo(tmp_path)))
    assert "Shell" in out


def test_ohne_metazeichen_keine_warnung(tmp_path):
    """Gegenprobe – sonst stünde die Warnung immer da und hätte keine Aussage."""
    out = klartext(tp.vorschau(
        'python3 .claude/scripts/obs.py set OBS-S110-1 --entscheidung "siehe foo.py"',
        root=repo(tmp_path)))
    assert "Shell" not in out


# --- Löschen: der irreversible Fall ------------------------------------------
OQ_BESTAND = """# Offene Fragen

## OQ-S094-1 — Erste Frage
**Frage:** Lohnt sich X?
**Fällig:** Phase:V1 – weil Y
**Hintergrund:** Kam mehrfach auf.
"""


def oq_repo(tmp_path):
    ziel = tmp_path / "docs"
    ziel.mkdir(parents=True)
    (ziel / "open-questions.md").write_text(OQ_BESTAND, encoding="utf-8")
    return tmp_path


def test_remove_zeigt_den_ganzen_eintrag(tmp_path):
    """`remove` ist irreversibel und hinterlässt keine Archivkopie – die Vorschau muss
    deshalb den vollständigen Eintrag zeigen, nicht nur betroffene Felder."""
    out = klartext(tp.vorschau('python3 .claude/scripts/oq.py remove OQ-S094-1',
                               root=oq_repo(tmp_path)))
    assert "ERSATZLOS" in out
    assert "Lohnt sich X?" in out
    assert "Kam mehrfach auf." in out


def test_oq_set_liest_das_andere_feldformat(tmp_path):
    """OQ nutzt `**Feld:**` statt `- Feld:` – ohne das Muster bliebe das Vorher leer."""
    out = klartext(tp.vorschau(
        'python3 .claude/scripts/oq.py set OQ-S094-1 --faellig "S200 – verschoben"',
        root=oq_repo(tmp_path)))
    assert "Phase:V1 – weil Y" in out      # Vorher, aus der Datei
    assert "S200 – verschoben" in out      # Nachher


# --- Robustheit: der Hook darf nie fallen ------------------------------------
def test_unbekannter_befehl_ergibt_none(tmp_path):
    assert tp.vorschau("python3 .claude/scripts/obs.py get OBS-S110-1",
                       root=repo(tmp_path)) is None


def test_unparsbare_quotes_ergeben_none(tmp_path):
    assert tp.vorschau('python3 .claude/scripts/obs.py set OBS-S110-1 --status "offen',
                       root=repo(tmp_path)) is None


def test_fehlende_datei_ergibt_none(tmp_path):
    assert tp.vorschau('python3 .claude/scripts/obs.py set OBS-S110-1 --status X',
                       root=tmp_path) is None


def test_unbekannte_id_ergibt_none(tmp_path):
    assert tp.vorschau('python3 .claude/scripts/obs.py set OBS-S999-9 --status X',
                       root=repo(tmp_path)) is None

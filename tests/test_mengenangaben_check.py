"""Tests für checks/mengenangaben.py – Warnung bei neuen Mengenangaben in Prosa (S133).

Mengenangaben („alle vier Agenten") veralten still, wenn die gezählte Menge anderswo definiert
ist und wächst. Blockieren wäre falsch – in S133 gesichtet waren 18 von 20 Treffern keine
echten Fälle –, also warnt der Check nach dem Edit, und der Autor entscheidet. Das Log hält
jede Warnung fest, damit die Retro messen kann, ob Warnungen etwas bewirken.
"""
import pytest

from prozesscode.hooks.checks import mengenangaben as mg
from prozesscode.hooks.checks.common import parse_input


def _edit(pfad, alt, neu):
    return parse_input({"tool_name": "Edit", "tool_input": {
        "file_path": str(pfad), "old_string": alt, "new_string": neu}})


def _write(pfad, inhalt):
    return parse_input({"tool_name": "Write", "tool_input": {
        "file_path": str(pfad), "content": inhalt}})


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Simuliertes Repo; Log und git-Stand zeigen ins Leere, nie auf die echten Dateien."""
    monkeypatch.setattr(mg.anchors, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mg, "LOG", tmp_path / ".claude" / "tmp" / "mengen.log")
    monkeypatch.setattr(mg, "_stand_in_git", lambda _rel: "")
    (tmp_path / "docs").mkdir()
    return tmp_path


# --- Warnung ---------------------------------------------------------------------
def test_neue_mengenangabe_erzeugt_eine_warnung(repo):
    warnung = mg.check(_edit(repo / "docs/guide.md", "Text.", "Text.\nWarte auf alle vier Agenten."))
    assert len(warnung) == 1
    assert "alle vier Agenten" in warnung[0]


def test_die_warnung_sagt_was_zu_tun_ist(repo):
    """Meldungen nennen den Ausweg (CGP-meldungen) – hier die Frage, die der Autor klären muss."""
    text = mg.check(_edit(repo / "docs/guide.md", "", "Die drei Felder sind Pflicht."))[0]
    assert "anderswo" in text
    assert "ordinal-ok" in text


def test_marker_hebt_die_warnung_auf(repo):
    """Die Warnung nennt `ordinal-ok` als Ausweg – der muss auch wirken."""
    neu = "Warte auf alle vier Agenten.  <!-- ordinal-ok -->"
    assert mg.check(_edit(repo / "docs/guide.md", "", neu)) == []


def test_ist_im_nicht_blockierenden_hook_registriert():
    """Ein Check ohne Aufrufer läuft fehlerfrei und tut nichts (RCL-prozess-code)."""
    from importlib import import_module
    hook = import_module("prozesscode.hooks.check-code-quality-nonblocking")
    assert mg.check in hook.CHECKS


def test_ohne_mengenangabe_keine_warnung(repo):
    assert mg.check(_edit(repo / "docs/guide.md", "Text.", "Warte auf alle Agenten.")) == []


def test_bestehende_mengenangabe_warnt_nicht(repo):
    """Nur hinzugekommene Zeilen – eine Altlast in der Nähe ist nicht der Autor dieses Edits."""
    zeile = "Warte auf alle vier Agenten."
    assert mg.check(_edit(repo / "docs/guide.md", zeile, zeile + "\nNeuer Satz.")) == []


@pytest.mark.parametrize("rel", ["docs/kaizen/countermeasures.md",
                                 "docs/kaizen/observations.md",
                                 "docs/kaizen/lessons_learned.md"])
def test_kaizen_chroniken_sind_ausgenommen(repo, rel):
    """Dort sind Zählungen Momentaufnahmen einer Retro und stimmen per Natur (S133: 13 von 20)."""
    assert mg.check(_edit(repo / rel, "", "Die sieben Rückfälle zerfallen.")) == []
    assert not mg.LOG.exists()


def test_historie_ist_ausgenommen(repo):
    assert mg.check(_edit(repo / "docs/history/adr.md", "", "Alle drei Punkte gelten.")) == []


def test_write_vergleicht_mit_dem_stand_in_git(repo, monkeypatch):
    """Ein Write ersetzt die ganze Datei; ohne Vorher-Stand wäre jede alte Zahl „neu"."""
    alt = "Warte auf alle vier Agenten.\n"
    monkeypatch.setattr(mg, "_stand_in_git", lambda _rel: alt)
    assert mg.check(_write(repo / "docs/guide.md", alt + "Neuer Satz.\n")) == []


def test_write_einer_neuen_datei_prueft_alles(repo):
    assert len(mg.check(_write(repo / "docs/neu.md", "Alle drei Punkte gelten.\n"))) == 1


# --- Log: Grundlage der Wirksamkeitsmessung ----------------------------------------
def test_jede_warnung_landet_mit_datum_im_log(repo):
    mg.check(_edit(repo / "docs/guide.md", "", "Warte auf alle vier Agenten."))
    spalten = mg.LOG.read_text(encoding="utf-8").rstrip("\n").split("\t")
    assert spalten[0] == "docs/guide.md"
    assert spalten[1] == "alle vier Agenten"
    assert len(spalten) == 4 and spalten[3][:4].isdigit()  # Datum: vor/nach der Warnung trennbar


def test_log_zeigt_die_umgebung_des_treffers(repo):
    """Doku-Zeilen sind lang: Die Beurteilung braucht die Umgebung, nicht den Zeilenanfang."""
    lang = "Vorspann dazu. " * 20 + "Warte auf alle vier Agenten, dann weiter."
    mg.check(_edit(repo / "docs/guide.md", "", lang))
    assert "dann weiter" in mg.LOG.read_text(encoding="utf-8")


def test_log_fehler_unterdrueckt_die_warnung_nicht(repo, monkeypatch):
    """Fail-open in beide Richtungen: Das Protokoll ist Nebenzweck."""
    monkeypatch.setattr(mg.Path, "mkdir", _wirft)
    assert len(mg.check(_edit(repo / "docs/guide.md", "", "Alle drei Punkte gelten."))) == 1


def _wirft(*_args, **_kwargs):
    raise OSError("Platte voll")


# --- Nachgeschärft nach der Mutationssichtung (S133) ---------------------------------
def test_stand_in_git_liest_den_echten_commit_stand():
    """Alle übrigen Tests ersetzen diese Funktion – genau die Lücke aus CM-S133-1."""
    assert "KISS" in mg._stand_in_git("docs/guidelines/coding-guideline-general.md")


def test_stand_in_git_ist_leer_fuer_unversionierte_dateien():
    assert mg._stand_in_git("docs/gibt-es-nicht-s133.md") == ""


def test_ausschnitt_zeigt_das_fenster_um_den_fund():
    zeile = "x" * 100 + "FUND" + "y" * 100
    assert mg._ausschnitt(zeile, "FUND", breite=20) == "…" + "x" * 8 + "FUND" + "y" * 8 + "…"


def test_ausschnitt_laesst_kurze_zeilen_unveraendert():
    assert mg._ausschnitt("alle vier Agenten", "vier", breite=160) == "alle vier Agenten"


def test_ausschnitt_am_zeilenanfang_ohne_fuehrende_auslassung():
    """Das Fenster bleibt symmetrisch: Der ungenutzte linke Rand wandert nicht nach rechts."""
    zeile = "FUND" + "y" * 100
    assert mg._ausschnitt(zeile, "FUND", breite=20) == "FUND" + "y" * 8 + "…"


def test_zweite_warnung_landet_ebenfalls_im_log(repo):
    """Beim zweiten Mal existiert der Log-Ordner schon – das darf nichts verschlucken."""
    mg.check(_edit(repo / "docs/guide.md", "", "Warte auf alle vier Agenten."))
    mg.check(_edit(repo / "docs/guide.md", "", "Die drei Felder sind Pflicht."))
    assert len(mg.LOG.read_text(encoding="utf-8").splitlines()) == 2


def test_muster_ausnahme_der_datei_unterdrueckt_die_warnung(repo, monkeypatch):
    monkeypatch.setitem(mg.anchors.MUSTER_AUSNAHMEN, "docs/werkzeugtest.md", frozenset({"ordinal"}))
    assert mg.check(_edit(repo / "docs/werkzeugtest.md", "", "Alle drei Punkte gelten.")) == []


def test_warnung_nennt_hoechstens_fuenf_fundstellen(repo):
    zeilen = "\n".join(f"Satz {i}: alle drei Punkte gelten." for i in range(7))
    warnung = mg.check(_edit(repo / "docs/guide.md", "", zeilen))[0]
    assert warnung.count("„alle drei Punkte“") == 5

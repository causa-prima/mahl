"""Tests für mutmut-run.py – Wrapper um den Mutationslauf des Prozess-Codes.

Geprüft wird, was der Wrapper aus den Ergebnissen macht: Verdikt, Deckelung und die
Ausweisung der Ausnahmeliste. Das Lesen der Ergebnisse selbst steht in
`test_mutmut_meta.py`, die Sperrklinke in `test_mutmut_ratchet.py`.
Ein echter Mutationslauf kommt hier nicht vor – er dauert Minuten bis Stunden und liefe
pytest aus pytest heraus.
"""
from importlib import import_module

mr = import_module("prozesscode.mutmut-run")

# --- Verdikt -----------------------------------------------------------------
def test_verdikt_ohne_befund_ist_gruen():
    eintraege = [(f"a.x__mutmut_{i}", "killed") for i in range(130)]
    verdikt, details = mr.baue_verdikt(eintraege)
    assert verdikt.startswith("✓")
    assert "130" in verdikt
    assert details is None


def test_das_verdikt_nennt_die_noch_offenen_mutanten():
    """Ein Lauf über ein großes Modul kommt nicht in einem Durchgang durch.

    Real gemessen: `check-bash-permission` hat 646 Mutanten, nach einem Lauf waren 242
    bewertet und 339 offen. „242 Mutanten bewertet" allein liest sich wie ein
    abgeschlossenes Ergebnis – der Rest verschwindet still, und der Score gilt für einen
    Ausschnitt, dessen Größe niemand kennt.
    """
    eintraege = ([("a.x__mutmut_1", "killed")]
                 + [(f"a.x__mutmut_{i}", "not checked") for i in range(2, 100)])
    verdikt, _ = mr.baue_verdikt(eintraege)
    assert "98 offen" in verdikt


def test_ohne_offene_kein_nachsatz():
    """GEGENPROBE: Ist ein Modul durch, soll die Zeile nicht mit einer Null zumüllen."""
    verdikt, _ = mr.baue_verdikt([("a.x__mutmut_1", "killed")])
    assert "offen" not in verdikt


def test_nicht_bewertete_zaehlen_nicht_in_den_nenner():
    """`not checked` heißt: der Mutant lag außerhalb des Ausschnitts.

    Real gemessen meldete der Wrapper zunächst „11606 Mutanten" für einen Lauf, der 130
    bewertet hatte – der Nenner war der Bestand des ganzen Baums, nicht das Gemessene.
    """
    eintraege = [("a.x__mutmut_1", "killed")] + [
        (f"a.x__mutmut_{i}", "not checked") for i in range(2, 100)]
    verdikt, _ = mr.baue_verdikt(eintraege)
    assert "1 Mutant" in verdikt and "100" not in verdikt


def test_verdikt_nennt_ueberlebende_und_ungetestete_getrennt():
    """Beides ist eine Lücke, aber eine andere: `survived` heißt, ein Test lief und merkte
    nichts; `no tests` heißt, kein Test deckt die Stelle überhaupt ab."""
    eintraege = [("a.x__mutmut_1", "survived"), ("b.y__mutmut_2", "no tests"),
                 ("c.z__mutmut_3", "killed")]
    verdikt, details = mr.baue_verdikt(eintraege)
    assert verdikt.startswith("✗")
    assert "1 überlebt" in verdikt and "1 ohne deckenden Test" in verdikt
    assert any("a.x__mutmut_1" in z for z in details)


def test_getoetete_stehen_nicht_in_der_liste():
    """Der Normalfall ist kein Befund – 130 grüne Zeilen wären reines Rauschen."""
    eintraege = [("a.x__mutmut_1", "survived"), ("c.z__mutmut_3", "killed")]
    _verdikt, details = mr.baue_verdikt(eintraege)
    assert not any("c.z__mutmut_3" in z for z in details)


def test_verdikt_deckelt_die_liste():
    """Bei hunderten Befunden ist die Liste keine Analysehilfe mehr, sondern Rauschen."""
    eintraege = [(f"a.x__mutmut_{i}", "survived") for i in range(50)]
    _verdikt, details = mr.baue_verdikt(eintraege)
    assert len(details) <= mr.MAX_ZEILEN + 2  # + Sammelzeile + Erklärung
    assert any("weitere" in z for z in details)


def test_verdikt_ohne_jeden_eintrag():
    """Ein Filter ohne Treffer: kein Befund, aber auch keine Messung – das muss auffallen."""
    verdikt, _ = mr.baue_verdikt([])
    assert "0 Mutanten" in verdikt


# --- Frischer Baum -----------------------------------------------------------
def test_frisch_raeumt_den_mutantenbaum(tmp_path, monkeypatch):
    """`--frisch` wirft `mutants/` weg, bevor der Lauf beginnt.

    Normalerweise unnötig: mutmut vergleicht die mtime und mutiert eine geänderte Datei neu
    (`create_mutants_for_file`). Nur die Test-zu-Funktion-Zuordnung in `mutmut-stats.json`
    wird beim Laden mit `|=` ergänzt und nie bereinigt – ein GEÄNDERTER (nicht neuer) Test
    behält dort seine alte Zuordnung und kann einen längst getöteten Mutanten weiter als
    überlebend melden.
    """
    baum = tmp_path / "mutants"
    baum.mkdir()
    (baum / "alt.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mr, "ROOT", tmp_path)

    mr.raeume_baum()
    assert not baum.exists()


def test_raeumen_ohne_baum_ist_kein_fehler(tmp_path, monkeypatch):
    """Der erste Lauf hat keinen Baum – das darf nicht knallen."""
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    mr.raeume_baum()


# --- Ausnahmeliste im Verdikt ------------------------------------------------
def test_das_verdikt_nennt_die_uebersprungenen_tests(monkeypatch):
    """Eine Ausnahme, die nur in einer Datei steht, wird zur Formalie (OBS-S112-8)."""
    monkeypatch.setattr(mr, "UNTER_MUTMUT_UEBERSPRUNGEN", {"tests/x.py::test_a": "Grund"})
    nachsatz = mr.ausnahmen_nachsatz()
    assert "1 Test" in nachsatz and "_mutmut_ausnahmen.py" in nachsatz


def test_ohne_ausnahmen_kein_nachsatz(monkeypatch):
    monkeypatch.setattr(mr, "UNTER_MUTMUT_UEBERSPRUNGEN", {})
    assert mr.ausnahmen_nachsatz() == ""


# --- Timeouts und Verdächtige ------------------------------------------------
def test_timeouts_gelten_nicht_als_ueberlebende():
    """Ein Timeout sagt nichts über die Testgüte – meist ist es eine Endlosschleife, die
    der Mutant erzeugt hat. Als „überlebt" gezählt wäre es ein Fehlbefund."""
    verdikt, details = mr.baue_verdikt([("a.x__mutmut_1", "timeout"),
                                        ("b.y__mutmut_2", "killed")])
    assert verdikt.startswith("✓")
    assert any("timeout" in z for z in details)

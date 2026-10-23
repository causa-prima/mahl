"""Tests für mutmut-run.py – Wrapper um den Mutationslauf des Prozess-Codes.

Geprüft wird, was der Wrapper aus den Ergebnissen macht: Verdikt, Deckelung und die
Ausweisung der Ausnahmeliste. Das Lesen der Ergebnisse selbst steht in
`test_mutmut_meta.py`, die Sperrklinke in `test_mutmut_ratchet.py`.
Ein echter Mutationslauf kommt hier nicht vor – er dauert Minuten bis Stunden und liefe
pytest aus pytest heraus.
"""
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest

mr = import_module("prozesscode.mutmut-run")


# --- Prozessstart ----------------------------------------------------------------
def test_mutmut_laeuft_ohne_core_dumps(monkeypatch):
    """Ein Timeout endet per SIGXCPU, und das schreibt einen Core-Dump – unter WSL über
    `core_pattern` als Datei nach Windows, je Mutant einige hundert MB. Am echten
    Prozessstart geprüft: Das Limit muss beim Kind ankommen."""
    monkeypatch.setattr(mr, "MUTMUT", Path(sys.executable))
    lauf = mr._laufe("-c", "import resource; print(resource.getrlimit(resource.RLIMIT_CORE)[0])")
    assert lauf.stdout.strip() == "1"


# --- Eine Stelle ansehen (S133) ------------------------------------------------
def test_das_verdikt_zeigt_auf_den_erlaubten_weg_zur_stelle():
    """Bis S133 empfahl es `.venv/bin/mutmut show` – den Befehl blockt der Bash-Hook."""
    _, details = mr.baue_verdikt([("a.x__mutmut_1", "survived")])
    hinweis = "\n".join(details)
    assert "mutmut-run --show" in hinweis
    assert ".venv/bin/mutmut show" not in hinweis


@pytest.mark.aufrufpfad("mutmut-run")
def test_show_gibt_die_mutation_aus_statt_einen_lauf_zu_starten(tmp_path, monkeypatch, capsys):
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    aufrufe = []

    def fake_laufe(*argv):
        aufrufe.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="- alt\n+ neu\n", stderr="")

    monkeypatch.setattr(mr, "_laufe", fake_laufe)
    assert mr.main(["--show", "prozesscode.anchors.x_f__mutmut_3"]) == 0
    assert aufrufe == [("show", "prozesscode.anchors.x_f__mutmut_3")]
    assert "+ neu" in capsys.readouterr().out


@pytest.mark.aufrufpfad("mutmut-run")
def test_tests_for_nennt_die_tests_eines_mutanten_statt_einen_lauf_zu_starten(
        tmp_path, monkeypatch, capsys):
    """Ein Mutant, der zwischen zwei Läufen umspringt, wird von einem selbst wackelnden Test
    bewertet – welcher Test das ist, sagt nur mutmut. Der Rohaufruf ist per Hook gesperrt."""
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    aufrufe = []

    def fake_laufe(*argv):
        aufrufe.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="tests/test_a.py::test_b\n", stderr="")

    monkeypatch.setattr(mr, "_laufe", fake_laufe)
    assert mr.main(["--tests-for", "prozesscode.anchors.x_f__mutmut_3"]) == 0
    assert aufrufe == [("tests-for-mutant", "prozesscode.anchors.x_f__mutmut_3")]
    assert "tests/test_a.py::test_b" in capsys.readouterr().out


@pytest.mark.parametrize("ausschnitt, filter_", [
    ("prozesscode.anchors", "prozesscode.anchors.*"),
    ("prozesscode.anchors.x_f__mutmut_3", "prozesscode.anchors.x_f__mutmut_3"),
])
def test_ein_voller_mutantenname_laeuft_ohne_platzhalter(tmp_path, monkeypatch, ausschnitt, filter_):
    """Mit angehängtem `.*` träfe mutmut keinen Mutanten und bräche ab."""
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    aufrufe = []

    def fake_laufe(*argv):
        aufrufe.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(mr, "_laufe", fake_laufe)
    monkeypatch.setattr(mr, "lies_ergebnisse", lambda _m: [(f"{ausschnitt}.x__mutmut_1", "killed")])
    mr.main(["--mutate", ausschnitt])
    assert aufrufe == [("run", filter_)]


# --- Abgebrochener Lauf --------------------------------------------------------
# Schluss einer echten Ausgabe von mutmut 3.8: Sammelfehler beim Testimport.
_ABBRUCH_SAMMELN = """\
E   ModuleNotFoundError: No module named 'gibt_es_nicht'
=========================== short test summary info ============================
ERROR tests/test_zz_gegenprobe_kaputt.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1595 tests collected, 1 error in 0.54s
Failed to collect list of tests
"""


def _main_mit_lauf(monkeypatch, tmp_path, lauf, *argv):
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    monkeypatch.setattr(mr, "_laufe", lambda *a: lauf)
    # Ergebnisse eines früheren, grünen Laufs liegen noch im Mutantenbaum.
    monkeypatch.setattr(mr, "lies_ergebnisse", lambda _m: [("a.x__mutmut_1", "killed")])
    monkeypatch.setattr(mr, "lies_baseline", lambda: {})
    monkeypatch.setattr(mr, "schreibe_baseline", lambda _s: None)
    return mr.main(list(argv))


@pytest.mark.aufrufpfad("mutmut-run")
def test_abgebrochener_lauf_meldet_den_abbruch_statt_alter_ergebnisse(
        tmp_path, monkeypatch, capsys):
    lauf = subprocess.CompletedProcess([], 1, stdout=_ABBRUCH_SAMMELN, stderr="")
    assert _main_mit_lauf(monkeypatch, tmp_path, lauf, "--ratchet") == 1
    ausgabe = capsys.readouterr().out
    assert ausgabe.startswith("✗")
    assert "Failed to collect list of tests" in ausgabe
    assert "Sperrklinke gehalten" not in ausgabe


@pytest.mark.aufrufpfad("mutmut-run")
def test_durchgelaufener_lauf_wertet_die_ergebnisse_aus(tmp_path, monkeypatch, capsys):
    lauf = subprocess.CompletedProcess([], 0, stdout="Running mutation testing\n", stderr="")
    assert _main_mit_lauf(monkeypatch, tmp_path, lauf, "--ratchet") == 0
    assert "Sperrklinke gehalten" in capsys.readouterr().out


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
    # S133: Bis dahin stand hier ✓ – ein Filter wie `…x_main` traf keinen Mutanten (die heißen
    # `x_main__mutmut_N`), und der Lauf meldete „keiner überlebt" über eine leere Menge.
    assert verdikt.startswith("✗")
    assert "__mutmut_" in verdikt  # nennt die Namensform, an der der Filter vorbeiging


def test_nur_nicht_bewertete_zaehlen_ebenfalls_als_leere_messung():
    verdikt, _ = mr.baue_verdikt([("a.x__mutmut_1", "not checked")])
    assert verdikt.startswith("✗")


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

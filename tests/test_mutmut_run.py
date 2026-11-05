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
# Schluss einer echten Ausgabe von mutmut 3.8.1 unter pytest 9.2: Sammelfehler beim Testimport.
_ABBRUCH_SAMMELN = """\
E   ModuleNotFoundError: No module named 'gibt_es_nicht'
=========================== short test summary info ============================
ERROR tests/test_zz_gegenprobe_kaputt.py
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
2030 tests collected, 1 error in 0.62s
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


def test_genau_ein_bewerteter_mutant_steht_im_singular():
    assert mr.baue_verdikt([("m.x_f__mutmut_1", "killed")], pragmas=1) == (
        "✓ mutmut: 1 Mutant bewertet, 1 Zeile per Pragma ausgenommen, keiner überlebt", None)


def test_zwei_bewertete_mutanten_stehen_im_plural():
    assert mr.baue_verdikt([("m.x_f__mutmut_1", "killed"), ("m.x_f__mutmut_2", "killed")],
                           pragmas=2) == (
        "✓ mutmut: 2 Mutanten bewertet, 2 Zeilen per Pragma ausgenommen, keiner überlebt", None)


def test_genau_so_viele_befunde_wie_zeilen_brauchen_keine_sammelzeile():
    eintraege = [(f"a.x__mutmut_{i}", "timeout") for i in range(mr.MAX_ZEILEN)]
    _verdikt, details = mr.baue_verdikt(eintraege)
    assert len(details) == mr.MAX_ZEILEN
    assert not any("weitere" in z for z in details)


def test_die_sammelzeile_nennt_den_rest():
    eintraege = [(f"a.x__mutmut_{i}", "timeout") for i in range(mr.MAX_ZEILEN + 1)]
    _verdikt, details = mr.baue_verdikt(eintraege)
    assert details[-1] == "  … und 1 weitere"


# --- Aufrufpfad: vollständige Ausgabe ----------------------------------------
_HINWEIS_BEFUND = (
    "  „überlebt\" heißt: die Änderung an dieser Stelle bricht keinen Test – die Lücke "
    "liegt im Test.\n"
    "  „ohne deckenden Test\" heißt: kein Test berührt die Stelle überhaupt.\n"
    "  Eine Stelle ansehen: python3 -m prozesscode.mutmut-run --show <name>\n"
    "  Liegt sie in einem Meldungstext: als Modulkonstante auslagern (dort mutiert mutmut "
    "nicht) oder eigene Anweisung mit `# pragma: no mutate – <Grund>` am Ende (mitten "
    "in einem mehrzeiligen Ausdruck liest mutmut es nicht)."
)
_HINT = "   (vollständiger Output: --verbose)"


def _lauf_mit(monkeypatch, tmp_path, ergebnisse, *argv,
              lauf=None, quelle=None, ausnahmen=None):
    """Startet `main` gegen einen ersetzten mutmut-Prozess und feste Ergebnisse.

    `quelle` wird als `prozesscode/a.py` unter einem eigenen ROOT abgelegt – dort zählt
    `pragma_zeilen` die Ausnahmen. Rückgabe: (Exit-Code, Ausschnitte an `lies_ergebnisse`).
    """
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    if quelle is not None:
        (tmp_path / "prozesscode").mkdir()
        (tmp_path / "prozesscode" / "a.py").write_text(quelle, encoding="utf-8")
    lauf = lauf or subprocess.CompletedProcess([], 0, stdout="", stderr="")
    monkeypatch.setattr(mr, "_laufe", lambda *a: lauf)
    ausschnitte = []

    def fake_lies(ausschnitt):
        ausschnitte.append(ausschnitt)
        return ergebnisse

    monkeypatch.setattr(mr, "lies_ergebnisse", fake_lies)
    monkeypatch.setattr(mr, "UNTER_MUTMUT_UEBERSPRUNGEN", ausnahmen or {})
    return mr.main(list(argv)), ausschnitte


@pytest.mark.aufrufpfad("mutmut-run")
def test_befund_im_ausschnitt_vollstaendige_ausgabe(tmp_path, monkeypatch, capsys):
    """Das ganze Verdikt über `main`: Liste, Erklärung, Zählung, Pragma, Ausschnitt,
    Ausnahmen – und der Ausschnitt geht an `lies_ergebnisse` weiter (sonst meldete ein Lauf
    auf Modul B die Überlebenden von Modul A mit)."""
    ergebnisse = [("prozesscode.a.x_f__mutmut_1", "survived"),
                  ("prozesscode.a.x_f__mutmut_2", "killed"),
                  ("prozesscode.a.x_f__mutmut_3", "no tests"),
                  ("prozesscode.a.x_f__mutmut_4", "timeout")]
    code, ausschnitte = _lauf_mit(
        monkeypatch, tmp_path, ergebnisse, "--mutate", "prozesscode.a",
        quelle="X = 1  # pragma: no mutate – Text\n",
        ausnahmen={"tests/x.py::test_a": "Grund"})
    assert code == 1
    assert ausschnitte == ["prozesscode.a"]
    assert capsys.readouterr().out == (
        "  survived    prozesscode.a.x_f__mutmut_1\n"
        "  no tests    prozesscode.a.x_f__mutmut_3\n"
        "  timeout     prozesscode.a.x_f__mutmut_4\n"
        f"{_HINWEIS_BEFUND}\n"
        "\n"
        "✗ mutmut: 4 Mutanten bewertet, 1 Zeile per Pragma ausgenommen, 1 überlebt, "
        "1 ohne deckenden Test\n"
        "  (Ausschnitt: prozesscode.a)\n"
        "  (1 Test(e) unter mutmut übersprungen – Begründungen in "
        "prozesscode/_mutmut_ausnahmen.py)\n"
        f"{_HINT}\n")


@pytest.mark.aufrufpfad("mutmut-run")
def test_gruener_volllauf_vollstaendige_ausgabe(tmp_path, monkeypatch, capsys):
    """Ohne `--mutate` kein Ausschnitt-Filter; Timeouts sind genannt, aber kein Befund."""
    ergebnisse = [("prozesscode.a.x_f__mutmut_1", "killed"),
                  ("prozesscode.a.x_f__mutmut_2", "timeout"),
                  ("prozesscode.a.x_f__mutmut_3", "not checked")]
    code, ausschnitte = _lauf_mit(
        monkeypatch, tmp_path, ergebnisse,
        quelle="X = 1  # pragma: no mutate\nY = 2  # pragma: no mutate\n")
    assert code == 0
    assert ausschnitte == [None]
    assert capsys.readouterr().out == (
        "  timeout     prozesscode.a.x_f__mutmut_2\n"
        "\n"
        "✓ mutmut: 2 Mutanten bewertet, 1 offen (weiterer Lauf nötig), 2 Zeilen per Pragma "
        "ausgenommen, keiner überlebt (1 ohne Aussage: timeout/suspicious)\n"
        f"{_HINT}\n")


@pytest.mark.aufrufpfad("mutmut-run")
def test_verbose_gibt_die_rohausgabe_aus(tmp_path, monkeypatch, capsys):
    lauf = subprocess.CompletedProcess([], 0, stdout="Running mutation testing\n",
                                       stderr="done\n")
    code, _ = _lauf_mit(monkeypatch, tmp_path, [("prozesscode.a.x_f__mutmut_1", "killed")],
                        "--verbose", lauf=lauf)
    assert code == 0
    assert capsys.readouterr().out == (
        "Running mutation testing\ndone\n✓ mutmut: 1 Mutant bewertet, keiner überlebt\n")


@pytest.mark.aufrufpfad("mutmut-run")
def test_abbruch_ohne_ausgabe_vollstaendige_meldung(tmp_path, monkeypatch, capsys):
    lauf = subprocess.CompletedProcess([], 2, stdout="", stderr="")
    code, ausschnitte = _lauf_mit(monkeypatch, tmp_path, [], lauf=lauf)
    assert code == 1
    assert ausschnitte == []  # alte Ergebnisse im Baum werden gar nicht erst gelesen
    assert capsys.readouterr().out == (
        "✗ mutmut ist abgebrochen (Exit 2): keine Ausgabe\n"
        "  Kein Ergebnis dieses Laufs – die Ursache steht davor: --verbose.\n"
        "  Häufig ein Fehler im Testcode, der nur im Mutantenbaum auftritt (Import, Pfad).\n"
        "  Nennt sie eine Datei, die es im Repo nicht mehr gibt: --frisch (s. raeume_baum).\n"
        f"{_HINT}\n")


@pytest.mark.aufrufpfad("mutmut-run")
def test_abbruch_mit_verbose_zeigt_die_echte_ausgabe(tmp_path, monkeypatch, capsys):
    lauf = subprocess.CompletedProcess([], 1, stdout=_ABBRUCH_SAMMELN, stderr="")
    code, _ = _lauf_mit(monkeypatch, tmp_path, [], "--verbose", lauf=lauf)
    assert code == 1
    verdikt = mr._ABBRUCH.format(code=1, zeile="Failed to collect list of tests")
    assert capsys.readouterr().out == _ABBRUCH_SAMMELN.rstrip() + "\n" + verdikt + "\n"


@pytest.mark.aufrufpfad("mutmut-run")
def test_show_reicht_ausgabe_und_exit_code_unveraendert_durch(tmp_path, monkeypatch, capsys):
    """Auch stderr und ein Fehler-Exit kommen an – ohne angehängten Zeilenumbruch."""
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    monkeypatch.setattr(mr, "_laufe", lambda *argv: subprocess.CompletedProcess(
        argv, 1, stdout="- alt\n+ neu\n", stderr="Fehler"))
    assert mr.main(["--show", "prozesscode.anchors.x_f__mutmut_3"]) == 1
    assert capsys.readouterr().out == "- alt\n+ neu\nFehler"


@pytest.mark.aufrufpfad("mutmut-run")
def test_ohne_venv_nennt_es_den_weg_zur_umgebung(tmp_path, monkeypatch, capsys):
    fehlt = tmp_path / "fehlt"
    monkeypatch.setattr(mr, "MUTMUT", fehlt)
    monkeypatch.setattr(mr, "_laufe", lambda *a: pytest.fail("ohne venv kein Lauf"))
    assert mr.main([]) == 2
    assert capsys.readouterr().out == (
        f"✗ Werkzeug-Umgebung fehlt ({fehlt}).\n"
        "  Herstellen:\n"
        "    python3 -m venv .venv\n"
        "    .venv/bin/pip install -r requirements-dev.txt\n")


@pytest.mark.aufrufpfad("mutmut-run")
def test_frisch_raeumt_den_baum_ueber_main(tmp_path, monkeypatch):
    (tmp_path / "mutants").mkdir()
    code, _ = _lauf_mit(monkeypatch, tmp_path, [("prozesscode.a.x_f__mutmut_1", "killed")],
                        "--frisch")
    assert code == 0
    assert not (tmp_path / "mutants").exists()


def test_ohne_frisch_bleibt_der_baum(tmp_path, monkeypatch):
    (tmp_path / "mutants").mkdir()
    _lauf_mit(monkeypatch, tmp_path, [("prozesscode.a.x_f__mutmut_1", "killed")])
    assert (tmp_path / "mutants").exists()


def test_der_mutmut_prozess_laeuft_im_repo_mit_zeitdeckel_und_ohne_dumps(monkeypatch):
    """Ohne `cwd` fände mutmut seine `setup.cfg` nicht, ohne `timeout` hinge ein Volllauf
    beliebig lange. Das Core-Limit lässt sich im Mutantenbaum nicht am Kind prüfen: mutmut
    setzt es dort schon für den Testprozess, das Kind erbt es auch ohne `preexec_fn`."""
    aufrufe = []
    monkeypatch.setattr(mr.subprocess, "run",
                        lambda cmd, **kw: aufrufe.append((cmd, kw)) or "lauf")
    assert mr._laufe("show", "x") == "lauf"
    assert aufrufe == [([str(mr.MUTMUT), "show", "x"], {
        "cwd": mr.ROOT, "capture_output": True, "text": True,
        "timeout": mr.TIMEOUT_S, "preexec_fn": mr._ohne_core_dump})]


def test_das_core_limit_wird_auf_eins_gesetzt_und_das_harte_bleibt(monkeypatch):
    """0 genügt nicht: Bei einem Pipe-Ziel in `core_pattern` wirkt erst 1 (core(5))."""
    gesetzt = []
    monkeypatch.setattr(mr.resource, "getrlimit",
                        lambda art: (0, 4711) if art == mr.resource.RLIMIT_CORE else None)
    monkeypatch.setattr(mr.resource, "setrlimit", lambda art, wert: gesetzt.append((art, wert)))
    mr._ohne_core_dump()
    assert gesetzt == [(mr.resource.RLIMIT_CORE, (1, 4711))]


# --- Timeouts und Verdächtige ------------------------------------------------
def test_timeouts_gelten_nicht_als_ueberlebende():
    """Ein Timeout sagt nichts über die Testgüte – meist ist es eine Endlosschleife, die
    der Mutant erzeugt hat. Als „überlebt" gezählt wäre es ein Fehlbefund."""
    verdikt, details = mr.baue_verdikt([("a.x__mutmut_1", "timeout"),
                                        ("b.y__mutmut_2", "killed")])
    assert verdikt.startswith("✓")
    assert any("timeout" in z for z in details)

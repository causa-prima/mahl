"""Tests für die Sperrklinke von mutmut-run.py – `--ratchet`.

Die Sperrklinke beantwortet die Frage, die ein einzelner Lauf nicht beantworten kann:
*Ist die Testgüte dieses Moduls schlechter als beim letzten Mal?* Ohne einen festgehaltenen
Vorher-Wert ist eine Mutationszahl nur eine Momentaufnahme – man sieht, dass 34 Mutanten
überleben, aber nicht, ob es gestern 12 waren.

Bewusst KEIN Gate (kein Hook, kein Commit-Zwang) – Grund in `docs/process/dev-workflow.md#DEV-python-werkzeuge`.
Die Klinke greift nur, wenn jemand sie zieht.
"""
from importlib import import_module

import pytest

mr =import_module("prozesscode.mutmut-run")


def eintraege(**je_status) -> list[tuple[str, str]]:
    """Baut Ergebnisse eines Moduls: `eintraege(killed=3, survived=1)`."""
    raus = []
    for status, anzahl in je_status.items():
        status = status.replace("_", " ")
        raus += [(f"prozesscode.a.x_f__mutmut_{i}_{status}", status) for i in range(anzahl)]
    return raus


# --- Score: was zählt in den Bruch? ------------------------------------------
def test_score_ist_getoetet_durch_beurteilbare():
    getoetet, relevant = mr.score(eintraege(killed=3, survived=1))
    assert (getoetet, relevant) == (3, 4)


def test_ohne_deckenden_test_zaehlt_als_lücke():
    """`no tests` ist keine Neutralität – die Stelle ist ungeprüft, also ungedeckt."""
    getoetet, relevant = mr.score(eintraege(killed=1, no_tests=3))
    assert (getoetet, relevant) == (1, 4)


def test_timeouts_stehen_ausserhalb_des_bruchs():
    """Ein Timeout sagt nichts über die Tests – im Nenner verschöbe er den Score beliebig."""
    getoetet, relevant = mr.score(eintraege(killed=2, timeout=5, suspicious=3))
    assert (getoetet, relevant) == (2, 2)


def test_nicht_bewertete_stehen_ausserhalb_des_bruchs():
    getoetet, relevant = mr.score(eintraege(killed=2, **{"not_checked": 99}))
    assert (getoetet, relevant) == (2, 2)


def test_ohne_beurteilbare_mutanten_kein_score():
    """Ein Modul ohne einen einzigen bewerteten Mutanten hat keinen Score – 0/0 ist keine
    Null, und als Null berichtet wäre es ein erfundener Befund."""
    assert mr.score(eintraege(**{"not_checked": 10})) == (0, 0)


# --- Gruppierung: die Baseline lebt je Modul ---------------------------------
def test_gruppiert_nach_modul():
    roh = [("prozesscode.a.x_f__mutmut_1", "killed"),
           ("prozesscode.b.x_g__mutmut_1", "survived")]
    assert set(mr.nach_modul(roh)) == {"prozesscode.a", "prozesscode.b"}


def test_das_modul_ist_der_name_ohne_den_mutantenteil():
    roh = [("prozesscode.hooks.check-td-capture.x_pruefe__mutmut_3", "killed")]
    assert list(mr.nach_modul(roh)) == ["prozesscode.hooks.check-td-capture"]


# --- Die Klinke --------------------------------------------------------------
def test_erstaufnahme_ist_kein_befund():
    """Beim ersten Lauf gibt es kein Vorher – das ist kein Rückschritt, sondern der Start."""
    zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (3, 4)}, {})
    assert not schlechter
    assert neu == {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    assert any("neu aufgenommen" in z for z in zeilen)


def test_gleichstand_geht_durch():
    """Sonst müsste jede Änderung den Score ERHÖHEN – das wäre keine Sperrklinke mehr,
    sondern eine Steigerungspflicht."""
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    _zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (3, 4)}, basis)
    assert not schlechter
    assert neu is None  # nichts fortzuschreiben


def test_verschlechterung_schlaegt_an():
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (2, 4)}, basis)
    assert schlechter
    assert neu is None  # eine gerissene Klinke schreibt NIE fort
    assert any("75" in z and "50" in z for z in zeilen)


def test_verbesserung_zieht_die_baseline_nach():
    """Ohne Fortschreiben friert die Klinke beim ersten Glücksfall ein und deckt jede
    spätere Verschlechterung bis auf das alte Niveau."""
    basis = {"prozesscode.a": {"getoetet": 2, "beurteilbar": 4}}
    zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (3, 4)}, basis)
    assert not schlechter
    assert neu == {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    assert any("→" in z for z in zeilen)


def test_wachsender_code_mit_ungetesteten_stellen_ist_eine_verschlechterung():
    """Gleich viele getötete, aber mehr beurteilbare Mutanten: Der Anteil sinkt, und genau
    das soll die Klinke fangen – neuer Code ohne Tests."""
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    _zeilen, schlechter, _neu = mr.ratchet({"prozesscode.a": (3, 6)}, basis)
    assert schlechter


def test_vergleich_rechnet_in_bruechen_nicht_in_prozenten():
    """Gerundet verschwinden kleine Rückschritte: 10000/30000 und 10001/30004 sind auf zwei
    Nachkommastellen beide 33.33 %, als Bruch ist der zweite kleiner – und drei offene
    Befunde mehr."""
    basis = {"prozesscode.a": {"getoetet": 10000, "beurteilbar": 30000}}
    _zeilen, schlechter, _neu = mr.ratchet({"prozesscode.a": (10001, 30004)}, basis)
    assert schlechter


@pytest.mark.parametrize("gemessen", [
    (1171, 1193),  # vier getötete Mutanten mit ihrem Code gelöscht (Bash-Guard)
    (1174, 1196),  # ein getöteter Mutant kippt je nach Testreihenfolge in den Timeout
])
def test_sinkender_bruch_ohne_neue_offene_befunde_ist_kein_rueckschritt(gemessen):
    """Rückschritt heißt: Der Bruch sinkt UND es gibt mehr offene Befunde (überlebt oder
    ohne deckenden Test). Sinkt nur der Bruch, sind getötete Mutanten weggefallen – mit
    gelöschtem Code oder in den Timeout, der außerhalb des Bruchs steht. Ein Rückschritt
    dafür bestrafte das Löschen gut getesteten Codes."""
    basis = {"prozesscode.a": {"getoetet": 1175, "beurteilbar": 1197}}
    zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": gemessen}, basis)
    assert not schlechter
    # Fortgeschrieben – sonst deckte der alte Stand später neue offene Befunde bis zur
    # Höhe der weggefallenen.
    assert neu == {"prozesscode.a": {"getoetet": gemessen[0], "beurteilbar": gemessen[1]}}
    assert zeilen == [
        "  prozesscode.a: 98.2 % → 98.2 %  (offene Befunde nicht gestiegen: 22 → 22, "
        "Baseline nachgezogen)"]


def test_nach_geloeschtem_code_zaehlen_neue_offene_befunde_ab_dem_neuen_stand():
    """Gelöschter Code mit 5 Überlebenden (und vielen getöteten – der Bruch sinkt), danach
    neuer mit 5: Gegen die alte Baseline (22 offen) wäre das kein Anstieg; gegen die
    nachgezogene (17) schon."""
    basis = {"prozesscode.a": {"getoetet": 1175, "beurteilbar": 1197}}
    _z, geloescht_schlechter, nachgezogen = mr.ratchet({"prozesscode.a": (900, 917)}, basis)
    assert not geloescht_schlechter
    _z, schlechter, _neu = mr.ratchet({"prozesscode.a": (900, 922)}, nachgezogen)
    assert schlechter


def test_ein_modul_ohne_score_wird_uebergangen():
    """0/0 lässt sich mit nichts vergleichen – weder als Rückschritt noch als Fortschritt."""
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (0, 0)}, basis)
    assert not schlechter and neu is None
    assert any("kein bewerteter Mutant" in z for z in zeilen)


def test_module_ausserhalb_des_laufs_bleiben_unberuehrt():
    """GEGENPROBE: Ein Ausschnitt darf die Baseline fremder Module nicht anfassen –
    sonst löschte ein `--mutate` auf ein Modul die Historie aller anderen."""
    basis = {"prozesscode.a": {"getoetet": 1, "beurteilbar": 4},
             "prozesscode.b": {"getoetet": 2, "beurteilbar": 4}}
    _zeilen, _schlechter, neu = mr.ratchet({"prozesscode.a": (4, 4)}, basis)
    assert neu["prozesscode.b"] == {"getoetet": 2, "beurteilbar": 4}


# --- Wer bestimmt das Verdikt? -----------------------------------------------
_BEFUND = "✗ mutmut: 85 Mutanten bewertet, 31 überlebt, 11 ohne deckenden Test"


def test_bei_gehaltener_klinke_entscheidet_die_klinke_nicht_der_befund():
    """Sonst meldete `--ratchet` auf jedem Modul mit Altlast dauerhaft rot.

    Ein Modul mit 31 überlebenden Mutanten ist ein bekannter Zustand, kein neuer Fehler –
    die Frage der Klinke ist, ob er SCHLECHTER geworden ist. Ein Werkzeug, das auch bei
    gehaltener Klinke ✗ sagt, gibt kein Signal mehr, das sich vom Rauschen abhebt.
    """
    verdikt, code = mr.klinken_verdikt(_BEFUND, schlechter=False, nachgezogen=False)
    assert verdikt.startswith("✓") and code == 0
    assert "31 überlebt" in verdikt  # der Befund bleibt sichtbar


def test_die_gerissene_klinke_ist_der_befund():
    verdikt, code = mr.klinken_verdikt(_BEFUND, schlechter=True, nachgezogen=False)
    assert verdikt.startswith("✗") and code == 1
    assert "gerissen" in verdikt


def test_das_nachziehen_wird_benannt():
    """Eine still fortgeschriebene Baseline wäre eine Zahl, die sich selbst verändert."""
    verdikt, _code = mr.klinken_verdikt(_BEFUND, schlechter=False, nachgezogen=True)
    assert "nachgezogen" in verdikt


# --- Baseline lesen und schreiben --------------------------------------------
def test_fehlende_baseline_ist_eine_leere(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "BASELINE", tmp_path / "gibt-es-nicht.json")
    assert mr.lies_baseline() == {}


def test_kaputte_baseline_reisst_den_lauf_nicht_mit(tmp_path, monkeypatch):
    """Fail-open: Eine unlesbare Baseline heißt „kein Vorher", nicht „Abbruch"."""
    pfad = tmp_path / "kaputt.json"
    pfad.write_text("{kein json", encoding="utf-8")
    monkeypatch.setattr(mr, "BASELINE", pfad)
    assert mr.lies_baseline() == {}


def test_geschriebene_baseline_ist_wieder_lesbar(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "BASELINE", tmp_path / "b.json")
    mr.schreibe_baseline({"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}})
    assert mr.lies_baseline() == {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}


# --- Unvollständiger Lauf: zwei Scores, zwei Grundgesamtheiten ----------------
# In S130 meldete die Klinke für `check-bash-permission` 53.5 % → 53.0 % VERSCHLECHTERT.
# Gemessen waren 237 Mutanten, die Baseline hielt 241 fest: verglichen wurden zwei
# verschiedene Grundgesamtheiten. Ursache ist ein Abbruch in mutmut selbst (KeyError bei
# Exit-Code -9 = SIGKILL); der Wrapper rechnet dann mit dem, was vorher durchkam. Ein
# erfundener Rückschritt ist teurer als gar keine Aussage: Er lässt Tests schreiben, die
# keine Lücke schließen, und macht die Klinke unglaubwürdig für den echten Fall.
def test_unvollstaendiger_lauf_meldet_keine_verschlechterung():
    basis = {"prozesscode.a": {"getoetet": 6, "beurteilbar": 10}}
    zeilen, schlechter, _neu = mr.ratchet({"prozesscode.a": (5, 10)}, basis,
                                          offen={"prozesscode.a": 20})
    assert schlechter is False
    assert "unvollständig" in " ".join(zeilen).lower()


def test_unvollstaendiger_lauf_schreibt_auch_eine_verbesserung_nicht_fort():
    """Ein Teillauf darf die Messlatte nicht verschieben – in keine Richtung.

    Sonst würde ein zufällig günstiger Ausschnitt zur neuen Baseline und deckte jede
    spätere echte Verschlechterung bis auf dieses Niveau.
    """
    basis = {"prozesscode.a": {"getoetet": 5, "beurteilbar": 10}}
    _zeilen, _schlechter, neu = mr.ratchet({"prozesscode.a": (9, 10)}, basis,
                                           offen={"prozesscode.a": 20})
    assert neu is None


def test_vollstaendiger_lauf_meldet_die_verschlechterung_weiterhin():
    """GEGENPROBE: Ohne offene Mutanten bleibt die Klinke scharf."""
    basis = {"prozesscode.a": {"getoetet": 6, "beurteilbar": 10}}
    _zeilen, schlechter, _neu = mr.ratchet({"prozesscode.a": (5, 10)}, basis,
                                           offen={"prozesscode.a": 0})
    assert schlechter is True


def test_unvollstaendiger_lauf_ist_kein_gruenes_verdikt():
    """Real passiert: dreimal 266 von 672 Mutanten, gemeldet als „✓ Sperrklinke gehalten", Exit 0.

    Nicht verglichen ist nicht gehalten: Das grüne Verdikt las sich als Beleg, dass der
    geänderte Guard von Tests gehalten wird – über den nicht gelaufenen Teil sagte es nichts.
    """
    verdikt, code = mr.klinken_verdikt(_BEFUND, schlechter=False, nachgezogen=False,
                                       ohne_aussage=["prozesscode.a"])
    assert not verdikt.startswith("✓") and code == 1
    assert "ohne Aussage" in verdikt and "prozesscode.a" in verdikt


def test_die_gerissene_klinke_geht_dem_teillauf_vor():
    """Ein echter Rückschritt in einem vollständigen Modul darf nicht hinter ⚠ verschwinden."""
    verdikt, code = mr.klinken_verdikt(_BEFUND, schlechter=True, nachgezogen=False,
                                       ohne_aussage=["prozesscode.b"])
    assert verdikt.startswith("✗") and code == 1


def test_vollstaendiger_lauf_bleibt_gruen():
    """GEGENPROBE: Ohne Teillauf hält die Klinke wie bisher."""
    verdikt, code = mr.klinken_verdikt(_BEFUND, schlechter=False, nachgezogen=False,
                                       ohne_aussage=[])
    assert verdikt.startswith("✓") and code == 0


def test_der_aufrufpfad_meldet_den_teillauf(tmp_path, monkeypatch, capsys):
    """Über `main`: Ein Modul mit nicht bewerteten Mutanten führt zu Exit 1, nicht zu ✓."""
    import subprocess
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    monkeypatch.setattr(mr, "BASELINE", tmp_path / "b.json")
    mr.schreibe_baseline({"prozesscode.a": {"getoetet": 1, "beurteilbar": 2}})
    monkeypatch.setattr(mr, "_laufe", lambda *argv: subprocess.CompletedProcess(argv, 0, "", ""))
    monkeypatch.setattr(mr, "lies_ergebnisse", lambda _a=None: [
        ("prozesscode.a.x_f__mutmut_1", "killed"),
        ("prozesscode.a.x_f__mutmut_2", mr.NICHT_BEWERTET)])
    assert mr.main(["--mutate", "prozesscode.a", "--ratchet"]) == 1
    assert "ohne Aussage" in capsys.readouterr().out
    # Die offenen Mutanten kommen auch bei der Klinke an: Der Teilscore 1/1 zieht nichts nach.
    assert mr.lies_baseline() == {"prozesscode.a": {"getoetet": 1, "beurteilbar": 2}}


# --- Wechsel des Messinstruments ---------------------------------------------
# mutmut 3.8 erzeugte für merke-rueckgaben 94 statt 39 Mutanten: Über einen Versionswechsel
# hinweg vergleicht die Klinke zwei Instrumente, nicht zwei Teststände.
def test_andere_messung_setzt_die_baseline_neu_statt_zu_vergleichen():
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4, "messung": "alt"}}
    zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (2, 4)}, basis, messung="neu")
    assert not schlechter
    assert neu == {"prozesscode.a": {"getoetet": 2, "beurteilbar": 4, "messung": "neu"}}
    assert any("neu gesetzt" in z and "alt" in z and "neu" in z for z in zeilen)


def test_baseline_ohne_messung_gilt_als_andere_messung():
    """Die Einträge von vor der Kennung sind alle mit einem älteren mutmut gemessen."""
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    _zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (2, 4)}, basis, messung="neu")
    assert not schlechter and neu["prozesscode.a"]["messung"] == "neu"


def test_gleiche_messung_vergleicht_wie_bisher():
    """GEGENPROBE: Bei gleichem Instrument bleibt die Klinke scharf."""
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4, "messung": "m"}}
    _zeilen, schlechter, neu = mr.ratchet({"prozesscode.a": (2, 4)}, basis, messung="m")
    assert schlechter and neu is None


def test_messung_nennt_mutmut_version_und_wertung(tmp_path, monkeypatch):
    (tmp_path / "lib" / "python3.12" / "site-packages" / "mutmut-3.8.0.dist-info").mkdir(
        parents=True)
    monkeypatch.setattr(mr, "MUTMUT", tmp_path / "bin" / "mutmut")
    assert mr.messung() == f"mutmut 3.8.0, Wertung {mr.WERTUNG_STAND}"


def test_der_aufrufpfad_traegt_die_messung_ein(tmp_path, monkeypatch):
    import subprocess
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    monkeypatch.setattr(mr, "BASELINE", tmp_path / "b.json")
    monkeypatch.setattr(mr, "messung", lambda: "m-test")
    monkeypatch.setattr(mr, "_laufe", lambda *argv: subprocess.CompletedProcess(argv, 0, "", ""))
    monkeypatch.setattr(mr, "lies_ergebnisse", lambda _a=None: [
        ("prozesscode.a.x_f__mutmut_1", "killed")])
    assert mr.main(["--mutate", "prozesscode.a", "--ratchet"]) == 0
    assert mr.lies_baseline()["prozesscode.a"]["messung"] == "m-test"


def test_mehrere_offene_im_selben_modul_summieren_sich():
    eintr = [("prozesscode.a.x_f__mutmut_1", mr.NICHT_BEWERTET),
             ("prozesscode.a.x_f__mutmut_2", mr.NICHT_BEWERTET),
             ("prozesscode.a.x_f__mutmut_3", "killed")]
    assert mr.offene_je_modul(eintr) == {"prozesscode.a": 2}


def test_messung_ohne_mutmut_im_venv(tmp_path, monkeypatch):
    """Fail-open: Ohne `dist-info` bleibt die Version offen, der Lauf geht weiter."""
    monkeypatch.setattr(mr, "MUTMUT", tmp_path / "bin" / "mutmut")
    assert mr.messung() == f"mutmut ?, Wertung {mr.WERTUNG_STAND}"


# --- Vollständige Meldungen --------------------------------------------------
def test_jeder_zweig_der_klinke_meldet_sich_und_laesst_die_folgenden_module_zu():
    """Ein Lauf über mehrere Module, je eines pro Zweig, in Sortierreihenfolge – kein Zweig
    darf die Auswertung der übrigen abbrechen, und jede Zeile steht exakt so da."""
    basis = {"prozesscode.b": {"getoetet": 1, "beurteilbar": 1, "messung": "m"},
             "prozesscode.d": {"getoetet": 1, "beurteilbar": 1, "messung": "alt"},
             "prozesscode.d2": {"getoetet": 1, "beurteilbar": 1},
             "prozesscode.e": {"getoetet": 1, "beurteilbar": 4, "messung": "m"},
             "prozesscode.f": {"getoetet": 1, "beurteilbar": 2, "messung": "m"},
             "prozesscode.z": {"getoetet": 9, "beurteilbar": 9, "messung": "m"}}
    gemessen = {"prozesscode.a": (0, 0), "prozesscode.b": (1, 2), "prozesscode.c": (2, 3),
                "prozesscode.d": (1, 4), "prozesscode.d2": (1, 4), "prozesscode.e": (3, 4),
                "prozesscode.f": (2, 4)}
    zeilen, schlechter, neu = mr.ratchet(gemessen, basis, offen={"prozesscode.b": 3},
                                         messung="m")
    assert zeilen == [
        "  prozesscode.a: kein bewerteter Mutant – nichts zu vergleichen",
        "  prozesscode.b: 50.0 % über 2 von 5 Mutanten – Lauf unvollständig, kein Vergleich "
        "mit der Baseline",
        "    Erneut laufen lassen; bleibt die Zahl stehen, kommt mutmut auf diesem Modul nicht "
        "durch – dann ist die Klinke hier ohne Aussage, und das Modul braucht eine eigene "
        "Untersuchung.",
        "  prozesscode.c: 66.7 % – neu aufgenommen",
        "  prozesscode.d: 25.0 % – Baseline neu gesetzt (Messung alt → m), kein Vergleich",
        "  prozesscode.d2: 25.0 % – Baseline neu gesetzt (Messung ohne Kennung → m), "
        "kein Vergleich",
        "  prozesscode.e: 25.0 % → 75.0 %  (Baseline nachgezogen)",
        "  prozesscode.f: 50.0 % – unverändert",
    ]
    assert schlechter is False
    assert neu == {**basis,
                   "prozesscode.c": {"getoetet": 2, "beurteilbar": 3, "messung": "m"},
                   "prozesscode.d": {"getoetet": 1, "beurteilbar": 4, "messung": "m"},
                   "prozesscode.d2": {"getoetet": 1, "beurteilbar": 4, "messung": "m"},
                   "prozesscode.e": {"getoetet": 3, "beurteilbar": 4, "messung": "m"}}


def test_die_verschlechterung_nennt_vorher_und_nachher():
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4}}
    zeilen, _schlechter, _neu = mr.ratchet({"prozesscode.a": (2, 4)}, basis)
    assert zeilen == ["  prozesscode.a: 75.0 % → 50.0 %  VERSCHLECHTERT"]


def test_ohne_beurteilbare_kein_prozentwert():
    assert mr._prozent(0, 0) == "–"


@pytest.mark.parametrize("schlechter, nachgezogen, ohne_aussage, erwartet", [
    (True, False, ["prozesscode.b"],
     ("✗ Sperrklinke gerissen – die Testgüte ist unter den festgehaltenen Stand gefallen\n"
      f"  {_BEFUND[2:]}", 1)),
    (False, False, ["prozesscode.a", "prozesscode.b"],
     ("⚠ Sperrklinke ohne Aussage – Lauf unvollständig für prozesscode.a, prozesscode.b "
      f"(Einzelheiten oben)\n  {_BEFUND[2:]}", 1)),
    (False, True, [], (f"✓ Sperrklinke gehalten (Baseline nachgezogen)\n  {_BEFUND[2:]}", 0)),
    (False, False, None, (f"✓ Sperrklinke gehalten\n  {_BEFUND[2:]}", 0)),
])
def test_klinken_verdikt_vollstaendig(schlechter, nachgezogen, ohne_aussage, erwartet):
    assert mr.klinken_verdikt(_BEFUND, schlechter=schlechter, nachgezogen=nachgezogen,
                              ohne_aussage=ohne_aussage) == erwartet


def test_die_baseline_wird_sortiert_und_eingerueckt_geschrieben(tmp_path, monkeypatch):
    """Die Datei ist getrackt – stabile Form, damit ein Diff nur zeigt, was sich änderte."""
    monkeypatch.setattr(mr, "BASELINE", tmp_path / "b.json")
    mr.schreibe_baseline({"prozesscode.b": {"getoetet": 1, "beurteilbar": 2},
                          "prozesscode.a": {"messung": "m", "beurteilbar": 4, "getoetet": 3}})
    assert (tmp_path / "b.json").read_text(encoding="utf-8") == (
        '{\n'
        '  "prozesscode.a": {\n'
        '    "beurteilbar": 4,\n'
        '    "getoetet": 3,\n'
        '    "messung": "m"\n'
        '  },\n'
        '  "prozesscode.b": {\n'
        '    "beurteilbar": 2,\n'
        '    "getoetet": 1\n'
        '  }\n'
        '}\n')


# --- Aufrufpfad: Klinke über main --------------------------------------------
_HINWEIS_ANFANG = "  „überlebt\" heißt"


def _klinke_ueber_main(tmp_path, monkeypatch, basis, ergebnisse, *zusatz, roh=""):
    import subprocess
    binaer = tmp_path / "mutmut"
    binaer.touch()
    monkeypatch.setattr(mr, "MUTMUT", binaer)
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    monkeypatch.setattr(mr, "BASELINE", tmp_path / "b.json")
    monkeypatch.setattr(mr, "UNTER_MUTMUT_UEBERSPRUNGEN", {})
    monkeypatch.setattr(mr, "messung", lambda: "m")
    mr.schreibe_baseline(basis)
    monkeypatch.setattr(mr, "_laufe", lambda *argv: subprocess.CompletedProcess(argv, 0, roh, ""))
    monkeypatch.setattr(mr, "lies_ergebnisse", lambda _a=None: ergebnisse)
    return mr.main(["--ratchet", *zusatz])


@pytest.mark.aufrufpfad("mutmut-run")
def test_nachgezogene_klinke_ueber_main(tmp_path, monkeypatch, capsys):
    ergebnisse = eintraege(killed=3, survived=1)
    code = _klinke_ueber_main(tmp_path, monkeypatch,
                              {"prozesscode.a": {"getoetet": 1, "beurteilbar": 2, "messung": "m"}},
                              ergebnisse)
    assert code == 0
    ausgabe = capsys.readouterr().out
    vor_hinweis, _, nach_hinweis = ausgabe.partition(_HINWEIS_ANFANG)
    assert vor_hinweis == f"  survived    {ergebnisse[-1][0]}\n"
    assert nach_hinweis.endswith(
        "liest mutmut es nicht).\n"
        "\n"
        "  prozesscode.a: 50.0 % → 75.0 %  (Baseline nachgezogen)\n"
        "\n"
        "✓ Sperrklinke gehalten (Baseline nachgezogen)\n"
        "  mutmut: 4 Mutanten bewertet, 1 überlebt\n"
        "   (vollständiger Output: --verbose)\n")
    assert mr.lies_baseline() == {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4,
                                                    "messung": "m"}}


@pytest.mark.aufrufpfad("mutmut-run")
def test_gerissene_klinke_ueber_main(tmp_path, monkeypatch, capsys):
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4, "messung": "m"}}
    code = _klinke_ueber_main(tmp_path, monkeypatch, basis, eintraege(killed=2, survived=2))
    assert code == 1
    assert capsys.readouterr().out.endswith(
        "  prozesscode.a: 75.0 % → 50.0 %  VERSCHLECHTERT\n"
        "\n"
        "✗ Sperrklinke gerissen – die Testgüte ist unter den festgehaltenen Stand gefallen\n"
        "  mutmut: 4 Mutanten bewertet, 2 überlebt\n"
        "   (vollständiger Output: --verbose)\n")
    assert mr.lies_baseline() == basis


@pytest.mark.aufrufpfad("mutmut-run")
def test_gerissene_klinke_mit_verbose_nennt_das_modul(tmp_path, monkeypatch, capsys):
    """Die Tabelle je Modul entsteht erst nach dem Lauf und steht nicht in dessen Rohausgabe.
    Ohne sie meldet ein Volllauf mit --verbose „gerissen", ohne zu sagen, wo."""
    basis = {"prozesscode.a": {"getoetet": 3, "beurteilbar": 4, "messung": "m"}}
    code = _klinke_ueber_main(tmp_path, monkeypatch, basis, eintraege(killed=2, survived=2),
                              "--verbose", roh="Running mutation testing\n\n")
    assert code == 1
    assert capsys.readouterr().out == (
        "Running mutation testing\n"
        "  prozesscode.a: 75.0 % → 50.0 %  VERSCHLECHTERT\n"
        "✗ Sperrklinke gerissen – die Testgüte ist unter den festgehaltenen Stand gefallen\n"
        "  mutmut: 4 Mutanten bewertet, 2 überlebt\n")


def test_offene_mutanten_werden_je_modul_gezaehlt():
    """Ein Teillauf in Modul a darf die Aussage über Modul b nicht entwerten."""
    eintr = [("prozesscode.a.x_f__mutmut_1", mr.NICHT_BEWERTET),
             ("prozesscode.b.x_g__mutmut_1", "killed")]
    assert mr.offene_je_modul(eintr) == {"prozesscode.a": 1, "prozesscode.b": 0}

"""Tests für die Sperrklinke von mutmut-run.py – `--ratchet`.

Die Sperrklinke beantwortet die Frage, die ein einzelner Lauf nicht beantworten kann:
*Ist die Testgüte dieses Moduls schlechter als beim letzten Mal?* Ohne einen festgehaltenen
Vorher-Wert ist eine Mutationszahl nur eine Momentaufnahme – man sieht, dass 34 Mutanten
überleben, aber nicht, ob es gestern 12 waren.

Bewusst KEIN Gate (kein Hook, kein Commit-Zwang): Ein Lauf über ein Modul mittlerer Größe
dauert gemessen 84 s, große Module liegen darüber. Ein Zwang in dieser Größenordnung
erzeugt den Druck, unter dem er umgangen wird. Die Klinke greift nur, wenn jemand sie zieht.
"""
from importlib import import_module

mr = import_module("prozesscode.mutmut-run")


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


def test_die_gruppierung_reicht_die_ausklammerung_durch():
    """Sonst rechnete die Klinke mit den Meldungstext-Mutanten, die das Verdikt bereits
    ausklammert – zwei verschiedene Zahlen für dieselbe Sache."""
    roh = [("prozesscode.a.x_f__mutmut_1", "survived"),
           ("prozesscode.a.x_f__mutmut_2", "killed")]
    assert mr.nach_modul(roh, {"prozesscode.a.x_f__mutmut_1"}) == {"prozesscode.a": (1, 1)}


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
    """1/3 und 33 % sind nicht dasselbe: Gerundet verschwinden kleine Rückschritte.

    33.33…% vs. 33.33…% – bei zwei Nachkommastellen wären 100/300 und 33/100 gleich, als
    Bruch ist 33/100 kleiner.
    """
    basis = {"prozesscode.a": {"getoetet": 100, "beurteilbar": 300}}
    _zeilen, schlechter, _neu = mr.ratchet({"prozesscode.a": (33, 100)}, basis)
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

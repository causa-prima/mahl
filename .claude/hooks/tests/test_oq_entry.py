"""Tests für oq_entry.py – offene Fragen lesen, erfassen, ändern, löschen.

Warum es dieses Modul gibt (OBS-S120-1): `open-questions.md` war der einzige Tracker ohne
Pflege-Werkzeug – `open_questions.py` ist ein reines Import-Modul (`parse`/`due`) ohne CLI.
Fürs Löschen entstanden dadurch zweimal Wegwerf-Scripte, bei insgesamt drei Löschungen in
der ganzen Projekthistorie. Das Löschen ist hier die teure Operation, nicht das Anlegen:
Es muss den `Fällig`-Anker nicht kennen, wohl aber die Verweise, die anderswo hängenbleiben
(in S120 blockte `check-dangling-refs.py` den ersten Versuch, danach blieb der Eintrag halb
erledigt stehen, weil nach dem Bereinigen niemand nachfasste).
"""
import os
import sys
from importlib import import_module

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
oq = import_module("oq_entry")

BESTAND = """# Offene Fragen

<!-- Header mit Format-Vorlage: ## OQ-S<NNN>-<n> — <Kurztitel> -->

## OQ-S094-1 — Erste Frage
**Frage:** Lohnt sich X?
**Fällig:** Phase:V1 – weil Y
**Hintergrund:** Kam mehrfach auf.

---

## OQ-S119-3 — Zweite Frage
**Frage:** Und Z?
**Fällig:** S130 – reiner Backstop
**Hintergrund:** Recherchiert in S119.
"""


# --- Lesen -------------------------------------------------------------------
def test_get_liefert_den_ganzen_eintrag():
    eintrag = oq.get(BESTAND, "OQ-S094-1")
    assert "Lohnt sich X?" in eintrag
    assert "Phase:V1" in eintrag


def test_get_liefert_nur_den_gefragten_eintrag():
    """Gegenprobe: sonst wäre `get` ein verkappter Vollread."""
    assert "Und Z?" not in oq.get(BESTAND, "OQ-S094-1")


def test_get_unbekannte_id_ist_none():
    assert oq.get(BESTAND, "OQ-S999-9") is None


# --- Anlegen -----------------------------------------------------------------
def test_add_vergibt_die_naechste_id_der_laufenden_session():
    neu, oid = oq.add(BESTAND, 124, titel="Dritte", frage="Wie?",
                      faellig="S140 – Backstop", hintergrund="H")
    assert oid == "OQ-S124-1"
    assert oq.get(neu, oid) is not None


def test_add_zaehlt_innerhalb_der_session_hoch():
    zwischen, _ = oq.add(BESTAND, 124, titel="A", frage="?",
                         faellig="S140 – x", hintergrund="H")
    _, zweite = oq.add(zwischen, 124, titel="B", frage="?",
                       faellig="S140 – x", hintergrund="H")
    assert zweite == "OQ-S124-2"


def test_add_weist_untragfaehigen_anker_ab():
    """Dieselbe Grammatik wie check-oq-capture.py – ein Vertipper darf nicht durchrutschen."""
    with pytest.raises(ValueError):
        oq.add(BESTAND, 124, titel="X", frage="?", faellig="irgendwann mal",
               hintergrund="H")


def test_add_akzeptiert_gueltigen_anker():
    """Gegenprobe zum Test darüber."""
    neu, oid = oq.add(BESTAND, 124, titel="X", frage="?",
                      faellig="Phase:MVP – beim Wechsel", hintergrund="H")
    assert oq.get(neu, oid) is not None


# --- Ändern ------------------------------------------------------------------
def test_set_ersetzt_ein_feld():
    neu = oq.set_fields(BESTAND, "OQ-S094-1", faellig="S200 – verschoben")
    assert "S200 – verschoben" in oq.get(neu, "OQ-S094-1")
    assert "Phase:V1" not in oq.get(neu, "OQ-S094-1")


def test_set_laesst_andere_eintraege_unberuehrt():
    neu = oq.set_fields(BESTAND, "OQ-S094-1", faellig="S200 – verschoben")
    assert oq.get(neu, "OQ-S119-3") == oq.get(BESTAND, "OQ-S119-3")


def test_set_prueft_den_anker_ebenfalls():
    with pytest.raises(ValueError):
        oq.set_fields(BESTAND, "OQ-S094-1", faellig="bald")


# --- Löschen -----------------------------------------------------------------
def test_remove_entfernt_den_eintrag():
    neu = oq.remove(BESTAND, "OQ-S094-1")
    assert oq.get(neu, "OQ-S094-1") is None


def test_remove_laesst_den_rest_intakt():
    """Der eigentliche Fehlerfall wäre ein Löschen, das den Nachbarn mitnimmt."""
    neu = oq.remove(BESTAND, "OQ-S094-1")
    assert oq.get(neu, "OQ-S119-3") is not None
    assert neu.startswith("# Offene Fragen")


def test_remove_laesst_keine_trennlinien_ruine():
    neu = oq.remove(BESTAND, "OQ-S094-1")
    assert "---\n\n---" not in neu
    assert not neu.rstrip().endswith("---")


def test_remove_unbekannte_id_scheitert():
    with pytest.raises(ValueError):
        oq.remove(BESTAND, "OQ-S999-9")


def test_remove_des_letzten_eintrags_haelt_den_header():
    ohne_erste = oq.remove(BESTAND, "OQ-S094-1")
    leer = oq.remove(ohne_erste, "OQ-S119-3")
    assert leer.startswith("# Offene Fragen")
    assert "OQ-S" not in leer.split("-->")[-1]

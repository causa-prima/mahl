"""Tests für guard-stats.py – welcher Guard hat je gefeuert?

Die eine Falle, gegen die hier vor allem getestet wird: Der Report darf seine eigene Jugend
nicht als Befund über die Guards ausgeben. Am ersten Tag hat nichts gefeuert – ein „7 Guards
tot" wäre dann eine Aussage über das Protokoll, nicht über die Guards.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
stats = import_module("guard-stats")


def test_definierte_guards_kommen_aus_beiden_dispatchern():
    """Die Liste wird nicht gepflegt, sondern aus den Dispatchern gelesen – eine gepflegte
    Kopie driftet, und zwar unbemerkt in Richtung „sieht vollständig aus"."""
    namen = stats.definierte_guards()
    assert "check-anchors" in namen          # blockierend, dispatch-edit-write
    assert "tooling_tests" in namen          # nicht-blockierend, check-code-quality
    assert "ruff_lint" in namen


def test_bericht_weist_jede_ausloesung_aus():
    zeilen = stats.bericht({"check-anchors": 3, "tooling_tests": 1}, seit="2026-01-01T00:00:00")
    text = "\n".join(zeilen)
    assert "check-anchors" in text and "3" in text
    assert "tooling_tests" in text


def test_nie_gefeuerte_guards_werden_markiert():
    zeilen = stats.bericht({"check-anchors": 400}, seit="2026-01-01T00:00:00")
    stumm = [z for z in zeilen if stats.MARKE_STUMM in z]
    assert stumm, "kein Guard als stumm markiert, obwohl nur einer gefeuert hat"
    assert not any("check-anchors" in z for z in stumm)


def test_duenne_datenlage_wird_als_solche_benannt():
    """Der Report darf seine eigene Jugend nicht als Befund ausgeben."""
    text = "\n".join(stats.bericht({"check-anchors": 2}, seit="2026-01-01T00:00:00"))
    assert stats.HINWEIS_DUENN in text


def test_reiche_datenlage_traegt_den_hinweis_nicht():
    """Gegenprobe: Sonst stünde die Einschränkung immer da und würde bedeutungslos."""
    viele = {"check-anchors": stats.GENUG_AUSLOESUNGEN + 50}
    text = "\n".join(stats.bericht(viele, seit="2026-01-01T00:00:00"))
    assert stats.HINWEIS_DUENN not in text


def test_ein_unbekannter_guard_im_protokoll_wird_ausgewiesen():
    """Ein umbenannter oder gelöschter Guard darf nicht stillschweigend verschwinden –
    sonst zählt der Report Auslösungen, die er niemandem zuordnet."""
    text = "\n".join(stats.bericht({"gibt-es-nicht-mehr": 5}, seit="2026-01-01T00:00:00"))
    assert "gibt-es-nicht-mehr" in text
    assert stats.MARKE_UNBEKANNT in text


def test_ohne_protokoll_sagt_der_bericht_das():
    text = "\n".join(stats.bericht({}, seit=None))
    assert "noch keine" in text.lower()

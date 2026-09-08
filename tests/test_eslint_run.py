"""Tests für das Verdikt von eslint-run.py.

Der Wrapper hatte bis S130 keinen Test – und meldete auf unverändertem `main` seit
mindestens S112 `✗ ESLint: 3 Problem(e)` bei **null Errors**. Die drei Meldungen sind
Warnungen, die `Client/eslint.config.js` mit ausbuchstabierter Begründung bewusst auf
`warn` statt `error` setzt. Damit widersprachen sich Konfiguration und Werkzeug.

Der Exit-Code war dabei immer korrekt (0), es blockte also nichts. Der Schaden liegt
woanders: Ein Verdikt, das im sauberen Ausgangszustand dauerhaft ✗ zeigt, wird überlesen –
auch dann, wenn es einmal recht hat.
"""
from importlib import import_module

er = import_module("prozesscode.eslint-run")


def summary(errors: int, warnings: int) -> str:
    """Die Abschlusszeile, wie ESLint sie schreibt."""
    gesamt = errors + warnings
    return f"✖ {gesamt} problems ({errors} errors, {warnings} warnings)"


def test_ohne_meldungen_ist_alles_sauber():
    assert er.verdikt("", []) == "✓ ESLint: keine Probleme"


def test_nur_warnungen_sind_kein_fehlschlag():
    """Der Kern von OBS-S112-4: `warn` ist die Einstufung der Konfiguration, kein Fehler."""
    ergebnis = er.verdikt(summary(0, 3), ["irgendeine Warnung"])
    assert ergebnis.startswith("✓")
    assert "3" in ergebnis


def test_fehler_bleiben_ein_fehlschlag():
    """GEGENPROBE: Die Lockerung darf echte Errors nicht mit durchlassen."""
    assert er.verdikt(summary(2, 1), ["ein Fehler"]).startswith("✗")


def test_ein_einziger_fehler_genuegt_fuer_den_fehlschlag():
    assert er.verdikt(summary(1, 0), ["ein Fehler"]).startswith("✗")


def test_unlesbare_zusammenfassung_meldet_lieber_fehlschlag():
    """Ein Parser-Fehlgriff darf nicht still zu einem ✓ werden.

    Ändert ESLint sein Ausgabeformat, findet die Regex die Fehlerzahl nicht mehr. Dann ist
    ✗ die einzig vertretbare Antwort: Es gibt Meldungen, und wie viele davon Fehler sind,
    weiß das Werkzeug gerade nicht.
    """
    assert er.verdikt("völlig anderes Format", ["irgendeine Meldung"]).startswith("✗")

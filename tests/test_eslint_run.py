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

import pytest
from conftest import cli_aufruf

er = import_module("prozesscode.eslint-run")

_HINT = "   (vollständiger Output: --verbose)"

# ESLint-Block einer echten Ausgabe (zwei Fehler in einer Wegwerfdatei – dieselbe wie in
# test_qa_check.py), mit dem npm-Kopf davor, wie `run_npm` ihn liefert.
_ESLINT_BLOCK = """\
/home/kieritz/repos/mahl/Client/e2e/api/zz-gegenprobe.ts
  2:3  error  Unexpected let, use const instead           functional/no-let
  3:3  error  Unexpected loop, use map or reduce instead  functional/no-loop-statements

/home/kieritz/repos/mahl/Client/src/pages/CreateRecipePage.tsx
  15:16  warning  Function 'CreateRecipePage' has too many lines (52). Maximum allowed is 50  max-lines-per-function

✖ 3 problems (2 errors, 1 warning)"""
_NPM_KOPF = "\n> mahl-client@0.0.0 lint\n> eslint .\n\n"
_ROH_ROT = f"{_NPM_KOPF}{_ESLINT_BLOCK}\n\n"


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


def test_unlesbare_zusammenfassung_vollstaendige_meldung():
    assert er.verdikt("völlig anderes Format", ["irgendeine Meldung"]) == (
        "✗ ESLint: Meldungen vorhanden, Zusammenfassung nicht lesbar – oben aufgelistet")


# --- Aufrufpfad -----------------------------------------------------------------
def _npm(monkeypatch, ausgabe: str, exit_code: int) -> None:
    monkeypatch.setattr(er, "run_npm", lambda _argumente: (ausgabe, exit_code))


@pytest.mark.aufrufpfad("eslint-run")
def test_roter_lauf_listet_die_meldungen_ohne_npm_kopf_vor_dem_verdikt(monkeypatch, capsys):
    _npm(monkeypatch, _ROH_ROT, 1)
    assert cli_aufruf(monkeypatch, er) == 1
    assert capsys.readouterr().out == (
        f"{_ESLINT_BLOCK}\n"
        "\n"
        "✗ ESLint: 2 Fehler, 1 Warnung(en) – oben aufgelistet\n"
        f"{_HINT}\n")


def test_sauberer_lauf_zeigt_nur_das_verdikt(monkeypatch, capsys):
    """ESLint schreibt bei sauberem Lauf nichts – übrig bleibt der npm-Kopf, und der ist Rauschen."""
    _npm(monkeypatch, _NPM_KOPF, 0)
    assert cli_aufruf(monkeypatch, er) == 0
    assert capsys.readouterr().out == f"✓ ESLint: keine Probleme\n{_HINT}\n"


def test_verbose_zeigt_die_rohausgabe(monkeypatch, capsys):
    _npm(monkeypatch, _ROH_ROT, 1)
    assert cli_aufruf(monkeypatch, er, "--verbose") == 1
    assert capsys.readouterr().out == (
        _ROH_ROT.rstrip() + "\n✗ ESLint: 2 Fehler, 1 Warnung(en) – oben aufgelistet\n")

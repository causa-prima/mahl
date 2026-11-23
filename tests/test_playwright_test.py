"""Tests für playwright-test.py: Verdikt und Exit-Code aus der Ausgabe von `npm run test:e2e`.

npm wird ersetzt. Der grüne Lauf und „No tests found“ sind echte Ausgaben (`playwright-test
--verbose`); der rote Lauf folgt deren Format (npm-Kopf, `Running N tests using M worker`,
Fehlerblock, Abschlusszeilen `N failed`/`N passed (Dauer)`), Test- und Dateinamen gekürzt.
"""
import os
import shutil
from importlib import import_module
from pathlib import Path

import pytest

from conftest import cli_aufruf
from prozesscode._run_lock import LOCK_BUSY_EXIT_CODE

modul = import_module("prozesscode.playwright-test")

_HINWEIS = "   (vollständiger Output: --verbose)\n"
_NPM_KOPF = "\n> mahl-client@0.0.0 test:e2e\n> playwright test\n\n"

# Echt: `playwright-test --filter US602_HappyPath_GetRecipes --verbose`.
_GRUEN = (
    "\n"
    "> mahl-client@0.0.0 test:e2e\n"
    "> playwright test --grep US602_HappyPath_GetRecipes\n"
    "\n"
    "\n"
    "Running 2 tests using 1 worker\n"
    "\n"
    "  ✓  1 [chromium] › e2e/recipes.spec.ts:12:3 › US602_HappyPath: Rezepte erfassen › "
    "US602_HappyPath_GetRecipes_EmptyDb_ShowsEmptyList (473ms)\n"
    "  ✓  2 [chromium] › e2e/recipes.spec.ts:67:3 › US602_HappyPath: Rezepte erfassen › "
    "US602_HappyPath_GetRecipes_MultipleRecipes_AppearAlphabeticallySorted (652ms)\n"
    "\n"
    "  2 passed (5.9s)\n"
)

# Echt: `playwright-test --filter "Zutat anlegen" --verbose` – kein Test heißt so.
_KEIN_TEST = "\n> mahl-client@0.0.0 test:e2e\n> playwright test --grep Zutat anlegen\n\nError: No tests found\n"

# Was nach dem Entfernen des npm-Kopfs übrig bleibt – das zeigt der Wrapper bei Rot, ohne die
# Zeilen grüner Tests.
_GRUENE_ZEILE = "  ✓  1 [chromium] › e2e/ingredients.spec.ts:264:3 › Zutaten › Name mit 30 Zeichen (1.0s)\n"
_ROT_DETAILS = (
    "Running 3 tests using 1 worker\n"
    "\n"
    + _GRUENE_ZEILE +
    "  ✘  2 [chromium] › e2e/ingredients.spec.ts:373:3 › Zutaten › Name zu lang (5.9s)\n"
    "  ✘  3 [chromium] › e2e/ingredients.spec.ts:390:3 › Zutaten › Einheit zu lang (5.8s)\n"
    "\n"
    "\n"
    "  1) [chromium] › e2e/ingredients.spec.ts:373:3 › Zutaten › Name zu lang \n"
    "\n"
    "    Error: expect(locator).toBeVisible() failed\n"
    "\n"
    "    Locator: getByText('Name darf maximal 30 Zeichen lang sein.')\n"
    "    Expected: visible\n"
    "    Timeout: 5000ms\n"
    "    Error: element(s) not found\n"
    "\n"
    "  2 failed\n"
    "    [chromium] › e2e/ingredients.spec.ts:373:3 › Zutaten › Name zu lang \n"
    "    [chromium] › e2e/ingredients.spec.ts:390:3 › Zutaten › Einheit zu lang \n"
    "  1 passed (16.5s)"
)
_ROT = _NPM_KOPF + _ROT_DETAILS + "\n"


def _npm(monkeypatch, ausgabe: str, exit_code: int) -> list:
    aufrufe = []
    monkeypatch.setattr(modul, "run_npm",
                        lambda argumente: aufrufe.append(argumente) or (ausgabe, exit_code))
    return aufrufe


@pytest.mark.aufrufpfad("playwright-test")
def test_gruener_lauf_zeigt_nur_das_verdikt_mit_anzahl_und_dauer(monkeypatch, capsys):
    aufrufe = _npm(monkeypatch, _GRUEN, 0)
    assert cli_aufruf(monkeypatch, modul, "--filter", "US602_HappyPath_GetRecipes") == 0
    assert aufrufe == [["run", "test:e2e", "--", "--grep", "US602_HappyPath_GetRecipes"]]
    assert capsys.readouterr().out == "✓ 2 E2E-Tests grün, 5.9s\n" + _HINWEIS


def test_laufender_e2e_lauf_sperrt_den_zweiten_bevor_npm_startet(monkeypatch, tmp_path, capsys):
    """Parallele Läufe (Auditoren) bauten dasselbe Backend und stritten um Port 5059."""
    monkeypatch.setattr(modul, "_LAUF_LOCK", tmp_path / "playwright_run")
    (tmp_path / "playwright_run.lock").write_text("1", encoding="utf-8")  # PID 1 lebt immer
    aufrufe = _npm(monkeypatch, _GRUEN, 0)
    assert cli_aufruf(monkeypatch, modul) == LOCK_BUSY_EXIT_CODE
    assert aufrufe == []
    assert "Konkurrierender E2E-Lauf aktiv" in capsys.readouterr().err


def test_ohne_filter_laufen_alle_tests(monkeypatch):
    aufrufe = _npm(monkeypatch, _GRUEN, 0)
    cli_aufruf(monkeypatch, modul)
    assert aufrufe == [["run", "test:e2e", "--"]]


@pytest.mark.aufrufpfad("playwright-test")
def test_filter_ohne_treffer_sagt_das_statt_rot(monkeypatch, capsys):
    """Es lief nichts – „rot" schickte die Suche zum falschen Test."""
    _npm(monkeypatch, _KEIN_TEST, 1)
    assert cli_aufruf(monkeypatch, modul, "--filter", "Zutat anlegen") == 1
    assert capsys.readouterr().out == (
        "Error: No tests found\n\n" + modul.KEIN_TEST_GEFUNDEN + "\n" + _HINWEIS)


def test_abschlusszeile_ohne_dauer_ergibt_verdikt_ohne_dauer(monkeypatch, capsys):
    _npm(monkeypatch, "  3 passed\n", 0)
    assert cli_aufruf(monkeypatch, modul) == 0
    assert capsys.readouterr().out == "✓ 3 E2E-Tests grün\n" + _HINWEIS


@pytest.mark.aufrufpfad("playwright-test")
def test_gruener_lauf_mit_verbose_zeigt_die_rohausgabe_und_das_verdikt(monkeypatch, capsys):
    _npm(monkeypatch, _GRUEN, 0)
    assert cli_aufruf(monkeypatch, modul, "--verbose") == 0
    assert capsys.readouterr().out == _GRUEN.rstrip() + "\n✓ 2 E2E-Tests grün, 5.9s\n"


@pytest.mark.aufrufpfad("playwright-test")
def test_roter_lauf_zeigt_den_fehlerblock_ohne_npm_kopf_und_gibt_den_exit_code_weiter(
        monkeypatch, capsys):
    """Der Fehlerblock (Erwartung, Locator) IST die Analyse-Information – er bleibt ganz. Die
    Zeilen grüner Tests fallen weg: Bei 169 Tests schoben sie den Fehlerblock in den Teil, den
    die Harness beim Kürzen der Ausgabe auslässt."""
    _npm(monkeypatch, _ROT, 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert capsys.readouterr().out == (
        _ROT_DETAILS.replace(_GRUENE_ZEILE, "") + "\n\n✗ 2 E2E-Test(s) rot – Details oben\n" + _HINWEIS)


@pytest.mark.aufrufpfad("playwright-test")
def test_roter_lauf_mit_verbose_zeigt_die_rohausgabe(monkeypatch, capsys):
    _npm(monkeypatch, _ROT, 1)
    assert cli_aufruf(monkeypatch, modul, "--verbose") == 1
    assert capsys.readouterr().out == _ROT.rstrip() + "\n✗ 2 E2E-Test(s) rot – Details oben\n"


def test_abbruch_ohne_abschlusszeile_meldet_unbekannte_anzahl(monkeypatch, capsys):
    """Startet der Webserver nicht, gibt es keine Zählzeile – das Verdikt rät dann nicht."""
    ausgabe = _NPM_KOPF + "Error: Process from config.webServer was not able to start. Exit code: 1\n"
    _npm(monkeypatch, ausgabe, 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert capsys.readouterr().out == (
        "Error: Process from config.webServer was not able to start. Exit code: 1\n"
        "\n✗ ? E2E-Test(s) rot – Details oben\n" + _HINWEIS)


# --- Sichtprüfung bei Handybreite ----------------------------------------------
# Echter Trace: `MAHL_HANDYBREITE=375`, Test „Formular öffnen, Felder leer" (8 Bilder).
_TRACE = Path(__file__).parent / "fixtures" / "playwright_trace_375px.zip"


def test_bilder_aus_dem_trace_in_zeitfolge_benannt_nach_der_laufenden_aktion(tmp_path):
    """Die Bildfolge hinkt dem Browser hinterher – benannt wird nach der zuletzt begonnenen
    Aktion, nicht behauptet, das Bild zeige deren Ergebnis."""
    bilder = modul.bilder_aus_trace(_TRACE, tmp_path)
    assert [b.name for b in bilder] == [
        "01-Navigate-recipes.jpeg",
        "02-Navigate-recipes.jpeg",
        "03-Click-getByRole-button-name-Rezept-anlegen.jpeg",
        "04-Click-getByRole-button-name-Rezept-anlegen.jpeg",
        "05-Expect-toHaveValue-getByLabel-Titel.jpeg",
        "06-Expect-toHaveValue-getByLabel-Zutaten.jpeg",
        "07-Expect-toHaveValue-getByLabel-Zutaten.jpeg",
        "08-Expect-toHaveValue-getByRole-group-name-Schritte-getByLabel.jpeg",  # auf 60 gekürzt
    ]
    assert all(b.read_bytes()[:3] == b"\xff\xd8\xff" for b in bilder)  # JPEG


def test_handybreite_setzt_die_breite_und_legt_die_bilder_je_test_ab(
        monkeypatch, tmp_path, capsys):
    ergebnisse = tmp_path / "test-results"
    monkeypatch.setattr(modul, "TEST_RESULTS", ergebnisse)
    monkeypatch.delenv("MAHL_HANDYBREITE", raising=False)
    breite_im_lauf = []

    def lauf(argumente):
        breite_im_lauf.append(os.environ.get("MAHL_HANDYBREITE"))
        (ergebnisse / "recipes-Formular-chromium").mkdir(parents=True)
        shutil.copy(_TRACE, ergebnisse / "recipes-Formular-chromium" / "trace.zip")
        return _GRUEN, 0

    monkeypatch.setattr(modul, "run_npm", lauf)
    assert cli_aufruf(monkeypatch, modul, "--handybreite", "375") == 0
    assert breite_im_lauf == ["375"]
    ziel = ergebnisse / "handybreite" / "recipes-Formular-chromium"
    assert len(list(ziel.glob("*.jpeg"))) == 8
    assert capsys.readouterr().out == (
        f"✓ 2 E2E-Tests grün, 5.9s\n  Bilder bei 375 px: {ergebnisse / 'handybreite'} "
        "(8 aus 1 Test)\n" + _HINWEIS)


def test_ohne_handybreite_keine_bilder(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(modul, "TEST_RESULTS", tmp_path)
    monkeypatch.delenv("MAHL_HANDYBREITE", raising=False)
    breite_im_lauf = []
    monkeypatch.setattr(modul, "run_npm", lambda a: breite_im_lauf.append(
        os.environ.get("MAHL_HANDYBREITE")) or (_GRUEN, 0))
    cli_aufruf(monkeypatch, modul)
    assert breite_im_lauf == [None]
    assert "Bilder" not in capsys.readouterr().out


def test_flaky_test_endet_trotz_exit_null_als_fehlschlag(monkeypatch, capsys):
    """Playwright endet bei flaky Tests mit 0. Ein ✗-Verdikt mit Exit 0 läse jedes Gate, das nur
    den Exit-Code prüft, als grün."""
    _npm(monkeypatch, "  1 flaky\n    [chromium] › e2e/a.spec.ts:3:3 › A › b \n  2 passed (4.0s)\n", 0)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert capsys.readouterr().out == (
        "  1 flaky\n    [chromium] › e2e/a.spec.ts:3:3 › A › b \n  2 passed (4.0s)\n"
        "\n✗ 1 E2E-Test(s) rot – Details oben\n" + _HINWEIS)

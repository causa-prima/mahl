"""Tests für vitest-run.py – Verdikt, Filter-Hinweise und DOM-Kürzung.

Ergänzt die Aufrufpfad-Tests in `test_aufrufpfad_wrapper.py` um die vollständige Ausgabe:
Ein Verdikt, das eine Zahl oder einen Zusatz verliert, bleibt dort grün. npm wird ersetzt;
die Ausgaben haben die Form von vitest 5.1 (Zusammenfassungsblock wie in der gespeicherten
Ausgabe `tests/fixtures/vitest_rot_dom_dump.txt`).
"""
from importlib import import_module
from pathlib import Path

import pytest
from conftest import cli_aufruf

vr = import_module("prozesscode.vitest-run")

_HINT = "   (vollständiger Output: --verbose)"

# Echte Ausgabe von vitest 5.1, `vitest-run --filter If-None-Match --verbose`: grün, mit
# übersprungenen Tests.
_GRUEN_MIT_UEBERSPRUNGENEN = """\
> mahl-client@0.0.0 test
> vitest run -t If-None-Match


 RUN  v5.1.0 /home/kieritz/repos/mahl/Client


 Test Files  1 passed | 3 skipped (4)
      Tests  2 passed | 85 skipped (87)
   Start at  13:07:24
   Duration  1.02s (environment 29%, import 28%, transform 27%, setup 14%, tests 1%, worker 1%)
"""

# Echte Ausgabe von vitest 5.1 bei einem Filter ohne Treffer, ohne npm-Kopf
# (dieselbe wie in test_aufrufpfad_wrapper.py).
_FILTER_OHNE_TREFFER = """\

 RUN  v5.1.0 /home/kieritz/repos/mahl/Client


 Test Files  4 skipped (4)
      Tests  87 skipped (87)
   Start at  09:30:40
   Duration  1.25s (environment 33%, transform 29%, import 24%, setup 13%, worker 1%)
"""

_ROT = (Path(__file__).parent / "fixtures" / "vitest_rot_dom_dump.txt").read_text(encoding="utf-8")

def _filter_zeile(pattern: str) -> str:
    return (f"\n[filter] --filter '{pattern}' matcht als Substring gegen den voll-qualifizierten "
            "Testnamen (describe-Block und Test mit ' > ' verbunden).\n")


def _npm(monkeypatch, ausgabe: str, exit_code: int = 0) -> None:
    monkeypatch.setattr(vr, "run_npm", lambda _argumente: (ausgabe, exit_code))


# --- Grünes Verdikt -----------------------------------------------------------
@pytest.mark.aufrufpfad("vitest-run")
def test_gruenes_verdikt_nennt_uebersprungene_dateien_und_dauer(monkeypatch, capsys):
    _npm(monkeypatch, _GRUEN_MIT_UEBERSPRUNGENEN)
    assert cli_aufruf(monkeypatch, vr, "--filter", "If-None-Match") == 0
    ausgabe = capsys.readouterr()
    assert ausgabe.out == f"✓ 2 Tests grün, 85 übersprungen, 4 Dateien, 1.02s\n{_HINT}\n"
    assert ausgabe.err == (_filter_zeile("If-None-Match")
                           + "[filter] 2 ausgeführt, 85 übersprungen (von 87).\n")


def test_gruenes_verdikt_ohne_zusaetze(monkeypatch, capsys):
    """Ohne übersprungene Tests, Datei- und Dauerzeile steht nur die Zahl da."""
    _npm(monkeypatch, "      Tests  3 passed (3)\n")
    assert cli_aufruf(monkeypatch, vr) == 0
    ausgabe = capsys.readouterr()
    assert ausgabe.out == f"✓ 3 Tests grün\n{_HINT}\n"
    assert ausgabe.err == ""


def test_gruener_lauf_mit_verbose_gibt_die_rohausgabe_aus(monkeypatch, capsys):
    _npm(monkeypatch, _GRUEN_MIT_UEBERSPRUNGENEN)
    assert cli_aufruf(monkeypatch, vr, "--verbose") == 0
    assert capsys.readouterr().out == (_GRUEN_MIT_UEBERSPRUNGENEN.rstrip()
                                       + "\n✓ 2 Tests grün, 85 übersprungen, 4 Dateien, 1.02s\n")


# --- Filter ohne Treffer ------------------------------------------------------
def test_filter_ohne_treffer_vollstaendige_meldung(monkeypatch, capsys):
    _npm(monkeypatch, _FILTER_OHNE_TREFFER)
    assert cli_aufruf(monkeypatch, vr, "--filter", "sucht") == 1
    ausgabe = capsys.readouterr()
    assert ausgabe.out == f"{vr.FILTER_OHNE_TREFFER}\n{_HINT}\n"
    assert ausgabe.err == (
        _filter_zeile("sucht")
        + "[filter] 0 ausgeführt, 87 übersprungen (von 87).\n"
        "[filter] ⚠️  0 Tests gematcht – alle übersprungen. Tippfehler im Pattern oder Test "
        "existiert (noch) nicht? → als FEHLER gewertet.\n")


# --- Roter Lauf ---------------------------------------------------------------
def test_roter_lauf_laesst_banner_und_zeitstempel_weg(monkeypatch, capsys):
    """Gegen die gespeicherte Ausgabe eines echten roten Laufs: Die Zusammenfassung bleibt,
    vitest-Banner, Startzeit und Dauer fallen weg – sie sagen nichts über die Tests."""
    _npm(monkeypatch, _ROT, 1)
    assert cli_aufruf(monkeypatch, vr) == 1
    zeilen = capsys.readouterr().out.splitlines()
    assert zeilen[-5:] == [" Test Files  1 failed (1)", "      Tests  5 failed (5)", "",
                           "✗ 5 Test(s) rot – Details oben", _HINT]
    assert not any("RUN  v5.1.0" in z or "Start at" in z or "Duration" in z for z in zeilen)


# --- DOM-Kürzung --------------------------------------------------------------
def _dom(innen: int) -> list[str]:
    return ["<body>", *[f"  <div>{i}</div>" for i in range(innen)]]


def test_eine_zeile_ueber_der_grenze_wird_schon_gekuerzt():
    """Bei `_DOM_DUMP_KEEP + 1` Zeilen ersetzte die Kürzungszeile nur eine – ab einer mehr
    lohnt sie sich."""
    dump = [*_dom(vr._DOM_DUMP_KEEP), "</body>"]  # KEEP + 2 Zeilen
    assert vr.shorten_dom_dumps(dump) == [
        *dump[:vr._DOM_DUMP_KEEP], "  … 2 Zeilen DOM gekürzt – vollständig: --verbose"]


def test_eine_offene_dom_ausgabe_am_ende_wird_gekuerzt_statt_verschluckt():
    zeilen = ["Fehler: Abfrage scheiterte", *_dom(20)]
    assert vr.shorten_dom_dumps(zeilen) == [
        "Fehler: Abfrage scheiterte", *_dom(20)[:vr._DOM_DUMP_KEEP],
        "  … 9 Zeilen DOM gekürzt – vollständig: --verbose"]


def test_eine_kurze_offene_dom_ausgabe_am_ende_bleibt_ganz():
    zeilen = ["Fehler", *_dom(3)]
    assert vr.shorten_dom_dumps(zeilen) == zeilen


# --- Aufruf von vitest --------------------------------------------------------

def test_jede_datei_geht_als_eigener_filter_an_vitest_ab_client(monkeypatch):
    # Zweimal --file heißt zwei Dateien: Ein einfaches argparse-Argument behielte nur die letzte, und der
    # Lauf wäre trotzdem grün – mit der Hälfte der Tests.
    argumente: list[list[str]] = []

    def run_npm(npm_args: list[str]) -> tuple[str, int]:
        argumente.append(npm_args)
        return "      Tests  3 passed (3)\n", 0

    monkeypatch.setattr(vr, "run_npm", run_npm)
    assert cli_aufruf(monkeypatch, vr, "--file", "Client/src/a.test.tsx", "--file", "src/b.test.tsx",
                      "--filter", "Titel") == 0
    assert argumente == [["run", "test", "--", "run", "src/a.test.tsx", "src/b.test.tsx", "-t", "Titel"]]

"""Aufrufpfad der Test-Wrapper und Gates: Argumente → `main()` → Aufruf des fremden Werkzeugs.

Die Wrapper sind für die Entwicklung entscheidend und liefen bis S133 in keinem Test über ihre
Kommandozeile (User-Vorgabe S133: keine Ausnahme für sie). Das fremde Werkzeug wird ersetzt;
geprüft wird, WIE es aufgerufen würde – dort gehen Argumente still verloren – und welches
Verdikt aus einer Ausgabe in echter Form entsteht.
"""
import subprocess
from importlib import import_module
from pathlib import Path

import pytest

from conftest import cli_aufruf


def _fake_npm(monkeypatch, modul, ausgabe: str, exit_code: int = 0) -> list:
    aufrufe = []
    monkeypatch.setattr(modul, "run_npm",
                        lambda argumente: aufrufe.append(argumente) or (ausgabe, exit_code))
    return aufrufe


# --- Frontend-Wrapper (npm) ---------------------------------------------------------
@pytest.mark.aufrufpfad("vitest-run")
def test_vitest_reicht_datei_und_filter_in_richtiger_reihenfolge_weiter(monkeypatch, capsys):
    modul = import_module("prozesscode.vitest-run")
    aufrufe = _fake_npm(monkeypatch, modul,
                        " Test Files  1 passed (1)\n      Tests  3 passed (3)\n   Duration  1.20s\n")
    code = cli_aufruf(monkeypatch, modul, "--file", "src/X.test.tsx", "--filter", "sucht")
    assert aufrufe == [["run", "test", "--", "run", "src/X.test.tsx", "-t", "sucht"]]
    assert code == 0
    assert "✓ 3 Tests grün" in capsys.readouterr().out


def test_vitest_nimmt_dateipfad_ab_repo_wurzel_an(monkeypatch):
    """vitest läuft in Client/ und matcht den Datei-Filter gegen Pfade relativ dazu; ein Pfad ab
    Repo-Wurzel (so, wie ihn git und die übrigen Werkzeuge nennen) fand sonst „No test files"."""
    modul = import_module("prozesscode.vitest-run")
    aufrufe = _fake_npm(monkeypatch, modul, "      Tests  3 passed (3)\n")
    cli_aufruf(monkeypatch, modul, "--file", "Client/src/pages/X.test.tsx")
    assert aufrufe == [["run", "test", "--", "run", "src/pages/X.test.tsx"]]


def test_vitest_roter_lauf_nennt_die_zahl_und_bleibt_rot(monkeypatch, capsys):
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, "      Tests  2 failed | 5 passed (7)\n", 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert "✗ 2 Test(s) rot" in capsys.readouterr().out


# Echte Ausgabe von vitest 5.1 bei einem Filter ohne Treffer, ohne npm-Kopf.
_VITEST_FILTER_OHNE_TREFFER = """\

 RUN  v5.1.0 /home/kieritz/repos/mahl/Client


 Test Files  4 skipped (4)
      Tests  87 skipped (87)
   Start at  09:30:40
   Duration  1.25s (environment 33%, transform 29%, import 24%, setup 13%, worker 1%)
"""


def test_vitest_filter_ohne_treffer_ist_ein_fehler_statt_gruen(monkeypatch, capsys):
    """Fail-closed-Guard: vitest -t überspringt Nicht-Treffer und läuft sonst grün durch.
    Bis S133 hielt kein Test diese Stelle (mutmut: `exit_code or 1` überlebte). Auch das
    Verdikt darf dann kein „✓" zeigen – sonst widerspricht es der Warnung darüber."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, _VITEST_FILTER_OHNE_TREFFER, 0)
    assert cli_aufruf(monkeypatch, modul, "--filter", "Tippfehler") == 1
    ausgabe = capsys.readouterr()
    assert "0 Tests gematcht" in ausgabe.err
    assert "✓" not in ausgabe.out
    assert ausgabe.out.startswith("✗")


def test_vitest_filter_ohne_treffer_zeigt_mit_verbose_die_rohausgabe(monkeypatch, capsys):
    """Hält `verbose` und `output` am Verdikt ohne Treffer – beide überlebten sonst mutmut."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, _VITEST_FILTER_OHNE_TREFFER, 0)
    assert cli_aufruf(monkeypatch, modul, "--filter", "Tippfehler", "--verbose") == 1
    ausgabe = capsys.readouterr().out
    assert "Tests  87 skipped (87)" in ausgabe
    assert ausgabe.endswith(modul.FILTER_OHNE_TREFFER + "\n")


def test_vitest_abbruch_ohne_zusammenfassung_meldet_rot_statt_abzustuerzen(monkeypatch, capsys):
    """Ohne `Tests`-Zeile (etwa wenn vitest schon beim Laden scheitert) gibt es keine Zähler;
    der Wrapper meldet dann rot statt mit einem Traceback abzustürzen (`if counts or True`).
    Handgeschriebene Ausgabe: Es kommt nur auf das Fehlen der Zusammenfassung an."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, "Error: failed to load config from vite.config.ts\n", 1)
    assert cli_aufruf(monkeypatch, modul, "--filter", "sucht") == 1
    assert "✗ ? Test(s) rot" in capsys.readouterr().out


def test_vitest_absturz_ohne_rote_tests_meldet_kein_gruen(monkeypatch, capsys):
    """Mutationssichtung S133: `exit_code == 0 or …` überlebte – ein Abbruch mit „0 failed" in
    der Zusammenfassung (etwa beim Einsammeln) hätte „✓ grün" gemeldet, bei rotem Exit-Code."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, "      Tests  5 passed (5)\nError: Unhandled rejection\n", 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert "✓" not in capsys.readouterr().out


_VITEST_ROT_DOM_DUMP = (Path(__file__).parent / "fixtures" / "vitest_rot_dom_dump.txt").read_text(encoding="utf-8")


def test_vitest_roter_lauf_kuerzt_jede_dom_ausgabe_auf_ihren_anfang(monkeypatch, capsys):
    """Gespeicherte Ausgabe eines echten roten Laufs (vitest 4.1.11, Testing Library, S143): ein
    roter Test mit zwei DOM-Ausgaben von je rund 210 Zeilen. Ungekürzt kamen beim RED von US-602
    run-6 (14 rote Tests) mehrere hundert KB beim Agenten an."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, _VITEST_ROT_DOM_DUMP, 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    ausgabe = capsys.readouterr().out
    # Befund und Fundstelle bleiben stehen …
    assert 'Unable to find role="button" and name "gibt es nicht"' in ausgabe
    assert "src/pages/zz-dom-dump.test.tsx:19:18" in ausgabe
    # … jede DOM-Ausgabe ist gekürzt und sagt, wie man sie ganz sieht
    assert ausgabe.count("Zeilen DOM gekürzt") == 2
    assert len(ausgabe.splitlines()) < 100


def test_vitest_roter_lauf_mit_offenem_dialog_kuerzt_auch_den_abgeschnittenen_dom(monkeypatch, capsys):
    """Gespeicherte Ausgabe eines echten roten Laufs mit offener Nachfrage (S143): MUI setzt `style`
    auf `<body>`, die Zeile lautet dann `<body` mit Attributen darunter, und Testing Library kürzt den
    Dump selbst auf `...` – ein `</body>` kommt nicht. Der Review-Auditor vermutete den ersten Teil;
    der Lauf zeigte beide."""
    fixture = Path(__file__).parent / "fixtures" / "vitest_rot_dom_dump_dialog.txt"
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, fixture.read_text(encoding="utf-8"), 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    ausgabe = capsys.readouterr().out
    assert ausgabe.count("Zeilen DOM gekürzt") == 2
    assert "src/pages/zz-dom-dialog.test.tsx:23:18" in ausgabe


def test_dom_ausgabe_ohne_schluss_verschluckt_nichts_dahinter():
    # // Given eine DOM-Ausgabe ohne </body>, danach Leerzeile, Fehlertext und eine zweite DOM-Ausgabe
    modul = import_module("prozesscode.vitest-run")
    dom = ["<body>", *[f"  <div>{i}</div>" for i in range(30)]]
    zeilen = [*dom, "", "Fehler: Abfrage scheiterte", "src/x.test.tsx:5:3", *dom, "</body>"]
    # // When gekürzt wird
    gekuerzt = modul.shorten_dom_dumps(zeilen)
    # // Then bleiben Fehlertext und Fundstelle stehen, beide Ausgaben sind gekürzt
    assert "Fehler: Abfrage scheiterte" in gekuerzt
    assert "src/x.test.tsx:5:3" in gekuerzt
    assert sum("Zeilen DOM gekürzt" in zeile for zeile in gekuerzt) == 2


def test_dom_ausgabe_folgt_direkt_auf_eine_offene_wird_einzeln_gekuerzt():
    # // Given zwei DOM-Ausgaben ohne Leerzeile dazwischen, die erste ohne </body>
    modul = import_module("prozesscode.vitest-run")
    dom = ["<body>", *[f"  <div>{i}</div>" for i in range(30)]]
    # // When / Then: jede wird für sich gekürzt
    gekuerzt = modul.shorten_dom_dumps([*dom, *dom, "</body>"])
    assert sum("Zeilen DOM gekürzt" in zeile for zeile in gekuerzt) == 2


def test_kurze_dom_ausgabe_bleibt_unveraendert():
    # // Given eine DOM-Ausgabe, die höchstens so lang ist wie der behaltene Anfang plus Kürzungszeile
    modul = import_module("prozesscode.vitest-run")
    kurz = ["<body>", *[f"  <div>{i}</div>" for i in range(11)], "</body>"]
    # // When / Then
    assert modul.shorten_dom_dumps(kurz) == kurz


def test_vitest_verbose_zeigt_die_dom_ausgabe_ungekuerzt(monkeypatch, capsys):
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, _VITEST_ROT_DOM_DUMP, 1)
    cli_aufruf(monkeypatch, modul, "--verbose")
    ausgabe = capsys.readouterr().out
    assert "Zeilen DOM gekürzt" not in ausgabe
    assert len(ausgabe.splitlines()) > 400


def test_vitest_filter_mit_gleich_vielen_roten_und_gruenen_treffern_hat_getroffen(monkeypatch, capsys):
    """Mutationssichtung S133: `passed - failed` überlebte – 1 grün + 1 rot ergäbe 0 Treffer."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, "      Tests  1 failed | 1 passed (2)\n", 1)
    assert cli_aufruf(monkeypatch, modul, "--filter", "sucht") == 1
    assert "0 Tests gematcht" not in capsys.readouterr().err


@pytest.mark.aufrufpfad("eslint-run")
def test_eslint_ruft_das_lint_skript_und_reicht_den_exit_code_durch(monkeypatch):
    modul = import_module("prozesscode.eslint-run")
    aufrufe = _fake_npm(monkeypatch, modul, "src/a.ts\n  3:1  error  x  no-unused-vars\n", 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert aufrufe == [["run", "lint"]]


@pytest.mark.aufrufpfad("playwright-test")
def test_playwright_reicht_den_filter_als_grep_weiter(monkeypatch, capsys):
    modul = import_module("prozesscode.playwright-test")
    aufrufe = _fake_npm(monkeypatch, modul, "  3 passed (5.1s)\n")
    assert cli_aufruf(monkeypatch, modul, "--filter", "Zutat") == 0
    assert aufrufe == [["run", "test:e2e", "--", "--grep", "Zutat"]]
    assert "✓ 3 E2E-Tests grün, 5.1s" in capsys.readouterr().out


# --- Stryker-Wrapper: --mutate wird je Werkzeug VERSCHIEDEN übergeben ---------------
@pytest.fixture
def stryker_lauf(tmp_path, monkeypatch):
    """Ersetzt den Stryker-Prozess; liefert die Liste der Aufrufe."""
    aufrufe = []

    def fake_run(argumente, **_kw):
        aufrufe.append(list(argumente))
        return subprocess.CompletedProcess(argumente, 1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    return aufrufe


def _stryker_modul(name, tmp_path, monkeypatch):
    modul = import_module(f"prozesscode.{name}")
    monkeypatch.setattr(modul, "_TMP_FILE", tmp_path / "stryker_out.txt")
    monkeypatch.setattr(modul, "resolve_mutate", lambda muster, *_: muster.split(","))
    return modul


@pytest.mark.aufrufpfad("stryker-frontend")
def test_stryker_frontend_uebergibt_mutate_als_eine_kommaliste(
        tmp_path, monkeypatch, stryker_lauf, capsys):
    """StrykerJS parst --mutate selbst als Liste; ein zweites Flag überschriebe das erste."""
    modul = _stryker_modul("stryker-frontend", tmp_path, monkeypatch)
    monkeypatch.setattr(modul, "_STRYKER_TMP", tmp_path / "stryker-tmp")
    monkeypatch.setattr(modul, "_STRYKER_SRC", tmp_path / "keine-reports")
    code = cli_aufruf(monkeypatch, modul, "--mutate", "src/a.ts,src/b.tsx")
    assert stryker_lauf[0] == ["npx", "stryker", "run", "--mutate", "src/a.ts,src/b.tsx"]
    assert code == 1
    assert "keinen Report" in capsys.readouterr().err


@pytest.mark.aufrufpfad("stryker-frontend")
def test_stryker_frontend_wiederholtes_mutate_flag_verliert_kein_muster(
        tmp_path, monkeypatch, stryker_lauf, capsys):
    """`--mutate a --mutate b` überschrieb still `a` – mutiert wurde nur `b` (S141)."""
    modul = _stryker_modul("stryker-frontend", tmp_path, monkeypatch)
    monkeypatch.setattr(modul, "_STRYKER_TMP", tmp_path / "stryker-tmp")
    monkeypatch.setattr(modul, "_STRYKER_SRC", tmp_path / "keine-reports")
    cli_aufruf(monkeypatch, modul, "--mutate", "src/a.ts", "--mutate", "src/b.tsx,src/c.ts")
    assert stryker_lauf[0] == ["npx", "stryker", "run", "--mutate", "src/a.ts,src/b.tsx,src/c.ts"]


@pytest.mark.aufrufpfad("dotnet-stryker")
def test_dotnet_stryker_wiederholtes_mutate_flag_verliert_kein_muster(
        tmp_path, monkeypatch, stryker_lauf, capsys):
    modul = _stryker_modul("dotnet-stryker", tmp_path, monkeypatch)
    monkeypatch.setattr(modul, "_snapshot_run_dirs", lambda: set())
    monkeypatch.setattr(modul, "_move_new_run", lambda _vorher: None)
    cli_aufruf(monkeypatch, modul, "--mutate", "Domain/A.cs", "--mutate", "Domain/B.cs")
    assert stryker_lauf[0] == ["dotnet", "stryker", "--mutate", "Domain/A.cs",
                               "--mutate", "Domain/B.cs"]


@pytest.mark.aufrufpfad("dotnet-stryker")
def test_dotnet_stryker_uebergibt_mutate_je_datei_als_eigenes_flag(
        tmp_path, monkeypatch, stryker_lauf, capsys):
    modul = _stryker_modul("dotnet-stryker", tmp_path, monkeypatch)
    monkeypatch.setattr(modul, "_snapshot_run_dirs", lambda: set())
    monkeypatch.setattr(modul, "_move_new_run", lambda _vorher: None)
    code = cli_aufruf(monkeypatch, modul, "--mutate", "Domain/A.cs,Domain/B.cs")
    assert stryker_lauf[0] == ["dotnet", "stryker", "--mutate", "Domain/A.cs",
                               "--mutate", "Domain/B.cs"]
    assert code == 1
    assert "keinen neuen Report" in capsys.readouterr().err


# --- dotnet-test --------------------------------------------------------------------
@pytest.mark.aufrufpfad("dotnet-test")
def test_dotnet_test_filter_wird_zur_filter_method_und_laesst_coverage_weg(monkeypatch):
    modul = import_module("prozesscode.dotnet-test")
    aufrufe = []
    monkeypatch.setattr(modul, "run_dotnet",
                        lambda argumente: aufrufe.append(argumente) or ("Passed!\n", 0))
    assert cli_aufruf(monkeypatch, modul, "--filter", "IngredientName") == 0
    argumente = aufrufe[0]
    assert argumente[argumente.index("--filter-method") + 1] == "*IngredientName*"
    assert not any("coverage" in a for a in argumente)  # gefilterter Lauf deckt nicht alles ab


# --- Gates --------------------------------------------------------------------------
@pytest.mark.aufrufpfad("qa-check")
def test_qa_check_weist_freigabe_ohne_sha_ab_bevor_etwas_laeuft(monkeypatch, capsys):
    code = cli_aufruf(monkeypatch, import_module("prozesscode.qa-check"),
                "--layer", "backend", "--verify", "x", "--approved-tests", "Server.Tests/A.cs")
    assert code == 2
    assert "pfad=sha" in capsys.readouterr().err


@pytest.mark.aufrufpfad("check-atdd-gate")
def test_atdd_gate_findet_den_lauf_ueber_story_tag_und_run(monkeypatch, capsys):
    """Gegen die echten features/ – der dokumentierte Aufruf aus implementing-scenario."""
    code = cli_aufruf(monkeypatch, import_module("prozesscode.check-atdd-gate"), "@US-904", "run-1")
    assert code == 0
    assert "run-1" in capsys.readouterr().out


def test_atdd_gate_titelfilter_grenzt_auf_das_eine_szenario_ein(monkeypatch, capsys):
    """Mutationssichtung S133: `_tag_mode(tag, None)` überlebte – der Titel hätte still nichts
    gefiltert, und das Gate hätte alle Szenarien des Tags geprüft statt des gemeinten."""
    code = cli_aufruf(monkeypatch, import_module("prozesscode.check-atdd-gate"),
                      "@US-904-happy-path", "Felder sind beim Öffnen des Dialogs leer")
    ausgabe = capsys.readouterr().out
    assert code == 0
    assert "Felder sind beim Öffnen des Dialogs leer" in ausgabe
    assert "Zutaten-Liste ist leer" not in ausgabe  # trägt denselben Tag


def test_atdd_gate_ergaenzt_das_fehlende_at_zeichen(monkeypatch, capsys):
    code = cli_aufruf(monkeypatch, import_module("prozesscode.check-atdd-gate"), "US-904", "run-1")
    assert code == 0
    assert "run-1" in capsys.readouterr().out


def test_atdd_gate_meldet_unbekannten_tag(monkeypatch, capsys):
    code = cli_aufruf(monkeypatch, import_module("prozesscode.check-atdd-gate"), "@US-999")
    assert code == 1
    assert "@US-999" in capsys.readouterr().out

"""Aufrufpfad der Test-Wrapper und Gates: Argumente → `main()` → Aufruf des fremden Werkzeugs.

Die Wrapper sind für die Entwicklung entscheidend und liefen bis S133 in keinem Test über ihre
Kommandozeile (User-Vorgabe S133: keine Ausnahme für sie). Das fremde Werkzeug wird ersetzt;
geprüft wird, WIE es aufgerufen würde – dort gehen Argumente still verloren – und welches
Verdikt aus einer Ausgabe in echter Form entsteht.
"""
import subprocess
from importlib import import_module

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


def test_vitest_roter_lauf_nennt_die_zahl_und_bleibt_rot(monkeypatch, capsys):
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, "      Tests  2 failed | 5 passed (7)\n", 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert "✗ 2 Test(s) rot" in capsys.readouterr().out


def test_vitest_filter_ohne_treffer_ist_ein_fehler_statt_gruen(monkeypatch, capsys):
    """Fail-closed-Guard: vitest -t überspringt Nicht-Treffer und läuft sonst grün durch.
    Bis S133 hielt kein Test diese Stelle (mutmut: `exit_code or 1` überlebte)."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, "      Tests  7 skipped (7)\n", 0)
    assert cli_aufruf(monkeypatch, modul, "--filter", "Tippfehler") == 1
    assert "0 Tests gematcht" in capsys.readouterr().err


def test_vitest_absturz_ohne_rote_tests_meldet_kein_gruen(monkeypatch, capsys):
    """Mutationssichtung S133: `exit_code == 0 or …` überlebte – ein Abbruch mit „0 failed" in
    der Zusammenfassung (etwa beim Einsammeln) hätte „✓ grün" gemeldet, bei rotem Exit-Code."""
    modul = import_module("prozesscode.vitest-run")
    _fake_npm(monkeypatch, modul, "      Tests  5 passed (5)\nError: Unhandled rejection\n", 1)
    assert cli_aufruf(monkeypatch, modul) == 1
    assert "✓" not in capsys.readouterr().out


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


@pytest.mark.aufrufpfad("test-stryker-guards")
def test_stryker_guard_suite_ist_gruen(capsys):
    """Die Suite bringt einen eigenen Runner mit und heißt mit Bindestrich – pytest sammelt sie
    nicht. Über `main()` läuft sie jetzt im Werkzeug-Gate mit (wie der Bash-Permission-Runner)."""
    import_module("prozesscode.test-stryker-guards").main()
    assert "Alle Tests bestanden" in capsys.readouterr().out

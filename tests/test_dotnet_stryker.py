"""Tests für dotnet-stryker.py – den Wrapper um Stryker.NET.

Gate-relevant ist der Exit-Code: rot, sobald Stryker oder die Auswertung (stryker-summary) rot
ist, und auch dann, wenn Stryker gar keinen Report hinterlässt. Die Stryker-Ausgabe ist echt
und gespeichert (`fixtures/dotnet_stryker_out.txt`, Stryker.NET 5.0.0, grüner Lauf); ersetzt
sind nur die beiden Prozesse und die Verzeichnisse.
"""
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest

from conftest import cli_aufruf

ds = import_module("prozesscode.dotnet-stryker")

_STRYKER_AUSGABE = (Path(__file__).parent / "fixtures" / "dotnet_stryker_out.txt").read_bytes()
# Schlusszeile eines Laufs unter der Break-Schwelle, wörtlich aus einer echten Wrapper-Ausgabe.
_BREAK_ZEILE = b"[08:41:50 WRN] Final mutation score is below threshold break. Crashing...\n"
_PREVIEW_ZEILE = ("[08:40:40 WRN] The Microsoft Test Platform testrunner is currently in preview. "
                  "Results should be verified since this feature is still being tested.")
_LAUF = "2026-11-05.08-40-27"
_FRUEHERER_LAUF = "2026-10-29.15-57-55"


class StrykerAttrappe:
    """Ersetzt beide Prozesse. `dotnet stryker` schreibt die echte Ausgabe über den
    Dateideskriptor in die übergebene Datei – wie der echte Prozess – und legt wie Stryker.NET
    einen Zeitstempel-Ordner mit Report unter StrykerOutput/ an. `stryker-summary` liefert
    nur seinen Exit-Code."""

    def __init__(self, wurzel: Path):
        self.wurzel = wurzel
        self.aufrufe: list[tuple[list[str], dict]] = []
        self.ausgabe = _STRYKER_AUSGABE
        self.stryker_exit = 0
        self.summary_exit = 0
        self.legt_report_an = True

    def __call__(self, argumente, **kw):
        self.aufrufe.append((list(argumente), kw))
        if argumente[:2] != ["dotnet", "stryker"]:
            return subprocess.CompletedProcess(argumente, self.summary_exit)
        os.write(kw["stdout"].fileno(), self.ausgabe)
        if self.legt_report_an:
            reports = self.wurzel / "StrykerOutput" / _LAUF / "reports"
            reports.mkdir(parents=True)
            (reports / "mutation-report.json").write_text("{}", encoding="utf-8")
        return subprocess.CompletedProcess(argumente, self.stryker_exit)


@pytest.fixture
def stryker(tmp_path, monkeypatch) -> StrykerAttrappe:
    """Repo-Wurzel im tmp_path mit dem Bestand eines Repos nach früheren Läufen: Backend/ mit
    einem alten Lauf, Frontend/. `.claude/tmp/` fehlt noch – der Wrapper legt es an."""
    wurzel = tmp_path / "repo"
    monkeypatch.setattr(ds, "_REPO_ROOT", wurzel)
    monkeypatch.setattr(ds, "_TMP_FILE", wurzel / ".claude" / "tmp" / "stryker_out.txt")
    monkeypatch.setattr(ds, "_STRYKER_OUT", wurzel / "StrykerOutput")
    monkeypatch.setattr(ds, "_BACKEND_OUT", wurzel / "StrykerOutput" / "Backend")
    monkeypatch.setattr(ds, "_PROJECT_DIR", wurzel / "Server")
    (wurzel / "StrykerOutput" / "Backend" / _FRUEHERER_LAUF / "reports").mkdir(parents=True)
    (wurzel / "StrykerOutput" / "Frontend").mkdir()
    attrappe = StrykerAttrappe(wurzel)
    monkeypatch.setattr(subprocess, "run", attrappe)
    return attrappe


def _kopf(stryker: StrykerAttrappe, befehl: str = "dotnet stryker") -> str:
    tmp_datei = stryker.wurzel / ".claude" / "tmp" / "stryker_out.txt"
    return f"Starte: {befehl}\nLive-Output (Fortschritt während des Laufs) → {tmp_datei}\n"


def _ablage(stryker: StrykerAttrappe) -> str:
    return f"\nReport verschoben → {stryker.wurzel / 'StrykerOutput' / 'Backend' / _LAUF}\n"


@pytest.mark.aufrufpfad("dotnet-stryker")
def test_gruener_lauf_zeigt_nur_start_und_ablage_und_verschiebt_den_report(
        stryker, monkeypatch, capsys):
    """Bei Erfolg trägt die Rohausgabe nichts bei, was die Auswertung nicht besser sagt."""
    code = cli_aufruf(monkeypatch, ds)

    ausgabe = capsys.readouterr()
    assert code == 0
    assert ausgabe.out == _kopf(stryker) + _ablage(stryker)
    assert ausgabe.err == ""
    ablage = stryker.wurzel / "StrykerOutput"
    assert (ablage / "Backend" / _LAUF / "reports" / "mutation-report.json").is_file()
    assert not (ablage / _LAUF).exists()
    assert (ablage / "Backend" / _FRUEHERER_LAUF).is_dir()


def test_stryker_laeuft_im_repo_root_und_schreibt_stdout_und_stderr_in_die_live_datei(
        stryker, monkeypatch):
    cli_aufruf(monkeypatch, ds)

    argumente, kw = stryker.aufrufe[0]
    assert argumente == ["dotnet", "stryker"]
    assert kw["cwd"] == str(stryker.wurzel)
    assert kw["stderr"] is subprocess.STDOUT
    live = stryker.wurzel / ".claude" / "tmp" / "stryker_out.txt"
    assert live.read_bytes() == _STRYKER_AUSGABE  # bleibt zum Nachlesen liegen


def test_auswertung_laeuft_als_modul_im_repo_root(stryker, monkeypatch):
    """`-m` statt Dateipfad: stryker-summary nutzt paketinterne Importe."""
    cli_aufruf(monkeypatch, ds)

    argumente, kw = stryker.aufrufe[1]
    assert argumente == [sys.executable, "-m", "prozesscode.stryker-summary"]
    assert kw["cwd"] == str(stryker.wurzel)


@pytest.mark.parametrize(("stryker_exit", "summary_exit", "erwartet"), [
    (0, 0, 0),
    (0, 1, 1),   # Auswertung rot → rot
    (0, 2, 2),   # der Exit-Code der Auswertung wird durchgereicht
    (1, 0, 1),   # Stryker rot, Auswertung grün: bei Abweichung gewinnt das Fail
    (1, 1, 1),
])
def test_exit_code_ist_rot_sobald_stryker_oder_auswertung_rot_ist(
        stryker, monkeypatch, stryker_exit, summary_exit, erwartet):
    stryker.stryker_exit = stryker_exit
    stryker.summary_exit = summary_exit

    assert cli_aufruf(monkeypatch, ds) == erwartet


def test_lauf_unter_der_schwelle_zeigt_die_warnzeilen_der_rohausgabe(stryker, monkeypatch, capsys):
    """Gegenstück zur echten Wrapper-Ausgabe eines Laufs unter der Break-Schwelle: zwischen Start
    und Ablage genau die beiden WRN-Zeilen, nicht die Tabelle."""
    stryker.ausgabe = _STRYKER_AUSGABE + _BREAK_ZEILE
    stryker.stryker_exit = 1
    stryker.summary_exit = 1

    code = cli_aufruf(monkeypatch, ds)

    erwartet = _kopf(stryker) + _PREVIEW_ZEILE + "\n" + _BREAK_ZEILE.decode() + _ablage(stryker)
    assert code == 1
    assert capsys.readouterr().out == erwartet


def test_verbose_zeigt_die_ganze_rohausgabe_und_reicht_verbose_an_die_auswertung(
        stryker, monkeypatch, capsys):
    code = cli_aufruf(monkeypatch, ds, "--verbose")

    assert code == 0
    assert capsys.readouterr().out == _kopf(stryker) + _STRYKER_AUSGABE.decode() + _ablage(stryker)
    assert stryker.aufrufe[1][0] == [sys.executable, "-m", "prozesscode.stryker-summary", "--verbose"]


def test_kaputtes_utf8_in_der_rohausgabe_bricht_den_wrapper_nicht_ab(stryker, monkeypatch, capsys):
    """Konstruiert: eine Tabellenzeile, abgeschnitten mitten in einem UTF-8-Zeichen. Fail-open –
    die Diagnose darf an einem Kodierungsfehler nicht scheitern."""
    abgeschnitten = _STRYKER_AUSGABE.replace("─╯".encode(), b"\xe2\x94")
    stryker.ausgabe = abgeschnitten + _BREAK_ZEILE
    stryker.stryker_exit = 1

    code = cli_aufruf(monkeypatch, ds)

    assert code == 1
    assert _BREAK_ZEILE.decode() in capsys.readouterr().out


def test_ohne_neuen_report_ist_es_ein_lauffehler_auch_bei_exit_null(stryker, monkeypatch, capsys):
    """Stryker.NET schreibt den Report vor dem Schwellen-Check; fehlt er, lief Stryker nicht
    durch – egal, was sein Exit-Code sagt. Die Auswertung startet dann gar nicht erst."""
    stryker.legt_report_an = False

    code = cli_aufruf(monkeypatch, ds)

    assert code == 1
    assert capsys.readouterr().err == (
        "\nStryker hat keinen neuen Report erzeugt (Exit 0) – Lauf-Fehler.\n")
    assert len(stryker.aufrufe) == 1


def test_ohne_neuen_report_bleibt_der_exit_code_von_stryker(stryker, monkeypatch):
    stryker.legt_report_an = False
    stryker.stryker_exit = 3

    assert cli_aufruf(monkeypatch, ds) == 3


def test_erster_lauf_ohne_strykeroutput_ordner(stryker, monkeypatch, tmp_path):
    """Frischer Klon: StrykerOutput/ legt erst Stryker selbst an."""
    for pfad in sorted((stryker.wurzel / "StrykerOutput").rglob("*"), reverse=True):
        pfad.rmdir()
    (stryker.wurzel / "StrykerOutput").rmdir()

    code = cli_aufruf(monkeypatch, ds)

    assert code == 0
    assert (stryker.wurzel / "StrykerOutput" / "Backend" / _LAUF / "reports").is_dir()


def test_konkurrierender_lauf_blockiert_bevor_stryker_startet(stryker, monkeypatch):
    """Zwei Läufe schrieben in dieselbe Live-Datei. Der Lock hängt an genau dieser Datei."""
    lock = stryker.wurzel / ".claude" / "tmp" / "stryker_out.txt.lock"
    lock.parent.mkdir(parents=True)
    # PID 1 (init): lebt und gehört einem anderen User. Nicht `os.getppid()` – mutiert mutmut
    # `os.kill(pid, 0)` zu `os.kill(pid, 1)`, ginge SIGHUP an den Elternprozess, unter mutmut
    # also an mutmut selbst, und der Lauf bräche ab.
    lock.write_text("1", encoding="utf-8")

    assert cli_aufruf(monkeypatch, ds) == 99
    assert stryker.aufrufe == []


def test_mutate_wird_gegen_server_geprueft_und_weitergereicht(stryker, monkeypatch):
    (stryker.wurzel / "Server" / "Domain").mkdir(parents=True)
    (stryker.wurzel / "Server" / "Domain" / "Foo.cs").write_text("", encoding="utf-8")

    cli_aufruf(monkeypatch, ds, "--mutate", "Domain/Foo.cs")

    assert stryker.aufrufe[0][0] == ["dotnet", "stryker", "--mutate", "Domain/Foo.cs"]


def test_repo_root_relatives_mutate_bricht_vor_dem_lauf_mit_vorschlag_ab(
        stryker, monkeypatch, capsys):
    """Stryker wertet projekt-relativ aus; der Vorschlag braucht beide Basen."""
    (stryker.wurzel / "Server" / "Domain").mkdir(parents=True)
    (stryker.wurzel / "Server" / "Domain" / "Foo.cs").write_text("", encoding="utf-8")

    code = cli_aufruf(monkeypatch, ds, "--mutate", "Server/Domain/Foo.cs")

    assert code == 2
    assert "`Domain/Foo.cs`" in capsys.readouterr().err
    assert stryker.aufrufe == []


def test_snapshot_kennt_nur_laufordner(stryker):
    """Backend/ und Frontend/ sind Ablagen, Dateien keine Läufe."""
    ablage = stryker.wurzel / "StrykerOutput"
    (ablage / _LAUF).mkdir()
    (ablage / "notiz.txt").write_text("", encoding="utf-8")

    assert ds._snapshot_run_dirs() == {ablage / _LAUF}

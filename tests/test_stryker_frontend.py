"""Tests für stryker-frontend.py: Lauf, Report-Übernahme, Auswertung und Exit-Code.

Der Stryker-Prozess und die Auswertung durch stryker-summary werden ersetzt; alles andere läuft
echt – `resolve_mutate` gegen ein Client/-Verzeichnis unter `tmp_path`, Lock, Pre-Clean, Kopie.
Die Live-Ausgabe, die der Ersatz-Prozess schreibt, ist die eines echten StrykerJS-Laufs
(`fixtures/stryker_frontend_lauf_gruen.txt`, aus `.claude/tmp/stryker_frontend_out.txt`).
"""
import subprocess
import sys
from datetime import datetime
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import cli_aufruf

modul = import_module("prozesscode.stryker-frontend")

_ECHTE_AUSGABE = (Path(__file__).parent / "fixtures" / "stryker_frontend_lauf_gruen.txt").read_bytes()
_ZEITSTEMPEL = "2026-11-05.09-39-27"


class _FesteZeit(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 5, 9, 39, 27)


@pytest.fixture
def umgebung(tmp_path, monkeypatch):
    """Repo im Kleinen; `.claude/tmp/` fehlt bewusst, der Wrapper legt sie an."""
    repo = tmp_path / "repo"
    client = repo / "Client"
    for datei in ("src/pages/IngredientsPage.tsx", "src/services/ingredientsApi.ts"):
        (client / datei).parent.mkdir(parents=True, exist_ok=True)
        (client / datei).write_text("", encoding="utf-8")
    pfade = SimpleNamespace(
        repo=repo,
        client=client,
        tmp_file=repo / ".claude" / "tmp" / "stryker_frontend_out.txt",
        sandbox=client / ".stryker-tmp",
        reports=client / "reports" / "mutation",
        ziel=repo / "StrykerOutput" / "Frontend" / _ZEITSTEMPEL / "reports",
    )
    monkeypatch.setattr(modul, "_REPO_ROOT", repo)
    monkeypatch.setattr(modul, "_CLIENT_DIR", client)
    monkeypatch.setattr(modul, "_TMP_FILE", pfade.tmp_file)
    monkeypatch.setattr(modul, "_STRYKER_TMP", pfade.sandbox)
    monkeypatch.setattr(modul, "_STRYKER_SRC", pfade.reports)
    monkeypatch.setattr(modul, "_OUTPUT_BASE", repo / "StrykerOutput" / "Frontend")
    monkeypatch.setattr(modul, "datetime", _FesteZeit)
    return pfade


class _Prozesse:
    """Ersetzt `subprocess.run`: erst Stryker, dann stryker-summary.

    Der Stryker-Ersatz tut, was StrykerJS tut: Er schreibt seine Ausgabe in den übergebenen
    Deskriptor und legt `mutation.json`/`mutation.html` ab – vor dem Threshold-Check, also auch
    bei Exit ≠ 0. Festgehalten wird, was während des Laufs galt (Lock, Sandbox).
    """

    def __init__(self, pfade, *, stryker_exit=0, summary_exit=0, ausgabe=_ECHTE_AUSGABE,
                 report=True):
        self.pfade = pfade
        self.stryker_exit, self.summary_exit = stryker_exit, summary_exit
        self.ausgabe, self.report = ausgabe, report
        self.aufrufe: list[tuple[list[str], dict]] = []
        self.lock_im_lauf = self.sandbox_im_lauf = None

    def __call__(self, argumente, **kw):
        self.aufrufe.append((list(argumente), kw))
        if argumente[0] != "npx":
            return subprocess.CompletedProcess(argumente, self.summary_exit)
        self.lock_im_lauf = Path(f"{self.pfade.tmp_file}.lock").exists()
        self.sandbox_im_lauf = self.pfade.sandbox.exists()
        kw["stdout"].write(self.ausgabe)
        if self.report:
            self.pfade.reports.mkdir(parents=True, exist_ok=True)
            (self.pfade.reports / "mutation.json").write_text('{"files": {}}', encoding="utf-8")
            (self.pfade.reports / "mutation.html").write_text("<html/>", encoding="utf-8")
        return subprocess.CompletedProcess(argumente, self.stryker_exit)


def _ersetze_prozesse(monkeypatch, pfade, **prozess) -> _Prozesse:
    prozesse = _Prozesse(pfade, **prozess)
    monkeypatch.setattr(subprocess, "run", prozesse)
    return prozesse


def _lauf(monkeypatch, pfade, *argumente, **prozess):
    """Kurzform für Tests ohne `aufrufpfad`-Marker – der Meta-Test folgt nur einer Ebene
    Hilfsfunktion, markierte Tests rufen `cli_aufruf` darum selbst."""
    prozesse = _ersetze_prozesse(monkeypatch, pfade, **prozess)
    return cli_aufruf(monkeypatch, modul, *argumente), prozesse


def _kopf(pfade, stryker_aufruf="npx stryker run"):
    return (f"Starte: {stryker_aufruf}\n"
            f"Live-Output (Fortschritt während des Laufs) → {pfade.tmp_file}\n")


def _fuss(pfade):
    return f"\nReport kopiert → {pfade.ziel.parent}\n"


# --- grüner Lauf ----------------------------------------------------------------------------
@pytest.mark.aufrufpfad("stryker-frontend")
def test_gruener_lauf_zeigt_nur_start_und_ablage_und_endet_mit_null(monkeypatch, capsys, umgebung):
    """Bei Erfolg trägt die Rohausgabe nichts bei, was die Auswertung nicht besser sagt."""
    prozesse = _ersetze_prozesse(monkeypatch, umgebung)
    code = cli_aufruf(monkeypatch, modul)
    ausgabe = capsys.readouterr()
    assert ausgabe.out == _kopf(umgebung) + _fuss(umgebung)
    assert ausgabe.err == ""
    assert code == 0
    stryker, summary = prozesse.aufrufe
    assert stryker == (["npx", "stryker", "run"],
                       {"cwd": str(umgebung.client), "stdout": stryker[1]["stdout"],
                        "stderr": subprocess.STDOUT})
    assert summary == ([sys.executable, "-m", "prozesscode.stryker-summary",
                        str(umgebung.ziel / "mutation-report.json")],
                       {"cwd": str(umgebung.repo)})


def test_live_ausgabe_landet_vollstaendig_in_der_datei(monkeypatch, umgebung):
    """Die Datei ist der einzige Weg, einen laufenden Lauf zu beobachten – sie bleibt liegen."""
    _lauf(monkeypatch, umgebung)
    assert umgebung.tmp_file.read_bytes() == _ECHTE_AUSGABE


def test_lauf_haelt_den_lock_und_raeumt_liegengebliebene_sandboxes_vorher_weg(monkeypatch, umgebung):
    (umgebung.sandbox / "sandbox-4711").mkdir(parents=True)
    (umgebung.sandbox / "sandbox-4711" / "package.json").write_text("{}", encoding="utf-8")
    _, prozesse = _lauf(monkeypatch, umgebung)
    assert prozesse.lock_im_lauf is True
    assert prozesse.sandbox_im_lauf is False
    assert not Path(f"{umgebung.tmp_file}.lock").exists()


def test_reports_werden_umbenannt_in_den_zeitstempel_ordner_kopiert(monkeypatch, umgebung):
    _lauf(monkeypatch, umgebung)
    assert sorted(p.name for p in umgebung.ziel.iterdir()) == ["mutation-report.html",
                                                              "mutation-report.json"]
    assert (umgebung.ziel / "mutation-report.json").read_text(encoding="utf-8") == '{"files": {}}'
    assert (umgebung.ziel / "mutation-report.html").read_text(encoding="utf-8") == "<html/>"


def test_weitere_dateien_im_report_ordner_kommen_unter_eigenem_namen_mit(monkeypatch, umgebung):
    umgebung.reports.mkdir(parents=True)
    (umgebung.reports / "mutation.js").write_text("x", encoding="utf-8")
    _lauf(monkeypatch, umgebung)
    assert (umgebung.ziel / "mutation.js").read_text(encoding="utf-8") == "x"


def test_vorhandener_zielordner_wird_ueberschrieben_statt_abzubrechen(monkeypatch, umgebung):
    umgebung.ziel.mkdir(parents=True)
    code, _ = _lauf(monkeypatch, umgebung)
    assert code == 0
    assert (umgebung.ziel / "mutation-report.json").exists()


@pytest.mark.aufrufpfad("stryker-frontend")
def test_mutate_wird_gegen_client_geprueft_und_weitergereicht(monkeypatch, capsys, umgebung):
    prozesse = _ersetze_prozesse(monkeypatch, umgebung)
    code = cli_aufruf(monkeypatch, modul, "--mutate", "src/pages/IngredientsPage.tsx")
    assert prozesse.aufrufe[0][0] == ["npx", "stryker", "run", "--mutate",
                                      "src/pages/IngredientsPage.tsx"]
    assert capsys.readouterr().out.startswith(
        _kopf(umgebung, "npx stryker run --mutate src/pages/IngredientsPage.tsx"))
    assert code == 0


@pytest.mark.aufrufpfad("stryker-frontend")
def test_repo_root_relatives_mutate_bricht_vor_dem_lauf_mit_vorschlag_ab(monkeypatch, capsys, umgebung):
    prozesse = _ersetze_prozesse(monkeypatch, umgebung)
    code = cli_aufruf(monkeypatch, modul, "--mutate", "Client/src/pages/IngredientsPage.tsx")
    assert code == 2
    assert prozesse.aufrufe == []
    assert "Meintest du `src/pages/IngredientsPage.tsx`?" in capsys.readouterr().err


# --- roter Lauf, --verbose ------------------------------------------------------------------
@pytest.mark.aufrufpfad("stryker-frontend")
def test_roter_lauf_zeigt_den_schluss_der_rohausgabe(monkeypatch, capsys, umgebung):
    """Die echte Ausgabe trägt kein Fehlersignal – dann zeigt der Wrapper ihren Schluss
    (fail-open), nicht nichts."""
    _ersetze_prozesse(monkeypatch, umgebung, stryker_exit=1, summary_exit=1)
    code = cli_aufruf(monkeypatch, modul)
    zeilen = _ECHTE_AUSGABE.decode("utf-8").splitlines()
    assert capsys.readouterr().out == (_kopf(umgebung) + "\n".join(zeilen[-30:]) + "\n"
                                       + _fuss(umgebung))
    assert code == 1


def test_abgeschnittene_rohausgabe_wird_ersetzt_statt_abzubrechen(monkeypatch, capsys, umgebung):
    """Ein abgebrochener Lauf kann mitten in einem Mehrbyte-Zeichen enden (hier: ein halbes ✓)."""
    code, _ = _lauf(monkeypatch, umgebung, stryker_exit=1, summary_exit=1,
                    ausgabe=b"Mutation testing 6% \xe2\x9c")
    assert capsys.readouterr().out == (_kopf(umgebung) + "Mutation testing 6% �\n"
                                       + _fuss(umgebung))
    assert code == 1


@pytest.mark.aufrufpfad("stryker-frontend")
def test_verbose_zeigt_die_ganze_rohausgabe_und_reicht_verbose_an_die_auswertung(
        monkeypatch, capsys, umgebung):
    prozesse = _ersetze_prozesse(monkeypatch, umgebung)
    code = cli_aufruf(monkeypatch, modul, "--verbose")
    assert capsys.readouterr().out == (_kopf(umgebung) + _ECHTE_AUSGABE.decode("utf-8").rstrip("\n")
                                       + "\n" + _fuss(umgebung))
    assert prozesse.aufrufe[1][0][-1] == "--verbose"
    assert code == 0


@pytest.mark.parametrize("stryker_exit, summary_exit, erwartet", [
    (0, 0, 0),
    (0, 1, 1),  # stryker-summary ist das maßgebliche Gate
    (1, 0, 1),  # Stryker unter seinem Threshold: bei Abweichung gewinnt das Fail
    (1, 1, 1),
])
def test_exit_code_folgt_dem_strengeren_der_beiden_gates(
        monkeypatch, umgebung, stryker_exit, summary_exit, erwartet):
    code, _ = _lauf(monkeypatch, umgebung, stryker_exit=stryker_exit, summary_exit=summary_exit)
    assert code == erwartet


# --- kein Report: Lauf-Fehler ---------------------------------------------------------------
@pytest.mark.parametrize("stryker_exit, ordner_da, erwartet", [
    (1, False, 1),
    (2, False, 2),  # der Exit-Code des Laufs bleibt erhalten
    (0, True, 1),  # leerer Ordner, Exit 0: trotzdem ein Fehler
])
def test_ohne_report_bricht_der_lauf_vor_der_auswertung_ab(
        monkeypatch, capsys, umgebung, stryker_exit, ordner_da, erwartet):
    if ordner_da:
        umgebung.reports.mkdir(parents=True)
    code, prozesse = _lauf(monkeypatch, umgebung, stryker_exit=stryker_exit, report=False)
    assert code == erwartet
    assert len(prozesse.aufrufe) == 1  # stryker-summary läuft nicht
    assert capsys.readouterr().err == (
        f"\nStryker hat keinen Report erzeugt (Exit {stryker_exit}) – Lauf-Fehler.\n")

"""Aufrufpfad der schreibenden und auswertenden Werkzeuge: Argumente → `main()` → Wirkung.

Schreibende Werkzeuge laufen gegen Dateien in `tmp_path` – nie gegen die echten Tracker.
Hintergrund und Maßgabe: tests/test_aufrufpfad.py, CGP-echtes-artefakt.
"""
import json
from importlib import import_module

import pytest

from conftest import cli_aufruf
from prozesscode import obs_entry


def _obs_eintrag(oid: str, status: str = "NEU") -> str:
    text = obs_entry.format_entry(
        oid, titel="Probe", quelle="User", impact="MITTEL", haeufigkeit="häufig",
        kategorie="PROZESS", kontext="Doku", beobachtung="Etwas fiel auf.", bezug=None,
        zusammen="keiner", aufschubgrund="Umfang – eigener Umbau")
    return text.replace("- Status: NEU", f"- Status: {status}")


# --- lessons ------------------------------------------------------------------------
LL_ARGUMENTE = ["add", "--titel", "Probe", "--impact", "MITTEL", "--kategorie", "PROZESS",
                "--kontext", "Doku", "--was", "W.", "--warum", "U.", "--regel", "R.",
                "--session", "999"]


@pytest.fixture
def ll_datei(tmp_path, monkeypatch):
    datei = tmp_path / "lessons_learned.md"
    datei.write_text("# Lessons Learned\n\n---\n", encoding="utf-8")
    monkeypatch.setattr(import_module("prozesscode.lessons"), "ll_path", lambda: datei)
    return datei


@pytest.mark.aufrufpfad("lessons")
def test_lessons_add_schreibt_den_eintrag_mit_allen_argumenten(ll_datei, monkeypatch):
    code = cli_aufruf(monkeypatch, import_module("prozesscode.lessons"),
                *LL_ARGUMENTE, "--quelle", "Orchestrator")
    inhalt = ll_datei.read_text(encoding="utf-8")
    assert code == 0
    assert "LL-S999-1 – Probe" in inhalt and "Quelle: Orchestrator" in inhalt


def test_lessons_get_liefert_den_eintrag_und_meldet_fehlende(ll_datei, monkeypatch, capsys):
    """Mutationssichtung S133: `set_defaults(func=cmd_get)` → None überlebte – der ganze
    `get`-Unterbefehl lief über keinen Test."""
    modul = import_module("prozesscode.lessons")
    cli_aufruf(monkeypatch, modul, *LL_ARGUMENTE, "--quelle", "Orchestrator")
    capsys.readouterr()
    code = cli_aufruf(monkeypatch, modul, "get", "LL-S999-1", "LL-S999-9")
    ausgabe = capsys.readouterr()
    assert "LL-S999-1 – Probe" in ausgabe.out
    assert "LL-S999-9" in ausgabe.err
    assert code == 1


def test_lessons_add_weist_eine_unbekannte_quelle_ab(ll_datei, monkeypatch, capsys):
    """D1 (S133) über den echten Weg: `--quelle Agent` darf nicht mehr durchkommen."""
    code = cli_aufruf(monkeypatch, import_module("prozesscode.lessons"), *LL_ARGUMENTE, "--quelle", "Agent")
    assert code == 1
    assert "Quelle" in capsys.readouterr().err
    assert "LL-S999" not in ll_datei.read_text(encoding="utf-8")


# --- obs-archive / obs-drain --------------------------------------------------------
@pytest.mark.aufrufpfad("obs-archive")
def test_obs_archive_dry_run_nennt_den_aufgeloesten_eintrag_und_schreibt_nichts(
        tmp_path, monkeypatch, capsys):
    obs = tmp_path / "observations.md"
    obs.write_text("# Beobachtungen\n\n" + _obs_eintrag("OBS-S100-1", "UMGESETZT (S101)")
                   + "\n" + _obs_eintrag("OBS-S100-2"), encoding="utf-8")
    archiv = tmp_path / "archiv.md"
    archiv.write_text("# Archiv\n", encoding="utf-8")
    vorher = obs.read_text(encoding="utf-8")
    code = cli_aufruf(monkeypatch, import_module("prozesscode.obs-archive"),
                "--file", str(obs), "--archive", str(archiv), "--dry-run")
    ausgabe = capsys.readouterr().out
    assert code == 0
    assert "OBS-S100-1" in ausgabe and "OBS-S100-2" not in ausgabe
    assert obs.read_text(encoding="utf-8") == vorher


@pytest.mark.aufrufpfad("obs-drain")
def test_obs_drain_liest_die_uebergebene_datei(tmp_path, capsys):
    obs = tmp_path / "observations.md"
    obs.write_text("# Beobachtungen\n\n" + _obs_eintrag("OBS-S100-1"), encoding="utf-8")
    code = import_module("prozesscode.obs-drain").main(["--file", str(obs)])
    assert code == 0
    assert "OBS-Drain" in capsys.readouterr().out


def test_obs_drain_meldet_fehlende_datei_statt_leer_zu_bleiben(tmp_path, capsys):
    code = import_module("prozesscode.obs-drain").main(["--file", str(tmp_path / "fehlt.md")])
    assert code == 1
    assert "nicht gefunden" in capsys.readouterr().err


# --- next_run -----------------------------------------------------------------------
@pytest.mark.aufrufpfad("next_run")
def test_next_run_check_prueft_das_echte_mapping(capsys):
    assert import_module("prozesscode.next_run").main(["--check"]) == 0
    assert "konsistent" in capsys.readouterr().out


# --- read-breakdown -----------------------------------------------------------------
@pytest.mark.aufrufpfad("read-breakdown")
def test_read_breakdown_since_ohne_sessions_meldet_sich(tmp_path, monkeypatch, capsys):
    modul = import_module("prozesscode.read-breakdown")
    monkeypatch.setattr(modul, "project_log_dir", lambda: tmp_path)
    code = cli_aufruf(monkeypatch, modul, "--since", "2999-01-01")
    assert code == 1
    assert "2999-01-01" in capsys.readouterr().err


# --- stryker-summary ----------------------------------------------------------------
@pytest.mark.aufrufpfad("stryker-summary")
def test_stryker_summary_liest_den_uebergebenen_report(tmp_path, monkeypatch, capsys):
    ort = {"start": {"line": 7, "column": 1}, "end": {"line": 7, "column": 5}}
    report = tmp_path / "lauf" / "reports" / "mutation-report.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"files": {"Server/Domain/A.cs": {"mutants": [
        {"id": "1", "status": "Killed", "mutatorName": "x", "location": ort},
        {"id": "2", "status": "Survived", "mutatorName": "Equality", "replacement": "!=",
         "location": ort}]}}}), encoding="utf-8")
    code = cli_aufruf(monkeypatch, import_module("prozesscode.stryker-summary"), str(report))
    ausgabe = capsys.readouterr().out
    assert code == 1  # ein Survivor ist kein bestandener Lauf
    assert "Score: 50.0%" in ausgabe and "Equality" in ausgabe

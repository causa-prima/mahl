"""Tests für read-breakdown.py – Messung je Agententyp und je Anker.

Warum je Agent (OBS-S109-1, OBS-S114-2): Die Session-Art ist eine grobe Einheit geworden.
Sessions sind gemischt und enthalten 1–3 Läufe; ein Wert „je Implementierungs-Session" hängt
damit an der Zahl der Läufe darin. Ein Subagenten-Aufruf hat genau einen Typ, und ein
Implementer-Aufruf gehört zu genau einem Lauf.

Warum je Anker (OBS-S114-2): Ob ein Abschnitt der Pflichtlektüre seinen Lesepreis wert ist,
zeigt sich daran, ob er je eine Regel für ein Finding liefert oder gezielt abgerufen wird.
"""
import json
import re
from importlib import import_module

import pytest

from conftest import cli_aufruf

rb = import_module("prozesscode.read-breakdown")


def _read(nr, pfad, inhalt, **extra):
    return [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": f"t{nr}", "name": "Read", "input": {"file_path": pfad, **extra}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"t{nr}", "content": inhalt}]}},
    ]


def _text(text):
    return [{"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}]


def _bash(befehl):
    return [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "b", "name": "Bash", "input": {"command": befehl}}]}}]


def _schreibe(pfad, records):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")


def _subagent(log_dir, session, name, typ, records):
    ordner = log_dir / session / "subagents"
    _schreibe(ordner / f"{name}.jsonl", records)
    (ordner / f"{name}.meta.json").write_text(json.dumps({"agentType": typ}), encoding="utf-8")


@pytest.fixture
def logs(tmp_path):
    """Zwei Sessions; in der ersten ein Orchestrator und zwei Aufrufe desselben Auditors."""
    start = [{"type": "meta", "timestamp": "2026-11-10T08:00:00Z",
              "attributionSkill": "implementing-scenario"}]
    # Der Orchestrator gibt Findings weiter (an den User, per SendMessage an den Implementer) –
    # seine Zitate sind Kopien und zählen nicht.
    _schreibe(tmp_path / "s1.jsonl",
              start + _read(1, "/home/x/repos/mahl/docs/AGENT_MEMORY.md", "m" * 100)
              + _bash("python3 -m prozesscode.doc get CGG-kiss")
              + _text("Weitergereicht: F1 Regel: CGG-naming"))
    _subagent(tmp_path, "s1", "agent-a", "code-quality-auditor",
              _read(2, "/home/x/repos/mahl/docs/guidelines/coding-guideline-general.md", "g" * 300)
              + _text("F1 Name sagt nichts. Regel: CGG-naming\nF2 Stil. Regel: keine"))
    _subagent(tmp_path, "s1", "agent-b", "code-quality-auditor",
              _read(3, "/home/x/repos/mahl/Client/src/App.tsx", "c" * 50, limit=10))
    _schreibe(tmp_path / "s2.jsonl",
              [{"type": "meta", "timestamp": "2026-11-20T08:00:00Z"}]
              + _read(4, "/home/x/repos/mahl/docs/AGENT_MEMORY.md", "m" * 70))
    return tmp_path


def test_je_agent_zaehlt_aufrufe_und_volumen_getrennt(logs):
    messung = rb.collect(logs)
    auditor = messung.je_agent["code-quality-auditor"]
    assert (auditor.kontexte, auditor.volume, auditor.targeted) == (2, 350, 50)
    haupt = messung.je_agent[rb.HAUPTSESSION]
    assert (haupt.kontexte, haupt.volume) == (2, 170)


def test_until_schliesst_spaetere_sessions_aus(logs):
    messung = rb.collect(logs, until="2026-11-15")
    assert messung.gesamt.volume == 450
    assert messung.je_agent[rb.HAUPTSESSION].kontexte == 1


def test_until_schliesst_den_tag_selbst_ein(logs):
    assert rb.collect(logs, until="2026-11-20").gesamt.volume == 520


def test_zitate_und_abrufe_landen_beim_agenten_der_sie_erzeugt(logs):
    messung = rb.collect(logs)
    assert dict(messung.je_agent["code-quality-auditor"].zitate) == {"CGG-naming": 1, "keine": 1}
    assert dict(messung.je_agent[rb.HAUPTSESSION].abrufe) == {"CGG-kiss": 1}
    assert not messung.je_agent[rb.HAUPTSESSION].zitate
    assert messung.gesamt.zitate["CGG-naming"] == 1


@pytest.mark.aufrufpfad("read-breakdown")
def test_by_agent_zeigt_je_typ_aufrufe_und_schnitt(logs, monkeypatch, capsys):
    monkeypatch.setattr(rb, "project_log_dir", lambda: logs)
    assert cli_aufruf(monkeypatch, rb, "--by-agent") == 0
    zeile = next(z for z in capsys.readouterr().out.splitlines() if "code-quality-auditor" in z)
    # Aufrufe, Volumen, Ø je Aufruf, gezielt, Pflichtlektüre je Aufruf, doc-get-Abrufe
    assert zeile.split()[1:] == ["2", "0k", "175", "14%", "150", "0"]


@pytest.mark.aufrufpfad("read-breakdown")
def test_agent_waehlt_die_dateien_eines_typs(logs, monkeypatch, capsys):
    monkeypatch.setattr(rb, "project_log_dir", lambda: logs)
    assert cli_aufruf(monkeypatch, rb, "--agent", "code-quality-auditor", "--top", "5") == 0
    dateien = capsys.readouterr().out.split("Größte gelesene Dateien")[1]
    assert "coding-guideline-general.md" in dateien
    assert "Client/src/App.tsx" in dateien
    assert "AGENT_MEMORY" not in dateien


@pytest.mark.aufrufpfad("read-breakdown")
def test_unbekannter_agent_nennt_die_vorhandenen(logs, monkeypatch, capsys):
    monkeypatch.setattr(rb, "project_log_dir", lambda: logs)
    assert cli_aufruf(monkeypatch, rb, "--agent", "gibt-es-nicht") == 1
    assert "code-quality-auditor" in capsys.readouterr().err


@pytest.mark.aufrufpfad("read-breakdown")
def test_agent_und_type_zugleich_wird_abgelehnt(logs, monkeypatch, capsys):
    monkeypatch.setattr(rb, "project_log_dir", lambda: logs)
    assert cli_aufruf(monkeypatch, rb, "--agent", "code-quality-auditor", "--type", "drain") == 2


@pytest.mark.aufrufpfad("read-breakdown")
def test_anker_zeigt_zitate_abrufe_und_den_ungenutzten_rest(logs, monkeypatch, capsys):
    monkeypatch.setattr(rb, "project_log_dir", lambda: logs)
    assert cli_aufruf(monkeypatch, rb, "--anker") == 0
    out = capsys.readouterr().out
    assert re.search(r"CGG-naming\s+1\s+0\b", out)
    assert re.search(r"CGG-kiss\s+0\s+1\b", out)
    assert "Regel: keine" in out and re.search(r"Regel: keine\D+1\b", out)
    # Der ungenutzte Rest stammt aus dem echten Bestand von docs/guidelines und docs/process.
    rest = out.split("nie zitiert und nie abgerufen")[1]
    assert "CGG-komplexitaet" in rest
    assert "CGG-naming" not in rest and "CGG-kiss" not in rest


def test_pflichtlektuere_anker_kommen_aus_beiden_ordnern():
    anker = rb.pflicht_anker()
    assert anker["CGG-kiss"].startswith("docs/guidelines/")
    assert anker["TDD-refactor"].startswith("docs/process/")
    assert not any(datei.startswith("docs/kaizen/") for datei in anker.values())

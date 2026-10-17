"""Offene Rückgaben: knüpfen (PostToolUse), erinnern (Stop, SessionStart), lösen (CLI).

Die Eingaben haben die Form, die eine Live-Probe aufgezeichnet hat – Felder und Werte
von dort übernommen, gekürzt um das, was kein Code liest (Prompt, Modell, Pfade).
"""
import io
import json
import os
import re
import sys
import time
from importlib import import_module
from pathlib import Path

import pytest

from conftest import cli_aufruf
from prozesscode import rueckgaben
from prozesscode.hooks.checks import guard_log

hook = import_module("prozesscode.hooks.merke-rueckgaben")
agent_start = import_module("prozesscode.hooks.check-agent-start")

SESSION = "9057b13c-9946-4e99-bd19-59cc47a7f9bd"

AGENT_START = {  # unbenannter Agent: async_launched
    "session_id": SESSION, "hook_event_name": "PostToolUse", "tool_name": "Agent",
    "tool_input": {"description": "Unbenannter Probe-Agent", "subagent_type": "general-purpose",
                   "prompt": "…"},
    "tool_response": {"isAsync": True, "status": "async_launched", "agentId": "a571eb0b10d33a5f3",
                      "description": "Unbenannter Probe-Agent"},
}
TEAMMATE_START = {  # benannter Agent: teammate_spawned, im Harness unter eigener Task-ID
    "session_id": SESSION, "hook_event_name": "PostToolUse", "tool_name": "Agent",
    "tool_input": {"description": "Probe-Agent für Hook-Eingaben", "name": "probe-agent",
                   "subagent_type": "general-purpose", "prompt": "…"},
    "tool_response": {"status": "teammate_spawned", "agentId": "aprobe-agent-e887fb6ec7d2f518",
                      "agent_id": "aprobe-agent-e887fb6ec7d2f518", "agent_type": "general-purpose",
                      "name": "probe-agent", "teammate_id": "probe-agent@session-77da6eeb"},
}
BASH_HINTERGRUND = {
    "session_id": SESSION, "hook_event_name": "PostToolUse", "tool_name": "Bash",
    "tool_input": {"command": "echo hintergrund-probe", "run_in_background": True,
                   "description": "Kurzen Befehl im Hintergrund als Probe ausführen"},
    "tool_response": {"stdout": "", "stderr": "", "interrupted": False, "isImage": False,
                      "noOutputExpected": False, "backgroundTaskId": "bywy2nlc5"},
}
TEAMMATE_LAEUFT = {"id": "t5j7lujzf", "type": "teammate", "status": "running",
                   "description": "Probe-Agent für Hook-Eingaben"}


def stop(*laufende, aktiv=False) -> dict:
    return {"session_id": SESSION, "hook_event_name": "Stop", "stop_hook_active": aktiv,
            "background_tasks": list(laufende), "last_assistant_message": "…"}


@pytest.fixture(autouse=True)
def ablage(tmp_path, monkeypatch):
    # Zwei Ebenen, die es noch nicht gibt: Im frischen Checkout fehlt auch `.claude/tmp/`.
    verzeichnis = tmp_path / "tmp" / "rueckgaben"
    monkeypatch.setattr(rueckgaben, "VERZEICHNIS", verzeichnis)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", SESSION)
    return verzeichnis


def _hook(monkeypatch, capsys, daten) -> str:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(daten)))
    with pytest.raises(SystemExit) as ende:
        hook.main()
    assert ende.value.code == 0
    return capsys.readouterr().out


def _ids() -> set[str]:
    return {e["id"] for e in rueckgaben.lade(SESSION)}


def _eintrag(eintrag_id, beschreibung="x", benannt=False) -> dict:
    return {"id": eintrag_id, "art": "Agent (general-purpose)", "benannt": benannt,
            "beschreibung": beschreibung, "gestartet": "2026-10-16 10:00"}


# --- Knüpfen ----------------------------------------------------------------

@pytest.mark.aufrufpfad("merke-rueckgaben")
def test_start_im_hintergrund_knuepft_einen_eintrag(monkeypatch, capsys):
    for start in (AGENT_START, TEAMMATE_START, BASH_HINTERGRUND):
        _hook(monkeypatch, capsys, start)
    assert _ids() == {"a571eb0b10d33a5f3", "aprobe-agent-e887fb6ec7d2f518", "bywy2nlc5"}


def test_start_nennt_den_befehl_zum_abhaken(monkeypatch, capsys):
    """Der Hinweis kommt beim Start, nicht erst beim Stop: Wer das Ergebnis verarbeitet, weiß
    dann schon, dass es abzuhaken ist – und mit welcher ID. Der Stop-Hook allein käme zu spät:
    Abgehakt würde losgelöst vom Verarbeiten, im Turn danach."""
    ausgabe = json.loads(_hook(monkeypatch, capsys, BASH_HINTERGRUND))["hookSpecificOutput"]
    assert ausgabe["hookEventName"] == "PostToolUse"
    assert ("python3 -m prozesscode.rueckgaben erledigt bywy2nlc5 --ausgang"
            in ausgabe["additionalContext"])


def test_eintrag_nennt_art_und_beschreibung(monkeypatch, capsys):
    auditor = {**AGENT_START, "tool_input": {"description": "Review", "prompt": "…",
                                             "subagent_type": "code-quality-auditor"}}
    ohne_typ = {**TEAMMATE_START, "tool_input": {"description": "Suche", "prompt": "…",
                                                 "name": "suche"}}
    for start in (auditor, ohne_typ, BASH_HINTERGRUND):
        _hook(monkeypatch, capsys, start)
    assert sorted((e["art"], e["beschreibung"], e["benannt"])
                  for e in rueckgaben.lade(SESSION)) == [
        ("Agent (code-quality-auditor)", "Review", False),
        ("Agent (general-purpose)", "Suche", True),  # ohne subagent_type: general-purpose
        ("Bash", "Kurzen Befehl im Hintergrund als Probe ausführen", False),
    ]


def test_bash_ohne_beschreibung_zeigt_den_befehl_gekuerzt(monkeypatch, capsys):
    lang = "python3 -m pytest tests/ -q " + "x" * 100
    _hook(monkeypatch, capsys, {**BASH_HINTERGRUND,
                                "tool_input": {"command": lang, "run_in_background": True}})
    assert rueckgaben.lade(SESSION)[0]["beschreibung"] == lang[:rueckgaben.BEFEHL_KUERZUNG]


def test_agent_id_als_zweiter_schluessel(monkeypatch, capsys):
    _hook(monkeypatch, capsys, {**AGENT_START, "tool_response": {"agent_id": "a-nur-snake"}})
    assert _ids() == {"a-nur-snake"}


@pytest.mark.parametrize("daten", [
    {**BASH_HINTERGRUND, "tool_input": {"command": "echo vorn", "description": "vorn"},
     "tool_response": {"stdout": "vorn"}},                     # Bash im Vordergrund
    {**AGENT_START, "agent_id": "a1", "agent_type": "general-purpose"},  # Subagent ruft selbst
    {**AGENT_START, "tool_response": "Spawned successfully."},  # Antwort ohne Struktur
    {**AGENT_START, "tool_response": {"status": "async_launched"}},  # ohne ID
    {**AGENT_START, "tool_name": "Read"},
    {**AGENT_START, "session_id": None},
    {**AGENT_START, "hook_event_name": "SubagentStop"},          # nicht registriert, aber harmlos
])
def test_was_nicht_im_hintergrund_startet_knuepft_nichts(monkeypatch, capsys, daten):
    assert _hook(monkeypatch, capsys, daten) == ""
    assert _ids() == set()


def test_doppelter_start_knuepft_einmal(monkeypatch, capsys):
    _hook(monkeypatch, capsys, AGENT_START)
    _hook(monkeypatch, capsys, AGENT_START)
    assert [e["id"] for e in rueckgaben.lade(SESSION)] == ["a571eb0b10d33a5f3"]


# --- Fertig oder laufend ----------------------------------------------------

def test_laufend_ist_wer_mit_seiner_id_im_harness_steht():
    eintraege = [_eintrag("a1"), _eintrag("a2")]
    fertig, laufend = rueckgaben.teile_auf(eintraege, [{"id": "a2", "type": "subagent"}])
    assert ([e["id"] for e in fertig], [e["id"] for e in laufend]) == (["a1"], ["a2"])


def test_benannte_agenten_findet_die_beschreibung():
    eintraege = [_eintrag("aprobe-agent-1", "Probe-Agent für Hook-Eingaben", benannt=True)]
    assert rueckgaben.teile_auf(eintraege, [TEAMMATE_LAEUFT]) == ([], eintraege)


def test_gleiche_beschreibung_haelt_keinen_unbenannten_fest():
    """Zweimal „Review": Läuft einer, darf der fertige nicht mit ihm als laufend gelten."""
    eintraege = [_eintrag("a1", "Review"), _eintrag("a2", "Review")]
    laeuft = [{"id": "a2", "type": "subagent", "description": "Review"}]
    fertig, _laufend = rueckgaben.teile_auf(eintraege, laeuft)
    assert [e["id"] for e in fertig] == ["a1"]


def test_beschreibung_zaehlt_nur_bei_einem_teammate_im_harness():
    eintraege = [_eintrag("aprobe-agent-1", "Review", benannt=True)]
    fremd = [{"id": "bx", "type": "bash", "description": "Review"}]
    assert rueckgaben.teile_auf(eintraege, fremd) == (eintraege, [])


# --- Erinnern beim Stop -----------------------------------------------------

def test_stop_blockt_einmal_bei_fertiger_rueckgabe(monkeypatch, capsys):
    _hook(monkeypatch, capsys, AGENT_START)
    _hook(monkeypatch, capsys, TEAMMATE_START)
    ausgabe = json.loads(_hook(monkeypatch, capsys, stop(TEAMMATE_LAEUFT)))
    assert ausgabe["decision"] == "block"
    assert ausgabe["reason"] == rueckgaben.erinnerung(*rueckgaben.teile_auf(
        rueckgaben.lade(SESSION), [TEAMMATE_LAEUFT]))
    assert guard_log.zaehlstand() == {"merke-rueckgaben": 1}

    assert _hook(monkeypatch, capsys, stop(TEAMMATE_LAEUFT, aktiv=True)) == ""


def test_erinnerung_nennt_fertige_den_befehl_und_laufende():
    text = rueckgaben.erinnerung([_eintrag("a1", "fertig")], [_eintrag("a2", "läuft")])
    assert "a1" in text and rueckgaben.ABHAKEN in text and "a2" in text
    assert text.index("a1") < text.index(rueckgaben.ABHAKEN) < text.index("a2")
    assert "a2" not in rueckgaben.erinnerung([_eintrag("a1")], [])


def test_stop_ohne_fertige_rueckgabe_laesst_durch(monkeypatch, capsys):
    _hook(monkeypatch, capsys, TEAMMATE_START)
    assert _hook(monkeypatch, capsys, stop(TEAMMATE_LAEUFT)) == ""
    assert _hook(monkeypatch, capsys, {**stop(), "session_id": "andere"}) == ""


def test_stop_ohne_background_tasks_haelt_alles_fuer_fertig(monkeypatch, capsys):
    """Fehlalarm statt stillem Übergehen, falls der Harness das Feld einmal nicht schickt."""
    _hook(monkeypatch, capsys, TEAMMATE_START)
    daten = stop()
    del daten["background_tasks"]
    assert "aprobe-agent" in json.loads(_hook(monkeypatch, capsys, daten))["reason"]


def test_ausfall_beim_stop_wird_einmal_sichtbar(monkeypatch, capsys):
    def kaputt(_session):
        raise PermissionError("Zugriff verweigert")
    monkeypatch.setattr(rueckgaben, "lade", kaputt)

    ausfall = json.loads(_hook(monkeypatch, capsys, stop()))
    assert ausfall["decision"] == "block"
    assert "ausgefallen (PermissionError: Zugriff verweigert)" in ausfall["reason"]
    assert f"ls {rueckgaben.VERZEICHNIS}" in ausfall["reason"]  # der Ausweg, nicht nur der Befund
    assert _hook(monkeypatch, capsys, stop(aktiv=True)) == ""  # keine Dauerschleife

    # Außerhalb des Stops: fail-open, nur die stderr-Zeile.
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(
        {"session_id": SESSION, "hook_event_name": "SessionStart"})))
    with pytest.raises(SystemExit):
        hook.main()
    ausgabe = capsys.readouterr()
    assert ausgabe.out == ""
    assert "merke-rueckgaben: PermissionError: Zugriff verweigert" in ausgabe.err


def test_unlesbare_eintragsdatei_erscheint_und_laesst_sich_abhaken(monkeypatch, capsys, ablage):
    rueckgaben.ordner(SESSION).mkdir(parents=True)
    (rueckgaben.ordner(SESSION) / "kaputt.json").write_text("{kaputt", encoding="utf-8")
    assert "kaputt  unlesbar" in json.loads(_hook(monkeypatch, capsys, stop()))["reason"]
    assert cli_aufruf(monkeypatch, rueckgaben, "erledigt", "kaputt", "--ausgang", "entfernt") == 0
    assert not rueckgaben.ordner(SESSION).exists()


@pytest.mark.parametrize("eingabe, meldung", [
    ("kein json", "merke-rueckgaben: unlesbare Eingabe"),
    ("[1, 2]", ""),  # JSON, aber kein Objekt: still durchlassen
])
def test_unlesbare_eingabe_blockt_nichts(monkeypatch, capsys, eingabe, meldung):
    monkeypatch.setattr(sys, "stdin", io.StringIO(eingabe))
    with pytest.raises(SystemExit) as ende:
        hook.main()
    ausgabe = capsys.readouterr()
    assert (ende.value.code, ausgabe.out) == (0, "")
    assert meldung in ausgabe.err


# --- Session-Start ----------------------------------------------------------

def _alt_machen(pfad: Path, tage: float) -> None:
    zeit = time.time() - tage * rueckgaben.SEKUNDEN_JE_TAG
    os.utime(pfad, (zeit, zeit))


def test_session_start_zeigt_offene_und_raeumt_alte_fremde_ab(monkeypatch, capsys, ablage):
    _hook(monkeypatch, capsys, AGENT_START)
    for fremd in ("alt", "jung"):
        (ablage / fremd).mkdir()
        (ablage / fremd / "x.json").write_text("{}", encoding="utf-8")
    _alt_machen(ablage / "alt", 15)
    _alt_machen(rueckgaben.ordner(SESSION), 15)  # die eigene bleibt trotzdem

    ausgabe = _hook(monkeypatch, capsys, {"session_id": SESSION, "hook_event_name": "SessionStart",
                                          "source": "compact"})
    assert "a571eb0b10d33a5f3" in ausgabe and "Offene Rückgaben" in ausgabe
    assert sorted(p.name for p in ablage.iterdir()) == [SESSION, "jung"]


def test_session_start_ohne_offene_schweigt(monkeypatch, capsys):
    assert _hook(monkeypatch, capsys, {"session_id": SESSION,
                                       "hook_event_name": "SessionStart"}) == ""


def test_haltbarkeit_endet_genau_nach_14_tagen(ablage):
    jetzt = time.time()
    grenze = jetzt - rueckgaben.HALTBARKEIT_TAGE * rueckgaben.SEKUNDEN_JE_TAG
    for name, alter in (("knapp-drueber", grenze - 1), ("genau", grenze),
                        ("knapp-drunter", grenze + 5)):
        (ablage / name).mkdir(parents=True)
        os.utime(ablage / name, (alter, alter))
    rueckgaben.raeume_alte(SESSION, jetzt)
    assert sorted(p.name for p in ablage.iterdir()) == ["genau", "knapp-drunter"]


# --- Lösen per CLI ----------------------------------------------------------

@pytest.mark.aufrufpfad("rueckgaben")
def test_erledigt_entfernt_und_raeumt_den_ordner_mit_dem_letzten(monkeypatch, capsys):
    _hook(monkeypatch, capsys, AGENT_START)
    _hook(monkeypatch, capsys, BASH_HINTERGRUND)

    assert cli_aufruf(monkeypatch, rueckgaben, "erledigt", "bywy2nlc5",
                      "--ausgang", "Ausgabe gelesen") == 0
    assert "abgehakt: Ausgabe gelesen" in capsys.readouterr().out
    assert _ids() == {"a571eb0b10d33a5f3"}

    assert cli_aufruf(monkeypatch, rueckgaben, "erledigt", "a571eb0b10d33a5f3",
                      "--ausgang", "2 umgesetzt") == 0
    assert not rueckgaben.ordner(SESSION).exists()


def test_erledigt_mit_unbekannter_id_nennt_die_offenen(monkeypatch, capsys):
    _hook(monkeypatch, capsys, AGENT_START)
    assert cli_aufruf(monkeypatch, rueckgaben, "erledigt", "gibt-es-nicht", "--ausgang", "x") == 1
    assert "a571eb0b10d33a5f3" in capsys.readouterr().err
    assert _ids() == {"a571eb0b10d33a5f3"}


def test_erledigt_verlangt_den_ausgang(monkeypatch, capsys):
    _hook(monkeypatch, capsys, AGENT_START)
    assert cli_aufruf(monkeypatch, rueckgaben, "erledigt", "a571eb0b10d33a5f3") == 2
    assert _ids() == {"a571eb0b10d33a5f3"}


def test_liste_zeigt_offene_und_meldet_leere_ablage(monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, rueckgaben, "liste") == 0
    assert "Keine offenen" in capsys.readouterr().out
    _hook(monkeypatch, capsys, AGENT_START)
    cli_aufruf(monkeypatch, rueckgaben, "liste")
    assert "Unbenannter Probe-Agent" in capsys.readouterr().out


def test_ohne_unterbefehl_meldet_argparse(monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, rueckgaben) == 2
    assert "erledigt" in capsys.readouterr().err


def test_ohne_session_id_klare_meldung(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID")
    with pytest.raises(SystemExit) as ende:
        rueckgaben.main(["liste"])
    assert "CLAUDE_CODE_SESSION_ID" in str(ende.value.code)


# --- check-agent-start ------------------------------------------------------

def _agent_start(monkeypatch, capsys, **eingabe) -> str:
    daten = {"session_id": SESSION, "hook_event_name": "PreToolUse", "tool_name": "Agent",
             "tool_input": {"description": "Review", "prompt": "…", **eingabe}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(daten)))
    with pytest.raises(SystemExit) as ende:
        agent_start.main()
    assert ende.value.code == 0  # nur bei Exit 0 liest Claude Code das Deny-JSON
    ausgabe = capsys.readouterr().out
    return json.loads(ausgabe)["hookSpecificOutput"]["permissionDecision"] if ausgabe else "allow"


@pytest.mark.aufrufpfad("check-agent-start")
@pytest.mark.parametrize("eingabe, erwartet", [
    ({"subagent_type": "code-quality-auditor", "name": "cq-probe"}, "deny"),
    ({"subagent_type": "workflow-auditor", "name": "FlowReview"}, "deny"),
    # Gegenproben: ohne Namen, oder kein Auditor – beides ist in Ordnung.
    ({"subagent_type": "code-quality-auditor"}, "allow"),
    ({"subagent_type": "backend-layer-implementer", "name": "backend-validation"}, "allow"),
    ({"name": "probe-agent"}, "allow"),
])
def test_auditor_mit_namen_wird_abgelehnt(monkeypatch, capsys, eingabe, erwartet):
    assert _agent_start(monkeypatch, capsys, **eingabe) == erwartet


def test_ablehnung_nennt_den_ausweg(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({
        "tool_name": "Agent", "tool_input": {"subagent_type": "security-auditor", "name": "sec"}})))
    with pytest.raises(SystemExit):
        agent_start.main()
    grund = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "ohne `name`" in grund and "security-auditor" in grund


def test_unlesbare_eingabe_blockt_den_start_nicht(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("kein json"))
    with pytest.raises(SystemExit) as ende:
        agent_start.main()
    ausgabe = capsys.readouterr()
    assert (ende.value.code, ausgabe.out) == (0, "")
    assert "check-agent-start: unlesbare Eingabe (JSONDecodeError" in ausgabe.err


# --- Registrierung ----------------------------------------------------------

def _registriert(ereignis: str, modul: str) -> list[str | None]:
    """Die Matcher, unter denen `modul` für `ereignis` in settings.json eingetragen ist."""
    settings = json.loads((Path(__file__).resolve().parent.parent / ".claude" / "settings.json")
                          .read_text(encoding="utf-8"))
    return [gruppe.get("matcher") for gruppe in settings["hooks"].get(ereignis, [])
            for h in gruppe["hooks"] if h["command"].endswith(f"python3 -m prozesscode.hooks.{modul}")]


@pytest.mark.parametrize("ereignis, modul, werkzeuge", [
    ("PostToolUse", "merke-rueckgaben", ["Agent", "Bash"]),
    ("PreToolUse", "check-agent-start", ["Agent"]),
    ("Stop", "merke-rueckgaben", None),
    ("SessionStart", "merke-rueckgaben", None),
])
def test_settings_loesen_die_hooks_aus(ereignis, modul, werkzeuge):
    """Ein nicht registrierter Hook läuft fehlerfrei und tut nichts (RCL-prozess-code)."""
    matcher = _registriert(ereignis, modul)
    assert len(matcher) == 1
    if werkzeuge is None:
        assert matcher == [None]
    else:
        assert all(re.fullmatch(matcher[0], w) for w in werkzeuge)

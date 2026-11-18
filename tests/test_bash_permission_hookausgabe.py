"""Was der Bash-Guard nach außen gibt: Hook-JSON, Exit-Code, Protokollzeile, Protokollschlüssel.

Der Runner `test-bash-permission.py` prüft, **welche** Entscheidung fällt. Diese Datei prüft,
wie sie Claude Code und die Retro erreicht – beides liest der Guard nicht selbst, ein Fehler
dort bliebe also still: ein falsch geschriebener Schlüssel im JSON, und Claude Code verwirft
die Entscheidung; ein falscher Protokollschlüssel, und die Retro zählt die Reibung unter dem
falschen Typ (`denied-commands.log` ist ihre Datenquelle).

Deshalb hier ganze Ausgaben statt einzelner Felder: Ein Vergleich mit dem vollständigen
erwarteten Objekt fällt auch bei einem zusätzlichen oder umbenannten Schlüssel.
"""
import io
import json
import os
import re
import sys
from importlib import import_module

import pytest

os.environ.setdefault("CLAUDE_CODE_SESSION_ID", "test-session-0000")
hook = import_module("prozesscode.hooks.check-bash-permission")


@pytest.fixture
def logs(tmp_path, monkeypatch):
    """Beide Protokolle des Guards in tmp_path – kein Test schreibt ins echte Log."""
    abgelehnt, erlaubt = tmp_path / "denied.log", tmp_path / "allowed.log"
    monkeypatch.setattr(hook, "_LOG_FILE", str(abgelehnt))
    monkeypatch.setattr(hook, "_ALLOWED_LOG_FILE", str(erlaubt))
    return abgelehnt, erlaubt


def _zeilen(pfad) -> list[str]:
    """Protokollzeilen ohne Zeitstempel – der ist eigens geprüft."""
    if not pfad.exists():
        return []
    return [re.sub(r"^\[[^]]*\] ", "", z) for z in pfad.read_text(encoding="utf-8").splitlines()]


def _hook(monkeypatch, capsys, eingabe, *argv) -> tuple[object, str]:
    """Startet `main()` wie Claude Code: JSON auf stdin. Gibt (Exit-Code, stdout) zurück.

    Eigener Helfer statt `cli_aufruf`: Der macht aus `sys.exit(None)` eine 0 – genau den
    Unterschied, den Claude Code am Exit-Code liest, darf der Test nicht einebnen.
    """
    monkeypatch.setattr(sys, "argv", ["check-bash-permission", *argv])
    text = eingabe if isinstance(eingabe, str) else json.dumps(eingabe)
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))
    with pytest.raises(SystemExit) as ende:
        hook.main()
    return ende.value.code, capsys.readouterr().out


def _bash(command, **mehr) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}, **mehr}


# --- Hook-JSON und Exit-Code --------------------------------------------------
def test_allow_meldet_die_entscheidung_im_erwarteten_format(monkeypatch, capsys, logs):
    code, out = _hook(monkeypatch, capsys, _bash("ls -la"))
    assert code == 0
    assert json.loads(out) == {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": hook._ALLOW_REASON,
    }}


def test_umgeschriebener_befehl_behaelt_die_uebrigen_eingabefelder(monkeypatch, capsys, logs):
    # Claude Code ersetzt die Eingabe durch `updatedInput` als Ganzes: Fehlten `timeout` oder
    # `run_in_background`, liefe ein langer Wrapper nach dem Umschreiben mit dem Standard-Timeout
    # im Vordergrund (S151 beobachtet: `| tail` gekürzt, Lauf nach zwei Minuten abgebrochen).
    eingabe = {"command": "python3 -m prozesscode.vitest-run | tail -5", "timeout": 600000,
               "run_in_background": True, "description": "Frontend-Tests"}
    code, out = _hook(monkeypatch, capsys, {"tool_name": "Bash", "tool_input": eingabe})
    assert code == 0
    assert json.loads(out)["hookSpecificOutput"]["updatedInput"] == {
        **eingabe, "command": "python3 -m prozesscode.vitest-run"}


def test_unnoetiger_marker_erlaubt_und_sagt_es_dem_agenten(monkeypatch, capsys, logs):
    code, out = _hook(monkeypatch, capsys, _bash("ls -la # --allow-once"))
    assert code == 0
    assert json.loads(out) == {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": hook._ALLOW_REASON,
        "additionalContext": hook._ONE_TIME_UNNEEDED_HINT,
    }}


def test_ask_traegt_den_grund_in_den_freigabedialog(monkeypatch, capsys, logs):
    """Geprüft wird, dass der Grund ankommt – nicht sein Wortlaut, den legt `check_command` fest."""
    befehl = "rm -rf build # --allow-once"
    grund = hook.check_command(befehl)[1]
    assert grund, "Gegenprobe: Ohne Grund verglichen sich hier zwei leere Felder"
    code, out = _hook(monkeypatch, capsys, _bash(befehl))
    assert code == 0
    assert json.loads(out) == {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": grund,
    }}


def test_ask_ohne_grund_laesst_das_feld_weg(monkeypatch, capsys, logs):
    """Ein leerer Reason zeigte im Dialog eine leere Zeile statt des Befehls."""
    code, out = _hook(monkeypatch, capsys, _bash("frobnicate --x # --allow-once"))
    assert code == 0
    assert json.loads(out) == {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "ask"}}


def test_deny_haengt_den_ausweg_an_den_grund(monkeypatch, capsys, logs):
    code, out = _hook(monkeypatch, capsys, _bash("rm -rf build"))
    assert code == 0
    grund = hook.check_command("rm -rf build")[1]
    assert json.loads(out) == {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": grund + hook._ALLOW_ONCE_WITH_HINT_FOOTER,
    }}


def test_auditoren_bekommen_den_nur_lesend_text(monkeypatch, capsys, logs):
    _, out = _hook(monkeypatch, capsys, _bash("mkdir x", agent_type="security-auditor"))
    grund = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert grund == hook._NUR_LESEND_DENY_REASON + hook._NUR_LESEND_FOOTER


@pytest.mark.parametrize("eingabe", [
    "kein json",
    {"tool_name": "Read", "tool_input": {"file_path": "x"}},
    {"tool_input": {"command": "rm -rf x"}},          # ohne tool_name: kein Bash-Aufruf
    {"tool_name": "Bash"},                            # ohne tool_input
    {"tool_name": "Bash", "tool_input": {}},          # ohne command
    _bash(""),
])
def test_was_kein_bash_befehl_ist_laesst_der_hook_stumm_durch(monkeypatch, capsys, logs, eingabe):
    code, out = _hook(monkeypatch, capsys, eingabe)
    assert (code, out) == (0, "")
    assert _zeilen(logs[0]) == _zeilen(logs[1]) == []


def test_list_druckt_die_allow_liste(monkeypatch, capsys):
    code, out = _hook(monkeypatch, capsys, "", "--list")
    assert code == 0
    assert out == hook.allow_list_text() + "\n"


# --- Protokoll ------------------------------------------------------------------
def test_erlaubtes_geht_ins_allow_log_und_nur_dorthin(monkeypatch, capsys, logs):
    _hook(monkeypatch, capsys, _bash("ls -la"))
    assert _zeilen(logs[1]) == ["[ALLOW] ls -la"]
    assert _zeilen(logs[0]) == []


@pytest.mark.parametrize("befehl, zeile", [
    ("rm -rf build", "[DESTRUCTIVE] rm -rf build"),
    ("rm -rf build # --allow-once", "[ONE_TIME] rm -rf build # --allow-once"),
])
def test_abgelehntes_und_rueckfragen_gehen_ins_deny_log(monkeypatch, capsys, logs, befehl, zeile):
    _hook(monkeypatch, capsys, _bash(befehl))
    assert _zeilen(logs[0]) == [zeile]
    assert _zeilen(logs[1]) == []


def test_abgelehnter_befehl_eines_subagenten_nennt_den_agenten_im_deny_log(
        monkeypatch, capsys, logs):
    # Given – Claude Code liefert bei Subagent-Aufrufen `agent_type` (bei benanntem Start: den Namen)
    eingabe = _bash("npm --prefix Client run lint", agent_type="frontend-layer-implementer")
    # When
    _hook(monkeypatch, capsys, eingabe)
    # Then – ohne den Agenten ist das Kriterium von CM-S056-1 („aus Subagent-Kontext") nicht prüfbar
    assert _zeilen(logs[0]) == [
        "[WRONG_APPROACH] [agent=frontend-layer-implementer] npm --prefix Client run lint"]


def test_erlaubter_befehl_eines_subagenten_nennt_den_agenten_im_allow_log(
        monkeypatch, capsys, logs):
    # Given
    eingabe = _bash("ls", agent_type="impl-frontend-run9")
    # When
    _hook(monkeypatch, capsys, eingabe)
    # Then
    assert _zeilen(logs[1]) == ["[ALLOW] [agent=impl-frontend-run9] ls"]
    assert _zeilen(logs[0]) == []


def test_rueckfrage_eines_subagenten_nennt_den_agenten_im_deny_log(monkeypatch, capsys, logs):
    # Given – der dritte Pfad neben allow und deny: Rückfrage an den User
    eingabe = _bash("rm -rf x # --allow-once", agent_type="backend-layer-implementer")
    # When
    _hook(monkeypatch, capsys, eingabe)
    # Then
    assert _zeilen(logs[0]) == ["[ONE_TIME] [agent=backend-layer-implementer] rm -rf x # --allow-once"]


def test_befehl_des_haupt_threads_traegt_kein_agentenfeld(monkeypatch, capsys, logs):
    # Given – ohne agent_type: Haupt-Thread; die Zeile bleibt im bisherigen Format
    eingabe = _bash("npm --prefix Client run lint")
    # When
    _hook(monkeypatch, capsys, eingabe)
    # Then
    assert _zeilen(logs[0]) == ["[WRONG_APPROACH] npm --prefix Client run lint"]


def test_protokollzeile_traegt_zeitstempel_typ_und_befehl(tmp_path):
    log = tmp_path / "unter" / "x.log"
    hook._log_command("echo ä", "UNKNOWN", str(log))
    assert re.fullmatch(r"\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] \[UNKNOWN\] echo ä\n",
                        log.read_text(encoding="utf-8"))


def test_ohne_ziel_schreibt_das_protokoll_ins_deny_log(logs):
    hook._log_command("x", "UNKNOWN")
    assert _zeilen(logs[0]) == ["[UNKNOWN] x"]


# --- Protokollschlüssel je Pfad -------------------------------------------------
@pytest.mark.parametrize("befehl, entscheidung, schluessel", [
    ("ls", "allow", "ALLOW"),
    ("ls # --allow-once", "allow", "ONE_TIME_UNNEEDED"),
    # Am Ende verankertes Muster: Der Marker muss ganz verschwinden, nicht nur unkenntlich werden.
    ("node --version # --allow-once", "allow", "ONE_TIME_UNNEEDED"),
    ("rm -rf x # --allow-once", "ask", "ONE_TIME"),
    ("cat <<EOF\nx\nEOF", "deny", "UNSUPPORTED_QUOTING"),
    ("echo $'a'", "deny", "UNSUPPORTED_QUOTING"),
    ("dotnet test", "deny", "WRONG_APPROACH"),
    ("cd Client && npm ci", "deny", "WRONG_APPROACH"),
    ("python3 -m prozesscode.td set TD-S080-1 --titel X", "ask", "WRITE_ACCESS"),
    ("frobnicate", "deny", "UNKNOWN"),
    ("ls; frobnicate", "deny", "COMPOUND_UNKNOWN"),
    ("ls && rm -rf x", "deny", "COMPOUND_DESTRUCTIVE"),
    ("done", "deny", "UNKNOWN"),
    ("eval ls", "deny", "INDIRECT_EXEC"),
    ("echo x > datei.txt", "deny", "UNSAFE_REDIRECT"),
])
def test_jeder_pfad_hat_seinen_protokollschluessel(befehl, entscheidung, schluessel):
    entschieden, _, typ = hook.check_command(befehl)
    assert (entschieden, typ) == (entscheidung, schluessel)


def test_erlaubt_ist_auch_der_grund_festgelegt():
    assert hook.check_command("ls") == ("allow", hook._ALLOW_REASON, "ALLOW")


def test_ohne_passenden_hinweis_bleibt_der_grund_leer():
    """Leer heißt: `_build_deny_message` setzt den allgemeinen Text ein."""
    assert hook.check_command("frobnicate")[1] == ""
    assert hook._build_deny_message("") == hook._NO_HINT_MESSAGE


def test_deny_nachricht_ohne_auditor_angabe_ist_die_regulaere():
    assert hook._build_deny_message("Grund") == "Grund" + hook._ALLOW_ONCE_WITH_HINT_FOOTER


# --- Abgelehnte Kette nennt das Glied (OBS-S151-2) --------------------------------
# Ohne die Angabe hielt ein Auditor ein erlaubtes Glied für gesperrt und ließ dessen Prüfung aus.
def test_abgelehnte_kette_nennt_das_glied():
    _, grund, _ = hook.check_command("git status; frobnicate --x")
    meldung = hook._build_deny_message(grund)
    assert "frobnicate --x" in meldung
    assert meldung.endswith(hook._NO_HINT_MESSAGE)   # ohne Hinweis bleibt der allgemeine Text


def test_abgelehnte_kette_nennt_das_glied_auch_dem_auditor():
    _, grund, _ = hook.check_command("python3 -m prozesscode.decisions list; touch x", nur_lesend=True)
    meldung = hook._build_deny_message(grund, nur_lesend=True)
    assert "touch x" in meldung
    assert meldung.endswith(hook._NUR_LESEND_DENY_REASON + hook._NUR_LESEND_FOOTER)


def test_redirect_in_eine_datei_verweist_auf_write_und_edit():
    """OBS-S141-1: Layer-Subagenten versuchten wiederholt `cat > datei <<'EOF'` – der Rat muss
    der Weg zum Ziel sein (Datei schreiben), nicht der zum Auffangen einer Befehlsausgabe."""
    _, grund, _ = hook.check_command("cat > Client/src/x.ts <<'EOF'\nexport {}\nEOF")
    assert grund.splitlines()[1].startswith("Datei anlegen, ändern oder anhängen")
    assert "Write" in grund and "Edit" in grund


def test_glied_kopf_trennt_auch_einen_hinweis_mit_leerzeile():
    """Der Hinweis zu `python3 -c` enthält selbst Leerzeilen – getrennt wird an der ersten."""
    _, grund, _ = hook.check_command("git status; python3 -c 1")
    hinweis = hook._get_smart_hint("python3 -c 1")
    assert "\n\n" in hinweis
    assert hook._build_deny_message(grund) == (
        hook._GLIED_KOPF.format(glied="python3 -c 1") + hinweis + hook._ALLOW_ONCE_WITH_HINT_FOOTER)


@pytest.mark.parametrize("befehl", ["frobnicate", "timeout 5 frobnicate"])
def test_einzelbefehl_bekommt_keine_gliedangabe(befehl):
    assert hook.check_command(befehl)[1] == ""


def test_glied_in_einer_substitution_wird_genannt():
    assert "frobnicate" in hook.check_command("out=$(ls | frobnicate)")[1]


# --- Segmentprüfung ------------------------------------------------------------
@pytest.mark.parametrize("befehl, schluessel", [
    ("eval x", "INDIRECT_EXEC"),
    ("rm x", "ALLOW"),                      # ohne Schleife: Dateiverwaltung ist erlaubt
    ("mkdir x", "ALLOW"),                   # ohne Auditor: keine Lese-Beschränkung
    ("echo x > datei.txt", "UNSAFE_REDIRECT"),
    ("rm -rf x", "DESTRUCTIVE"),
    ("frobnicate", "UNKNOWN"),
])
def test_segmentpruefung_mit_vorgaben(befehl, schluessel):
    assert hook.check_simple_command(befehl)[2] == schluessel


def test_segmentpruefung_im_schleifenrumpf_und_fuer_auditoren():
    assert hook.check_simple_command("rm x", in_loop=True)[::2] == ("deny", "LOOP_WRITE")
    assert hook.check_simple_command("mkdir x", nur_lesend=True)[::2] == ("deny", "NUR_LESEND")
    assert hook.check_simple_command("ls", nur_lesend=True) == ("allow", hook._ALLOW_REASON, "ALLOW")


# --- Schleifen über Segmentgrenzen ----------------------------------------------
@pytest.mark.parametrize("befehl, entscheidung", [
    # Nach `done` ist der Rumpf zu Ende: Dateiverwaltung wieder erlaubt.
    ("for f in a; do echo $f; done; rm x", "allow"),
    # Verschachtelt: Nach dem inneren `done` ist man noch im äußeren Rumpf.
    ("for a in x; do for b in y; do echo $b; done; rm z; done", "deny"),
    ("for a in x; do for b in y; do echo $b; done; done; rm z", "allow"),
    # Nach `done` geht die Prüfung weiter – der Rest ist nicht freigegeben, weil eine Schleife davor stand.
    ("for f in a; do echo $f; done; rm -rf x", "deny"),
])
def test_schleifentiefe_folgt_den_segmenten(befehl, entscheidung):
    assert hook.check_command(befehl)[0] == entscheidung


# --- Freigabe-Vorschau ----------------------------------------------------------
_TRACKER = "python3 -m prozesscode.td set TD-S080-1 --titel X"


def test_freigabe_stellt_die_vorschau_vor_den_grund():
    vorschau = hook.tracker_preview.vorschau(_TRACKER)
    grund = next(r for p, r in hook.WRITE_ACCESS_PATTERNS if p.search(_TRACKER))
    assert hook.check_command(_TRACKER)[1] == f"{vorschau}\n\n{grund}"


def test_ohne_vorschau_bleibt_der_grund_allein(monkeypatch):
    assert hook._mit_vorschau("ls", "Grund") == "Grund"
    monkeypatch.setattr(hook, "tracker_preview", None)
    assert hook._mit_vorschau(_TRACKER, "Grund") == "Grund"


# --- Allow-Ausgabe mit Umschreibung ---------------------------------------------
_ROH = {"hookEventName": "PreToolUse", "permissionDecision": "allow",
        "permissionDecisionReason": hook._ALLOW_REASON}


def test_allow_ausgabe_ohne_umschreibung():
    assert hook._build_allow_output("ls -la") == _ROH


def test_allow_ausgabe_nur_filter_entfernt():
    assert hook._build_allow_output("python3 -m prozesscode.vitest-run | tail -5") == {
        **_ROH,
        "updatedInput": {"command": "python3 -m prozesscode.vitest-run"},
        "additionalContext": hook._FILTER_STRIPPED_HINT,
    }


def test_allow_ausgabe_nur_pfad_normalisiert():
    assert hook._build_allow_output(f"ls {hook._NORMALIZE_ROOT}/docs") == {
        **_ROH,
        "updatedInput": {"command": "ls docs"},
        "additionalContext": hook._NORMALIZE_HINT,
    }


def test_allow_ausgabe_beide_hinweise_getrennt():
    befehl = f"python3 {hook._NORMALIZE_ROOT}/prozesscode/vitest-run.py | tail -5"
    assert hook._build_allow_output(befehl) == {
        **_ROH,
        "updatedInput": {"command": "python3 prozesscode/vitest-run.py"},
        "additionalContext": hook._NORMALIZE_HINT + "\n\n" + hook._FILTER_STRIPPED_HINT,
    }


# --- Scratchpad ----------------------------------------------------------------
def test_scratchpad_folgt_session_und_repo_pfad(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "abc")
    monkeypatch.setattr(hook, "_REPO_ROOT", "/home/u/repos/x/")
    assert hook._resolve_scratchpad() == f"/tmp/claude-{os.getuid()}/-home-u-repos-x/abc/scratchpad"


def test_ohne_session_kein_scratchpad(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID")
    assert hook._resolve_scratchpad() is None


# --- Allow-Liste als Text --------------------------------------------------------
def _muster(*eintraege):
    return [(re.compile("x"), gruppe, text) for gruppe, text in eintraege]


@pytest.fixture
def kleine_liste(monkeypatch):
    """Eine Allow-Liste mit Fällen, an denen die Sortierung sichtbar wird: Groß-/Kleinschreibung
    und `[` (liegt zwischen den Groß- und den Kleinbuchstaben, sortiert also klein vor `a`,
    groß hinter `Z`)."""
    monkeypatch.setattr(hook, "ALLOW_PATTERNS", _muster(
        (None, "beta"), (None, "Alpha"), (None, "[ test ]"), (None, None),
        ("b-Gruppe", "Zwei"), ("b-Gruppe", "eins"), ("A-Gruppe", "x"), ("A-Gruppe", None),
        ("Leer", None),
    ))
    monkeypatch.setattr(hook, "DESTRUCTIVE_PATTERNS", [
        (re.compile("x"), "h", "zap"), (re.compile("x"), "h", "Boom"),
        (re.compile("x"), "h", "[ x ]"), (re.compile("x"), "h", None),
    ])
    monkeypatch.setattr(hook, "_SCRATCHPAD", None)


def _abschnitt(text: str, kopf: str) -> list[str]:
    """Die Zeilen ab `kopf` bis zur nächsten Leerzeile."""
    zeilen = text.split("\n")
    start = zeilen.index(kopf)
    ende = zeilen.index("", start) if "" in zeilen[start:] else len(zeilen)
    return zeilen[start:ende]


def test_allow_liste_sortiert_ohne_ansehen_der_schreibweise(kleine_liste):
    text = hook.allow_list_text()
    zeilen = text.split("\n")
    kopf = zeilen.index(hook._KOPF_ERLAUBT)
    assert zeilen[kopf:kopf + 12] == [
        hook._KOPF_ERLAUBT,
        "  [ test ]", "  Alpha", "  beta",
        "",
        "  [A-Gruppe]", "    x",
        "  [b-Gruppe]", "    eins, Zwei",
        "  [Leer]", "    ",
        "",
    ]


def test_destruktive_sortiert_ohne_ansehen_der_schreibweise(kleine_liste):
    assert _abschnitt(hook.allow_list_text(), hook._KOPF_DESTRUKTIV) == [
        hook._KOPF_DESTRUKTIV, "  [ x ]", "  Boom", "  zap"]


def test_abschnitte_der_allow_liste_stehen_durch_leerzeilen_getrennt(kleine_liste):
    text = hook.allow_list_text()
    for kopf in (hook._KOPF_TASKS, hook._KOPF_LESEN, hook._KOPF_ERLAUBT,
                 hook._KOPF_SCHREIBEN, hook._KOPF_DESTRUKTIV):
        assert f"\n\n{kopf}\n" in text, kopf


def test_scratchpad_steht_nur_in_der_liste_wenn_es_eines_gibt(kleine_liste, monkeypatch):
    assert "Scratchpad" not in hook.allow_list_text()
    monkeypatch.setattr(hook, "_SCRATCHPAD", "/tmp/sp")
    text = hook.allow_list_text()
    assert "\n  /tmp/sp/\n" in text
    assert f"python3 <scratchpad>/<name>.py {hook.ONE_TIME_MARKER}" in text

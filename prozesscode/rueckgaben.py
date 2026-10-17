#!/usr/bin/env python3
"""Rückgaben: was im Hintergrund gestartet wurde und noch nicht verarbeitet ist.

**Wozu.** Subagenten und Hintergrund-Befehle liefern zeitversetzt. Arbeitet der Agent weiter,
während etwas läuft, lebt die Erinnerung „das muss ich noch verarbeiten" nur im Kontext – und
geht dort genauso unter wie der Bericht selbst: Ein verifizierter Befund bleibt liegen, weil der
nächste Bericht hereinkommt, oder ein „finished" wird ganz übersehen. Eine Regel „am Ende
abgleichen" hätte dieselbe Schwäche. Deshalb ein Knoten im Taschentuch:

- **Knüpfen, automatisch:** `hooks/merke-rueckgaben.py` (PostToolUse) legt je Start eines
  Agenten oder eines Bash-Befehls mit `run_in_background` einen Eintrag an – nur in der
  Hauptsession; Subagenten verarbeiten ihre Rückgaben selbst.
- **Lösen, bewusst:** `rueckgaben erledigt <id> --ausgang '…'` – erst, wenn alles aus der
  Rückgabe verarbeitet ist. Der Ausgang wird nicht gespeichert: Er erzwingt, das Ergebnis zu
  benennen, und steht danach im Transkript.
- **Erinnern:** Der Stop-Hook blockt einmal je Turn, solange ein fertiger Eintrag offen ist;
  der SessionStart-Hook zeigt offene Einträge nach `compact` und `resume`.

**Ablage.** Je Session ein Verzeichnis unter `.claude/tmp/rueckgaben/`, je Eintrag eine Datei –
nicht im Scratchpad: `/tmp` wird beim Booten geleert (systemd-tmpfiles). Eine Datei je Eintrag,
weil parallel gestartete Agenten ihre PostToolUse-Hooks gleichzeitig laufen lassen können; eine
gemeinsame Datei verlöre dabei Einträge. Das
Verzeichnis trägt nur Offenes und verschwindet mit dem letzten Eintrag. Was eine abgebrochene
Session hinterlässt, räumt der SessionStart-Hook nach HALTBARKEIT_TAGE ab; jüngere fremde
Verzeichnisse bleiben, sie können einer parallelen Session gehören.

**Fertig oder laufend** entscheidet das Feld `background_tasks` der Stop-Eingabe – die Liste des
Harness mit den noch laufenden Tasks (live gemessen). Benannte Agenten stehen dort als
`teammate` unter einer eigenen Task-ID; für sie zählt ersatzweise die Beschreibung. Fehlt das
Feld, gilt alles als fertig – ein Fehlalarm, kein stilles Übergehen.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERZEICHNIS = ROOT / ".claude" / "tmp" / "rueckgaben"
HALTBARKEIT_TAGE = 14
SEKUNDEN_JE_TAG = 86400
BEFEHL_KUERZUNG = 80  # Bash ohne `description`: so viel vom Befehl erkennt man in der Liste
ABHAKEN = "python3 -m prozesscode.rueckgaben erledigt <id> --ausgang '…'"


def ordner(session_id: str) -> Path:
    return VERZEICHNIS / session_id


def _lies(pfad: Path) -> dict:
    """Ein Eintrag – eine unlesbare Datei wird selbst zum Eintrag, damit sie auffällt und sich
    mit `erledigt <id>` entfernen lässt, statt die Erinnerung lautlos auszuschalten."""
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except ValueError:
        return {"id": pfad.stem, "art": "unlesbar", "benannt": False,
                "beschreibung": f"kein gültiges JSON: {pfad}", "gestartet": "?"}


def lade(session_id: str) -> list[dict]:
    """Die offenen Einträge in Startreihenfolge."""
    dateien = []
    for pfad in ordner(session_id).glob("*.json"):
        try:
            dateien.append((pfad.stat().st_mtime_ns, pfad.name, pfad))
        except FileNotFoundError:  # zwischen glob und stat abgehakt
            continue
    return [_lies(pfad) for _zeit, _name, pfad in sorted(dateien)]


def vermerke(session_id: str, eintrag: dict) -> None:
    ziel = ordner(session_id) / f"{eintrag['id']}.json"
    if ziel.exists():
        return
    ziel.parent.mkdir(parents=True, exist_ok=True)
    zwischen = ziel.with_name(f".{ziel.name}.{os.getpid()}")  # eindeutig je Prozess
    zwischen.write_text(json.dumps(eintrag), encoding="utf-8")
    zwischen.replace(ziel)  # atomar: ein Leser sieht nie eine halbe Datei


def entferne(session_id: str, eintrag_id: str) -> dict | None:
    pfad = ordner(session_id) / f"{eintrag_id}.json"
    if not pfad.exists():
        return None
    eintrag = _lies(pfad)
    pfad.unlink(missing_ok=True)
    try:
        pfad.parent.rmdir()  # nur, wenn es der letzte war
    except OSError:
        pass
    return eintrag


def eintrag_aus_start(daten: dict) -> dict | None:
    """Der Eintrag zu einem PostToolUse – oder None, wenn nichts im Hintergrund startete.

    Nur die Hauptsession knüpft: Trägt die Eingabe eine `agent_id`, ruft ein Subagent das
    Werkzeug, und dessen Rückgaben verarbeitet er selbst.
    """
    if daten.get("agent_id"):
        return None
    eingabe = daten.get("tool_input") or {}
    antwort = daten.get("tool_response")
    if not isinstance(antwort, dict):
        return None
    if daten.get("tool_name") == "Agent":
        eintrag_id = antwort.get("agentId") or antwort.get("agent_id")
        art = f"Agent ({eingabe.get('subagent_type') or 'general-purpose'})"
    elif daten.get("tool_name") == "Bash" and eingabe.get("run_in_background"):
        eintrag_id = antwort.get("backgroundTaskId")
        art = "Bash"
    else:
        return None
    if not eintrag_id:
        return None
    return {"id": eintrag_id, "art": art, "benannt": bool(eingabe.get("name")),
            "beschreibung": eingabe.get("description")
            or eingabe.get("command", "")[:BEFEHL_KUERZUNG],
            "gestartet": time.strftime("%Y-%m-%d %H:%M")}


def teile_auf(eintraege: list[dict], laufende: list[dict]) -> tuple[list[dict], list[dict]]:
    """(fertig, laufend) – fertig ist, was der Harness nicht mehr als laufend führt.

    Die Beschreibung zählt nur bei benannten Agenten: Sie stehen im Harness unter einer
    eigenen Task-ID. Für alle anderen genügt die ID – sonst hielte ein laufender Task jeden
    fertigen Eintrag mit gleicher Beschreibung fest, und der bliebe stumm.
    """
    laufende_ids = {t.get("id") for t in laufende}
    teammates = {t.get("description") for t in laufende if t.get("type") == "teammate"}

    def laeuft(eintrag: dict) -> bool:
        return eintrag["id"] in laufende_ids or (
            eintrag["benannt"] and eintrag["beschreibung"] in teammates)

    return ([e for e in eintraege if not laeuft(e)], [e for e in eintraege if laeuft(e)])


def _zeilen(eintraege: list[dict]) -> str:
    return "\n".join(f"  {e['id']}  {e['art']}  „{e['beschreibung']}“ (gestartet {e['gestartet']})"
                     for e in eintraege)


def hinweis_beim_start(eintrag: dict) -> str:
    return (f"Rückgabe {eintrag['id']} geknüpft. Sobald ihr Ergebnis verarbeitet ist (jedes Finding "
            "umgesetzt, verworfen oder dem User vorgelegt), im selben Zug abhaken: "
            + ABHAKEN.replace("<id>", eintrag["id"]))


def erinnerung(fertig: list[dict], laufend: list[dict]) -> str:
    text = ("Rückgaben fertig, aber nicht abgehakt – ist alles daraus verarbeitet (jedes Finding "
            "umgesetzt, verworfen oder dem User vorgelegt)?\n" + _zeilen(fertig)
            + f"\nDann: {ABHAKEN}\nBewusst offen lassen (Rückfrage an den User, Warten): einfach "
              "erneut beenden – die Erinnerung kommt je Turn nur einmal.")
    if laufend:
        text += "\nLäuft noch:\n" + _zeilen(laufend)
    return text


def session_start_text(eintraege: list[dict]) -> str | None:
    if not eintraege:
        return None
    return ("Offene Rückgaben dieser Session – vor der Unterbrechung gestartet, nicht abgehakt. "
            "Prüfen, ob ihr Ergebnis verarbeitet ist (sonst nachholen), dann abhaken:\n"
            + _zeilen(eintraege) + f"\n{ABHAKEN}")


def raeume_alte(eigene_session: str, jetzt: float | None = None) -> None:
    """Löscht fremde Verzeichnisse, die älter als HALTBARKEIT_TAGE sind – das eigene nie."""
    if not VERZEICHNIS.is_dir():
        return
    grenze = (jetzt or time.time()) - HALTBARKEIT_TAGE * SEKUNDEN_JE_TAG
    for pfad in VERZEICHNIS.iterdir():
        try:
            if pfad.name != eigene_session and pfad.stat().st_mtime < grenze:
                shutil.rmtree(pfad, ignore_errors=True)
        except FileNotFoundError:  # eine parallele Session hat es gerade selbst geräumt
            continue


def _session_aus_umgebung() -> str:
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        sys.exit("Keine Session-ID: CLAUDE_CODE_SESSION_ID fehlt. Der Befehl läuft nur in einer "
                 "Claude-Code-Session.")
    return session_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offene Rückgaben (Agenten, Hintergrund-Befehle) zeigen und abhaken.")
    befehle = parser.add_subparsers(dest="befehl", required=True)
    erledigt = befehle.add_parser("erledigt", help="Rückgabe als verarbeitet abhaken")
    erledigt.add_argument("id")
    erledigt.add_argument("--ausgang", required=True,
                          help="was aus der Rückgabe wurde, z.B. '3 umgesetzt, 1 verworfen'")
    befehle.add_parser("liste", help="offene Rückgaben dieser Session")
    args = parser.parse_args(argv)

    session_id = _session_aus_umgebung()
    if args.befehl == "liste":
        offen = lade(session_id)
        print(_zeilen(offen) if offen else "Keine offenen Rückgaben.")
        return 0
    treffer = entferne(session_id, args.id)
    if treffer is None:
        offen = lade(session_id)
        print(f"Keine offene Rückgabe mit ID {args.id}. Offen sind:\n"
              + (_zeilen(offen) if offen else "  (nichts)"), file=sys.stderr)
        return 1
    print(f"✓ {treffer['id']} ({treffer['art']}, „{treffer['beschreibung']}“) abgehakt: "
          f"{args.ausgang}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

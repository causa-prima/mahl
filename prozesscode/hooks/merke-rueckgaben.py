#!/usr/bin/env python3
"""Knüpft und erinnert an offene Rückgaben – ein Einstieg für drei Hook-Ereignisse.

- **PostToolUse** (Agent, Bash): Startete etwas im Hintergrund, entsteht ein Eintrag, und der
  Kontext nennt den Befehl zum Abhaken – gebraucht wird er beim Verarbeiten, nicht erst beim Stop.
- **Stop:** Ist ein Eintrag fertig, aber nicht abgehakt, blockt der Hook das Turn-Ende EINMAL
  und nennt ihn. Beim zweiten Versuch (`stop_hook_active`) lässt er durch – Rückfragen an den
  User und bewusstes Warten bleiben möglich. Eine Erinnerung, keine Sperre.
- **SessionStart:** Zeigt die offenen Einträge der Session (nach `compact`/`resume` der Fall,
  in dem der Kontext sie verloren hat) und räumt verwaiste Verzeichnisse fremder Sessions ab.

Hintergrund und Ablage: `prozesscode/rueckgaben.py`. **Fail-open:** Ein Fehler hier darf kein
Werkzeug blockieren. Beim Stop wird er einmal sichtbar, sonst fiele der Knoten lautlos aus –
stderr eines Hooks mit Exit 0 sieht niemand.
"""
import json
import sys

from .. import rueckgaben
from .checks import guard_log


_AUSFALL = ("merke-rueckgaben ist ausgefallen ({art}: {fehler}) – offene Rückgaben werden nicht "
            "erinnert. Ablage ansehen: ls {ablage}. Danach erneut beenden.")


def _block(grund: str) -> str:
    return json.dumps({"decision": "block", "reason": grund})


def _kontext(text: str) -> str:
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                              "additionalContext": text}})


def entscheide(daten: dict) -> str | None:
    """Was der Hook ausgibt: Kontext-JSON beim Start, JSON beim Stop-Block, Text beim
    SessionStart, sonst None."""
    session_id = daten.get("session_id")
    if not session_id:
        return None
    ereignis = daten.get("hook_event_name")
    if ereignis == "PostToolUse":
        eintrag = rueckgaben.eintrag_aus_start(daten)
        if not eintrag:
            return None
        rueckgaben.vermerke(session_id, eintrag)
        return _kontext(rueckgaben.hinweis_beim_start(eintrag))
    if ereignis == "Stop":
        fertig, laufend = rueckgaben.teile_auf(rueckgaben.lade(session_id),
                                               daten.get("background_tasks") or [])
        if not fertig:
            return None
        guard_log.protokolliere("merke-rueckgaben")
        return _block(rueckgaben.erinnerung(fertig, laufend))
    if ereignis == "SessionStart":
        rueckgaben.raeume_alte(session_id)
        return rueckgaben.session_start_text(rueckgaben.lade(session_id))
    return None


def main() -> None:
    try:
        daten = json.load(sys.stdin)
    except ValueError as fehler:
        print(f"merke-rueckgaben: unlesbare Eingabe ({fehler})", file=sys.stderr)
        sys.exit(0)
    if not isinstance(daten, dict) or daten.get("stop_hook_active"):
        # Zweiter Stop-Versuch im selben Turn: immer durchlassen – auch im Fehlerfall unten,
        # sonst blockte ein dauerhafter Fehler jedes Turn-Ende.
        sys.exit(0)
    try:
        ausgabe = entscheide(daten)
    except Exception as fehler:  # noqa: BLE001 – fail-open, siehe Modul-Docstring
        print(f"merke-rueckgaben: {type(fehler).__name__}: {fehler}", file=sys.stderr)
        ausgabe = None if daten.get("hook_event_name") != "Stop" else _block(_AUSFALL.format(
            art=type(fehler).__name__, fehler=fehler, ablage=rueckgaben.VERZEICHNIS))
    if ausgabe:
        print(ausgabe)
    sys.exit(0)


if __name__ == "__main__":
    main()

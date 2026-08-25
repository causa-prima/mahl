#!/usr/bin/env python3
"""Einzelne Tech-Debt-Einträge in `docs/tech-debt.md` lesen, erfassen, ändern, löschen.

Warum (OBS-S120-2): `tech-debt.md` führte 28 offene Einträge (35 über die Historie, 7 davon
inzwischen gelöscht) und hatte als einziger großer Tracker überhaupt kein Werkzeug – nur die
Anker-Helfer `td_anchors.py`/`td_due.py`. Jeder Zugriff bedeutete den Vollread der Datei,
jedes Löschen einen Hand-Edit.

Struktur und Mechanik liegen in `tracker_entry.py`, geteilt mit `oq_entry.py`. Zwei Dinge
sind TD-eigen:

  1. Die `Fällig`-Anker-Grammatik (`td_anchors`, dieselbe Prüfung wie in
     `check-td-capture.py` – ohne sie entstünden Einträge, die der Hook danach blockt).
  2. Die Kopplung an `AGENT_MEMORY.md` (OBS-S118-1). `**Fällig:** jetzt` verlangt, dass die
     TD-ID dort unter „Nächste Prioritäten" steht: `tech-debt.md` wird nur situativ gelesen,
     `AGENT_MEMORY.md` bei jedem Session-Start injiziert – ein „jetzt" ohne diesen Eintrag
     wird nie vorgelegt. Bisher wurde der Punkt von Hand dupliziert; der Hook blockt sein
     Fehlen, erzeugt ihn aber nicht. Hier entsteht er mit dem Eintrag und verschwindet mit ihm.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import td_anchors  # noqa: E402
import tracker_entry as te  # noqa: E402
from obs_parse import repo_root, running_session  # noqa: E402

TD_FILE = "docs/tech-debt.md"
MEMORY_FILE = "docs/AGENT_MEMORY.md"

SPEC = te.TrackerSpec(datei=TD_FILE, praefix="TD",
                      felder=("Fällig", "Problem", "Behebung"))

_JETZT = re.compile(r"^jetzt\b", re.I)
_PRIO_UEBERSCHRIFT = re.compile(r"^## Nächste Prioritäten\s*$", re.M)


def td_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / TD_FILE


def memory_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / MEMORY_FILE


def entry_spans(text: str) -> dict[str, tuple[int, int]]:
    return te.entry_spans(SPEC, text)


def get(text: str, tid: str) -> str | None:
    return te.get(SPEC, text, tid)


def titel(text: str, tid: str) -> str | None:
    return te.titel(SPEC, text, tid)


def next_id(text: str, session: int) -> str:
    return te.next_id(SPEC, text, session)


def braucht_memory_punkt(faellig: str) -> bool:
    """True, wenn die Fälligkeit `jetzt` ist (ggf. mit nachgestellter Begründung)."""
    return bool(_JETZT.match(faellig.strip()))


def _pruefe_anker(tid: str, faellig: str, root: Path | None = None) -> None:
    try:
        ktx = td_anchors.lade_kontext(root or repo_root())
    except Exception:  # noqa: BLE001 – ohne Kontext bleibt die syntaktische Prüfung
        ktx = td_anchors.Kontext()
    fehler = td_anchors.validiere(tid, faellig, ktx)
    if fehler:
        raise ValueError(
            f"{tid}: `Fällig` trägt nicht – " + "; ".join(fehler)
            + f". Grammatik: .claude/scripts/td_anchors.py, Vorlage im Header von {TD_FILE}.")


def add(text: str, session: int, root: Path | None = None, *, titel: str, faellig: str,
        problem: str, behebung: str) -> tuple[str, str]:
    """Hängt einen Eintrag unten an. Liefert (neuer Dateiinhalt, vergebene ID)."""
    _pruefe_anker(te.next_id(SPEC, text, session), faellig, root)
    return te.add(SPEC, text, session, titel,
                  {"Fällig": faellig, "Problem": problem, "Behebung": behebung})


def set_fields(text: str, tid: str, faellig: str | None = None, problem: str | None = None,
               behebung: str | None = None, root: Path | None = None) -> str:
    if faellig is not None:
        _pruefe_anker(tid, faellig, root)
    werte = {f: w for f, w in (("Fällig", faellig), ("Problem", problem),
                               ("Behebung", behebung)) if w is not None}
    return te.set_fields(SPEC, text, tid, werte)


def remove(text: str, tid: str) -> str:
    return te.remove(SPEC, text, tid)


# --- AGENT_MEMORY-Kopplung ---------------------------------------------------
def memory_hat(memory_text: str, tid: str) -> bool:
    return tid in memory_text


def memory_zeile(tid: str, done: str) -> str:
    """Die AGENT_MEMORY-Zeile eines TD-Punkts: ID und Done-Kriterium, sonst nichts.

    Titel und Fälligkeit stehen NICHT hier – sie leben in `tech-debt.md` und werden beim
    Rendern aufgelöst (`memory_aufloesen`). Vorher trug diese Zeile eine Kopie des Titels;
    beide Orte konnten driften, und beim Beheben der Schuld waren zwei Dateien zu räumen
    (OBS-S118-1). Was hier bleibt, ist genau das, was es nur hier gibt: die Rangfolge (durch
    die Position in der Liste) und das Done-Kriterium (im TD-Format kein Feld).
    """
    return f"- {tid} · Done: {done.strip()}"


_PLATZHALTER = re.compile(r"^- (TD-S\d+-\d+)\s*·\s*Done:\s*(.*)$", re.M)


def memory_aufloesen(memory_text: str, td_text: str) -> str:
    """Ersetzt TD-Platzhalter durch die volle Prioritäten-Zeile.

    Läuft beim Rendern der Session-Agenda, nicht beim Schreiben: `AGENT_MEMORY.md` behält die
    kurze Form, der injizierte Block zeigt die aufgelöste. Ein Platzhalter ohne TD-Eintrag
    wird SICHTBAR gemeldet statt still übergangen – sonst stünde ein Prioritäten-Punkt ohne
    Inhalt da, und dass er fehlt, merkte niemand.
    """
    def ersetze(m: re.Match) -> str:
        tid, done = m.group(1), m.group(2).strip()
        eintrag = get(td_text, tid)
        if eintrag is None:
            return (f"- **⚠ {tid} steht nicht in {TD_FILE}** — Platzhalter ohne Eintrag "
                    f"· Done: {done}")
        kurztitel = titel(td_text, tid) or tid
        faellig = "?"
        for zeile in eintrag.splitlines():
            if zeile.startswith("**Fällig:**"):
                faellig = zeile.split("**Fällig:**", 1)[1].split("–")[0].strip()
                break
        return (f"- **{kurztitel} ({tid})** — `Fällig: {faellig}` · Quelle: `{TD_FILE}` "
                f"→ {tid} · Done: {done}")

    return _PLATZHALTER.sub(ersetze, memory_text)


def _ist_jetzt_punkt(zeile: str, td_text: str) -> bool:
    """Trägt dieser Prioritäten-Punkt `jetzt`? Für Platzhalter steht das in tech-debt.md."""
    platzhalter = _PLATZHALTER.match(zeile)
    if platzhalter:
        eintrag = get(td_text, platzhalter.group(1)) or ""
        return any(braucht_memory_punkt(z.split("**Fällig:**", 1)[1])
                   for z in eintrag.splitlines() if z.startswith("**Fällig:**"))
    return zeile.startswith("- ") and "`Fällig: jetzt`" in zeile


def memory_ergaenzen(memory_text: str, tid: str, done: str, td_text: str = "") -> str:
    """Fügt einen Prioritäten-Punkt als Platzhalter ein.

    Eingefügt wird hinter dem letzten `jetzt`-Punkt, nicht am Listenende: Die Reihenfolge
    dort IST die Auswahl – gezeigt wird der erste `jetzt`-Punkt in Dokumentreihenfolge. Ein
    `jetzt` hinter den terminierten Punkten bräche die Gruppierung.

    Ob ein bestehender Punkt `jetzt` trägt, ist seit der Platzhalter-Form nicht mehr allein
    aus AGENT_MEMORY ablesbar – für TD-Punkte steht die Fälligkeit in `tech-debt.md`. Fehlt
    `td_text`, zählen nur die ausgeschriebenen Punkte; der neue landet dann eher zu früh als
    zu spät, was die Rangfolge stört, aber nichts verliert.
    """
    if memory_hat(memory_text, tid):
        return memory_text
    punkt = memory_zeile(tid, done)

    jetzt_enden = [m.end() for m in re.finditer(r"^- .*$", memory_text, re.M)
                   if _ist_jetzt_punkt(m.group(0), td_text)]
    if jetzt_enden:
        pos = jetzt_enden[-1]
        return memory_text[:pos] + "\n\n" + punkt + memory_text[pos:]

    ueberschrift = _PRIO_UEBERSCHRIFT.search(memory_text)
    if not ueberschrift:
        raise ValueError(
            f"{MEMORY_FILE} hat keinen Abschnitt `## Nächste Prioritäten` – "
            f"der Punkt für {tid} kann nicht abgelegt werden.")
    pos = ueberschrift.end()
    return memory_text[:pos] + "\n\n" + punkt + memory_text[pos:]


def memory_entfernen(memory_text: str, tid: str) -> str:
    """Entfernt den Prioritäten-Punkt einer TD-ID samt Folgezeilen bis zum nächsten Punkt.

    Ein Punkt darf eingerückte Erläuterungszeilen tragen (der Datei-Header sieht zwei bis
    drei Zeilen vor); sie gehören zu ihm und müssen mitgehen, sonst bleibt eine Ruine ohne
    Bezug stehen.
    """
    muster = re.compile(rf"^- \*\*.*?{re.escape(tid)}.*?$(?:\n(?!\s*-\s\*\*|##)[^\n]*)*\n?",
                        re.M)
    if not muster.search(memory_text):
        return memory_text
    return re.sub(r"\n{3,}", "\n\n", muster.sub("", memory_text, count=1))


def laufende_session(root: Path | None = None) -> int:
    """Nummer der laufenden Session (Mechanik: `obs_parse.running_session`)."""
    return running_session(root or repo_root())

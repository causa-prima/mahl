"""Lesen und Schreiben einzelner OBS-Einträge in `docs/kaizen/observations.md`.

Zwei Gründe für diesen Zugriffsweg statt Read/Edit auf der ganzen Datei:

**Lesen.** Wer einen Eintrag ändert, muss die Datei vorher lesen – der Harness verlangt das.
Gemessen ist rund die Hälfte des Lesens auf `docs/kaizen` genau dieser erzwungene Vor-Edit-Read,
und nur ein Viertel davon ist gezielt. Für die Änderung eines Eintrags wird also meist die
gesamte Datei gelesen.

**Form.** Die Erfassungsregeln (abschließende Feldliste, Pflichtfelder, `Entscheidung/Maßnahme`
bei Erfassung nur mit dem Kanon-Wert) werden bisher **nachträglich** von
`.claude/hooks/check-obs-capture.py` erzwungen – ein Eintrag entsteht, ist falsch, wird geblockt.
Über `add()` kann er gar nicht erst falsch entstehen: Die Felder werden aus geprüften Argumenten
zusammengesetzt, und das Entscheidungsfeld ist nicht setzbar.

Format-Kopplung: Eintrags-Heading und Feld-Präfixe sind im Header von `observations.md`
kanonisch festgelegt – dieselbe Kopplung wie `obs_parse.py` und `check-obs-capture.py`.
"""
import re
from pathlib import Path

from obs_parse import OBS_FILE, repo_root, running_session

IMPACT_WERTE = ("KRITISCH", "HOCH", "MITTEL", "GERING")
HAEUFIGKEIT_WERTE = ("gelegentlich", "häufig", "dauerhaft")
KATEGORIE_WERTE = ("PROZESS", "AGENT", "QUALITÄT", "TOOLING")

# Genau der Wert, den check-obs-capture.py bei der Erfassung zulässt.
KANON_OFFEN = "offen - beim Drain Kandidaten erstellen und bewerten"

_HEADING = re.compile(r"^## (OBS-S\d+-\d+)", re.M)


def obs_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / OBS_FILE


def entry_spans(text: str) -> dict[str, tuple[int, int]]:
    """OBS-ID → (Start, Ende) als Zeichen-Offsets im Text; Ende = vor der nächsten Überschrift."""
    treffer = list(_HEADING.finditer(text))
    spans = {}
    for i, match in enumerate(treffer):
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
        spans[match.group(1)] = (match.start(), ende)
    return spans


def get(text: str, oid: str) -> str | None:
    """Vollständiger Text eines Eintrags (None, wenn es ihn nicht gibt)."""
    span = entry_spans(text).get(oid)
    return text[span[0]:span[1]].rstrip() if span else None


def next_id(text: str, session: int) -> str:
    """Nächste freie ID für diese Session (`OBS-S<NNN>-<n>`)."""
    belegt = [
        int(m.group(1))
        for oid in entry_spans(text)
        if (m := re.fullmatch(rf"OBS-S0*{session}-(\d+)", oid))
    ]
    return f"OBS-S{session:03d}-{max(belegt, default=0) + 1}"


def _pruefe(name: str, wert: str, erlaubt: tuple[str, ...]) -> None:
    if wert not in erlaubt:
        raise ValueError(f"{name}: '{wert}' ist nicht zulässig. Erlaubt: {', '.join(erlaubt)}")


def format_entry(oid: str, titel: str, quelle: str, impact: str, haeufigkeit: str,
                 kategorie: str, kontext: str, beobachtung: str, bezug: str | None) -> str:
    """Baut einen formatgetreuen Eintrag. `Entscheidung/Maßnahme` ist bewusst nicht setzbar."""
    _pruefe("Impact", impact, IMPACT_WERTE)
    _pruefe("Häufigkeit", haeufigkeit, HAEUFIGKEIT_WERTE)
    _pruefe("Kategorie", kategorie, KATEGORIE_WERTE)
    if not titel.strip() or not beobachtung.strip():
        raise ValueError("Titel und Beobachtung dürfen nicht leer sein.")

    zeilen = [
        f"## {oid} – {titel.strip()}",
        f"- Quelle: {quelle.strip()}",
        "- Status: NEU",
        f"- Impact: {impact}    Häufigkeit: {haeufigkeit}",
        f"- Kategorie: {kategorie}    Kontext: {kontext.strip()}",
        f"- Beobachtung: {beobachtung.strip()}",
        f"- Entscheidung/Maßnahme: {KANON_OFFEN}",
    ]
    if bezug and bezug.strip():
        zeilen.append(f"- Bezug: {bezug.strip()}")
    return "\n".join(zeilen) + "\n"


def add(text: str, session: int, **felder) -> tuple[str, str]:
    """Hängt einen neuen Eintrag an. Liefert (neuer Dateiinhalt, vergebene ID)."""
    oid = next_id(text, session)
    eintrag = format_entry(oid, **felder)
    return text.rstrip("\n") + "\n\n" + eintrag, oid


def set_fields(text: str, oid: str, status: str | None = None,
               entscheidung: str | None = None) -> str:
    """Ersetzt Status und/oder Entscheidung eines bestehenden Eintrags."""
    span = entry_spans(text).get(oid)
    if not span:
        raise ValueError(f"{oid} existiert nicht in {OBS_FILE}.")

    block = text[span[0]:span[1]]
    for feld, wert in (("Status", status), ("Entscheidung/Maßnahme", entscheidung)):
        if wert is None:
            continue
        muster = re.compile(rf"^- {re.escape(feld)}:.*$", re.M)
        if not muster.search(block):
            raise ValueError(f"{oid} hat kein Feld `- {feld}:` – Datei von Hand prüfen.")
        block = muster.sub(f"- {feld}: {wert}", block, count=1)

    return text[:span[0]] + block + text[span[1]:]


def laufende_session(root: Path | None = None) -> int:
    """Nummer der laufenden Session (Mechanik: `obs_parse.running_session`)."""
    session = running_session(root or repo_root())
    if session is None:
        raise ValueError("Session-Nummer nicht bestimmbar – docs/history/sessions/ fehlt.")
    return session

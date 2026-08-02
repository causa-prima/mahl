"""Lesen und Schreiben einzelner Learnings in `docs/kaizen/lessons_learned.md`.

Gleiche Begründung wie `obs_entry.py`: Ein Learning wird in nahezu jeder Session geschrieben,
und wer die Datei ändert, muss sie vorher lesen. Über `add()` entsteht der Eintrag stattdessen
formatgetreu aus geprüften Argumenten.

Format-Kopplung: `## Session NNN – YYYY-MM-DD`, darunter je Learning ein Bullet
`- **[IMPACT] [KATEGORIE] [KONTEXT] LL-S<NNN>-<n> – Titel**` mit den eingerückten Zeilen
`Quelle:` / `Was:` / `Warum:` / `Regel:`. Kanonisch im Header der Datei festgelegt; `jenga_score.py`
und `retro_report.py` parsen dieselbe Struktur – Reihenfolge und Klammerform nicht ändern.
"""
import re
from datetime import date
from pathlib import Path

from obs_parse import repo_root, running_session

LL_FILE = "docs/kaizen/lessons_learned.md"

IMPACT_WERTE = ("KRITISCH", "HOCH", "MITTEL", "GERING")
KATEGORIE_WERTE = ("PROZESS", "AGENT", "QUALITÄT", "TOOLING")

_BULLET = re.compile(r"^- \*\*\[[^\]]+\] \[[^\]]+\] \[[^\]]+\] (LL-S\d+-\d+)", re.M)
_SESSION_HEADING = re.compile(r"^## Session (\d+)\b.*$", re.M)


def ll_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / LL_FILE


def entry_spans(text: str) -> dict[str, tuple[int, int]]:
    """LL-ID → (Start, Ende) im Text. Ein Eintrag endet vor der nächsten Leerzeile gefolgt
    von einem Bullet oder einer Überschrift – praktisch: vor dem nächsten Bullet/`## `."""
    treffer = list(_BULLET.finditer(text))
    spans = {}
    for i, match in enumerate(treffer):
        # Ein Eintrag endet am nächsten Bullet ODER an der nächsten Session-Überschrift –
        # je nachdem was früher kommt. Ohne die Überschrift schluckt der letzte Eintrag einer
        # Session die Überschrift der folgenden mit.
        grenzen = [len(text)]
        if i + 1 < len(treffer):
            grenzen.append(treffer[i + 1].start())
        if (naechste := _SESSION_HEADING.search(text, match.end())):
            grenzen.append(naechste.start())
        spans[match.group(1)] = (match.start(), min(grenzen))
    return spans


def get(text: str, lid: str) -> str | None:
    span = entry_spans(text).get(lid)
    return text[span[0]:span[1]].rstrip() if span else None


def next_id(text: str, session: int) -> str:
    belegt = [
        int(m.group(1))
        for lid in entry_spans(text)
        if (m := re.fullmatch(rf"LL-S0*{session}-(\d+)", lid))
    ]
    return f"LL-S{session:03d}-{max(belegt, default=0) + 1}"


def _pruefe(name: str, wert: str, erlaubt: tuple[str, ...]) -> None:
    if wert not in erlaubt:
        raise ValueError(f"{name}: '{wert}' ist nicht zulässig. Erlaubt: {', '.join(erlaubt)}")


def format_entry(lid: str, titel: str, impact: str, kategorie: str, kontext: str,
                 quelle: str, was: str, warum: str, regel: str) -> str:
    """Baut einen formatgetreuen Learning-Bullet."""
    _pruefe("Impact", impact, IMPACT_WERTE)
    _pruefe("Kategorie", kategorie, KATEGORIE_WERTE)
    for name, wert in (("Titel", titel), ("Was", was), ("Warum", warum), ("Regel", regel)):
        if not wert.strip():
            raise ValueError(f"{name} darf nicht leer sein.")

    return (
        f"- **[{impact}] [{kategorie}] [{kontext.strip()}] {lid} – {titel.strip()}**\n"
        f"  Quelle: {quelle.strip()}\n"
        f"  Was: {was.strip()}\n"
        f"  Warum: {warum.strip()}\n"
        f"  Regel: {regel.strip()}\n"
    )


def session_heading_span(text: str, session: int) -> tuple[int, int] | None:
    """(Start, Ende) des Abschnitts dieser Session – Ende = vor der nächsten Überschrift."""
    for match in _SESSION_HEADING.finditer(text):
        if int(match.group(1)) != session:
            continue
        naechste = _SESSION_HEADING.search(text, match.end())
        return match.start(), naechste.start() if naechste else len(text)
    return None


def add(text: str, session: int, heute: str | None = None, **felder) -> tuple[str, str]:
    """Hängt ein Learning an den Abschnitt dieser Session an (legt ihn bei Bedarf an)."""
    lid = next_id(text, session)
    bullet = format_entry(lid, **felder)
    span = session_heading_span(text, session)

    if span is None:
        datum = heute or date.today().isoformat()
        neu = f"{text.rstrip(chr(10))}\n\n## Session {session} – {datum}\n\n{bullet}"
        return neu, lid

    start, ende = span
    abschnitt = text[start:ende].rstrip("\n")
    return text[:start] + abschnitt + "\n\n" + bullet + text[ende:], lid


def laufende_session(root: Path | None = None) -> int:
    """Nummer der laufenden Session (Mechanik: `obs_parse.running_session`)."""
    session = running_session(root or repo_root())
    if session is None:
        raise ValueError("Session-Nummer nicht bestimmbar – docs/history/sessions/ fehlt.")
    return session

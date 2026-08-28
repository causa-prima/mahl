#!/usr/bin/env python3
"""Erlaubte Kontext-Tags – eine Quelle für Schreibpfad und Bestandsprüfung.

Die Tag-Liste lebt in `docs/kaizen/process.md`, Abschnitt `## Kontext-Tags`, und wird von
dort **gelesen** statt im Code dupliziert: `obs.py`/`lessons.py` validieren neue Einträge
gegen sie (Meldung im Moment der Entstehung), `retro_report.py` prüft mit derselben Liste
den Bestand inklusive der von Hand gepflegten `countermeasures.md` (Meldung für alles, was
an keinem Script vorbeikam). Ein neuer Tag entsteht damit durch Ergänzen der Tabelle, nicht
durch einen Code-Edit.

Warum überhaupt geprüft wird: `retro_report.py` clustert Findings auf dem Tripel
Impact/Kategorie/Kontext und ordnet Countermeasures über `cm.kontexte` zu. Ein Tag außerhalb
der Liste kann mit nichts zusammenfallen – der Eintrag zählt in der Statistik mit, bildet
aber nie ein Muster, und eine so getaggte CM deckt über diesen Tag nie ein Finding ab.
Der Ausfall ist still: Nichts schlägt fehl, es fehlt nur ein Treffer (OBS-S116-4).
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repo_kontext import repo_root  # noqa: E402

PROCESS_FILE = "docs/kaizen/process.md"
_ABSCHNITT = re.compile(r"^## Kontext-Tags\s*$(.*?)^## ", re.M | re.S)
_ZEILE = re.compile(r"^\|\s*`([^`]+)`\s*\|", re.M)

# Platzhalter aus Format-Vorlagen (Datei-Header, Archiv-Header). Sie stehen in den
# Dokumenten als Ausfüllhilfe und sind keine Verstöße.
PLATZHALTER = frozenset({"KONTEXT", "–", "-", "", "<Tags oder –>",
                         "<Kontext-Tag wie in lessons_learned>"})


class TabelleFehlt(RuntimeError):
    """Die Tag-Tabelle ist nicht auffindbar oder leer.

    Eigener Fehler statt einer leeren Liste: Ein Prüfer, der nichts zu prüfen hat, meldet
    nie einen Verstoß und fällt damit lautlos aus – genau der Zustand, den er verhindern soll.
    """


def process_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / PROCESS_FILE


def erlaubte(root: Path | None = None) -> tuple[str, ...]:
    """Die Tags aus der Tabelle in `process.md`, in Dokumentreihenfolge."""
    pfad = process_path(root)
    try:
        text = pfad.read_text(encoding="utf-8")
    except OSError as fehler:
        raise TabelleFehlt(f"{pfad} nicht lesbar: {fehler}") from fehler

    abschnitt = _ABSCHNITT.search(text)
    if abschnitt is None:
        raise TabelleFehlt(f"Abschnitt '## Kontext-Tags' fehlt in {pfad}")
    tags = tuple(_ZEILE.findall(abschnitt.group(1)))
    if not tags:
        raise TabelleFehlt(f"Abschnitt '## Kontext-Tags' in {pfad} enthält keine Tag-Zeilen")
    return tags


def zerlege(rohwert: str) -> list[str]:
    """Kontext-Feld → einzelne Tags. Mehrfach-Tags sind kommasepariert (CM-Format)."""
    return [t.strip() for t in rohwert.split(",") if t.strip()]


def unbekannte(rohwert: str, erlaubt: tuple[str, ...]) -> list[str]:
    """Die Tags aus `rohwert`, die weder erlaubt noch Platzhalter sind."""
    return [t for t in zerlege(rohwert) if t not in erlaubt and t not in PLATZHALTER]

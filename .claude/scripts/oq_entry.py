#!/usr/bin/env python3
"""Einzelne offene Fragen in `docs/open-questions.md` lesen, erfassen, ändern, löschen.

Warum (OBS-S120-1): `open-questions.md` war der einzige der fünf Eintrags-Tracker ohne
Pflege-Werkzeug – `open_questions.py` ist ein reines Import-Modul (`parse`/`due`) für die
Session-Agenda und hat keine CLI. Für das Entfernen eines erledigten Eintrags entstanden
deshalb zweimal Wegwerf-Scripte, bei drei Löschungen in der gesamten Projekthistorie.

Das **Löschen** ist hier die teure Operation, nicht das Anlegen – anders als bei
`observations.md`/`lessons_learned.md`, wo Erledigtes archiviert statt entfernt wird. Diese
Datei ist ein Zustandsdokument: Mit der Entscheidung verlässt der Eintrag sie ersatzlos
(`principles.md`, „Zustandsdokumente tragen nur den offenen Zustand").

Struktur und Mechanik liegen in `tracker_entry.py` – geteilt mit `td_entry.py`, weil beide
Dateien bis auf Feldnamen und Prüfung identisch aufgebaut sind. Hier bleibt nur, was
wirklich OQ-eigen ist: die Feldnamen und die `Fällig`-Anker-Prüfung. Diese wird
**wiederverwendet, nicht kopiert** – `td_anchors.validiere` ist dieselbe Prüfung, die
`check-oq-capture.py` zur Schreibzeit fährt; ohne sie erzeugte dieses Modul Einträge, die
der Hook anschließend blockt.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import td_anchors  # noqa: E402
import tracker_entry as te  # noqa: E402
from obs_parse import repo_root, running_session  # noqa: E402

OQ_FILE = "docs/open-questions.md"

SPEC = te.TrackerSpec(datei=OQ_FILE, praefix="OQ",
                      felder=("Frage", "Fällig", "Hintergrund"))

FELDER_EIGENE_ZEILE = SPEC.felder


def oq_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / OQ_FILE


def entry_spans(text: str) -> dict[str, tuple[int, int]]:
    return te.entry_spans(SPEC, text)


def get(text: str, oid: str) -> str | None:
    return te.get(SPEC, text, oid)


def next_id(text: str, session: int) -> str:
    return te.next_id(SPEC, text, session)


def pruefe_wohlgeformt(oid: str, block: str) -> None:
    te.pruefe_wohlgeformt(SPEC, oid, block)


def _pruefe_anker(oid: str, faellig: str, root: Path | None = None) -> None:
    """Dieselbe Prüfung wie `check-oq-capture.py`."""
    try:
        ktx = td_anchors.lade_kontext(root or repo_root())
    except Exception:  # noqa: BLE001 – ohne Kontext bleibt die syntaktische Prüfung
        ktx = td_anchors.Kontext()
    fehler = td_anchors.validiere(oid, faellig, ktx)
    if fehler:
        raise ValueError(
            f"{oid}: `Fällig` trägt nicht – " + "; ".join(fehler)
            + f". Grammatik: .claude/scripts/td_anchors.py, Vorlage im Header von {OQ_FILE}.")


def format_entry(oid: str, titel: str, frage: str, faellig: str, hintergrund: str,
                 root: Path | None = None) -> str:
    _pruefe_anker(oid, faellig, root)
    return te.format_entry(SPEC, oid, titel,
                           {"Frage": frage, "Fällig": faellig, "Hintergrund": hintergrund})


def add(text: str, session: int, root: Path | None = None, *, titel: str, frage: str,
        faellig: str, hintergrund: str) -> tuple[str, str]:
    """Hängt eine neue Frage unten an. Liefert (neuer Dateiinhalt, vergebene ID)."""
    _pruefe_anker(te.next_id(SPEC, text, session), faellig, root)
    return te.add(SPEC, text, session, titel,
                  {"Frage": frage, "Fällig": faellig, "Hintergrund": hintergrund})


def set_fields(text: str, oid: str, frage: str | None = None, faellig: str | None = None,
               hintergrund: str | None = None, root: Path | None = None) -> str:
    if faellig is not None:
        _pruefe_anker(oid, faellig, root)
    werte = {f: w for f, w in (("Frage", frage), ("Fällig", faellig),
                               ("Hintergrund", hintergrund)) if w is not None}
    return te.set_fields(SPEC, text, oid, werte)


def remove(text: str, oid: str) -> str:
    return te.remove(SPEC, text, oid)


def laufende_session(root: Path | None = None) -> int:
    """Nummer der laufenden Session (Mechanik: `obs_parse.running_session`)."""
    return running_session(root or repo_root())

#!/usr/bin/env python3
"""Fällige offene Fragen aus `docs/open-questions.md`.

Bis S116 hing diese Logik in `obs-drain.py` – angehängt, weil dort der einzige
Session-Start-Vorlage-Mechanismus lag. Mit `session-agenda.py` gibt es einen Träger, dem
offene Fragen als eigenes Modul gehören: Sie sind ein anderer Tracker mit anderem Ausgang
(mit dem User klären, nicht im Drain entscheiden) und haben in einem OBS-Script nichts zu
suchen.

Warum es den Mechanismus überhaupt braucht (S115): `open-questions.md` hatte als einziger
Tracker keinen Lese-Trigger – sämtliche Verweise darauf waren Schreib-Verweise („dort
eintragen"), kein Prozessschritt legte Fragen vor. Folge im Bestand: vier Fragen lagen
14–25 Sessions unbeantwortet, und eine davon (Taxonomie ADR vs. Tech-Debt) wurde mehrfach
ad hoc neu verhandelt, ohne dass die offene Frage konsultiert wurde.
"""
import re

OQ_FILE = "docs/open-questions.md"
STALE = 10   # ohne Termin gilt eine Frage ab diesem Alter als überaltert → vorlegen
MAX = 3      # Deckel: der Session-Start-Block soll nicht von Fragen überschwemmt werden

_HEADER_RE = re.compile(r"^## (OQ-S(\d{3})-\d+)\s+[—–-]\s+(.+)$", re.M)
_FAELLIG_RE = re.compile(r"^\*\*Fällig:\*\*\s*S(\d+)", re.M)


def parse(text: str) -> list[dict]:
    """Einträge als (id, session, title, faellig).

    `Fällig: S<NNN>` ist optional – fehlt es, entscheidet das Alter (s. `due`).
    """
    treffer = list(_HEADER_RE.finditer(text))
    fragen = []
    for i, m in enumerate(treffer):
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
        termin = _FAELLIG_RE.search(text[m.end():ende])
        fragen.append({
            "id": m.group(1),
            "session": int(m.group(2)),
            "title": m.group(3).strip(),
            "faellig": int(termin.group(1)) if termin else None,
        })
    return fragen


def due(fragen: list[dict], cur: int | None) -> list[dict]:
    """Vorzulegende Fragen: Termin erreicht – oder ohne Termin überaltert. Älteste zuerst.

    Ein gesetzter Termin unterdrückt die Alters-Regel: Sonst wäre eine bewusst weit geparkte
    Frage trotzdem sofort fällig, und der Termin damit wirkungslos.
    """
    if cur is None:
        return []

    def ist_faellig(f: dict) -> bool:
        if f["faellig"] is not None:
            return f["faellig"] <= cur
        return cur - f["session"] >= STALE

    return sorted(filter(ist_faellig, fragen), key=lambda f: f["session"])[:MAX]

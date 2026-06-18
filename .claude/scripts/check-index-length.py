#!/usr/bin/env python3
"""Prüft die Kurzfassungs-Länge der Einträge in docs/history/sessions/index.md.

Hintergrund: Die Index-Einträge waren über die Sessions hinweg immer länger
geworden (Verbosity-Ratchet, OBS-S085-9). Regel (siehe closing-session SKILL Schritt 6):
die Kurzfassung (letzte Tabellenspalte) ist ein Satz – *was* sich geändert hat,
kein „warum". Soft-Ziel ~150, harter Cap 250 Zeichen.

Misst die **letzte Tabellenspalte** (Kurzfassung) jeder Daten-Zeile, nicht die ganze
Zeile (Nr./Datum/Phase zählen nicht zum Budget).

Grandfathering: Die Regel gilt vorwärts. Hart erzwungen wird nur der **neueste** Eintrag
(oberste Daten-Zeile – den fügt closing-session gerade hinzu). Ältere Überschreitungen
werden nur informativ gelistet (History ist read-only).

Exit-Code: 0 = neuester Eintrag ≤ HARD_CAP, 1 = neuester Eintrag verletzt den Cap.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _index_length import HARD_CAP, SOFT_TARGET, summary_cell  # noqa: E402

_REPO_ROOT = os.environ.get(
    "CLAUDE_PROJECT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
)
_INDEX_FILE = os.path.join(_REPO_ROOT, "docs", "history", "sessions", "index.md")


def main() -> None:
    try:
        with open(_INDEX_FILE, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as exc:
        print(f"FEHLER: {_INDEX_FILE} nicht lesbar ({exc}).")
        sys.exit(1)

    newest: tuple[int, int, str] | None = None  # (zeilennr, länge, session) – oberste Daten-Zeile
    historical: list[tuple[int, int, str]] = []  # ältere Überschreitungen (nur informativ)
    for i, line in enumerate(lines, start=1):
        cell = summary_cell(line)
        if cell is None:
            continue
        session = line.strip().strip("|").split("|")[0].strip()
        rec = (i, len(cell), session)
        if newest is None:
            newest = rec
        elif len(cell) > HARD_CAP:
            historical.append(rec)

    if newest is None:
        print(f"index.md: keine Daten-Zeilen gefunden ({_INDEX_FILE}).")
        sys.exit(1)

    if historical:
        print(f"Hinweis: {len(historical)} ältere Einträge über {HARD_CAP} (grandfathered, read-only History):")
        for zeile, laenge, session in historical:
            print(f"  Zeile {zeile} (Session {session}): {laenge} Zeichen")
        print()

    _, laenge, session = newest
    if laenge > HARD_CAP:
        print(f"VERLETZUNG: neuester Eintrag (Session {session}) {laenge} > {HARD_CAP} Zeichen.")
        print("Regel: ein Satz – was sich aenderte, kein Warum. Details: closing-session SKILL Schritt 6.")
        sys.exit(1)

    print(f"OK – neuester Eintrag (Session {session}) {laenge} Zeichen ≤ {HARD_CAP} (Soft-Ziel {SOFT_TARGET}).")
    sys.exit(0)


if __name__ == "__main__":
    main()

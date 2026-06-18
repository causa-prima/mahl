"""Geteilte Logik für den Index-Kurzfassungs-Längen-Check (OBS-S085-9).

Single source für Cap-Werte + Zeilen-Parsing. Genutzt von:
- `.claude/scripts/check-index-length.py` (CLI-Report, in closing-session)
- `.claude/hooks/check-index-length.py` (PreToolUse-Hook, blockiert zu lange Einträge)

Gemessen wird die letzte Tabellenspalte (Kurzfassung) einer Daten-Zeile, nicht die
ganze Zeile (Nr./Datum/Phase zählen nicht zum Budget).
"""

SOFT_TARGET = 150
HARD_CAP = 300


def summary_cell(line: str) -> str | None:
    """Kurzfassungs-Zelle einer Tabellen-Daten-Zeile, sonst None.

    Daten-Zeile = beginnt mit '|', erste Zelle ist eine Zahl (Session-Nr.).
    Trenn-Zeile (|---|) und Header (| # | Datum | ...) fallen raus.
    """
    if not line.lstrip().startswith("|"):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 4 or not cells[0].isdigit():
        return None
    return cells[-1]


def session_of(line: str) -> str:
    """Session-Nummer (erste Zelle) einer Daten-Zeile als String."""
    return line.strip().strip("|").split("|")[0].strip()


def table_rows(text: str):
    """Yield (raw_stripped_line, session, kurzfassungs_länge) je Daten-Zeile in text."""
    for line in text.splitlines():
        cell = summary_cell(line)
        if cell is not None:
            yield line.strip(), session_of(line), len(cell)

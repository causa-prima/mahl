#!/usr/bin/env python3
"""repo_kontext.py – Auskunft über das Repo, in dem gerade gearbeitet wird: wo liegt es,
welche Session läuft.

Konsumenten sind die Erfassungswerkzeuge aller Tracker und jedes weitere Werkzeug, das die
Repo-Wurzel oder die laufende Session braucht – deshalb ein eigenes Modul und keines davon als
Wirt.

Die Session-Nummer hängt an der Git-Historie: Der Abschluss-Commit einer Session trägt den
Trailer `Session-Ende: <NNN>` (geschrieben von `closing-session`), und das ist das einzige
Merkmal für „abgeschlossen". Zwischen-Commits tragen ihn nicht – ein Commit gehört zu der
Session, deren `Session-Ende`-Marke als nächste folgt.
"""
import re
import subprocess
import sys
from pathlib import Path

# Merkmal des Abschluss-Commits. GREP geht an git (Zeilen-Anker wirken dort dank REG_NEWLINE),
# RE prüft die Fundstelle noch einmal in Python – git filtert Commits, nicht Zeilen.
TRAILER_GREP = r"^Session-Ende: [0-9]+$"
TRAILER_RE = r"^Session-Ende:\s*(\d+)\s*$"

# Alt-Historie: Bis S125 trug jeder Session-Commit seine Nummer im Betreff. Reiner Rückfallpfad,
# keine zweite lebende Konvention – neue Commits führen das Präfix nicht mehr.
BETREFF_GREP = r"^Session [0-9]+:"
BETREFF_RE = r"^Session\s+(\d+):"

# Der Rückfall meldet sich einmal je Prozess. `session-agenda.py` fragt die Nummer mehrfach an;
# viermal dieselbe Zeile liest sich wie vier Befunde.
_betreff_gewarnt = False


def repo_root() -> Path:
    # Modul liegt in prozesscode/ -> eine Ebene hoch ist der Repo-Root.
    return Path(__file__).resolve().parents[1]


def _session_nummern(root: Path, grep: str, muster: str, format_: str) -> list[int]:
    """Session-Nummern aus allen Commit-Nachrichten, die `grep` treffen. Leer, wenn git nicht
    läuft (kein Repo, kein git im Pfad) – was das bedeutet, entscheidet der Aufrufer."""
    try:
        ergebnis = subprocess.run(
            ["git", "log", "-E", "--grep", grep, f"--format={format_}"],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if ergebnis.returncode != 0:
        return []
    return [int(m.group(1)) for m in re.finditer(muster, ergebnis.stdout, flags=re.M)]


def abgeschlossene_sessions(root: Path) -> list[int]:
    """Nummern aller Sessions mit Abschluss-Commit. Basis für `current_session` und für die
    Vergabe-Prüfung im `commit-msg`-Hook (die nächste Nummer ist max + 1)."""
    return _session_nummern(root, TRAILER_GREP, TRAILER_RE, "%B")


def current_session(root: Path):
    """Nummer der LAUFENDEN Session = höchste abgeschlossene + 1.

    Eine Session darf mehrfach committen, aber nur einer dieser Commits beendet sie – deshalb
    zählt der Trailer und nicht, wie viele Commits eine Nummer nennen.

    Rückfall auf die Betreffzeile: die Alt-Historie vor S126 und der Fall „Session ohne
    `closing-session` abgeschlossen". Der Rückfall kann die beiden Commit-Arten nicht
    unterscheiden und meldet sich deshalb hörbar.

    None, wenn gar kein Session-Commit auffindbar ist (Nummer unbestimmbar, kein 0-Sentinel).
    """
    if enden := abgeschlossene_sessions(root):
        return max(enden) + 1
    if betreffe := _session_nummern(root, BETREFF_GREP, BETREFF_RE, "%s"):
        global _betreff_gewarnt  # noqa: PLW0603 – ein Prozess, eine Meldung
        if not _betreff_gewarnt:
            _betreff_gewarnt = True
            print(f"WARNUNG: kein Commit mit Trailer 'Session-Ende: <NNN>' – Session-Nummer aus "
                  f"der Betreffzeile abgeleitet (S{max(betreffe)} + 1). Trägt ein Zwischen-Commit "
                  f"denselben Betreff, ist sie um eins zu hoch.", file=sys.stderr)
        return max(betreffe) + 1
    return None

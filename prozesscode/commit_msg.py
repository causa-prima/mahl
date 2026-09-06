#!/usr/bin/env python3
"""commit_msg.py – Form des Abschluss-Commits prüfen. Läuft als git-`commit-msg`-Hook.

Der Trailer `Session-Ende: <NNN>` markiert das Ende einer Session und ist die Quelle jeder
Tracker-ID (`repo_kontext.current_session`). Eine vertippte, doppelte oder falsch nummerierte
Marke bricht die Ableitung still – deshalb prüft der Hook die Marke selbst und nicht bloß
Längen. Nicht jeder Commit beendet eine Session: Ohne Trailer werden nur Betreff-Regeln geprüft.

Der Hook läuft über `core.hooksPath` (s. `hooks/commit-msg`), also bei JEDEM Commit – auch bei
einem von Hand getippten. Ein PreToolUse-Hook auf `git commit` sähe nur die Kommandozeile und
ginge bei `-F`, Editor-Eingabe oder Heredoc-Varianten ins Leere.

Aufruf: `python3 -m prozesscode.commit_msg <nachrichtendatei>` – exit 1 blockiert den Commit.
Einzelfall-Ausnahme von der Nummernprüfung: `session-ok` in der Nachricht.
"""
import re
import subprocess
import sys
from pathlib import Path

from .repo_kontext import TRAILER_RE, current_session, repo_root

BETREFF_MAX = 72  # Git-Konvention: `--oneline` und Weboberflächen kürzen darüber hinaus.
MARKER = "session-ok"

# Zeile, die eine Marke sein WILL, es aber nicht ist: eingerückt, mit Leerzeichen statt
# Bindestrich, mit Text dahinter. Nur relevant, solange keine gültige Marke existiert.
VERDACHT_RE = re.compile(r"^\s*Session[-\s]?Ende\s*:", re.IGNORECASE)
SCHERE = "# ------------------------ >8 ------------------------"


def nutztext(roh: str) -> str:
    """Kommentarzeilen und den `--verbose`-Diff entfernen – git hängt beides an die Vorlage."""
    ohne_diff = roh.split(SCHERE)[0]
    return "\n".join(z for z in ohne_diff.split("\n") if not z.startswith("#"))


def befunde(roh: str, erwartete_session=None, head_session=None) -> list[str]:
    """Liste der Regelverstöße; leer heißt: Commit darf durch."""
    text = nutztext(roh)
    zeilen = text.split("\n")
    betreff = zeilen[0].strip() if zeilen else ""

    ergebnis = []
    if not betreff:
        ergebnis.append("Betreff fehlt – die erste Zeile ist leer.")
    elif len(betreff) > BETREFF_MAX:
        ergebnis.append(
            f"Betreff ist {len(betreff)} Zeichen lang, erlaubt sind {BETREFF_MAX} "
            f"(Git-Konvention: `--oneline` und Weboberflächen kürzen darüber hinaus)."
        )

    marken = [(i, int(m.group(1))) for i, z in enumerate(zeilen)
              if (m := re.match(TRAILER_RE, z))]
    if len(marken) > 1:
        ergebnis.append(
            f"`Session-Ende:` steht {len(marken)}-mal – erlaubt ist genau einmal. "
            "Nur ein Commit beendet eine Session."
        )
    if not marken:
        if any(VERDACHT_RE.match(z) for z in zeilen):
            ergebnis.append(
                "Eine Zeile sieht aus wie die Abschluss-Marke, trifft aber die Schreibweise "
                "nicht. Sie muss exakt `Session-Ende: <NNN>` lauten – eigene Zeile, keine "
                "Einrückung, nichts dahinter."
            )
        return ergebnis

    zeilen_index, nummer = marken[0]
    # Git parst ausschließlich den LETZTEN Absatz als Trailer-Block. Steht die Marke davor,
    # findet `--format='%(trailers:key=Session-Ende)'` sie nicht – die dokumentierten
    # Abrufbefehle lieferten dann still leer, während die grep-basierte Nummernableitung
    # weiterliefe. Genau diese Kombination fällt sonst niemandem auf.
    danach = zeilen[zeilen_index + 1:]
    while danach and not danach[-1].strip():   # abschließende Leerzeilen sind kein Absatz
        danach.pop()
    if any(not z.strip() for z in danach):
        ergebnis.append(
            "`Session-Ende:` steht nicht im letzten Absatz. Git erkennt nur den letzten "
            "Block als Trailer – davor ist die Marke per `%(trailers:…)` unsichtbar. "
            "Zu den übrigen Trailern (`Co-Authored-By:`) stellen, ohne Leerzeile dazwischen."
        )

    rumpf = [z for i, z in enumerate(zeilen[1:], start=1) if i != zeilen_index and z.strip()]
    if not rumpf:
        ergebnis.append(
            "Der Rumpf ist leer. Die Marke allein ist keine Session-Historie – es fehlt, "
            "was in dieser Session passierte und warum."
        )

    if MARKER in text or erwartete_session is None:
        return ergebnis
    if nummer != erwartete_session and nummer != head_session:
        ergebnis.append(
            f"`Session-Ende: {nummer}` – erwartet ist {erwartete_session}. Die Nummer zählt von "
            f"der letzten ABGESCHLOSSENEN Session weiter, nicht von der jüngsten bestehenden "
            f"Tracker-Serie. Bewusster Einzelfall → `{MARKER}` in die Nachricht."
        )
    return ergebnis


def _head_session(root: Path):
    """Nummer im HEAD-Commit – daran ist ein `--amend` erkennbar: Die Marke steht dort schon,
    erwartet wäre sonst bereits die Folge-Session."""
    try:
        ergebnis = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if ergebnis.returncode != 0:
        return None
    treffer = re.search(TRAILER_RE, ergebnis.stdout, flags=re.M)
    return int(treffer.group(1)) if treffer else None


def main() -> int:
    if len(sys.argv) != 2:
        print("Aufruf: commit_msg.py <nachrichtendatei>", file=sys.stderr)
        return 1
    root = repo_root()
    # `current_session` liefert None, wenn die Nummer nicht ableitbar ist – dann entfällt die
    # Nummernprüfung, die Form wird trotzdem geprüft.
    probleme = befunde(
        Path(sys.argv[1]).read_text(encoding="utf-8"),
        erwartete_session=current_session(root),
        head_session=_head_session(root),
    )
    if not probleme:
        return 0
    print("❌ Commit-Nachricht (Poka-Yoke):", file=sys.stderr)
    for problem in probleme:
        print(f"  - {problem}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

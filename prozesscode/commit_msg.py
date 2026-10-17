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
_GIT_TIMEOUT_S = 10
MARKER = "session-ok"

# Zeile, die eine Marke sein WILL, es aber nicht ist: eingerückt, mit Leerzeichen statt
# Bindestrich, mit Text dahinter. Nur relevant, solange keine gültige Marke existiert.
VERDACHT_RE = re.compile(r"^\s*Session[-\s]?Ende\s*:", re.IGNORECASE)
# Trailer-Zeile nach git: Schlüssel nur aus ASCII-Buchstaben, Ziffern und `-`. Strenger als git,
# das auch eingerückte Fortsetzungszeilen und – mit `Signed-off-by:` – gemischte Blöcke annimmt;
# unsere Trailer brauchen beides nicht.
TRAILER_ZEILE_RE = re.compile(r"^[A-Za-z0-9-]+\s*:")
SCHERE = "# ------------------------ >8 ------------------------"

_BETREFF_FEHLT = "Betreff fehlt – die erste Zeile ist leer."
_BETREFF_LANG = ("Betreff ist {laenge} Zeichen lang, erlaubt sind {maximum} "
                 "(Git-Konvention: `--oneline` und Weboberflächen kürzen darüber hinaus).")
_MEHRFACH = ("`Session-Ende:` steht {anzahl}-mal – erlaubt ist genau einmal. "
             "Nur ein Commit beendet eine Session.")
_VERTIPPT = ("Eine Zeile sieht aus wie die Abschluss-Marke, trifft aber die Schreibweise "
             "nicht. Sie muss exakt `Session-Ende: <NNN>` lauten – eigene Zeile, keine "
             "Einrückung, nichts dahinter.")
_NICHT_ZULETZT = ("`Session-Ende:` steht nicht im letzten Absatz. Git erkennt nur den letzten "
                  "Block als Trailer – davor ist die Marke per `%(trailers:…)` unsichtbar. "
                  "Zu den übrigen Trailern (`Co-Authored-By:`) stellen, ohne Leerzeile dazwischen.")
_KEIN_TRAILER = ("`{zeile}` im letzten Absatz ist kein Trailer – damit liest git den ganzen "
                 "Absatz als Fließtext, und `Session-Ende:` ist per `%(trailers:…)` unsichtbar. "
                 "Ein Schlüssel besteht nur aus ASCII-Buchstaben, Ziffern und `-`: umbenennen "
                 "oder die Zeile in den Rumpf verschieben.")
_RUMPF_LEER = ("Der Rumpf ist leer. Die Marke allein ist keine Session-Historie – es fehlt, "
               "was in dieser Session passierte und warum.")
_NUMMER_FALSCH = ("`Session-Ende: {nummer}` – erwartet ist {erwartet}. Die Nummer zählt von "
                  "der letzten ABGESCHLOSSENEN Session weiter, nicht von der jüngsten bestehenden "
                  "Tracker-Serie. Bewusster Einzelfall → `{marker}` in die Nachricht.")
_AUFRUF = "Aufruf: commit_msg.py <nachrichtendatei>"
_KOPF = "❌ Commit-Nachricht (Poka-Yoke):"


def nutztext(roh: str) -> str:
    """Kommentarzeilen und den `--verbose`-Diff entfernen – git hängt beides an die Vorlage."""
    ohne_diff = roh.split(SCHERE)[0]
    return "\n".join(z for z in ohne_diff.split("\n") if not z.startswith("#"))


def befunde(roh: str, erwartete_session=None, head_session=None) -> list[str]:
    """Liste der Regelverstöße; leer heißt: Commit darf durch."""
    text = nutztext(roh)
    zeilen = text.split("\n")
    betreff = zeilen[0].strip()

    ergebnis = []
    if not betreff:
        ergebnis.append(_BETREFF_FEHLT)
    elif len(betreff) > BETREFF_MAX:
        ergebnis.append(_BETREFF_LANG.format(laenge=len(betreff), maximum=BETREFF_MAX))

    marken = [(i, int(m.group(1))) for i, z in enumerate(zeilen)
              if (m := re.match(TRAILER_RE, z))]
    if len(marken) > 1:
        ergebnis.append(_MEHRFACH.format(anzahl=len(marken)))
    if not marken:
        if any(VERDACHT_RE.match(z) for z in zeilen):
            ergebnis.append(_VERTIPPT)
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
        ergebnis.append(_NICHT_ZULETZT)
    else:
        # Der erste Absatz ist für git der Titel, nie ein Trailer-Block – deshalb zählt der
        # Betreff mit, wenn die Marke ohne Leerzeile an ihm hängt.
        beginn = zeilen_index
        while beginn > 0 and zeilen[beginn - 1].strip():
            beginn -= 1
        fremd = [z for z in zeilen[beginn:zeilen_index] + danach if not TRAILER_ZEILE_RE.match(z)]
        if fremd:
            ergebnis.append(_KEIN_TRAILER.format(zeile=fremd[0]))

    rumpf = [z for i, z in enumerate(zeilen[1:], start=1) if i != zeilen_index and z.strip()]
    if not rumpf:
        ergebnis.append(_RUMPF_LEER)

    if MARKER in text or erwartete_session is None:
        return ergebnis
    if nummer != erwartete_session and nummer != head_session:
        ergebnis.append(_NUMMER_FALSCH.format(nummer=nummer, erwartet=erwartete_session,
                                              marker=MARKER))
    return ergebnis


def _head_session(root: Path):
    """Nummer im HEAD-Commit – daran ist ein `--amend` erkennbar: Die Marke steht dort schon,
    erwartet wäre sonst bereits die Folge-Session."""
    try:
        ergebnis = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            cwd=str(root), capture_output=True, text=True, timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    # Kein eigener Zweig für returncode ≠ 0: git schreibt den Fehler nach stderr, stdout bleibt leer.
    treffer = re.search(TRAILER_RE, ergebnis.stdout, flags=re.M)
    return int(treffer.group(1)) if treffer else None


def main() -> int:
    if len(sys.argv) != 2:
        print(_AUFRUF, file=sys.stderr)
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
    print(_KOPF, file=sys.stderr)
    for problem in probleme:
        print(f"  - {problem}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Übersicht über alle Eintrags-Tracker – ein Hilfe-Aufruf statt fünf.

Warum (OBS-S120-2): Das Projekt führt fünf Dokumente mit strukturierten Einträgen, und wer
einen anlegen wollte, musste erst wissen, welches Werkzeug für seine Datei zuständig ist und
welche Befehle es kennt – also `--help` fünfmal aufrufen. Diese Übersicht beantwortet beides
an einer Stelle.

**Bewusst ohne Delegation.** `tracker.py oq remove …` gibt es nicht: Ein zweiter Aufrufweg
für Schreibbefehle liefe an den `WRITE_ACCESS`-Mustern in `check-bash-permission.py` vorbei,
die auf `oq.py remove` und Geschwister passen. Jedes Muster müsste dann beide Formen kennen,
und ein vergessenes wäre ein stiller Freibrief auf ein versioniertes Projektdokument. Der
Bequemlichkeitsgewinn wäre ein Wort; der Preis eine verdoppelte Angriffsfläche.

Die Befehlsliste wird **abgefragt, nicht gepflegt**: `tracker.py` liest sie aus dem `--help`
der Scripte selbst. Eine hier gepflegte Kopie wäre nach dem ersten neuen Unterbefehl falsch,
ohne dass es auffiele.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent

# Datei, Werkzeug, wofür sie da ist (Aufnahmebedingung in einem Satz), Lebensende eines
# Eintrags. Die Abgrenzung untereinander steht kanonisch in CLAUDE.md.
TRACKER = [
    ("docs/kaizen/observations.md", "obs.py",
     "Vorausschauende Beobachtung: wie das System besser wäre (Prozess)",
     "wird im Drain entschieden, dann archiviert"),
    ("docs/kaizen/lessons_learned.md", "lessons.py",
     "Konkreter schlechter Ausgang, der schon eingetreten ist (Prozess)",
     "bleibt, wird zur Retro archiviert"),
    ("docs/history/adr.md", "decisions.py",
     "Entschiedene Sache am Produkt, die weiter zu erklären ist",
     "bleibt als `Superseded` stehen"),
    ("docs/tech-debt.md", "td.py",
     "Entschiedene Sache am Produkt, die mit der Behebung ersatzlos verschwindet",
     "wird gelöscht"),
    ("docs/open-questions.md", "oq.py",
     "Noch nicht entschiedene Frage am Produkt, mit dem User zu klären",
     "wird gelöscht"),
]

_UNTERBEFEHL = re.compile(r"^\s{2,}\{([a-z,\-]+)\}", re.M)


def befehle(script: str) -> str:
    """Die Unterbefehle eines Tracker-Scripts – aus seinem eigenen `--help` gelesen."""
    pfad = HIER / script
    if not pfad.exists():
        return "—"
    try:
        proc = subprocess.run([sys.executable, str(pfad), "--help"],
                              capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return "?"
    treffer = _UNTERBEFEHL.search(proc.stdout)
    return treffer.group(1).replace(",", " ") if treffer else "—"


def main() -> int:
    argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    ).parse_args()

    zeilen = [(datei, script, befehle(script), zweck, ende)
              for datei, script, zweck, ende in TRACKER]
    b_breite = max(len(z[2]) for z in zeilen)

    print("\nEintrags-Tracker – wer ist wofür zuständig\n")
    for datei, script, cmds, zweck, ende in zeilen:
        print(f"  {script:<14} {datei}")
        print(f"    Wofür:    {zweck}")
        print(f"    Erledigt: {ende}")
        print(f"    Befehle:  {cmds:<{b_breite}}   (Details: python3 "
              f".claude/scripts/{script} --help)")
        print()

    print("Gemeinsame Grammatik, soweit ein Tracker den Befehl führt:")
    print("  get <ID>…        Volltext eines Eintrags, ohne die Datei ganz zu lesen")
    print("  list             Übersicht aller Einträge")
    print("  add --…          Neuen Eintrag formatgetreu anlegen")
    print("  set <ID> --…     Felder eines bestehenden Eintrags ändern")
    print("  remove <ID>      Eintrag löschen – nur bei Trackern, aus denen Erledigtes "
          "verschwindet")
    print()
    print("Wohin gehört ein Eintrag? → CLAUDE.md, Sektion „Ablage: in welchen Tracker "
          "gehört dieser Eintrag?“")
    print("Prozess-Taxonomie (OBS/CM/LL) → docs/kaizen/process.md, „Wann gehört etwas "
          "wohin?“")
    print()
    print("Schreibende Aufrufe brauchen eine Freigabe und zeigen dabei den Eintrag im "
          "Klartext.")
    print("Dieses Werkzeug führt keine Schreibbefehle aus – es zeigt nur, welches Script "
          "welchen kennt.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

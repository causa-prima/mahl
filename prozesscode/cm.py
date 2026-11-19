#!/usr/bin/env python3
"""Maßnahmen (Countermeasures) einzeln abrufen und auflisten – lesen statt Volldatei.

Warum (OBS-S136-2): `countermeasures.md` ist mit rund 150 KB größer als die Read-Grenze; ein
Read zeigt nur den Anfang, und die Retro sah so im Maßnahmen-Review keinen BEWÄHRT-Eintrag.
Alle anderen Tracker haben ein Werkzeug mit `list`/`get` (`python3 -m prozesscode.tracker`) –
die Maßnahmen hatten nur einen grep-Sonderweg in closing-session.

**Nur lesend.** Maßnahmen entstehen und ändern sich in der Retro per Edit; ein Schreibweg
käme mit eigenem Format-Risiko und hat bisher keinen Bedarf.

**Eigener, toleranter Status-Leser** statt `retro_report.load_cm`: Dessen Muster kennt nur
OFFEN, IN UMSETZUNG, AKTIV und BEWÄHRT und überspringt Einträge mit anderem Status (OBSOLET)
still – für die Retro-Auswertung gewollt, für eine Liste ein stiller Verlust.

Beispiele:
  python3 -m prozesscode.cm list
  python3 -m prozesscode.cm list --status AKTIV
  python3 -m prozesscode.cm get CM-S102-3
"""
import argparse
import re
import sys
from pathlib import Path

from ._cli import Parser
from ._util import REPO_ROOT
from .retro_report import CM_HEADER_RE

CM_FILE = "docs/kaizen/countermeasures.md"

# Ein Eintrag endet vor der nächsten Überschrift jeder Ebene – auch vor dem nächsten
# Status-Abschnitt (`## Bewährte Maßnahmen`), der sonst am letzten Eintrag davor hinge.
_UEBERSCHRIFT = re.compile(r"^#{1,6}\s", re.M)
# Dasselbe Kopfzeilen-Muster wie die Retro-Auswertung, nur zeilenweise über die ganze Datei.
_KOPF = re.compile(CM_HEADER_RE.pattern, re.M)
_STATUS = re.compile(r"\*\*Status:\*\*\s*([^|*\n]+?)\s*\|")

_UNBEKANNT = "{cm_id} gibt es nicht. Vorhandene Maßnahmen: python3 -m prozesscode.cm list"
_KEINE = "Keine Maßnahme mit Status {status}."


def cm_path() -> Path:
    return REPO_ROOT / CM_FILE


def eintraege(text: str) -> list[tuple[str, str, str, str]]:
    """(ID, Titel, Status, Volltext) je Maßnahme, in Dateireihenfolge."""
    ergebnis = []
    for kopf in _KOPF.finditer(text):
        naechste = _UEBERSCHRIFT.search(text, kopf.end())
        block = text[kopf.start():naechste.start() if naechste else len(text)].rstrip()
        status = _STATUS.search(block)
        ergebnis.append((kopf.group("id"), kopf.group("titel").strip(),
                         status.group(1) if status else "?", block))
    return ergebnis


def cmd_list(args) -> int:
    alle = eintraege(cm_path().read_text(encoding="utf-8"))
    gewaehlt = [e for e in alle
                if args.status is None or e[2].upper() == args.status.upper()]
    if not gewaehlt:
        print(_KEINE.format(status=args.status), file=sys.stderr)
        return 1
    for cm_id, titel, status, _block in gewaehlt:
        # Breite für den längsten Status, den die Retro vergibt („IN UMSETZUNG").
        print(f"{cm_id:<11} {status:<12} {titel}")
    return 0


def cmd_get(args) -> int:
    for cm_id, _titel, _status, block in eintraege(cm_path().read_text(encoding="utf-8")):
        if cm_id == args.id:
            print(block)
            return 0
    print(_UNBEKANNT.format(cm_id=args.id), file=sys.stderr)
    return 1


def main() -> int:
    parser = Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="befehl", required=True)
    p_list = sub.add_parser("list", help="Alle Maßnahmen: ID, Status, Titel")
    p_list.add_argument("--status", help="nur diesen Status (AKTIV, BEWÄHRT, …)")
    p_list.set_defaults(fn=cmd_list)
    p_get = sub.add_parser("get", help="Eine Maßnahme im Volltext")
    p_get.add_argument("id", help="z.B. CM-S102-3")
    p_get.set_defaults(fn=cmd_get)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

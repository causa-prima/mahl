#!/usr/bin/env python3
"""Zugriff auf einzelne Learnings – lesen und erfassen.

Statt `docs/kaizen/lessons_learned.md` ganz zu lesen, um einen Eintrag zu sehen oder einen
neuen anzuhängen. Der neue Eintrag entsteht formatgetreu; `jenga_score.py` und
`retro_report.py` parsen dieselbe Struktur.

Beispiele:
  python3 .claude/scripts/lessons.py get LL-S113-1
  python3 .claude/scripts/lessons.py add --impact HOCH --kategorie PROZESS --kontext Doku \\
      --titel "…" --quelle User --was "…" --warum "…" --regel "…"
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lessons_entry import (  # noqa: E402
    IMPACT_WERTE,
    KATEGORIE_WERTE,
    add,
    get,
    laufende_session,
    ll_path,
)


def cmd_get(args) -> int:
    text = ll_path().read_text(encoding="utf-8")
    fehlend = []
    for i, lid in enumerate(args.ids):
        eintrag = get(text, lid)
        if eintrag is None:
            fehlend.append(lid)
            continue
        if i:
            print()
        print(eintrag)
    if fehlend:
        print(f"Nicht gefunden: {', '.join(fehlend)}", file=sys.stderr)
        return 1
    return 0


def cmd_add(args) -> int:
    path = ll_path()
    neu, lid = add(
        path.read_text(encoding="utf-8"),
        args.session or laufende_session(),
        titel=args.titel,
        impact=args.impact,
        kategorie=args.kategorie,
        kontext=args.kontext,
        quelle=args.quelle,
        was=args.was,
        warum=args.warum,
        regel=args.regel,
    )
    path.write_text(neu, encoding="utf-8")
    print(f"✓ {lid} erfasst.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Einzelne Learnings lesen und erfassen.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="befehl", required=True)

    p_get = sub.add_parser("get", help="Volltext eines oder mehrerer Learnings")
    p_get.add_argument("ids", nargs="+", metavar="LL-ID")
    p_get.set_defaults(func=cmd_get)

    p_add = sub.add_parser("add", help="neues Learning erfassen")
    p_add.add_argument("--titel", required=True)
    p_add.add_argument("--impact", required=True, choices=IMPACT_WERTE)
    p_add.add_argument("--kategorie", required=True, choices=KATEGORIE_WERTE)
    p_add.add_argument("--kontext", required=True,
                       help="z.B. TDD, C#-Code, TS-Code, Hook/Script, Review, Doku, Testing")
    p_add.add_argument("--quelle", required=True, help="User | Subagent | Orchestrator")
    p_add.add_argument("--was", required=True, help="Was ist passiert?")
    p_add.add_argument("--warum", required=True, help="Ursache.")
    p_add.add_argument("--regel", required=True, help="Destillierte Erkenntnis, imperativ.")
    p_add.add_argument("--session", type=int, help="überschreibt die erkannte Session-Nummer")
    p_add.set_defaults(func=cmd_add)

    args = parser.parse_args()
    try:
        sys.exit(args.func(args))
    except ValueError as fehler:
        print(f"✗ {fehler}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

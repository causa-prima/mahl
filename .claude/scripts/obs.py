#!/usr/bin/env python3
"""Zugriff auf einzelne OBS-Einträge – lesen, erfassen, beim Drain entscheiden.

Statt `docs/kaizen/observations.md` ganz zu lesen, um einen Eintrag zu sehen oder zu ändern.
Ein neu erfasster Eintrag entsteht dabei per Konstruktion formatgetreu – die Erfassungsregeln
werden nicht nachträglich geprüft, sondern sind nicht verletzbar.

Beispiele:
  python3 .claude/scripts/obs.py get OBS-S112-7
  python3 .claude/scripts/obs.py add --titel "…" --quelle User --impact MITTEL \\
      --haeufigkeit dauerhaft --kategorie PROZESS --kontext Doku --beobachtung "…"
  python3 .claude/scripts/obs.py set OBS-S114-1 --status "UMGESETZT (S114)" \\
      --entscheidung "Umgesetzt via …; verworfen wurde …"

Verwandt: `obs-drain.py` (Drain-Satz vorschlagen), `obs-archive.py` (aufgelöste Einträge
ins Archiv verschieben).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs_entry import (  # noqa: E402
    HAEUFIGKEIT_WERTE,
    IMPACT_WERTE,
    KATEGORIE_WERTE,
    add,
    append_beobachtung,
    get,
    laufende_session,
    obs_path,
    set_fields,
)


def cmd_get(args) -> int:
    text = obs_path().read_text(encoding="utf-8")
    fehlend = []
    for i, oid in enumerate(args.ids):
        eintrag = get(text, oid, mit_vorpraegung=args.vorpraegung)
        if eintrag is None:
            fehlend.append(oid)
            continue
        if i:
            print()
        print(eintrag)
    if fehlend:
        print(f"Nicht gefunden: {', '.join(fehlend)}", file=sys.stderr)
        return 1
    return 0


def cmd_add(args) -> int:
    path = obs_path()
    text = path.read_text(encoding="utf-8")
    neu, oid = add(
        text,
        args.session or laufende_session(),
        titel=args.titel,
        quelle=args.quelle,
        impact=args.impact,
        haeufigkeit=args.haeufigkeit,
        kategorie=args.kategorie,
        kontext=args.kontext,
        beobachtung=args.beobachtung,
        bezug=args.bezug,
        vorpraegung=args.vorpraegung,
    )
    path.write_text(neu, encoding="utf-8")
    print(f"✓ {oid} erfasst.")
    return 0


def cmd_set(args) -> int:
    if args.status is None and args.entscheidung is None and args.beobachtung_anhaengen is None:
        print("Nichts zu ändern – --status, --entscheidung und/oder "
              "--beobachtung-anhängen angeben.", file=sys.stderr)
        return 1
    path = obs_path()
    inhalt = path.read_text(encoding="utf-8")
    if args.status is not None or args.entscheidung is not None:
        inhalt = set_fields(inhalt, args.id,
                            status=args.status, entscheidung=args.entscheidung)
    if args.beobachtung_anhaengen is not None:
        inhalt = append_beobachtung(inhalt, args.id, args.beobachtung_anhaengen)
    path.write_text(inhalt, encoding="utf-8")
    geaendert = ", ".join(n for n, v in (("Status", args.status),
                                         ("Entscheidung", args.entscheidung),
                                         ("Beobachtung erweitert",
                                          args.beobachtung_anhaengen)) if v is not None)
    print(f"✓ {args.id}: {geaendert} aktualisiert.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Einzelne OBS-Einträge lesen und schreiben.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="befehl", required=True)

    p_get = sub.add_parser("get", help="Volltext eines oder mehrerer Einträge")
    p_get.add_argument("ids", nargs="+", metavar="OBS-ID")
    p_get.add_argument("--vorprägung", dest="vorpraegung", action="store_true",
                       help="das Feld `Vorprägung` mit ausgeben – erst NACH eigener "
                            "Kandidatenbildung abrufen (es enthält Lösungsideen und "
                            "Ursachenvermutungen, die die Bewertung prägen)")
    p_get.set_defaults(func=cmd_get)

    p_add = sub.add_parser("add", help="neuen Eintrag erfassen (Form garantiert)")
    p_add.add_argument("--titel", required=True)
    p_add.add_argument("--quelle", required=True,
                       help="User | Orchestrator | Subagent (auch kombiniert, z.B. 'User + Orchestrator')")
    p_add.add_argument("--impact", required=True, choices=IMPACT_WERTE)
    p_add.add_argument("--haeufigkeit", required=True, choices=HAEUFIGKEIT_WERTE)
    p_add.add_argument("--kategorie", required=True, choices=KATEGORIE_WERTE)
    p_add.add_argument("--kontext", required=True, help="Kontext-Tag, z.B. Doku, TDD, Hook/Script")
    p_add.add_argument("--beobachtung", required=True,
                       help="Was ist nicht ideal? Ausführlich – Lösungen gehören NICHT hierher, "
                            "die entstehen im Drain.")
    p_add.add_argument("--vorprägung", dest="vorpraegung", metavar="TEXT",
                       help="optional: was die Bewertung prägen würde – genannte Lösungen, "
                            "vermutete Ursachen, Analogieschlüsse. Wird erfasst, aber beim "
                            "normalen `get` nicht mitgelesen (nur als Hinweis)")
    p_add.add_argument("--bezug", help="optional: LL-/OBS-/CM-IDs")
    p_add.add_argument("--session", type=int, help="überschreibt die erkannte Session-Nummer")
    p_add.set_defaults(func=cmd_add)

    p_set = sub.add_parser("set", help="Status/Entscheidung eines Eintrags ändern (Drain)")
    p_set.add_argument("id", metavar="OBS-ID")
    p_set.add_argument("--status", help='z.B. "UMGESETZT (S114)", "VERWORFEN (Grund)", '
                                        '"IN BEOBACHTUNG bis S120"')
    p_set.add_argument("--entscheidung", help="gewählte Lösung + warum statt der Alternativen")
    p_set.add_argument("--beobachtung-anhängen", dest="beobachtung_anhaengen",
                       metavar="TEXT",
                       help="Text an die Beobachtung anhängen – für die Konsolidierung, wenn "
                            "dasselbe Problem an anderer Stelle erneut auftritt (statt einen "
                            "zweiten Eintrag anzulegen)")
    p_set.set_defaults(func=cmd_set)

    args = parser.parse_args()
    try:
        sys.exit(args.func(args))
    except ValueError as fehler:
        print(f"✗ {fehler}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

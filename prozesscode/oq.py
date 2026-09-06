#!/usr/bin/env python3
"""Zugriff auf einzelne offene Fragen – lesen, erfassen, ändern, löschen.

Statt `docs/open-questions.md` ganz zu lesen, um einen Eintrag zu sehen oder zu ändern, und
statt für jedes Löschen ein Wegwerf-Script zu schreiben (OBS-S120-1: zweimal geschehen bei
drei Löschungen insgesamt). Ein neuer Eintrag entsteht per Konstruktion formatgetreu, inkl.
der `Fällig`-Anker-Grammatik, die `check-oq-capture.py` sonst nachträglich blockt.

Befehle wie bei `obs.py` – dieselbe Grammatik für alle Tracker (`get`/`add`/`set`/`list`),
ergänzt um `remove`: Anders als OBS und Learnings ist `open-questions.md` ein
Zustandsdokument, aus dem Erledigtes verschwindet statt archiviert zu werden.

Beispiele:
  python3 -m prozesscode.oq list
  python3 -m prozesscode.oq get OQ-S094-1
  python3 -m prozesscode.oq add --titel "…" --frage "…" \\
      --faellig "Phase:V1 – warum jetzt noch nicht" --hintergrund "…"
  python3 -m prozesscode.oq set OQ-S094-1 --faellig "S140 – verschoben, weil …"
  python3 -m prozesscode.oq remove OQ-S094-1

Verwandt: `open_questions.py` (Fälligkeit für die Session-Agenda – nur lesend).
"""
import argparse
import os
import sys


from .oq_entry import (  # noqa: E402
    add,
    entry_spans,
    get,
    laufende_session,
    oq_path,
    remove,
    set_fields,
)

_HOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".claude", "hooks")


def _verweise(oid: str) -> tuple[list[str], str | None]:
    """Fundstellen, die auf `oid` zeigen – (Treffer, Warnung falls Prüfung ausfiel).

    Der Löschvorgang meldet sie SELBST, statt sie `check-dangling-refs.py` finden zu lassen:
    In S120 blockte der Hook den ersten Versuch, danach blieb der Eintrag versehentlich
    stehen, weil nach dem Bereinigen der Fundstellen niemand nachfasste. Wer vorher weiß,
    was hängt, räumt in einem Zug auf.
    """
    try:
        sys.path.insert(0, _HOOKS)
        from importlib import import_module
        refs = import_module("check-dangling-refs")
        treffer = refs.find_references([oid], oq_path())
        return [f"{pfad}:{zeile}: {text.strip()[:90]}" for pfad, zeile, text in treffer], None
    except Exception as fehler:  # noqa: BLE001 – Prüfung ist Zusatznutzen, kein Muss
        return [], f"Verweis-Prüfung nicht gelaufen ({fehler.__class__.__name__}); " \
                   f"check-dangling-refs.py entscheidet beim Schreiben."


def cmd_list(args) -> int:
    text = oq_path().read_text(encoding="utf-8")
    ids = list(entry_spans(text))
    if not ids:
        print("Keine offenen Fragen.")
        return 0
    for oid in ids:
        eintrag = get(text, oid) or ""
        titel = eintrag.splitlines()[0].split("—", 1)[-1].strip()
        termin = next((z.split("**Fällig:**", 1)[1].split("–")[0].strip()
                       for z in eintrag.splitlines() if z.startswith("**Fällig:**")), "–")
        print(f"{oid:<14} [{termin:<12}] {titel}")
    print(f"\n{len(ids)} offen.")
    return 0


def cmd_get(args) -> int:
    text = oq_path().read_text(encoding="utf-8")
    fehlend = []
    for i, oid in enumerate(args.ids):
        eintrag = get(text, oid)
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
    path = oq_path()
    text = path.read_text(encoding="utf-8")
    neu, oid = add(text, args.session or laufende_session(), titel=args.titel,
                   frage=args.frage, faellig=args.faellig, hintergrund=args.hintergrund)
    path.write_text(neu, encoding="utf-8")
    print(f"✓ {oid} angelegt.")
    return 0


def cmd_set(args) -> int:
    path = oq_path()
    text = path.read_text(encoding="utf-8")
    if not any((args.frage, args.faellig, args.hintergrund, args.titel)):
        print("Nichts zu ändern – mindestens ein Feld angeben.", file=sys.stderr)
        return 1
    neu = set_fields(text, args.id, frage=args.frage, faellig=args.faellig,
                     hintergrund=args.hintergrund, titel=args.titel)
    path.write_text(neu, encoding="utf-8")
    geaendert = [n for n, w in (("Titel", args.titel), ("Frage", args.frage),
                                ("Fällig", args.faellig),
                                ("Hintergrund", args.hintergrund)) if w]
    print(f"✓ {args.id}: {', '.join(geaendert)} aktualisiert.")
    return 0


def cmd_remove(args) -> int:
    path = oq_path()
    text = path.read_text(encoding="utf-8")
    if get(text, args.id) is None:
        print(f"{args.id} existiert nicht.", file=sys.stderr)
        return 1

    treffer, warnung = _verweise(args.id)
    if treffer and not args.trotz_verweisen:
        print(f"{args.id} wird noch referenziert – erst die Fundstellen bereinigen "
              f"(oder --trotz-verweisen, wenn der Verweis bestehen bleiben soll):",
              file=sys.stderr)
        for t in treffer:
            print(f"  {t}", file=sys.stderr)
        return 1
    if warnung:
        print(f"⚠ {warnung}", file=sys.stderr)

    path.write_text(remove(text, args.id), encoding="utf-8")
    print(f"✓ {args.id} entfernt. Ergebnis am stabilen Ort festhalten "
          f"(ADR, Guideline oder tech-debt.md), falls noch nicht geschehen.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Offene Fragen lesen, erfassen, ändern, löschen.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="Alle offenen Fragen mit Fälligkeit").set_defaults(fn=cmd_list)

    p_get = sub.add_parser("get", help="Einen oder mehrere Einträge im Volltext")
    p_get.add_argument("ids", nargs="+", metavar="OQ-ID")
    p_get.set_defaults(fn=cmd_get)

    p_add = sub.add_parser("add", help="Neue offene Frage anlegen")
    p_add.add_argument("--titel", required=True)
    p_add.add_argument("--frage", required=True,
                       help="Die offene, mit dem User zu klärende Frage")
    p_add.add_argument("--faellig", required=True,
                       help="Anker + Prosa, z.B. 'Phase:V1 – warum jetzt noch nicht'. "
                            "Grammatik: td_anchors.py")
    p_add.add_argument("--hintergrund", required=True,
                       help="Auslöser, Kontext, betroffene Artefakte")
    p_add.add_argument("--session", type=int, help="Session-Nummer (Default: laufende)")
    p_add.set_defaults(fn=cmd_add)

    p_set = sub.add_parser("set", help="Felder einer bestehenden Frage ändern")
    p_set.add_argument("id", metavar="OQ-ID")
    p_set.add_argument("--titel", help="Titel korrigieren – er ist zugleich der Kurztitel, "
                                       "unter dem die Frage im Gespräch läuft")
    p_set.add_argument("--frage")
    p_set.add_argument("--faellig")
    p_set.add_argument("--hintergrund")
    p_set.set_defaults(fn=cmd_set)

    p_rm = sub.add_parser("remove", help="Geklärte Frage entfernen (Zustandsdokument)")
    p_rm.add_argument("id", metavar="OQ-ID")
    p_rm.add_argument("--trotz-verweisen", action="store_true",
                      dest="trotz_verweisen",
                      help="Löschen, obwohl noch Fundstellen auf die ID zeigen")
    p_rm.set_defaults(fn=cmd_remove)

    args = p.parse_args()
    try:
        return args.fn(args)
    except ValueError as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

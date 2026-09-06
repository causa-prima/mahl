#!/usr/bin/env python3
"""Zugriff auf einzelne Tech-Debt-Einträge – lesen, erfassen, ändern, löschen.

Statt `docs/tech-debt.md` ganz zu lesen (28 offene Einträge), um einen Posten zu sehen oder
zu ändern. Ein neuer Eintrag entsteht per Konstruktion formatgetreu, inkl. der
`Fällig`-Anker-Grammatik, die `check-td-capture.py` sonst nachträglich blockt.

**Ein `jetzt` pflegt beide Dateien.** `**Fällig:** jetzt` verlangt einen Punkt in
`docs/AGENT_MEMORY.md` – sonst wird der Posten nie vorgelegt, weil nur diese Datei bei jedem
Session-Start injiziert wird. Bisher war das Handarbeit und der Hook blockte nur das Fehlen
(OBS-S118-1); hier entsteht der Punkt mit dem Eintrag und verschwindet mit ihm.

Beispiele:
  python3 -m prozesscode.td list
  python3 -m prozesscode.td get TD-S089-1
  python3 -m prozesscode.td add --titel "…" --faellig "jetzt – warum sofort" \\
      --problem "…" --behebung "…" --done "woran man das Erledigtsein erkennt"
  python3 -m prozesscode.td set TD-S089-1 --faellig "Phase:MVP – verschoben, weil …"
  python3 -m prozesscode.td remove TD-S089-1

Verwandt: `td_due.py` (Fälligkeit für die Session-Agenda), `td_anchors.py` (Anker-Grammatik).
"""
import argparse
import sys


from . import td_entry as tde  # noqa: E402


def _memory_lesen() -> tuple[object, str]:
    pfad = tde.memory_path()
    return pfad, pfad.read_text(encoding="utf-8")


def cmd_list(args) -> int:
    text = tde.td_path().read_text(encoding="utf-8")
    ids = list(tde.entry_spans(text))
    if not ids:
        print("Keine offenen Posten.")
        return 0
    for tid in ids:
        eintrag = tde.get(text, tid) or ""
        termin = next((z.split("**Fällig:**", 1)[1].split("–")[0].strip()
                       for z in eintrag.splitlines() if z.startswith("**Fällig:**")), "–")
        if args.jetzt and not tde.braucht_memory_punkt(termin):
            continue
        print(f"{tid:<14} [{termin:<16}] {tde.titel(text, tid)}")
    print(f"\n{len(ids)} offen.")
    return 0


def cmd_get(args) -> int:
    text = tde.td_path().read_text(encoding="utf-8")
    fehlend = []
    for i, tid in enumerate(args.ids):
        eintrag = tde.get(text, tid)
        if eintrag is None:
            fehlend.append(tid)
            continue
        if i:
            print()
        print(eintrag)
    if fehlend:
        print(f"Nicht gefunden: {', '.join(fehlend)}", file=sys.stderr)
        return 1
    return 0


def cmd_add(args) -> int:
    if tde.braucht_memory_punkt(args.faellig) and not args.done:
        print("`Fällig: jetzt` braucht --done: Der Punkt in AGENT_MEMORY.md trägt ein "
              "Done-Kriterium, sonst ist nicht erkennbar, wann er erledigt ist.",
              file=sys.stderr)
        return 1

    pfad = tde.td_path()
    text = pfad.read_text(encoding="utf-8")
    neu, tid = tde.add(text, args.session or tde.laufende_session(), titel=args.titel,
                       faellig=args.faellig, problem=args.problem, behebung=args.behebung)
    pfad.write_text(neu, encoding="utf-8")
    print(f"✓ {tid} angelegt.")

    if tde.braucht_memory_punkt(args.faellig):
        m_pfad, m_text = _memory_lesen()
        m_pfad.write_text(tde.memory_ergaenzen(m_text, tid, args.done, neu),
                          encoding="utf-8")
        print(f"✓ {tid} als Priorität in {tde.MEMORY_FILE} eingetragen.")
    return 0


def cmd_set(args) -> int:
    pfad = tde.td_path()
    text = pfad.read_text(encoding="utf-8")
    if tde.get(text, args.id) is None:
        print(f"{args.id} existiert nicht.", file=sys.stderr)
        return 1
    if not any((args.faellig, args.problem, args.behebung, args.titel)):
        print("Nichts zu ändern – mindestens ein Feld angeben.", file=sys.stderr)
        return 1

    neu = tde.set_fields(text, args.id, faellig=args.faellig, problem=args.problem,
                         behebung=args.behebung, titel=args.titel)
    pfad.write_text(neu, encoding="utf-8")
    geaendert = [n for n, w in (("Titel", args.titel), ("Fällig", args.faellig),
                                ("Problem", args.problem),
                                ("Behebung", args.behebung)) if w]
    print(f"✓ {args.id}: {', '.join(geaendert)} aktualisiert.")

    # Die Fälligkeit steuert, ob der Posten in AGENT_MEMORY gehört – beide Richtungen, sonst
    # bleibt beim Verschieben eine Karteileiche stehen bzw. beim Vorziehen fehlt der Punkt.
    if args.faellig is not None:
        m_pfad, m_text = _memory_lesen()
        if tde.braucht_memory_punkt(args.faellig):
            if not tde.memory_hat(m_text, args.id):
                if not args.done:
                    print(f"⚠ {args.id} ist jetzt `jetzt`, steht aber nicht in "
                          f"{tde.MEMORY_FILE}. Mit --done nachtragen, sonst blockt "
                          f"check-td-capture.py den nächsten Edit.", file=sys.stderr)
                else:
                    m_pfad.write_text(
                        tde.memory_ergaenzen(m_text, args.id, args.done, neu),
                        encoding="utf-8")
                    print(f"✓ {args.id} als Priorität in {tde.MEMORY_FILE} eingetragen.")
        elif tde.memory_hat(m_text, args.id):
            m_pfad.write_text(tde.memory_entfernen(m_text, args.id), encoding="utf-8")
            print(f"✓ {args.id} aus {tde.MEMORY_FILE} entfernt (nicht mehr `jetzt`).")
    return 0


def cmd_remove(args) -> int:
    pfad = tde.td_path()
    text = pfad.read_text(encoding="utf-8")
    if tde.get(text, args.id) is None:
        print(f"{args.id} existiert nicht.", file=sys.stderr)
        return 1

    pfad.write_text(tde.remove(text, args.id), encoding="utf-8")
    print(f"✓ {args.id} entfernt.")

    m_pfad, m_text = _memory_lesen()
    if tde.memory_hat(m_text, args.id):
        m_pfad.write_text(tde.memory_entfernen(m_text, args.id), encoding="utf-8")
        print(f"✓ {args.id} aus {tde.MEMORY_FILE} entfernt.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Technische Schuld lesen, erfassen, ändern, löschen.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="Alle Posten mit Fälligkeit")
    p_list.add_argument("--jetzt", action="store_true", help="nur `Fällig: jetzt`")
    p_list.set_defaults(fn=cmd_list)

    p_get = sub.add_parser("get", help="Einen oder mehrere Posten im Volltext")
    p_get.add_argument("ids", nargs="+", metavar="TD-ID")
    p_get.set_defaults(fn=cmd_get)

    p_add = sub.add_parser("add", help="Neuen Posten anlegen")
    p_add.add_argument("--titel", required=True, help="Bereich/Kurztitel")
    p_add.add_argument("--faellig", required=True,
                       help="Anker + Prosa, z.B. 'Phase:MVP – warum dann'. "
                            "Grammatik: td_anchors.py")
    p_add.add_argument("--problem", required=True, help="Was ist die Schuld")
    p_add.add_argument("--behebung", required=True, help="Wie behoben wird")
    p_add.add_argument("--done", help="Done-Kriterium für AGENT_MEMORY.md "
                                      "(Pflicht bei `Fällig: jetzt`)")
    p_add.add_argument("--session", type=int, help="Session-Nummer (Default: laufende)")
    p_add.set_defaults(fn=cmd_add)

    p_set = sub.add_parser("set", help="Felder eines bestehenden Postens ändern")
    p_set.add_argument("id", metavar="TD-ID")
    p_set.add_argument("--titel", help="Titel korrigieren – er ist zugleich der Kurztitel, "
                                       "unter dem der Posten im Gespräch läuft")
    p_set.add_argument("--faellig")
    p_set.add_argument("--problem")
    p_set.add_argument("--behebung")
    p_set.add_argument("--done", help="Done-Kriterium, falls die Änderung auf `jetzt` geht")
    p_set.set_defaults(fn=cmd_set)

    p_rm = sub.add_parser("remove", help="Behobenen Posten entfernen (Zustandsdokument)")
    p_rm.add_argument("id", metavar="TD-ID")
    p_rm.set_defaults(fn=cmd_remove)

    args = p.parse_args()
    try:
        return args.fn(args)
    except ValueError as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Wohin geht das Read-Volumen? Aufgeschlüsselt nach Session-Art, Bereich und Datei.

Hintergrund: `Read` ist der mit Abstand größte Token-Posten (OBS-S109-1). Dieses Script
misst ihn an den Session-Logs statt ihn zu schätzen, und trennt dabei nach **Session-Art**
(implementierung / drain / retro / tooling …) – die Vorgänger-Messung aus S109 scannte nur
Sessions mit Subagenten und traf damit unbemerkt eine Aussage über allein
implementing-scenario-Sessions.

Warum als reguläres Script statt als Wegwerf-Code: Die S109-Fassung lag in `.claude/tmp/`,
wurde nach Gebrauch gelöscht und musste in S114 aus dem rohen Session-Log rekonstruiert
werden – dasselbe Muster, das OBS-S111-3 für den Stryker-Report beschreibt. Die
Wiedervorlagen von OBS-S085-3/-4 brauchen dieselbe Sorte Messung erneut.

Beispiele:
  python3 .claude/scripts/read-breakdown.py                  # Überblick je Session-Art
  python3 .claude/scripts/read-breakdown.py --by-area        # Bereiche, alle Arten
  python3 .claude/scripts/read-breakdown.py --by-area --type drain
  python3 .claude/scripts/read-breakdown.py --top 20         # größte Einzeldateien
  python3 .claude/scripts/read-breakdown.py --sessions       # erkannte Art je Session
  python3 .claude/scripts/read-breakdown.py --json
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _session_logs import (  # noqa: E402
    MAPPING_FILE,
    UNBEKANNT,
    categorize,
    edited_paths,
    load_mapping,
    load_records,
    project_log_dir,
    read_events,
    relative_path,
    session_logs,
    session_type,
    skills_in,
)


class Totals:
    """Sammelt die Kennzahlen einer Auswertung."""

    def __init__(self) -> None:
        self.volume = 0
        self.calls = 0
        self.by_area: Counter = Counter()
        self.calls_by_area: Counter = Counter()
        self.by_file: Counter = Counter()
        self.pre_edit = 0          # Read auf eine Datei, die im selben Kontext editiert wird
        self.rereads = 0           # dieselbe Datei im selben Kontext erneut gelesen
        self.reread_calls = 0
        self.targeted = 0          # mit offset/limit gelesen, also bewusst nur ein Ausschnitt
        self.pre_edit_by_area: Counter = Counter()
        self.targeted_by_area: Counter = Counter()

    def add(self, path: str, size: int, is_pre_edit: bool, is_reread: bool,
            is_targeted: bool) -> None:
        self.volume += size
        self.calls += 1
        area = categorize(path)
        self.by_area[area] += size
        self.calls_by_area[area] += 1
        self.by_file[relative_path(path)] += size
        if is_pre_edit:
            self.pre_edit += size
            self.pre_edit_by_area[area] += size
        if is_targeted:
            self.targeted += size
            self.targeted_by_area[area] += size
        if is_reread:
            self.rereads += size
            self.reread_calls += 1


def scan_context(records: list[dict], sinks: list[Totals]) -> None:
    """Wertet einen Kontext (Hauptlog ODER ein Subagent-Log) aus und speist alle Senken.

    „Kontext" ist bewusst das einzelne Log: Ein Subagent startet frisch, seine Re-Reads und
    Vor-Edit-Reads sind seine eigenen und dürfen nicht mit denen des Orchestrators verrechnet
    werden.
    """
    touched = edited_paths(records)
    seen: set[str] = set()
    for path, size, targeted in read_events(records):
        is_reread = path in seen
        seen.add(path)
        for sink in sinks:
            sink.add(path, size, path in touched, is_reread, targeted)


def collect(log_dir: Path) -> tuple[Totals, dict[str, Totals], dict[str, int], list[tuple[str, str]]]:
    """Misst alle Sessions. Liefert Gesamt, je Art, Sessions je Art und die Art-Zuordnung."""
    mapping = load_mapping()
    gesamt = Totals()
    je_art: dict[str, Totals] = defaultdict(Totals)
    sessions_je_art: Counter = Counter()
    zuordnung: list[tuple[str, str]] = []

    for session_id, main_log, sub_logs in session_logs(log_dir):
        haupt = load_records(main_log)
        sub_records = [load_records(p) for p in sub_logs]

        skills = skills_in(haupt)
        edits = edited_paths(haupt)
        for recs in sub_records:
            skills += skills_in(recs)
            edits |= edited_paths(recs)
        art, herkunft = session_type(session_id, skills, mapping, edits)

        zuordnung.append((session_id, art, herkunft))
        sessions_je_art[art] += 1
        sinks = [gesamt, je_art[art]]
        for recs in [haupt, *sub_records]:
            scan_context(recs, sinks)

    return gesamt, dict(je_art), dict(sessions_je_art), zuordnung


def _bar(anteil: float, breite: int = 24) -> str:
    return "█" * round(anteil * breite)


def print_overview(gesamt: Totals, je_art: dict[str, Totals], sessions: dict[str, int]) -> None:
    print("=" * 78)
    print(f"READ-Volumen je Session-Art   ({gesamt.volume / 1000:.0f}k Zeichen, "
          f"{gesamt.calls} Aufrufe, {sum(sessions.values())} Sessions)")
    print("=" * 78)
    print(f"  {'Art':<18} {'Sess.':>6} {'Volumen':>10} {'Anteil':>8} {'Ø/Session':>11}")
    for art, totals in sorted(je_art.items(), key=lambda kv: -kv[1].volume):
        n = sessions[art]
        anteil = totals.volume / gesamt.volume if gesamt.volume else 0
        print(f"  {art:<18} {n:>6} {totals.volume / 1000:>9.0f}k {anteil * 100:>7.1f}% "
              f"{totals.volume / (n or 1) / 1000:>10.0f}k  {_bar(anteil)}")

    if gesamt.volume:
        print()
        print(f"  Vor-Edit-Reads (Harness-Zwang): {gesamt.pre_edit / 1000:.0f}k "
              f"({gesamt.pre_edit / gesamt.volume * 100:.1f}%) – der Rest ist Lektüre/Recherche")
        print(f"  Re-Reads derselben Datei:       {gesamt.rereads / 1000:.0f}k "
              f"({gesamt.rereads / gesamt.volume * 100:.1f}%, {gesamt.reread_calls} Aufrufe)")


def print_areas(totals: Totals, titel: str) -> None:
    print()
    print("=" * 78)
    print(f"Bereiche – {titel}   ({totals.volume / 1000:.0f}k Zeichen)")
    print("=" * 78)
    print(f"  {'Bereich':<38} {'Volumen':>8} {'Anteil':>7} {'Reads':>6} {'Ø':>7} "
          f"{'vor Edit':>9} {'gezielt':>8}")
    for area, value in totals.by_area.most_common():
        n = totals.calls_by_area[area]
        anteil = value / totals.volume if totals.volume else 0
        vor_edit = totals.pre_edit_by_area[area] / value * 100 if value else 0
        gezielt = totals.targeted_by_area[area] / value * 100 if value else 0
        print(f"  {area:<38} {value / 1000:>7.0f}k {anteil * 100:>6.1f}% "
              f"{n:>6} {value / (n or 1):>7.0f} {vor_edit:>8.0f}% {gezielt:>7.0f}%")
    print("\n  „vor Edit\" = die Datei wird im selben Kontext noch editiert (Harness verlangt "
          "den Read).\n  „gezielt\" = mit offset/limit gelesen statt vollständig.")


def print_top_files(totals: Totals, limit: int, titel: str) -> None:
    print()
    print("=" * 78)
    print(f"Größte gelesene Dateien – {titel}")
    print("=" * 78)
    for path, value in totals.by_file.most_common(limit):
        print(f"  {value / 1000:>7.0f}k  {path[:64]}")


def print_sessions(zuordnung: list[tuple[str, str, str]]) -> None:
    print()
    print("=" * 78)
    print("Erkannte Art je Session   (Herkunft: mapping > skill > heuristik)")
    print("=" * 78)
    for session_id, art, herkunft in zuordnung:
        marker = "  ← manuell zuordnen" if art == UNBEKANNT else ""
        print(f"  {session_id[:8]}…  {art:<18} {herkunft}{marker}")
    offen = [s for s, art, _ in zuordnung if art == UNBEKANNT]
    if offen:
        print(f"\n  {len(offen)} Session(s) ohne Signal. Ergänze sie in {MAPPING_FILE.name}:")
        print('    { "%s": "drain" }' % offen[0][:8])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-Volumen nach Session-Art, Bereich und Datei.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--by-area", action="store_true", help="Aufschlüsselung nach Bereich")
    parser.add_argument("--top", type=int, metavar="N", help="Top-N Einzeldateien")
    parser.add_argument("--type", metavar="ART", help="nur eine Session-Art auswerten")
    parser.add_argument("--sessions", action="store_true", help="erkannte Art je Session zeigen")
    parser.add_argument("--json", action="store_true", help="maschinenlesbar")
    args = parser.parse_args()

    log_dir = project_log_dir()
    if not log_dir.exists():
        print(f"Keine Session-Logs unter {log_dir}", file=sys.stderr)
        sys.exit(1)

    gesamt, je_art, sessions, zuordnung = collect(log_dir)

    if args.type:
        if args.type not in je_art:
            print(f"Unbekannte Art '{args.type}'. Verfügbar: {', '.join(sorted(je_art))}",
                  file=sys.stderr)
            sys.exit(1)
        gewaehlt, titel = je_art[args.type], args.type
    else:
        gewaehlt, titel = gesamt, "alle Session-Arten"

    if args.json:
        print(json.dumps({
            "gesamt": {"volumen": gesamt.volume, "aufrufe": gesamt.calls},
            "je_art": {
                art: {"volumen": t.volume, "aufrufe": t.calls, "sessions": sessions[art]}
                for art, t in je_art.items()
            },
            "bereiche": dict(gewaehlt.by_area),
            "dateien": dict(gewaehlt.by_file.most_common(args.top or 20)),
            "zuordnung": {sid: {"art": art, "herkunft": h} for sid, art, h in zuordnung},
        }, ensure_ascii=False, indent=2))
        return

    print_overview(gesamt, je_art, sessions)
    if args.by_area:
        print_areas(gewaehlt, titel)
    if args.top:
        print_top_files(gewaehlt, args.top, titel)
    if args.sessions:
        print_sessions(zuordnung)
    if not (args.by_area or args.top or args.sessions):
        print("\n  Mehr Tiefe: --by-area | --top N | --sessions | --type ART")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Wie nutzen die Agenten ihr Werkzeug? Zwei terminierte Wiedervorlage-Messungen.

**Filter-Quote (OBS-S085-3):** Wie oft wird die Ausgabe eines Wrapper-Scripts nachgelagert
durch `| grep`/`| tail`/… gefiltert, obwohl die Wrapper seit S109 im Erfolgsfall nur noch das
Verdikt ausgeben? Sinkt die Quote nicht, ist die Gewohnheits-These bestätigt und nur noch ein
mechanischer Guard wirksam. Gezählt wird ausschließlich die AUSFÜHRUNG eines Wrappers, nicht
das Lesen seiner Datei (`grep … qa-check.py`) – sonst zählte Datei-Inspektion als Filterung.

**LSP-Nutzung (OBS-S085-4):** Wird der Language-Server tatsächlich benutzt? Die Bewertung
hängt daran; eine dritte Nullrunde bedeutet laut Eintrag verwerfen. Die Aufschlüsselung nach
Session-Art ist hier entscheidend: LSP soll in implementing-scenario-Sessions helfen, und nur
dort ist die Nullnutzung ein Urteil über das Werkzeug statt über die Gelegenheit.

Beispiele:
  python3 .claude/scripts/tool-usage.py              # beide Messungen
  python3 .claude/scripts/tool-usage.py --filter     # nur die Filter-Quote
  python3 .claude/scripts/tool-usage.py --lsp        # nur die LSP-Nutzung
  python3 .claude/scripts/tool-usage.py --verbose    # zusätzlich Beispielzeilen
  python3 .claude/scripts/tool-usage.py --since 2026-07-30   # nur nach dem S109-Umbau

`--since` trennt Vor- und Nach-Maßnahme: Die Monats-Buckets allein können das nicht, wenn der
Stichtag mitten im Monat liegt (der S109-Wrapper-Umbau fiel auf den 29.07.). Ohne den Filter
ließe sich die Wirkung nur aus Monatssummen ableiten – rechnen statt messen.
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _session_logs import (  # noqa: E402
    load_mapping,
    load_records,
    project_log_dir,
    session_logs,
    session_type,
    skills_in,
    edited_paths,
)
from _util import REPO_ROOT  # noqa: E402

ALLOWED_LOG = REPO_ROOT / ".claude" / "tmp" / "allowed-commands.log"

# Genau die Gate-/Test-Wrapper, die S109 gemessen hat – die Liste NICHT erweitern, sonst wird
# die Quote unvergleichbar mit der Basislinie (517 Läufe, 83 %). Analyse-Scripte wie
# `read-breakdown.py` gehören ausdrücklich nicht dazu: Ihre lange Ausgabe ist zum Zerschneiden
# gedacht, ein Filter darauf ist bestimmungsgemäß und kein Symptom.
WRAPPERS = ("dotnet-test", "dotnet-stryker", "vitest-run", "playwright-test",
            "stryker-frontend", "eslint-run", "jscpd-run", "qa-check", "stryker-summary")
RUN_RE = re.compile(r"python3\s+\S*\.claude/scripts/(" + "|".join(WRAPPERS) + r")\.py")
FILTER_RE = re.compile(r"\|\s*(tail|head|grep|sed|awk)\b")
STAMP_RE = re.compile(r"^\[((\d{4}-\d{2})-\d{2}) ")


def line_date(line: str) -> str | None:
    """Der Tag der Zeile als `YYYY-MM-DD` – oder None, wenn sie keinen Zeitstempel trägt.

    Das Log schreibt den vollen Zeitstempel; die Monats-Aggregation unten wirft den Tag weg.
    Für ein Vor/Nach-Urteil über eine Maßnahme braucht es ihn aber (ein Stichtag mitten im
    Monat lässt sich sonst nicht schneiden), deshalb hier getrennt zugänglich.
    """
    stamp = STAMP_RE.match(line)
    return stamp.group(1) if stamp else None


def classify_line(line: str) -> tuple[str, str, bool] | None:
    """(Monat, Wrapper, wurde gefiltert) – oder None, wenn die Zeile kein Wrapper-Lauf ist.

    Zwei Feinheiten: Nur Zeilen mit Zeitstempel sind Befehlsanfänge (der Rest sind
    Fortsetzungszeilen mehrzeiliger Befehle), und ein Filter zählt nur, wenn er **nach** dem
    Wrapper-Aufruf steht – `grep foo | python3 … qa-check.py` filtert dessen Ausgabe nicht.
    """
    stamp = STAMP_RE.match(line)
    if not stamp:
        return None
    match = RUN_RE.search(line)
    if not match:
        return None
    return stamp.group(2), match.group(1), bool(FILTER_RE.search(line, match.end()))


def measure_filter_quote(path=None, since=None) -> tuple[Counter, Counter, Counter, list[str]]:
    """(Läufe je Monat, gefiltert je Monat, gefiltert je Wrapper, Beispielzeilen).

    `since` (`YYYY-MM-DD`, inklusiv) beschränkt auf Läufe ab diesem Tag – so wird die Quote
    nach einem Maßnahmen-Stichtag messbar statt aus Monatssummen abgeleitet.
    """
    runs: Counter = Counter()
    filtered: Counter = Counter()
    by_wrapper: Counter = Counter()
    examples: list[str] = []

    log = path or ALLOWED_LOG
    if not log.exists():
        return runs, filtered, by_wrapper, examples

    with open(log, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if since:
                day = line_date(line)
                # ISO-Datum: lexikographischer Vergleich ist chronologisch.
                if day is None or day < since:
                    continue
            result = classify_line(line)
            if not result:
                continue
            month, wrapper, was_filtered = result
            runs[month] += 1
            if was_filtered:
                filtered[month] += 1
                by_wrapper[wrapper] += 1
                if len(examples) < 10:
                    examples.append(line.strip()[:130])

    return runs, filtered, by_wrapper, examples


def print_filter_quote(verbose: bool, since: str | None = None) -> None:
    runs, filtered, by_wrapper, examples = measure_filter_quote(since=since)
    print("=" * 78)
    print("OBS-S085-3: nachgelagert gefilterte Wrapper-AUSFÜHRUNGEN")
    if since:
        print(f"  (nur Läufe ab {since})")
    print("=" * 78)
    if not runs:
        quelle = f"keine Wrapper-Läufe ab {since}" if since else "enthält keine Wrapper-Läufe"
        print(f"  Keine Daten – {ALLOWED_LOG} fehlt oder {quelle}.")
        return

    print(f"  {'Monat':<10} {'Läufe':>8} {'gefiltert':>11} {'Quote':>7}")
    for month in sorted(runs):
        quote = filtered[month] / runs[month] * 100
        print(f"  {month:<10} {runs[month]:>8} {filtered[month]:>11} {quote:>6.0f}%")
    total_r, total_f = sum(runs.values()), sum(filtered.values())
    print(f"  {'GESAMT':<10} {total_r:>8} {total_f:>11} {total_f / total_r * 100:>6.0f}%")
    print(f"\n  Gefiltert je Wrapper: {dict(by_wrapper.most_common())}")

    if verbose and examples:
        print("\n  Beispiele:")
        for example in examples:
            print(f"    {example}")


def measure_lsp() -> tuple[Counter, Counter, dict[str, Counter], int]:
    """(Calls je Session-Art, Operationen, Sessions je Art mit/ohne LSP, Sessions gesamt)."""
    log_dir = project_log_dir()
    mapping = load_mapping()
    calls_by_type: Counter = Counter()
    ops: Counter = Counter()
    sessions_by_type: dict[str, Counter] = defaultdict(Counter)
    total = 0

    for session_id, main_log, sub_logs in session_logs(log_dir):
        total += 1
        records = load_records(main_log)
        sub_records = [load_records(p) for p in sub_logs]

        skills = skills_in(records)
        edits = edited_paths(records)
        for recs in sub_records:
            skills += skills_in(recs)
            edits |= edited_paths(recs)
        art, _ = session_type(session_id, skills, mapping, edits)

        calls = 0
        for recs in [records, *sub_records]:
            for rec in recs:
                for block in (rec.get("message") or {}).get("content") or []:
                    if (isinstance(block, dict) and block.get("type") == "tool_use"
                            and block.get("name") == "LSP"):
                        calls += 1
                        ops[str((block.get("input") or {}).get("operation", "?"))] += 1

        calls_by_type[art] += calls
        sessions_by_type[art]["mit" if calls else "ohne"] += 1

    return calls_by_type, ops, dict(sessions_by_type), total


def print_lsp() -> None:
    calls_by_type, ops, sessions_by_type, total = measure_lsp()
    print("=" * 78)
    print("OBS-S085-4: LSP-Nutzung je Session-Art")
    print("=" * 78)
    print(f"  {'Art':<18} {'Sessions':>9} {'davon mit LSP':>15} {'Calls':>8}")
    for art in sorted(sessions_by_type, key=lambda a: -calls_by_type[a]):
        counts = sessions_by_type[art]
        gesamt = counts["mit"] + counts["ohne"]
        print(f"  {art:<18} {gesamt:>9} {counts['mit']:>15} {calls_by_type[art]:>8}")

    gesamt_calls = sum(calls_by_type.values())
    print(f"\n  Sessions gesamt: {total}   LSP-Calls gesamt: {gesamt_calls}")
    print(f"  Operationen: {dict(ops.most_common()) if ops else '–'}")
    if not gesamt_calls:
        print("\n  ⚠ Nullnutzung – laut OBS-S085-4 bedeutet die dritte Nullrunde: verwerfen.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Werkzeug-Nutzung der Agenten: Filter-Quote und LSP-Nutzung.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--filter", action="store_true", help="nur die Filter-Quote (OBS-S085-3)")
    parser.add_argument("--lsp", action="store_true", help="nur die LSP-Nutzung (OBS-S085-4)")
    parser.add_argument("--verbose", action="store_true", help="Beispielzeilen zeigen")
    parser.add_argument("--since", metavar="YYYY-MM-DD",
                        help="nur Läufe ab diesem Tag (inklusiv) – trennt Vor/Nach einer Maßnahme")
    args = parser.parse_args()

    if args.since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.since):
        parser.error(f"--since braucht das Format YYYY-MM-DD, nicht {args.since!r}")

    beide = not (args.filter or args.lsp)
    if args.filter or beide:
        print_filter_quote(args.verbose, args.since)
    if beide:
        print()
    if args.lsp or beide:
        print_lsp()


if __name__ == "__main__":
    main()

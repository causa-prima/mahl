#!/usr/bin/env python3
"""
Stryker JSON-Report aufbereiten für LLM-Analyse.

Verwendung:
  python3 .claude/scripts/stryker-summary.py                          # neuester Report
  python3 .claude/scripts/stryker-summary.py path/to/report.json
  python3 .claude/scripts/stryker-summary.py --verbose                # alle nicht-getöteten Mutanten
  python3 .claude/scripts/stryker-summary.py path/to/report.json --verbose
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _stryker_report import (
    NO_MUTANTS_HINT,
    collect_undetected,
    compute_metrics,
    format_mutant_group,
    format_score,
    format_scope,
    format_status_breakdown,
    gate_code,
    has_no_mutants,
    short_path,
)


MAX_REPORT_AGE_MINUTES = 5


def find_latest_report(base_dir: str = "StrykerOutput/Backend") -> Path:
    output_dir = Path(__file__).parent.parent.parent / base_dir
    if not output_dir.exists():
        print(f"Kein {base_dir}-Verzeichnis gefunden.", file=sys.stderr)
        sys.exit(1)
    reports = sorted(output_dir.glob("*/reports/mutation-report.json"), reverse=True)
    if not reports:
        print("Kein Report gefunden.", file=sys.stderr)
        sys.exit(1)
    latest = reports[0]
    age_minutes = (time.time() - os.path.getmtime(latest)) / 60
    if age_minutes > MAX_REPORT_AGE_MINUTES:
        print(
            f"⚠️  Neuester Report ist {age_minutes:.0f} Minuten alt – kein aktueller Stryker-Lauf?\n"
            f"   Report: {latest}",
            file=sys.stderr,
        )
        sys.exit(1)
    return latest


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("report", nargs="?", help="Pfad zur mutation-report.json (optional)")
    parser.add_argument("--verbose", action="store_true", help="Alle nicht-getöteten Mutanten anzeigen (inkl. Ignored, NoCoverage, Timeout)")
    args = parser.parse_args()

    report_path = Path(args.report) if args.report else find_latest_report()

    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", {})
    metrics = compute_metrics(files)
    counts = metrics["counts"]

    survivors_by_file, nocoverage_by_file = collect_undetected(files)
    detail_by_file: dict[str, list[dict]] = {}
    if args.verbose:
        for path, file_data in files.items():
            for m in file_data.get("mutants", []):
                if m.get("status") != "Killed":
                    detail_by_file.setdefault(short_path(path), []).append(m)

    print(f"Stryker-Report: {report_path.parent.parent.name}")
    print(f"Score: {format_score(metrics)}  |  {format_scope(metrics)}  |  "
          f"Killed: {counts['Killed']}  |  Survived: {counts['Survived']}  |  "
          f"Timeout: {counts['Timeout']}  |  NoCoverage: {counts['NoCoverage']}")

    # Ein Lauf ohne validen Mutanten ist kein bestandener Lauf, sondern ein misslungener –
    # ohne diesen Abbruch fiele er als „keine Survivors" durch das Gate (OBS-S108-3).
    if has_no_mutants(metrics):
        sys.stdout.flush()  # stderr ist ungepuffert – sonst stünde der Fehler VOR der Score-Zeile
        print(f"\n❌ {NO_MUTANTS_HINT}\n{format_status_breakdown(metrics)}", file=sys.stderr)
        sys.exit(gate_code(metrics))

    if counts["Timeout"] > 0:
        print(
            f"\n⏱️  {counts['Timeout']} Timeout(s) zählen als detected (Standard), können aber\n"
            f"   Timing-Artefakte bei Partial-Runs sein – mit `--verbose` prüfen."
        )

    if not survivors_by_file and not nocoverage_by_file:
        print("\n✅ Keine Survivors / NoCoverage.")
    else:
        if survivors_by_file:
            print(f"\n⚠️  {counts['Survived']} Survivor(s):\n")
            print("\n".join(format_mutant_group(survivors_by_file)))
        if nocoverage_by_file:
            print(f"\n⚠️  {counts['NoCoverage']} NoCoverage (von keinem Test ausgeführt):\n")
            print("\n".join(format_mutant_group(nocoverage_by_file)))

    if args.verbose and detail_by_file:
        total_detail = sum(len(v) for v in detail_by_file.values())
        print(f"\n📋 Alle nicht-getöteten Mutanten ({total_detail}):\n")
        for file, mutants in sorted(detail_by_file.items()):
            print(f"  {file} ({len(mutants)})")
            for m in sorted(mutants, key=lambda x: (x["location"]["start"]["line"], x["location"]["start"]["column"])):
                loc = m["location"]["start"]
                line, col = loc["line"], loc["column"]
                status = m.get("status", "?")
                status_reason = m.get("statusReason", "")
                mutator = m["mutatorName"]
                replacement = m.get("replacement", "?")
                print(f"    Zeile {line:>4}  Col {col:>3}  [{status}]  {mutator}")
                if status_reason:
                    print(f"           StatusReason: {status_reason}")
                print(f"           → {replacement}")
            print()

    # Mechanisches Gate: Score < 100 % (Survivor oder NoCoverage) → exit 1.
    sys.exit(gate_code(metrics))


if __name__ == "__main__":
    main()

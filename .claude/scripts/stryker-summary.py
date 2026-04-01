#!/usr/bin/env python3
"""
Stryker JSON-Report aufbereiten für LLM-Analyse.

Verwendung:
  python3 .claude/scripts/stryker-summary.py                          # neuester Report
  python3 .claude/scripts/stryker-summary.py path/to/report.json
  python3 .claude/scripts/stryker-summary.py --detail                 # alle nicht-getöteten Mutanten
  python3 .claude/scripts/stryker-summary.py path/to/report.json --detail
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path


MAX_REPORT_AGE_MINUTES = 5


def find_latest_report() -> Path:
    output_dir = Path(__file__).parent.parent.parent / "StrykerOutput"
    if not output_dir.exists():
        print("Kein StrykerOutput-Verzeichnis gefunden.", file=sys.stderr)
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


def short_path(full_path: str) -> str:
    normalized = full_path.replace("\\", "/")
    for anchor in ("Server/", "Server.Tests/"):
        if anchor in normalized:
            return normalized[normalized.index(anchor):]
    return normalized.split("/")[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Stryker JSON-Report aufbereiten.")
    parser.add_argument("report", nargs="?", help="Pfad zur mutation-report.json (optional)")
    parser.add_argument("--detail", action="store_true", help="Alle nicht-getöteten Mutanten anzeigen (inkl. Ignored, NoCoverage, Timeout)")
    args = parser.parse_args()

    report_path = Path(args.report) if args.report else find_latest_report()

    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", {})

    # Aggregieren
    total_tested = 0
    total_killed = 0
    total_survived = 0
    total_timeout = 0
    survivors_by_file: dict[str, list[dict]] = {}
    detail_by_file: dict[str, list[dict]] = {}

    for path, file_data in files.items():
        for m in file_data.get("mutants", []):
            status = m.get("status")
            if status in ("Killed", "Survived", "Timeout"):
                total_tested += 1
            if status == "Killed":
                total_killed += 1
            elif status == "Survived":
                total_survived += 1
                key = short_path(path)
                survivors_by_file.setdefault(key, []).append(m)
            elif status == "Timeout":
                total_timeout += 1
            if args.detail and status != "Killed":
                key = short_path(path)
                detail_by_file.setdefault(key, []).append(m)

    score = (total_killed / total_tested * 100) if total_tested > 0 else 0

    print(f"Stryker-Report: {report_path.parent.parent.name}")
    print(f"Score: {score:.1f}%  |  Tested: {total_tested}  |  Killed: {total_killed}  |  Survived: {total_survived}  |  Timeout: {total_timeout}")

    if total_timeout > 0:
        print(
            f"\n⏱️  {total_timeout} Timeout(s) – können Timing-Artefakte bei Partial-Runs sein.\n"
            f"   Bitte mit `--detail` prüfen ob die Mutanten wirklich getötet sein sollten."
        )

    if not survivors_by_file:
        print("\n✅ Keine Survivors.")
    else:
        print(f"\n⚠️  {total_survived} Survivor(s):\n")
        for file, mutants in sorted(survivors_by_file.items()):
            print(f"  {file} ({len(mutants)})")
            for m in sorted(mutants, key=lambda x: x["location"]["start"]["line"]):
                line = m["location"]["start"]["line"]
                mutator = m["mutatorName"]
                replacement = m.get("replacement", "?")
                print(f"    Zeile {line:>4}  {mutator}")
                print(f"           → {replacement}")
            print()

    if args.detail and detail_by_file:
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


if __name__ == "__main__":
    main()

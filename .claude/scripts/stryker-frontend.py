#!/usr/bin/env python3
"""
Stryker JS/TS via cmd.exe (WSL-Wrapper) + automatische Auswertung via stryker-summary.py.

Verwendung:
  python3 .claude/scripts/stryker-frontend.py                              # alle Dateien
  python3 .claude/scripts/stryker-frontend.py --mutate src/pages/Foo.tsx   # eine Datei
  python3 .claude/scripts/stryker-frontend.py --detail                     # alle nicht-getöteten Mutanten

Pfade für --mutate: relativ zu Client/ (z.B. src/pages/IngredientsPage.tsx).
Output wird nach StrykerOutput/Frontend/<timestamp>/reports/ kopiert.
"""
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _util import REPO_ROOT_WIN, _win_path

_SCRIPTS_DIR  = Path(__file__).parent
_REPO_ROOT    = _SCRIPTS_DIR.parent.parent
_TMP_FILE     = _SCRIPTS_DIR.parent / "tmp" / "stryker_frontend_out.txt"
_TMP_FILE_WIN = _win_path(str(_TMP_FILE))
_CLIENT_WIN   = REPO_ROOT_WIN + r"\Client"
_CLIENT_DIR   = _REPO_ROOT / "Client"
_STRYKER_SRC  = _CLIENT_DIR / "reports" / "mutation"
_OUTPUT_BASE  = _REPO_ROOT / "StrykerOutput" / "Frontend"


def _copy_reports(timestamp: str) -> Path:
    target_reports = _OUTPUT_BASE / timestamp / "reports"
    target_reports.mkdir(parents=True, exist_ok=True)

    rename_map = {
        "mutation.json": "mutation-report.json",
        "mutation.html": "mutation-report.html",
    }
    for src_file in _STRYKER_SRC.iterdir():
        dest_name = rename_map.get(src_file.name, src_file.name)
        shutil.copy2(src_file, target_reports / dest_name)

    return target_reports / "mutation-report.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Stryker JS/TS via cmd.exe (WSL)")
    parser.add_argument("--mutate", metavar="GLOB",
                        help="Datei oder Glob relativ zu Client/ (z.B. src/pages/Foo.tsx)")
    parser.add_argument("--detail", action="store_true",
                        help="Alle nicht-getöteten Mutanten anzeigen (via stryker-summary.py)")
    args = parser.parse_args()

    stryker_cmd = "npx stryker run"
    if args.mutate:
        stryker_cmd += f" --mutate {args.mutate}"

    _TMP_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starte: {stryker_cmd}")
    print(f"Output → {_TMP_FILE}")

    cmd_inner = f"cd /d {_CLIENT_WIN} && {stryker_cmd} > {_TMP_FILE_WIN} 2>&1"
    result = subprocess.run(["cmd.exe", "/c", cmd_inner])

    if _TMP_FILE.exists():
        lines = _TMP_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n".join(lines[-30:]))
        _TMP_FILE.unlink()

    if result.returncode != 0:
        print(f"\nStryker fehlgeschlagen (Exit-Code {result.returncode}).", file=sys.stderr)
        sys.exit(result.returncode)

    if not _STRYKER_SRC.exists():
        print(f"\nKein Report-Verzeichnis gefunden: {_STRYKER_SRC}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d.%H-%M-%S")
    report_json = _copy_reports(timestamp)
    print(f"\nReport kopiert → {report_json.parent.parent}")

    summary_args = [sys.executable, str(_SCRIPTS_DIR / "stryker-summary.py"), str(report_json)]
    if args.detail:
        summary_args.append("--detail")
    summary_result = subprocess.run(summary_args)
    sys.exit(summary_result.returncode)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
dotnet stryker via cmd.exe (WSL-Wrapper) + automatische Auswertung via stryker-summary.py.

Verwendung:
  python3 .claude/scripts/dotnet-stryker.py
  python3 .claude/scripts/dotnet-stryker.py --mutate Domain/Foo.cs
  python3 .claude/scripts/dotnet-stryker.py --detail
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _util import REPO_ROOT_WIN, _win_path

_SCRIPTS_DIR = Path(__file__).parent
_TMP_FILE = _SCRIPTS_DIR.parent / "tmp" / "stryker_out.txt"
_TMP_FILE_WIN = _win_path(str(_TMP_FILE))

def main() -> None:
    parser = argparse.ArgumentParser(description="dotnet stryker via cmd.exe (WSL)")
    parser.add_argument("--mutate", help="Datei mutieren (z.B. Domain/Foo.cs)")
    parser.add_argument("--detail", action="store_true", help="Alle nicht-getöteten Mutanten")
    args = parser.parse_args()

    cwd_win = REPO_ROOT_WIN

    # dotnet stryker Aufruf zusammenbauen
    stryker_cmd = "dotnet stryker"
    if args.mutate:
        stryker_cmd += f" --mutate {args.mutate}"

    # .claude/tmp/ sicherstellen
    _TMP_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starte: {stryker_cmd}")
    print(f"Output → {_TMP_FILE}")

    cmd_inner = f"cd /d {cwd_win} && {stryker_cmd} > {_TMP_FILE_WIN} 2>&1"
    result = subprocess.run(["cmd.exe", "/c", cmd_inner])

    # Letzte Zeilen des Stryker-Outputs anzeigen
    if _TMP_FILE.exists():
        lines = _TMP_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n".join(lines[-30:]))
        _TMP_FILE.unlink()

    if result.returncode != 0:
        print(f"\nStryker fehlgeschlagen (Exit-Code {result.returncode}).", file=sys.stderr)
        sys.exit(result.returncode)

    # Auswertung via stryker-summary.py
    summary_args = [sys.executable, str(_SCRIPTS_DIR / "stryker-summary.py")]
    if args.detail:
        summary_args.append("--detail")
    summary_result = subprocess.run(summary_args)
    sys.exit(summary_result.returncode)


if __name__ == "__main__":
    main()

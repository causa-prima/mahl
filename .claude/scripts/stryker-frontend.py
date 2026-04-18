#!/usr/bin/env python3
"""
Stryker JS/TS via cmd.exe (WSL-Wrapper).

Verwendung:
  python3 .claude/scripts/stryker-frontend.py                              # alle Dateien
  python3 .claude/scripts/stryker-frontend.py --mutate src/pages/Foo.tsx   # eine Datei
  python3 .claude/scripts/stryker-frontend.py --detail                     # mehr Output-Zeilen

Pfade für --mutate: relativ zu Client/ (z.B. src/pages/IngredientsPage.tsx).
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _util import REPO_ROOT_WIN, _win_path

_SCRIPTS_DIR  = Path(__file__).parent
_TMP_FILE     = _SCRIPTS_DIR.parent / "tmp" / "stryker_frontend_out.txt"
_TMP_FILE_WIN = _win_path(str(_TMP_FILE))
_CLIENT_WIN   = REPO_ROOT_WIN + r"\Client"

_TAIL_DEFAULT = 30
_TAIL_DETAIL  = 60


def main() -> None:
    parser = argparse.ArgumentParser(description="Stryker JS/TS via cmd.exe (WSL)")
    parser.add_argument("--mutate", metavar="GLOB",
                        help="Datei oder Glob relativ zu Client/ (z.B. src/pages/Foo.tsx)")
    parser.add_argument("--detail", action="store_true",
                        help="Mehr Output-Zeilen anzeigen (Survivor-Details)")
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
        tail = _TAIL_DETAIL if args.detail else _TAIL_DEFAULT
        print("\n".join(lines[-tail:]))
        _TMP_FILE.unlink()

    if result.returncode != 0:
        print(f"\nStryker fehlgeschlagen (Exit-Code {result.returncode}).", file=sys.stderr)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

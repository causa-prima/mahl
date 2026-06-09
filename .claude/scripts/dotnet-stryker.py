#!/usr/bin/env python3
"""
dotnet stryker via cmd.exe (WSL-Wrapper) + automatische Auswertung via stryker-summary.py.

Verwendung:
  python3 .claude/scripts/dotnet-stryker.py
  python3 .claude/scripts/dotnet-stryker.py --mutate Domain/Foo.cs
  python3 .claude/scripts/dotnet-stryker.py --detail

Output wird nach StrykerOutput/Backend/<timestamp>/reports/ verschoben.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _util import REPO_ROOT_WIN, _win_path, check_dotnet_dll_lock

_SCRIPTS_DIR  = Path(__file__).parent
_REPO_ROOT    = _SCRIPTS_DIR.parent.parent
_TMP_FILE     = _SCRIPTS_DIR.parent / "tmp" / "stryker_out.txt"
_TMP_FILE_WIN = _win_path(str(_TMP_FILE))
_STRYKER_OUT  = _REPO_ROOT / "StrykerOutput"
_BACKEND_OUT  = _STRYKER_OUT / "Backend"


def _snapshot_run_dirs() -> set[Path]:
    """Gibt alle aktuellen Timestamp-Ordner direkt unter StrykerOutput/ zurück (kein Backend/Frontend)."""
    if not _STRYKER_OUT.exists():
        return set()
    return {
        p for p in _STRYKER_OUT.iterdir()
        if p.is_dir() and p.name not in ("Backend", "Frontend")
    }


def _move_new_run(before: set[Path]) -> Path | None:
    """Verschiebt den neu angelegten Timestamp-Ordner nach StrykerOutput/Backend/."""
    after = _snapshot_run_dirs()
    new_dirs = after - before
    if not new_dirs:
        return None
    src = max(new_dirs, key=lambda p: p.stat().st_mtime)
    _BACKEND_OUT.mkdir(parents=True, exist_ok=True)
    dest = _BACKEND_OUT / src.name
    shutil.move(str(src), dest)
    return dest


def main() -> None:
    check_dotnet_dll_lock()
    parser = argparse.ArgumentParser(description="dotnet stryker via cmd.exe (WSL)")
    parser.add_argument("--mutate", help="Datei mutieren (z.B. Domain/Foo.cs)")
    parser.add_argument("--detail", action="store_true", help="Alle nicht-getöteten Mutanten")
    args = parser.parse_args()

    stryker_cmd = "dotnet stryker"
    if args.mutate:
        stryker_cmd += f" --mutate {args.mutate}"

    _TMP_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starte: {stryker_cmd}")
    print(f"Output → {_TMP_FILE}")

    before = _snapshot_run_dirs()
    cmd_inner = f"cd /d {REPO_ROOT_WIN} && {stryker_cmd} > {_TMP_FILE_WIN} 2>&1"
    result = subprocess.run(["cmd.exe", "/c", cmd_inner])

    if _TMP_FILE.exists():
        lines = _TMP_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n".join(lines[-30:]))
        _TMP_FILE.unlink()

    if result.returncode != 0:
        print(f"\nStryker fehlgeschlagen (Exit-Code {result.returncode}).", file=sys.stderr)
        sys.exit(result.returncode)

    run_dir = _move_new_run(before)
    if run_dir:
        print(f"\nReport verschoben → {run_dir}")

    # Auswertung via stryker-summary.py
    summary_args = [sys.executable, str(_SCRIPTS_DIR / "stryker-summary.py")]
    if args.detail:
        summary_args.append("--detail")
    summary_result = subprocess.run(summary_args)
    sys.exit(summary_result.returncode)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
dotnet stryker (nativ) + automatische Auswertung via stryker-summary.py.

Verwendung:
  python3 .claude/scripts/dotnet-stryker.py
  python3 .claude/scripts/dotnet-stryker.py --mutate Domain/Foo.cs
  python3 .claude/scripts/dotnet-stryker.py --mutate Domain/Foo.cs,Endpoints/Bar.cs
  python3 .claude/scripts/dotnet-stryker.py --verbose

Pfade für --mutate: relativ zu Server/ (z.B. Endpoints/Foo.cs) – NICHT repo-root-relativ.
Mehrere Ziele als Kommaliste. Ein Muster ohne Treffer bricht den Lauf ab, statt still über
null Dateien zu laufen.

Output wird nach StrykerOutput/Backend/<timestamp>/reports/ verschoben.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _run_lock import RunLock
from _stryker_target import resolve_mutate
from _wrapper_output import error_lines

_SCRIPTS_DIR  = Path(__file__).parent
_REPO_ROOT    = _SCRIPTS_DIR.parent.parent
_TMP_FILE     = _SCRIPTS_DIR.parent / "tmp" / "stryker_out.txt"
_STRYKER_OUT  = _REPO_ROOT / "StrykerOutput"
_BACKEND_OUT  = _STRYKER_OUT / "Backend"
_PROJECT_DIR  = _REPO_ROOT / "Server"


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
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mutate", metavar="GLOB[,GLOB…]",
                        help="Datei(en) mutieren, relativ zu Server/ (z.B. Domain/Foo.cs "
                             "oder Domain/Foo.cs,Endpoints/Bar.cs)")
    parser.add_argument("--verbose", action="store_true",
                        help="Alle nicht-getöteten Mutanten (Survived/Ignored/Timeout/NoCoverage) "
                             "mit Status, StatusReason, Zeile, Spalte")
    args = parser.parse_args()

    stryker_args = ["dotnet", "stryker"]
    if args.mutate:
        for pattern in resolve_mutate(args.mutate, _PROJECT_DIR, _REPO_ROOT):
            stryker_args += ["--mutate", pattern]

    _TMP_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starte: {' '.join(stryker_args)}")
    print(f"Live-Output (Fortschritt während des Laufs) → {_TMP_FILE}")
    # Erzwungen, weil stryker-summary.py als Subprozess denselben stdout ungepuffert beschreibt:
    # ohne Flush erscheint dessen Score VOR dieser Startzeile (OBS-S108-4 c).
    sys.stdout.flush()

    before = _snapshot_run_dirs()
    with RunLock(_TMP_FILE), open(_TMP_FILE, "w", encoding="utf-8") as out:
        result = subprocess.run(stryker_args, cwd=str(_REPO_ROOT), stdout=out, stderr=subprocess.STDOUT)

    # Rohoutput nur zeigen, wenn er zur Analyse gebraucht wird: bei Erfolg trägt er nichts bei,
    # was die Auswertung unten nicht besser sagt. Datei bewusst NICHT löschen – sie ist der
    # einzige Weg, einen laufenden Lauf zu beobachten, und erlaubt danach das vollständige
    # Nachlesen. Der nächste Lauf überschreibt sie ohnehin ("w").
    if _TMP_FILE.exists() and (result.returncode != 0 or args.verbose):
        lines = _TMP_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n".join(error_lines(lines, verbose=args.verbose)))

    # Stryker.NET schreibt den Report vor dem Threshold-Check, daher existiert er auch bei
    # Below-Threshold-Exit. Nur wenn kein neuer Report angelegt wurde, ist es ein echter Lauf-Fehler.
    run_dir = _move_new_run(before)
    if run_dir is None:
        print(f"\nStryker hat keinen neuen Report erzeugt (Exit {result.returncode}) – Lauf-Fehler.", file=sys.stderr)
        sys.exit(result.returncode or 1)
    print(f"\nReport verschoben → {run_dir}")
    sys.stdout.flush()

    # stryker-summary.py ist das maßgebliche Gate (Score < 100 % → exit 1) und deckt sich mit
    # Strykers eigenem break-Threshold. Bei Abweichung gewinnt das Fail.
    summary_args = [sys.executable, str(_SCRIPTS_DIR / "stryker-summary.py")]
    if args.verbose:
        summary_args.append("--verbose")
    summary_result = subprocess.run(summary_args)
    sys.exit(summary_result.returncode or (1 if result.returncode != 0 else 0))


if __name__ == "__main__":
    main()

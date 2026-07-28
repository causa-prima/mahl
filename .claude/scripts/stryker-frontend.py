#!/usr/bin/env python3
"""
Stryker JS/TS (nativ via npx) + automatische Auswertung via stryker-summary.py.

Verwendung:
  python3 .claude/scripts/stryker-frontend.py                              # alle Dateien
  python3 .claude/scripts/stryker-frontend.py --mutate src/pages/Foo.tsx   # eine Datei
  python3 .claude/scripts/stryker-frontend.py --mutate src/a.ts,src/b.tsx  # mehrere Dateien
  python3 .claude/scripts/stryker-frontend.py --verbose                    # alle nicht-getöteten Mutanten

Pfade für --mutate: relativ zu Client/ (z.B. src/pages/IngredientsPage.tsx) – NICHT
repo-root-relativ. Mehrere Ziele als Kommaliste (keine Brace-Globs: StrykerJS splittet
am Komma und zerreißt sie). Ein Muster ohne Treffer bricht den Lauf ab, statt still über
null Dateien zu laufen.

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
from _run_lock import RunLock
from _stryker_target import resolve_mutate
from _wrapper_output import error_lines

_SCRIPTS_DIR  = Path(__file__).parent
_REPO_ROOT    = _SCRIPTS_DIR.parent.parent
_TMP_FILE     = _SCRIPTS_DIR.parent / "tmp" / "stryker_frontend_out.txt"
_CLIENT_DIR   = _REPO_ROOT / "Client"
_STRYKER_TMP  = _CLIENT_DIR / ".stryker-tmp"
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
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mutate", metavar="GLOB[,GLOB…]",
                        help="Datei(en) oder Glob(s) relativ zu Client/ (z.B. src/pages/Foo.tsx "
                             "oder src/a.ts,src/b.tsx)")
    parser.add_argument("--verbose", action="store_true",
                        help="Alle nicht-getöteten Mutanten anzeigen (via stryker-summary.py)")
    args = parser.parse_args()

    stryker_args = ["npx", "stryker", "run"]
    if args.mutate:
        # StrykerJS parst --mutate selbst als Kommaliste (createSplitter(',') in stryker-cli.js);
        # ein zweites --mutate-Flag würde das erste überschreiben → EIN Argument übergeben.
        patterns = resolve_mutate(args.mutate, _CLIENT_DIR, _REPO_ROOT)
        stryker_args += ["--mutate", ",".join(patterns)]

    _TMP_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starte: {' '.join(stryker_args)}")
    print(f"Live-Output (Fortschritt während des Laufs) → {_TMP_FILE}")
    # Erzwungen, weil stryker-summary.py als Subprozess denselben stdout ungepuffert beschreibt:
    # ohne Flush erscheint dessen Score VOR dieser Startzeile (OBS-S108-4 c).
    sys.stdout.flush()

    with RunLock(_TMP_FILE), open(_TMP_FILE, "w", encoding="utf-8") as out:
        # Pre-Clean innerhalb des Locks: liegengebliebene Sandboxes aus gekillten/gecrashten
        # Läufen entfernen. Stryker räumt .stryker-tmp/sandbox-XXX nur bei sauberem Abschluss
        # weg; ein Rest poisont den nächsten Lauf (ENOENT beim copyfile) und verfälscht ESLint.
        # Im Lock ausgeführt → kein Wettlauf mit einem Parallellauf (den weist der Lock ohnehin ab).
        shutil.rmtree(_STRYKER_TMP, ignore_errors=True)
        result = subprocess.run(stryker_args, cwd=str(_CLIENT_DIR), stdout=out, stderr=subprocess.STDOUT)

    # Rohoutput nur zeigen, wenn er zur Analyse gebraucht wird: bei Erfolg trägt er nichts bei,
    # was die Auswertung unten nicht besser sagt. Datei bewusst NICHT löschen – sie ist der
    # einzige Weg, einen laufenden Lauf zu beobachten, und erlaubt danach das vollständige
    # Nachlesen. Der nächste Lauf überschreibt sie ohnehin ("w").
    if _TMP_FILE.exists() and (result.returncode != 0 or args.verbose):
        lines = _TMP_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n".join(error_lines(lines, verbose=args.verbose)))

    # StrykerJS schreibt den Report VOR dem Threshold-Check, daher existiert er auch bei
    # Below-Threshold-Exit (Score < break). Nur wenn gar kein Report da ist, ist es ein echter
    # Lauf-Fehler (z.B. Compile-Fehler) – dann hart abbrechen.
    report_present = _STRYKER_SRC.exists() and any(_STRYKER_SRC.iterdir())
    if not report_present:
        print(f"\nStryker hat keinen Report erzeugt (Exit {result.returncode}) – Lauf-Fehler.", file=sys.stderr)
        sys.exit(result.returncode or 1)

    timestamp = datetime.now().strftime("%Y-%m-%d.%H-%M-%S")
    report_json = _copy_reports(timestamp)
    print(f"\nReport kopiert → {report_json.parent.parent}")
    sys.stdout.flush()

    # stryker-summary.py ist das maßgebliche Gate (Score < 100 % → exit 1) und deckt sich mit
    # Strykers eigenem break-Threshold. Bei Abweichung gewinnt das Fail.
    summary_args = [sys.executable, str(_SCRIPTS_DIR / "stryker-summary.py"), str(report_json)]
    if args.verbose:
        summary_args.append("--verbose")
    summary_result = subprocess.run(summary_args)
    sys.exit(summary_result.returncode or (1 if result.returncode != 0 else 0))


if __name__ == "__main__":
    main()

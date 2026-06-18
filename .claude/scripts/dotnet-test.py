#!/usr/bin/env python3
"""
dotnet test (nativ).

Verwendung:
  python3 .claude/scripts/dotnet-test.py
  python3 .claude/scripts/dotnet-test.py --filter TestMethodName
  python3 .claude/scripts/dotnet-test.py --verbose

Branch-Coverage wird automatisch gemessen, wenn kein --filter gesetzt ist.
Threshold: 100% Branch + Line. Unterschreitung → Exit-Code 1.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _util import REPO_ROOT, run_dotnet

_RELEVANT = re.compile(
    r"(^\s*Failed|^\s*Passed|^\s*Skipped|^\s*Total"
    r"|Error Message|Build FAILED|Build succeeded"
    r"|\s+at mahl\.)",
    re.MULTILINE,
)

_RESULTS_DIR = REPO_ROOT / "TestResults" / "coverage"
# Deterministischer Output-Pfad (kein rglob/latest → kein Stale-Masking).
_COVERAGE_FILE = _RESULTS_DIR / "coverage.cobertura.xml"
_THRESHOLD = 1.0  # 100 %


# LineDetail = (line_number | None, description)
# FileGap    = (filename, min_branch_rate, line_rate, [LineDetail])
type LineDetail = tuple[int | None, str]
type FileGap    = tuple[str, float, float, list[LineDetail]]


def _shorten(filename: str) -> str:
    """Kürzt den Dateipfad auf den projektrelativen Teil ab Server/ oder Client/."""
    for marker in ("Server/", "Client/"):
        idx = filename.replace("\\", "/").find(marker)
        if idx != -1:
            return filename[idx:]
    return filename


def _parse_coverage(path: Path) -> tuple[dict[str, float], list[FileGap]]:
    """
    Parst die cobertura.xml und gibt zurück:
      - Gesamt-Raten (Branch, Line)
      - Pro Datei mit Branch < 100%: (Dateiname, Branch-Rate, Line-Rate, Zeilen-Details)
        Zeilen-Details: [(Zeilennummer | None, Beschreibung)]
          - Zeilennummer + Beschreibung: konkrete Condition mit < 100% coverage
          - None + Beschreibung:         kein Zeilen-Detail (compiler-generierte Klasse, z.B. async state machine)
    """
    root = ET.parse(path).getroot()
    totals = {
        "Branch": float(root.get("branch-rate", "0")),
        "Line":   float(root.get("line-rate",   "0")),
    }

    # filename → (min_branch_rate, line_rate, details)
    by_file: dict[str, tuple[float, float, list[LineDetail]]] = {}

    for cls in root.iter("class"):
        br = float(cls.get("branch-rate", "0"))
        lr = float(cls.get("line-rate", "0"))
        if br >= _THRESHOLD and lr >= _THRESHOLD:
            continue

        filename = _shorten(cls.get("filename", cls.get("name", "?")))

        # Zeilen-Details sammeln
        details: list[LineDetail] = []
        has_lines = False
        for method in cls.iter("method"):
            for line in method.iter("line"):
                has_lines = True
                # Branch-Lücken: Conditions mit < 100% coverage
                for cond in line.findall("conditions/condition"):
                    cov = cond.get("coverage", "100%")
                    if cov != "100%":
                        line_num = int(line.get("number", "0"))
                        details.append((line_num, f"branch condition {cov}"))
                # Zeilen-Lücken: Zeilen mit 0 Hits und ohne Branch-Condition (sonst Doppelmeldung)
                if line.get("hits", "0") == "0" and not line.findall("conditions/condition"):
                    line_num = int(line.get("number", "0"))
                    details.append((line_num, "nicht ausgeführt (0 hits)"))

        if not has_lines and br < _THRESHOLD:
            # Compiler-generierte Klasse (z.B. async state machine): kein Zeilen-Detail
            short_class = cls.get("name", "").split("/")[-1]
            details.append((None, f"kein Zeilen-Detail (compiler-generiert: {short_class})"))

        if filename in by_file:
            existing_br, existing_lr, existing_details = by_file[filename]
            by_file[filename] = (min(existing_br, br), min(existing_lr, lr), existing_details + details)
        else:
            by_file[filename] = (br, lr, details)

    gaps: list[FileGap] = [
        (fn, br, lr, sorted(details, key=lambda d: d[0] or 0))
        for fn, (br, lr, details) in sorted(by_file.items(), key=lambda x: x[1][0])
    ]
    return totals, gaps


def _report_coverage(totals: dict[str, float], gaps: list[FileGap]) -> bool:
    sep = "─" * 60
    print(f"\n{sep}")
    print("  Branch Coverage")
    print(sep)
    all_ok = True
    for metric, rate in totals.items():
        pct = rate * 100
        ok = rate >= _THRESHOLD
        status = "✓" if ok else f"✗  (threshold: {_THRESHOLD * 100:.0f}%)"
        print(f"  {metric:<8} {pct:6.2f}%  {status}")
        if not ok:
            all_ok = False
    if gaps:
        print(f"\n  {'Datei':<48} {'Branch':>7}  {'Line':>6}")
        print(f"  {'─' * 48} {'──────':>7}  {'──────':>6}")
        for filename, br, lr, details in gaps:
            short = filename if len(filename) <= 48 else "…" + filename[-47:]
            print(f"  {short:<48} {br * 100:6.1f}%  {lr * 100:5.1f}%")
            for line_num, desc in details:
                if line_num is not None:
                    print(f"      Zeile {line_num:>3}: {desc}")
                else:
                    print(f"      → {desc}")
    print(sep)
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--filter", dest="filter_name", help="Test-Filter (FullyQualifiedName~...)")
    parser.add_argument("--verbose", action="store_true", help="Vollständigen Output anzeigen")
    args = parser.parse_args()

    # Coverage-Gate geparkt (docs/tech-debt.md TD-S089-1): unter dem MTP-Runner ist
    # coverlet.collector wirkungslos und ein MTP-natives Setup steht noch aus. Bis dahin
    # KEINE Coverage erheben (kein Fake-100% über Stale-Reports). Re-Enable: Collection-Args
    # engine-abhängig setzen (Output → _COVERAGE_FILE) + collect_coverage reaktivieren.
    collect_coverage = False

    dotnet_args = ["test"]
    if args.filter_name:
        dotnet_args.extend(["--filter", args.filter_name])

    output, exit_code = run_dotnet(dotnet_args)

    if args.verbose or not output.strip():
        print(output)
    else:
        lines = output.splitlines()
        relevant = [l for l in lines if _RELEVANT.search(l)]
        if relevant:
            print("\n".join(relevant))
        else:
            # Kein Match → vollständigen Output zeigen (z.B. unerwarteter Fehler)
            print(output)

    if collect_coverage:
        # Fail-closed: keine cobertura = kein bestandenes Gate (nie wieder still durchwinken).
        if exit_code != 0:
            sys.exit(exit_code)  # Tests rot → Coverage irrelevant
        if not _COVERAGE_FILE.exists():
            print(
                f"\n[coverage] FEHLER: keine cobertura erzeugt ({_COVERAGE_FILE}) → Gate fail-closed.",
                file=sys.stderr,
            )
            sys.exit(1)
        totals, gaps = _parse_coverage(_COVERAGE_FILE)
        all_ok = _report_coverage(totals, gaps)
        if not all_ok:
            sys.exit(1)
    else:
        print(
            "\n[coverage] ⚠️  Gate deaktiviert – MTP-Coverage-Setup ausstehend (docs/tech-debt.md TD-S089-1).",
            file=sys.stderr,
        )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

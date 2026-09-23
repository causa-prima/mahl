#!/usr/bin/env python3
"""
dotnet test (nativ).

Verwendung:
  python3 -m prozesscode.dotnet-test
  python3 -m prozesscode.dotnet-test --filter TestMethodName   # Substring der FQN (Klasse/Methode)
  python3 -m prozesscode.dotnet-test --verbose

Branch-Coverage wird automatisch gemessen, wenn kein --filter gesetzt ist.
Threshold: 100% Branch + Line. Unterschreitung → Exit-Code 1.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from ._util import REPO_ROOT, run_dotnet

_RELEVANT = re.compile(
    r"(^\s*Failed|^\s*Passed|^\s*Skipped|^\s*Total"
    r"|Error Message|Build FAILED|Build succeeded"
    r"|\s+at mahl\.)",
    re.MULTILINE,
)

_RESULTS_DIR = REPO_ROOT / "TestResults" / "coverage"
_STRYKER_CONFIG = REPO_ROOT / "stryker-config.json"
_TEST_PROJECT = "Server.Tests/mahl.Server.Tests.csproj"
_THRESHOLD = 1.0  # 100 %


_SUMMARY_PASSED = re.compile(r"Test run summary: Passed!.*?total: (\d+).*?duration: ([^\n]+)", re.DOTALL)


def verdict(output: str) -> str | None:
    """Eine Zeile für einen grünen Lauf im MTP-Modus von `dotnet test` – sonst None (Details nötig)."""
    match = _SUMMARY_PASSED.search(output)
    return f"✓ {match.group(1)} Backend-Tests grün, {match.group(2).strip()}" if match else None


def coverage_args(stryker_config: dict, results_dir: Path) -> list[str]:
    """MTP-Argumente für coverlet.MTP (ADR-S089-1).

    Gemessen wird wie vor S089: nur `mahl.Server`, Auto-Properties übersprungen (keine echten
    Branches). Die Datei-Ausschlüsse sind die `!`-Einträge aus Strykers `mutate` – Coverage und
    Mutation sollen denselben Code als „Produktcode" ansehen, also eine Liste, nicht zwei.
    """
    args = [
        "--coverlet", "--coverlet-output-format", "cobertura",
        "--coverlet-include", "[mahl.Server]*",
        "--coverlet-skip-auto-props",
        # Eigenes Attribut statt [ExcludeFromCodeCoverage]: das verwirft Stryker.NET mit (ADR-S041-9).
        "--coverlet-exclude-by-attribute", "ExcludeFromCoverageGate",
        "--results-directory", str(results_dir),
    ]
    for glob in stryker_config["stryker-config"]["mutate"]:
        if glob.startswith("!"):
            args.extend(["--coverlet-exclude-by-file", glob[1:]])
    return args


def clear_results(results_dir: Path) -> None:
    """Leert das Report-Verzeichnis vor dem Lauf – danach kann nur ein frischer Report darin liegen."""
    results_dir.mkdir(parents=True, exist_ok=True)
    for old in results_dir.iterdir():
        if old.is_file():
            old.unlink()


def find_report(results_dir: Path) -> Path | None:
    """Der cobertura-Report dieses Laufs – oder None, wenn nicht genau einer existiert.

    coverlet.MTP hängt einen Zeitstempel an den Dateinamen, ein fester Pfad ist nicht vorgebbar.
    Fail-closed: kein Report ist kein bestandenes Gate, mehrere sind nicht eindeutig einem Lauf
    zuzuordnen (Stale-Masking, TD-S089-1).
    """
    # Real beobachtet (S132): `coverage.cobertura.<Zeitstempel>.xml` – nicht das Muster des Doku-Beispiels.
    reports = list(results_dir.glob("*.cobertura.*.xml"))
    return reports[0] if len(reports) == 1 else None


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


def _is_noise(line: str) -> bool:
    """Zeilen eines Fehlerblocks, die nichts zur Analyse beitragen: Framework-Frames, Assembly-Pfad."""
    stripped = line.strip()
    if stripped.startswith("at "):
        return not stripped.startswith("at mahl.")  # nur der Quellort im eigenen Code zählt
    return stripped.startswith(("from ", "--- End of stack trace"))


def _failure_blocks(output: str) -> list[str]:
    """Die 'failed …'-Blöcke: Kopfzeile plus die eingerückten Folgezeilen bis zur nächsten
    nicht eingerückten Zeile – Assertion-Meldung und Quell-Frame, ohne Rauschen."""
    lines = output.splitlines()
    blocks: list[str] = []
    for idx, line in enumerate(lines):
        if not line.startswith("failed "):
            continue
        kept = [line]
        for folge in lines[idx + 1:]:
            if not folge[:1].isspace():
                break
            if not _is_noise(folge):
                kept.append(folge)
        blocks.append("\n".join(kept))
    return blocks


_SUMMARY_COUNTS = re.compile(r"total: (\d+)\s+failed: (\d+)")


def failure_report(output: str) -> str | None:
    """Kompakter Bericht eines roten Laufs im MTP-Modus – oder None ohne Testblöcke (z.B.
    Build-Fehler). Die Details stehen im MTP-Modus direkt auf stdout (S132 beobachtet); die
    frühere UTF-16-Log-Datei, auf die stdout verwies, gibt es dort nicht mehr."""
    blocks = _failure_blocks(output)
    if not blocks:
        return None
    counts = _SUMMARY_COUNTS.search(output)
    kopf = f"✗ {counts.group(2)} von {counts.group(1)} Backend-Tests rot" if counts else "✗ Backend-Tests rot"
    return kopf + "\n\n" + "\n\n".join(blocks)


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
    parser.add_argument("--filter", dest="filter_name",
                        help="Substring des voll-qualifizierten Testnamens (Namespace.Klasse.Methode)")
    parser.add_argument("--verbose", action="store_true", help="Vollständigen Output anzeigen")
    args = parser.parse_args()

    # Coverage nur beim vollen Lauf – ein gefilterter Lauf deckt per Definition nicht alles ab.
    collect_coverage = not args.filter_name

    app_args: list[str] = []
    if args.filter_name:
        # MTP/xunit.v3 ignoriert die VSTest-Option --filter (warning MTP0001, läuft still die
        # volle Suite). Der Runner filtert über --filter-method gegen den voll-qualifizierten
        # Namen (Namespace.Klasse.Methode); *…* macht das Pattern zur Substring-Suche.
        # 0 Treffer → MTP failt fail-closed (Exit 1), kein eigener Guard nötig.
        app_args.extend(["--filter-method", f"*{args.filter_name}*"])
    if collect_coverage:
        clear_results(_RESULTS_DIR)
        stryker_config = json.loads(_STRYKER_CONFIG.read_text(encoding="utf-8"))
        app_args.extend(coverage_args(stryker_config, _RESULTS_DIR))

    # MTP-Modus von `dotnet test` (global.json): Test-App-Argumente direkt, ohne VSTest-`--`.
    dotnet_args = ["test", "--project", _TEST_PROJECT, *app_args]
    output, exit_code = run_dotnet(dotnet_args)

    summary = verdict(output) or failure_report(output)
    if args.verbose or not output.strip():
        print(output)
    elif summary:
        print(summary)
    else:
        lines = output.splitlines()
        relevant = [line for line in lines if _RELEVANT.search(line)]
        if relevant:
            print("\n".join(relevant))
        else:
            # Kein Match → vollständigen Output zeigen (z.B. unerwarteter Fehler)
            print(output)

    if collect_coverage:
        # Fail-closed: keine cobertura = kein bestandenes Gate (nie wieder still durchwinken).
        if exit_code != 0:
            sys.exit(exit_code)  # Tests rot → Coverage irrelevant
        report = find_report(_RESULTS_DIR)
        if report is None:
            print(
                f"\n[coverage] FEHLER: nicht genau ein cobertura-Report in {_RESULTS_DIR} → Gate fail-closed.\n"
                "   Prüfen: ist coverlet.MTP im Testprojekt referenziert (ADR-S089-1)? Details: --verbose",
                file=sys.stderr,
            )
            sys.exit(1)
        totals, gaps = _parse_coverage(report)
        all_ok = _report_coverage(totals, gaps)
        if not all_ok:
            sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Wie nutzen die Agenten ihr Werkzeug? Die Filter-Quote der Wrapper-Läufe.

**Filter-Quote (OBS-S085-3):** Wie oft wird die Ausgabe eines Wrapper-Scripts nachgelagert
durch `| grep`/`| tail`/… gefiltert, obwohl die Wrapper seit S109 im Erfolgsfall nur noch das
Verdikt ausgeben? Sinkt die Quote nicht, ist die Gewohnheits-These bestätigt und nur noch ein
mechanischer Guard wirksam. Gezählt wird ausschließlich die AUSFÜHRUNG eines Wrappers, nicht
das Lesen seiner Datei (`grep … qa-check.py`) – sonst zählte Datei-Inspektion als Filterung.

Beispiele:
  python3 -m prozesscode.tool-usage              # Filter-Quote je Monat
  python3 -m prozesscode.tool-usage --verbose    # zusätzlich Beispielzeilen
  python3 -m prozesscode.tool-usage --since 2026-07-30   # nur nach dem S109-Umbau

`--since` trennt Vor- und Nach-Maßnahme: Die Monats-Buckets allein können das nicht, wenn der
Stichtag mitten im Monat liegt (der S109-Wrapper-Umbau fiel auf den 29.07.). Ohne den Filter
ließe sich die Wirkung nur aus Monatssummen ableiten – rechnen statt messen.
"""
import argparse
import re
from collections import Counter


from ._cli import Parser
from ._util import REPO_ROOT  # noqa: E402

ALLOWED_LOG = REPO_ROOT / ".claude" / "tmp" / "allowed-commands.log"

# Genau die Gate-/Test-Wrapper, die S109 gemessen hat – die Liste NICHT erweitern, sonst wird
# die Quote unvergleichbar mit der Basislinie (517 Läufe, 83 %). Analyse-Scripte wie
# `read-breakdown.py` gehören ausdrücklich nicht dazu: Ihre lange Ausgabe ist zum Zerschneiden
# gedacht, ein Filter darauf ist bestimmungsgemäß und kein Symptom.
WRAPPERS = ("dotnet-test", "dotnet-stryker", "vitest-run", "playwright-test",
            "stryker-frontend", "eslint-run", "jscpd-run", "qa-check", "stryker-summary")
# Drei Aufrufformen, ein Name: `-m prozesscode.X` ist der heutige Weg, `prozesscode/X.py` und
# `.claude/scripts/X.py` sind die früheren. Die ausgewerteten Logs reichen über den Umzug
# (S129) hinaus zurück – ein Muster nur für die neue Form setzte die halbe Historie
# stillschweigend auf null, und die Quote verglichen mit der Basislinie wäre wertlos.
RUN_RE = re.compile(r"python3\s+(?:-m\s+prozesscode\.|\S*(?:prozesscode|\.claude/scripts)/)("
                    + "|".join(WRAPPERS) + r")(?:\.py)?\b")
FILTER_RE = re.compile(r"\|\s*(tail|head|grep|sed|awk)\b")
STAMP_RE = re.compile(r"^\[((\d{4}-\d{2})-\d{2}) ")


def line_date(line: str) -> str | None:
    """Der Tag der Zeile als `YYYY-MM-DD` – oder None, wenn sie keinen Zeitstempel trägt.

    Das Log schreibt den vollen Zeitstempel; die Monats-Aggregation unten wirft den Tag weg.
    Für ein Vor/Nach-Urteil über eine Maßnahme braucht es ihn aber (ein Stichtag mitten im
    Monat lässt sich sonst nicht schneiden), deshalb hier getrennt zugänglich.
    """
    stamp = STAMP_RE.match(line)
    return stamp.group(1) if stamp else None


def classify_line(line: str) -> tuple[str, str, bool] | None:
    """(Monat, Wrapper, wurde gefiltert) – oder None, wenn die Zeile kein Wrapper-Lauf ist.

    Zwei Feinheiten: Nur Zeilen mit Zeitstempel sind Befehlsanfänge (der Rest sind
    Fortsetzungszeilen mehrzeiliger Befehle), und ein Filter zählt nur, wenn er **nach** dem
    Wrapper-Aufruf steht – `grep foo | python3 … qa-check.py` filtert dessen Ausgabe nicht.
    """
    stamp = STAMP_RE.match(line)
    if not stamp:
        return None
    match = RUN_RE.search(line)
    if not match:
        return None
    return stamp.group(2), match.group(1), bool(FILTER_RE.search(line, match.end()))


def measure_filter_quote(path=None, since=None) -> tuple[Counter, Counter, Counter, list[str]]:
    """(Läufe je Monat, gefiltert je Monat, gefiltert je Wrapper, Beispielzeilen).

    `since` (`YYYY-MM-DD`, inklusiv) beschränkt auf Läufe ab diesem Tag – so wird die Quote
    nach einem Maßnahmen-Stichtag messbar statt aus Monatssummen abgeleitet.
    """
    runs: Counter = Counter()
    filtered: Counter = Counter()
    by_wrapper: Counter = Counter()
    examples: list[str] = []

    log = path or ALLOWED_LOG
    if not log.exists():
        return runs, filtered, by_wrapper, examples

    with open(log, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if since:
                day = line_date(line)
                # ISO-Datum: lexikographischer Vergleich ist chronologisch.
                if day is None or day < since:
                    continue
            result = classify_line(line)
            if not result:
                continue
            month, wrapper, was_filtered = result
            runs[month] += 1
            if was_filtered:
                filtered[month] += 1
                by_wrapper[wrapper] += 1
                if len(examples) < 10:
                    examples.append(line.strip()[:130])

    return runs, filtered, by_wrapper, examples


def print_filter_quote(verbose: bool, since: str | None = None) -> None:
    runs, filtered, by_wrapper, examples = measure_filter_quote(since=since)
    print("=" * 78)
    print("OBS-S085-3: nachgelagert gefilterte Wrapper-AUSFÜHRUNGEN")
    if since:
        print(f"  (nur Läufe ab {since})")
    print("=" * 78)
    if not runs:
        quelle = f"keine Wrapper-Läufe ab {since}" if since else "enthält keine Wrapper-Läufe"
        print(f"  Keine Daten – {ALLOWED_LOG} fehlt oder {quelle}.")
        return

    print(f"  {'Monat':<10} {'Läufe':>8} {'gefiltert':>11} {'Quote':>7}")
    for month in sorted(runs):
        quote = filtered[month] / runs[month] * 100
        print(f"  {month:<10} {runs[month]:>8} {filtered[month]:>11} {quote:>6.0f}%")
    total_r, total_f = sum(runs.values()), sum(filtered.values())
    print(f"  {'GESAMT':<10} {total_r:>8} {total_f:>11} {total_f / total_r * 100:>6.0f}%")
    print(f"\n  Gefiltert je Wrapper: {dict(by_wrapper.most_common())}")

    if verbose and examples:
        print("\n  Beispiele:")
        for example in examples:
            print(f"    {example}")


def main() -> None:
    parser = Parser(
        description="Werkzeug-Nutzung der Agenten: Filter-Quote der Wrapper-Läufe.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--verbose", action="store_true", help="Beispielzeilen zeigen")
    parser.add_argument("--since", metavar="YYYY-MM-DD",
                        help="nur Läufe ab diesem Tag (inklusiv) – trennt Vor/Nach einer Maßnahme")
    args = parser.parse_args()

    if args.since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.since):
        parser.error(f"--since braucht das Format YYYY-MM-DD, nicht {args.since!r}")
    print_filter_quote(args.verbose, args.since)


if __name__ == "__main__":
    main()

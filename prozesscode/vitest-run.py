#!/usr/bin/env python3
"""
vitest run (nativ über npm).

Verwendung:
  python3 -m prozesscode.vitest-run                   # alle Tests (einmalig, kein Watch)
  python3 -m prozesscode.vitest-run --filter Pattern  # nach TESTname filtern (vitest -t)
  python3 -m prozesscode.vitest-run --file Pattern    # nach DATEIname filtern (vitest positional;
                                                      #  Pfad relativ zu Client/ oder ab Repo-Wurzel;
                                                      #  mehrfach angebbar)
  python3 -m prozesscode.vitest-run --verbose         # vollständiger Output inkl. npm-Header

--filter und --file sind jeweils unabhängig optional und beliebig kombinierbar.

--filter matcht als Substring gegen den voll-qualifizierten Testnamen (describe-Block und Test
mit ' > ' verbunden, seit vitest 5);
nicht-passende Tests werden übersprungen. Matcht das Pattern nichts, würde vitest grün durchlaufen –
der Wrapper meldet das als FEHLER (Exit 1) und weist ausgeführte/übersprungene Tests aus.
"""
import argparse
import re
import sys

from ._cli import Parser
from ._util import run_npm
from ._wrapper_output import emit, strip_noise

# Verzeichnis, in dem run_npm vitest startet (Default von run_npm), als Pfadpräfix ab Repo-Wurzel.
_CLIENT_PREFIX = "Client/"

_FILE_HELP = ("Dateiname-Filter (vitest positional) – grenzt auf Testdateien mit passendem Pfad ein; "
              "mehrfach angegeben läuft jede passende Datei")

# vitest-Banner und Zeitstempel – kein Aussagewert für „sind die Tests grün?".
_VITEST_CHROME = re.compile(r"^\s*RUN\s+v[\d.]|^\s*Start at\s|^\s*Duration\s")

# Testing Library gibt bei einer fehlgeschlagenen Abfrage den ganzen DOM aus – je rotem Test oft zweimal
# und je rund 200 Zeilen (14 rote Tests ergaben mehrere hundert KB). Der Anfang zeigt, welche Seite
# gerendert war; den Rest gibt es mit --verbose.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
# `<body>` – oder `<body` mit Attributen auf den Folgezeilen (ein offener MUI-Dialog setzt `style`).
_DOM_DUMP_START = re.compile(r"<body(?:>|\s|$)")
# `</body>` – oder `...`, mit dem Testing Library einen zu langen Dump selbst abschneidet; danach
# folgt der Stacktrace ohne Leerzeile.
_DOM_DUMP_END = frozenset({"</body>", "..."})
_DOM_DUMP_KEEP = 12
DOM_DUMP_CUT = "  … {count} Zeilen DOM gekürzt – vollständig: --verbose"

# vitest-Zusammenfassung: "  Tests  3 passed | 13 skipped (16)" (nicht "Test Files …").
_TESTS_SUMMARY = re.compile(r"^\s*Tests\s+(?P<body>.+?)\s+\((?P<total>\d+)\)\s*$", re.MULTILINE)
_FILES_SUMMARY = re.compile(r"^\s*Test Files\s+.+?\((?P<total>\d+)\)\s*$", re.MULTILINE)
_DURATION = re.compile(r"^\s*Duration\s+(?P<value>[\d.]+m?s)", re.MULTILINE)

FILTER_OHNE_TREFFER = "✗ --filter traf keinen Test – Pattern prüfen (s. [filter]-Zeilen)"


def _parse_counts(output: str) -> dict[str, int] | None:
    """Liest passed/failed/skipped/total aus der vitest-'Tests'-Zeile (None, wenn keine da)."""
    match = _TESTS_SUMMARY.search(output)
    if not match:
        return None

    def count(status: str) -> int:
        found = re.search(rf"(\d+)\s+{status}", match.group("body"))
        return int(found.group(1)) if found else 0

    return {
        "passed":  count("passed"),
        "failed":  count("failed"),
        "skipped": count("skipped"),
        "total":   int(match.group("total")),
    }


def shorten_dom_dumps(lines: list[str]) -> list[str]:
    """Kürzt jede DOM-Ausgabe auf ihre ersten Zeilen plus Hinweis.

    Eine Ausgabe beginnt mit `<body` und endet mit `</body>` oder – von Testing Library selbst
    gekürzt (`DEBUG_PRINT_LIMIT`) – mit `...`. Fehlt beides, endet sie an der ersten Leerzeile oder
    dort, wo die nächste beginnt. So verschluckt eine Ausgabe nie den Fehlertext dahinter.
    """
    result: list[str] = []
    dump: list[str] | None = None
    for line in lines:
        # Nur ASCII-Leerraum abschneiden: Ein Textknoten aus einem schmalen Leerzeichen (U+2009 vor dem
        # Pflicht-Asterisk) ist DOM-Inhalt, keine Leerzeile – str.strip() machte ihn zum Dump-Ende.
        plain = _ANSI.sub("", line).strip(" \t\r")
        if dump is not None and (not plain or _DOM_DUMP_START.match(plain)):
            result.extend(_shortened(dump))
            dump = None
        if dump is None:
            if _DOM_DUMP_START.match(plain):
                dump = [line]
            else:
                result.append(line)
            continue
        dump.append(line)
        if plain in _DOM_DUMP_END:
            result.extend(_shortened(dump))
            dump = None
    return result + (_shortened(dump) if dump else [])


def _shortened(dump: list[str]) -> list[str]:
    if len(dump) <= _DOM_DUMP_KEEP + 1:
        return dump
    return [*dump[:_DOM_DUMP_KEEP], DOM_DUMP_CUT.format(count=len(dump) - _DOM_DUMP_KEEP)]


def main() -> None:
    parser = Parser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--filter", dest="filter_name", metavar="PATTERN",
                        help="Testname-Filter via vitest -t (Substring/Regex gegen Testnamen)")
    parser.add_argument("--file", dest="file_names", metavar="PATTERN", action="append", default=[],
                        help=_FILE_HELP)
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output ohne Filterung")
    args = parser.parse_args()

    # "run" als erstes Argument → einmaliger Lauf, kein Watch-Mode
    npm_args = ["run", "test", "--", "run"]
    # Positional (Datei) muss vor den Optionen stehen. vitest läuft in Client/ und matcht relativ dazu –
    # ein Pfad ab Repo-Wurzel, wie git ihn nennt, fände sonst keine Datei.
    npm_args.extend(name.removeprefix(_CLIENT_PREFIX) for name in args.file_names)
    if args.filter_name:
        npm_args.extend(["-t", args.filter_name])

    output, exit_code = run_npm(npm_args)

    counts = _parse_counts(output)
    files = _FILES_SUMMARY.search(output)
    duration = _DURATION.search(output)
    matched = counts["passed"] + counts["failed"] if counts else None
    ohne_treffer = bool(args.filter_name) and matched == 0
    if ohne_treffer:
        emit(verbose=args.verbose, output=output, verdict=FILTER_OHNE_TREFFER)
    elif exit_code == 0 and counts and counts["failed"] == 0:
        skipped = f", {counts['skipped']} übersprungen" if counts["skipped"] else ""
        scope = f", {files.group('total')} Dateien" if files else ""
        took = f", {duration.group('value')}" if duration else ""
        verdict = f"✓ {counts['passed']} Tests grün{skipped}{scope}{took}"
        emit(verbose=args.verbose, output=output, verdict=verdict)
    else:
        # Rot: der vitest-Fehlerblock (Diff, Stack, Datei/Zeile) IST die Analyse-Information –
        # Banner und Zeitstempel fallen weg, DOM-Ausgaben werden auf ihren Anfang gekürzt.
        failed = counts["failed"] if counts else "?"
        emit(verbose=args.verbose, output=output,
             verdict=f"✗ {failed} Test(s) rot – Details oben",
             details=shorten_dom_dumps(strip_noise(output, _VITEST_CHROME)))

    # --filter (vitest -t) matcht als Substring gegen den voll-qualifizierten Testnamen.
    # Nicht-passende Tests werden ÜBERSPRUNGEN, nicht gefiltert – matcht das Pattern nichts,
    # läuft vitest grün durch (0 ausgeführt). Das machen wir explizit und fail-closed.
    if args.filter_name:
        print(
            f"\n[filter] --filter '{args.filter_name}' matcht als Substring gegen den "
            f"voll-qualifizierten Testnamen (describe-Block und Test mit ' > ' verbunden).",
            file=sys.stderr,
        )
        if counts is not None:
            print(
                f"[filter] {matched} ausgeführt, {counts['skipped']} übersprungen "
                f"(von {counts['total']}).",
                file=sys.stderr,
            )
            if ohne_treffer:
                print(
                    "[filter] ⚠️  0 Tests gematcht – alle übersprungen. Tippfehler im Pattern "
                    "oder Test existiert (noch) nicht? → als FEHLER gewertet.",
                    file=sys.stderr,
                )
                exit_code = exit_code or 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

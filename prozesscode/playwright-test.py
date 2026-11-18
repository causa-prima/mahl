#!/usr/bin/env python3
"""
Playwright E2E-Tests (nativ über npm).

Verwendung:
  python3 -m prozesscode.playwright-test                        # alle E2E-Tests
  python3 -m prozesscode.playwright-test --filter ingredients   # nach Datei/Testname filtern
  python3 -m prozesscode.playwright-test --verbose              # vollständiger Output
  python3 -m prozesscode.playwright-test --filter X --handybreite 375   # Sichtprüfung

--handybreite lässt die Tests im schmalen Viewport laufen und legt je Test die Bilder des
Laufs ab (Pfad im Verdikt; mit Read ansehen). Die Bildfolge hinkt dem Browser leicht
hinterher: Ein Bild heißt nach der zuletzt begonnenen Aktion, es zeigt nicht zwingend deren
Ergebnis – die Folge der Bilder ansehen, nicht ein einzelnes.
"""
import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

from ._cli import Parser
from ._run_lock import RunLock
from ._util import REPO_ROOT, run_npm
from ._wrapper_output import emit, strip_noise

# Playwrights Abschlusszeilen, z.B. "  12 passed (34.5s)" / "  2 failed".
_PASSED = re.compile(r"^\s*(\d+)\s+passed\b", re.MULTILINE)
_FAILED = re.compile(r"^\s*(\d+)\s+(?:failed|flaky)\b", re.MULTILINE)
_DURATION = re.compile(r"passed\s+\(([^)]+)\)")
_KEIN_TEST = re.compile(r"^Error: No tests found", re.MULTILINE)

KEIN_TEST_GEFUNDEN = "✗ --filter traf keinen E2E-Test – Pattern prüfen"

# Playwrights Ausgabeordner (leert Playwright bei jedem Lauf); `Client/playwright.config.ts`
# liest die Breite aus MAHL_HANDYBREITE und schaltet dann den Trace ein.
TEST_RESULTS = REPO_ROOT / "Client" / "test-results"
# Ein Lauf zur Zeit: Ein zweiter baute dasselbe Backend (gemeinsame Build-Ausgabe), scheiterte
# an dessen Port und läge zudem parallel im Speicher. Parallel starten Auditoren im Review-Loop.
_LAUF_LOCK = REPO_ROOT / ".claude" / "tmp" / "playwright_run"


def _ereignisse(archiv: zipfile.ZipFile, name: str) -> list[dict]:
    return [json.loads(zeile) for zeile in archiv.read(name).decode().splitlines() if zeile]


def bilder_aus_trace(trace: Path, ziel: Path) -> list[Path]:
    """Schreibt die Bilder eines Traces in Zeitfolge nach `ziel`, je benannt nach der zuletzt
    begonnenen Aktion des Tests (`03-Click-getByRole-….jpeg`)."""
    with zipfile.ZipFile(trace) as archiv:
        bilder = sorted((e["timestamp"], e["file"])
                        for name in archiv.namelist()
                        if name.endswith(".trace") and name != "test.trace"
                        for e in _ereignisse(archiv, name) if e["type"] == "screencast-frame")
        aktionen = sorted((e["startTime"], e["title"], e["params"])
                          for e in _ereignisse(archiv, "test.trace")
                          if e["type"] == "before" and e["method"] in ("pw:api", "expect"))
        ziel.mkdir(parents=True, exist_ok=True)
        dateien = []
        for nummer, (zeit, datei) in enumerate(bilder, 1):
            laufend = [a for a in aktionen if a[0] <= zeit][-1:]
            beschreibung = (f"{laufend[0][1]} {laufend[0][2].get('locator') or laufend[0][2].get('url', '')}"
                            if laufend else "Start")
            name = re.sub(r"\W+", "-", beschreibung).strip("-")[:60].rstrip("-")
            pfad = ziel / f"{nummer:02d}-{name}.jpeg"
            pfad.write_bytes(archiv.read(datei))
            dateien.append(pfad)
    return dateien


def _bilder_ablegen(breite: int) -> str:
    """Bilder aller Traces des Laufs nach `test-results/handybreite/<test>/`; Zeile fürs Verdikt."""
    ablage = TEST_RESULTS / "handybreite"
    traces = sorted(TEST_RESULTS.glob("*/trace.zip"))
    anzahl = sum(len(bilder_aus_trace(t, ablage / t.parent.name)) for t in traces)
    return f"\n  Bilder bei {breite} px: {ablage} ({anzahl} aus {len(traces)} Test" \
           f"{'s' if len(traces) != 1 else ''})"


def main() -> None:
    parser = Parser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--filter", dest="filter_name", metavar="PATTERN",
                        help="Dateiname oder Testname-Filter (Substring-Match)")
    parser.add_argument("--handybreite", type=int, metavar="PX",
                        help="Tests in dieser Breite laufen lassen und je Test die Bilder ablegen")
    parser.add_argument("--verbose", action="store_true",
                        help="Vollständiger Output ohne Filterung")
    args = parser.parse_args()

    npm_args = ["run", "test:e2e", "--"]
    if args.filter_name:
        npm_args.extend(["--grep", args.filter_name])
    if args.handybreite:
        os.environ["MAHL_HANDYBREITE"] = str(args.handybreite)

    with RunLock(_LAUF_LOCK, "E2E-Lauf"):
        output, exit_code = run_npm(npm_args)
    bilder = _bilder_ablegen(args.handybreite) if args.handybreite else ""

    passed = _PASSED.search(output)
    # Nur zusammenfassen, wenn der Lauf grün war UND die Abschlusszeile erkannt wurde –
    # sonst bleibt es beim vollständigen Output (fail-open, s. _wrapper_output).
    if exit_code == 0 and passed and not _FAILED.search(output):
        duration = _DURATION.search(output)
        took = f", {duration.group(1)}" if duration else ""
        emit(verbose=args.verbose, output=output,
             verdict=f"✓ {passed.group(1)} E2E-Tests grün{took}{bilder}")
        return
    if _KEIN_TEST.search(output):
        verdict = KEIN_TEST_GEFUNDEN
    else:
        # Rot: Playwrights Fehlerblock (Erwartung/Ist, Locator, Screenshot-Pfad) IST die
        # Analyse-Information und bleibt vollständig erhalten.
        failed = _FAILED.search(output)
        count = failed.group(1) if failed else "?"
        verdict = f"✗ {count} E2E-Test(s) rot – Details oben"
    emit(verbose=args.verbose, output=output, verdict=verdict + bilder,
         details=strip_noise(output))
    # Ein ✗ endet nie mit 0 – auch nicht, wenn Playwright selbst 0 meldet (flaky, nichts
    # bestanden): Ein Gate, das nur den Exit-Code liest, hielte den Lauf sonst für grün.
    sys.exit(exit_code or 1)


if __name__ == "__main__":
    main()

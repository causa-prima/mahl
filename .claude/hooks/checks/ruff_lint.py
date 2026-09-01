"""PostToolUse-Check: ruff über die gerade geänderte Python-Datei des Prozess-Codes.

Warum nicht nur `ruff-run.py` (S128): Ein Linter, den jemand aufrufen müsste, ist eine
Vorschrift ohne Praxis. Die Findings, die bei der Einführung im Bestand lagen, waren
überwiegend Hygiene – aber eines war ein `zip()` ohne `strict=`, das eine Regression bei
ungleich langen Listen still falsch rechnen ließ. Solche Stellen entstehen laufend und
werden ohne Automatik erst gefunden, wenn jemand gezielt sucht.

Nur die GEÄNDERTE Datei, nicht der Bestand: Fremde Fundstellen mitten in fremder Arbeit
werden weggeklickt, und ein Volllauf bei jedem Edit kostet Zeit ohne Gegenwert.

Nicht-blockierend: Der Linter ist Beiwerk. Sein Ausfall – oder ein Fund – darf das Schreiben
nicht anhalten; blockierend sind die Guards, die Korrektheit sichern.
"""
import subprocess
from pathlib import Path

from .common import HookInput

ROOT = Path(__file__).resolve().parents[3]
RUFF = ROOT / ".venv" / "bin" / "ruff"

_WATCHED = (".claude/scripts/", ".claude/hooks/")
# Mehr Zeilen sagen nichts Neues – der volle Lauf steht im Hinweis darunter.
_MAX_ZEILEN = 8


def _is_watched(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    return norm.endswith(".py") and any(seg in norm for seg in _WATCHED)


def _ruff_vorhanden() -> bool:
    return RUFF.is_file()


def _laufe(*befehl: str) -> subprocess.CompletedProcess:
    return subprocess.run(befehl, capture_output=True, text=True, cwd=ROOT, timeout=30)


def check(inp: HookInput) -> list[str]:
    if not _is_watched(inp.file_path):
        return []

    # Meldet sich statt stumm auszufallen: Ohne venv gäbe es sonst nie wieder eine
    # Lint-Meldung, und der Ausfall wäre von „alles sauber" nicht zu unterscheiden.
    if not _ruff_vorhanden():
        return ["⚠️ ruff nicht verfügbar – Prozess-Code wird nicht gelintet.\n"
                "  Herstellen: python3 -m venv .venv && "
                ".venv/bin/pip install -r requirements-dev.txt"]

    try:
        ergebnis = _laufe(str(RUFF), "check", inp.file_path, "--output-format", "concise")
    except Exception as exc:  # noqa: BLE001 – der Linter darf das Schreiben nie mitreißen
        return [f"⚠️ ruff-Lauf fehlgeschlagen: {exc}"]

    if ergebnis.returncode == 0:
        return []

    zeilen = [z for z in ergebnis.stdout.splitlines()
              if z.strip() and not z.startswith(("Found ", "[*]"))]
    gezeigt = zeilen[:_MAX_ZEILEN]
    rest = f"\n  … und {len(zeilen) - len(gezeigt)} weitere" if len(zeilen) > len(gezeigt) else ""
    return ["⚠️ ruff meldet in dieser Datei:\n  " + "\n  ".join(gezeigt) + rest +
            "\n  Vollständig: python3 .claude/scripts/ruff-run.py "
            "(sichere Fixes: --fix)"]

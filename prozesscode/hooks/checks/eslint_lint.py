"""PostToolUse-Check: ESLint über die gerade geänderte TypeScript-Datei des Clients.

Warum nicht nur `eslint-run.py`: Bis hierher lief ESLint erst im qa-check, also nach der
Test-Freigabe. Ein Lint-Fehler blockierte dann einen Lauf, dessen Tests schon freigegeben
waren, und der Fix musste durch die Freigabe zurück. Je Edit kostet der Lauf rund 1,5 s,
beim ersten Mal mehr (die TypeScript-Typinformation wird aufgebaut).

Nur FEHLER, keine Warnungen: `Client/eslint.config.js` stuft Regeln wie `max-params` mit
Begründung als `warn` ein – das ist die Aussage der Konfiguration, dass diese Befunde
tolerabel sind, und blockieren kann auch der qa-check nur an Fehlern. Die Warnungen zeigt
`eslint-run` vollständig.

Nur die GEÄNDERTE Datei, nicht der Bestand, und nicht-blockierend – dieselben Gründe wie beim
ruff-Check (`ruff_lint.py`).
"""
import json
import subprocess
from pathlib import Path

from .common import HookInput

ROOT = Path(__file__).resolve().parents[3]
CLIENT = ROOT / "Client"
ESLINT = CLIENT / "node_modules" / ".bin" / "eslint"

# Mehr Zeilen sagen nichts Neues – der volle Lauf steht im Hinweis darunter.
_MAX_ZEILEN = 8
_FEHLER = 2  # ESLints Schweregrad: 1 = Warnung, 2 = Fehler


def _is_watched(file_path: str) -> bool:
    return (file_path.endswith((".ts", ".tsx"))
            and ("/Client/" in file_path or file_path.startswith("Client/"))
            and "/node_modules/" not in file_path)


def _eslint_vorhanden() -> bool:
    return ESLINT.is_file()


def _laufe(*befehl: str) -> subprocess.CompletedProcess:
    return subprocess.run(befehl, capture_output=True, text=True, cwd=CLIENT, timeout=60)


def _zeile(meldung: dict) -> str:
    position = f"{meldung['line']}:{meldung['column']} " if "line" in meldung else ""
    regel = f"{meldung['ruleId']}: " if meldung["ruleId"] else ""
    return position + regel + meldung["message"].splitlines()[0]


def check(inp: HookInput) -> list[str]:
    if not _is_watched(inp.file_path):
        return []

    # Meldet sich statt stumm auszufallen: Ohne node_modules gäbe es sonst nie wieder eine
    # Lint-Meldung, und der Ausfall wäre von „alles sauber" nicht zu unterscheiden.
    if not _eslint_vorhanden():
        return ["⚠️ ESLint nicht verfügbar – TypeScript wird je Edit nicht gelintet.\n"
                "  Herstellen: npm --prefix Client ci"]

    try:
        ergebnis = _laufe(str(ESLINT), "--format", "json", inp.file_path)
    except Exception as exc:  # noqa: BLE001 – der Linter darf das Schreiben nie mitreißen
        return [f"⚠️ ESLint-Lauf fehlgeschlagen: {exc}"]

    try:
        dateien = json.loads(ergebnis.stdout)
    except json.JSONDecodeError:
        grund = (ergebnis.stderr.strip().splitlines() or ["keine Meldung"])[0]
        return [f"⚠️ ESLint-Lauf ohne lesbares Ergebnis (Exit {ergebnis.returncode}): {grund}"]

    zeilen = [_zeile(m) for datei in dateien for m in datei["messages"]
              if m["severity"] == _FEHLER]
    if not zeilen:
        return []
    gezeigt = zeilen[:_MAX_ZEILEN]
    rest = f"\n  … und {len(zeilen) - len(gezeigt)} weitere" if len(zeilen) > len(gezeigt) else ""
    return [f"⚠️ ESLint meldet in dieser Datei {len(zeilen)} Fehler:\n  " + "\n  ".join(gezeigt)
            + rest + "\n  Vollständig: python3 -m prozesscode.eslint-run"]

"""
Tooling-Tests: fährt die eigene Werkzeug-Testsuite, wenn ein Script oder Hook geändert wurde.

Warum als PostToolUse-Check: Die Suite unter `.claude/hooks/tests/` sichert Hooks und
Wrapper-Scripts ab – also genau die Mechanismen, die alle anderen Gates durchsetzen –,
lief aber selbst in keinem Gate. In S113 fiel auf, dass eine geänderte Signatur in
`.claude/scripts/qa-check.py` vier Tests brach, ohne dass etwas rot wurde.

Warum nicht PreToolUse: Dort liegt die Änderung noch nicht auf der Platte; der Lauf
prüfte den alten Stand und wäre wertlos.

Ausgabe folgt der Wrapper-Politik des Projekts: im Erfolgsfall nichts, im Fehlerfall nur
das Analyse-Relevante (Datei:Zeile + Assertion), gedeckelt auf `_MAX_LINES` Einträge.

Registriert in der `CHECKS`-Liste von `check-code-quality-nonblocking.py` – nicht in
`settings.json`; ein Wechsel dort wirkt daher ohne Claude-Code-Reload.
"""
import os
import re
import subprocess
import sys

from .common import HookInput

_HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HOOKS_DIR))
_TESTS_REL = os.path.join(".claude", "hooks", "tests")

# Änderungen hier können die Suite brechen. `.claude/scripts/` ist ausdrücklich dabei:
# der Auslöser in S113 lag dort, nicht in den Hooks selbst.
_WATCHED = (".claude/scripts/", ".claude/hooks/")

_MAX_LINES = 10
_TIMEOUT_S = 120

_SUMMARY = re.compile(r'^\d+ failed')


def _is_watched(file_path: str) -> bool:
    """True für Python-Dateien unterhalb der beobachteten Verzeichnisse."""
    if not file_path.endswith(".py"):
        return False
    norm = file_path.replace("\\", "/")
    return any(seg in norm for seg in _WATCHED)


def _format_failures(stdout: str) -> str:
    """Baut die Meldung aus der `--tb=line`-Ausgabe von pytest."""
    details: list[str] = []
    summary = ""
    for line in stdout.splitlines():
        if "/tests/" in line and line.startswith("/"):
            details.append("  " + line.split("/tests/", 1)[1])
        elif _SUMMARY.match(line):
            summary = line

    shown = details[:_MAX_LINES]
    if len(details) > _MAX_LINES:
        shown.append(f"  … und {len(details) - _MAX_LINES} weitere")

    body = "\n".join(shown) if shown else "  (keine Detailzeilen – vollständig via pytest)"
    return (
        "⚠️ Tooling-Tests rot – die eigene Werkzeug-Suite ist nach dieser Änderung nicht grün:\n"
        f"{body}\n"
        f"{summary}\n"
        "  Diese Suite läuft in keinem anderen Gate. Ist das eine beabsichtigte RED-Phase, "
        "ignorieren; sonst vor dem Weiterarbeiten beheben.\n"
        "  Vollständig: python3 -m pytest .claude/hooks/tests/"
    )


def check(inp: HookInput) -> list[str]:
    if not _is_watched(inp.file_path):
        return []

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", _TESTS_REL, "-q", "--tb=line"],
            cwd=_REPO_ROOT, capture_output=True, text=True, timeout=_TIMEOUT_S,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []  # fail-open: ein nicht lauffähiger Testlauf ist kein Befund

    if proc.returncode == 0:
        return []
    return [_format_failures(proc.stdout)]

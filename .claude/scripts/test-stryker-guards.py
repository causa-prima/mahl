#!/usr/bin/env python3
"""Tests für die Stryker-Fehlsignal-Guards (_stryker_report.py, _stryker_target.py).

Diese Guards sind der Grund, warum ein Mutations-Lauf nicht mehr „100 %" melden kann, ohne
etwas gemessen zu haben. Genau solche Sicherungen brechen still – deshalb hier festgenagelt.

Aufruf: python3 .claude/scripts/test-stryker-guards.py
"""
import io
import os
import sys
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _stryker_report import (
    compute_metrics,
    format_score,
    format_status_breakdown,
    gate_code,
    has_no_mutants,
)
from _stryker_target import resolve_mutate

_REPO_ROOT = Path(__file__).parent.parent.parent

GREEN, RED, RESET = "\033[92m", "\033[91m", "\033[0m"
_failures: list[str] = []


def check(condition: bool, description: str) -> None:
    if condition:
        print(f"{GREEN}✓{RESET} {description}")
    else:
        print(f"{RED}✗{RESET} {description}")
        _failures.append(description)


def _files(*statuses_per_file: list[str]) -> dict:
    """Baut einen minimalen Report-`files`-Block aus Status-Listen (eine Liste je Datei)."""
    return {
        f"/repo/Server/File{i}.cs": {
            "mutants": [
                {"id": str(n), "status": s, "mutatorName": "Equality", "replacement": "!=",
                 "location": {"start": {"line": n + 1, "column": 1}}}
                for n, s in enumerate(statuses)
            ]
        }
        for i, statuses in enumerate(statuses_per_file)
    }


def _resolve_fails(raw: str, project_dir: Path) -> tuple[bool, str]:
    """Ruft resolve_mutate und meldet, ob es abgebrochen hat (+ die Fehlermeldung)."""
    buffer = io.StringIO()
    try:
        with redirect_stderr(buffer):
            resolve_mutate(raw, project_dir, _REPO_ROOT)
    except SystemExit as exit_signal:
        return exit_signal.code != 0, buffer.getvalue()
    return False, buffer.getvalue()


def test_null_mutanten_gate() -> None:
    print("\n── Null-Mutanten-Gate (ein Lauf ohne Messung ist kein bestandener Lauf) ──")
    # Nur Ignored/CompileError: genau das Bild eines --mutate-Laufs auf einen Excluded-Pfad.
    empty = compute_metrics(_files(["Ignored", "CompileError"]))
    check(has_no_mutants(empty), "Report ohne validen Mutanten wird als leer erkannt")
    check(empty["score"] is None, "Score ist None statt 100.0")
    check(gate_code(empty) == 1, "Gate schlägt fehl (vorher: exit 0 bei „100 %“)")
    check("n/a" in format_score(empty), "Anzeige nennt n/a statt einer Scheinzahl")

    nothing_at_all = compute_metrics({})
    check(gate_code(nothing_at_all) == 1, "Auch ein völlig leerer Report schlägt fehl")

    # Reale Variante: alle Mutanten scheitern am TypeScript-Checker. StrykerJS meldet dafür
    # einen NaN-Score und lässt ihn durchs eigene break-Threshold – hier muss es fehlschlagen.
    compile_errors = compute_metrics(_files(["CompileError", "CompileError"]))
    check(gate_code(compile_errors) == 1, "Nur-CompileError-Lauf schlägt fehl (Stryker lässt NaN durch)")
    check("CompileError: 2" in format_status_breakdown(compile_errors),
          "Status-Verteilung nennt den Grund für die 0 validen Mutanten")


def test_score_und_umfang() -> None:
    print("\n── Score & Umfang ──")
    perfect = compute_metrics(_files(["Killed", "Timeout"], ["Killed"]))
    check(gate_code(perfect) == 0, "Echte 100 % über valide Mutanten passieren das Gate")
    check(perfect["score"] == 100.0, "Killed + Timeout zählen als detected")
    check(perfect["mutated_files"] == 2, "Umfang zählt Dateien mit validen Mutanten")

    survived = compute_metrics(_files(["Killed", "Survived"]))
    check(gate_code(survived) == 1, "Ein Survivor schlägt fehl")
    check(survived["score"] == 50.0, "Score rechnet Survivor in den Nenner")

    nocoverage = compute_metrics(_files(["Killed", "NoCoverage"]))
    check(gate_code(nocoverage) == 1, "NoCoverage schlägt fehl (nicht mal ausgeführt)")

    # Ignored darf den Score NICHT verwässern – sonst könnten Suppressions ihn hochziehen.
    mixed = compute_metrics(_files(["Killed", "Survived", "Ignored", "CompileError"]))
    check(mixed["total_valid"] == 2, "Ignored/CompileError bleiben aus dem Nenner")

    scope_only_ignored = compute_metrics(_files(["Killed"], ["Ignored"]))
    check(scope_only_ignored["mutated_files"] == 1,
          "Eine Datei nur mit Ignored-Mutanten zählt nicht zum Umfang")


def test_mutate_validierung() -> None:
    print("\n── --mutate-Validierung (Abbruch statt stillem Leerlauf) ──")
    server, client = _REPO_ROOT / "Server", _REPO_ROOT / "Client"

    failed, message = _resolve_fails("Server/Endpoints/IngredientsEndpoints.cs", server)
    check(failed, "Repo-root-relativer Pfad bricht ab statt leer zu laufen")
    check("Endpoints/IngredientsEndpoints.cs" in message,
          "Fehlermeldung schlägt den projekt-relativen Pfad vor")

    failed, message = _resolve_fails("src/pages/{A.tsx,B.tsx}", client)
    check(failed, "Brace-Glob bricht ab")
    check("Kommaliste" in message, "Fehlermeldung nennt die Kommaliste als Ersatz")

    failed, _ = _resolve_fails("Domain/GibtsNicht.cs", server)
    check(failed, "Nicht existierende Datei bricht ab")

    failed, _ = _resolve_fails("   ", server)
    check(failed, "Leeres --mutate bricht ab")

    # Gültige Eingaben müssen unverändert durchgehen.
    check(resolve_mutate("Endpoints/IngredientsEndpoints.cs", server, _REPO_ROOT)
          == ["Endpoints/IngredientsEndpoints.cs"], "Einzelne gültige Datei passiert")
    check(resolve_mutate("Middleware/ETagMiddleware.cs,Types/NonEmptyTrimmedString.cs",
                         server, _REPO_ROOT) == ["Middleware/ETagMiddleware.cs",
                                                 "Types/NonEmptyTrimmedString.cs"],
          "Kommaliste wird in Einzelmuster zerlegt")
    check(len(resolve_mutate("src/**/*.ts", client, _REPO_ROOT)) == 1, "Glob mit Treffern passiert")
    check(resolve_mutate("Endpoints/IngredientsEndpoints.cs,!Domain/GibtsNicht.cs",
                         server, _REPO_ROOT)[1] == "!Domain/GibtsNicht.cs",
          "Ausschlussmuster (!) darf ins Leere zeigen")


def main() -> None:
    test_null_mutanten_gate()
    test_score_und_umfang()
    test_mutate_validierung()

    print()
    if _failures:
        print(f"{RED}{len(_failures)} Test(s) fehlgeschlagen:{RESET}")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print(f"{GREEN}Alle Tests bestanden.{RESET}")


if __name__ == "__main__":
    main()

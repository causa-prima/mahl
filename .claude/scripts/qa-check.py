#!/usr/bin/env python3
"""
QA-Check + Stryker-Lauf für den implementing-scenario-Ablauf.

Führt Stryker für die angegebene Schicht aus, liest den frisch erzeugten Report,
und prüft zusätzliche Qualitätsindikatoren (Suppressionen, Linting, Unit-Test-Muster).
Gibt alle Findings strukturiert aus und berechnet einen SHA-256-Hash als
Übergabe-Attestierung.

Der Hash ist manipulationsresistent: er ist über den Report-Inhalt des gerade
ausgeführten Stryker-Laufs und den gestagten Code-Zustand berechnet. Der Subagent
muss qa-check.py ausführen – er kann weder `touch` noch manuelle Score-Angaben nutzen,
um ihn zu fälschen.

Verwendung (Subagent – führt Stryker aus):
  python3 .claude/scripts/qa-check.py --layer backend
  python3 .claude/scripts/qa-check.py --layer frontend

Verwendung (Orchestrator-Verifikation – kein neuer Stryker-Lauf):
  python3 .claude/scripts/qa-check.py --layer backend --skip-stryker
  python3 .claude/scripts/qa-check.py --layer frontend --skip-stryker
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).parent

# Dateipfad-Präfixe die zu welcher Schicht gehören
_LAYER_PATHS = {
    "backend":  "Server/",
    "frontend": "Client/src/",
}


# ── Git-Hilfsfunktionen ──────────────────────────────────────────────────────

def _git(*args: str) -> str:
    return subprocess.run(["git"] + list(args), capture_output=True, text=True).stdout


def _staged_tree_fingerprint() -> str:
    """SHA-256 von 'git ls-files --stage': Fingerabdruck des gestagten Zustands."""
    out = _git("ls-files", "--stage")
    return hashlib.sha256(out.encode()).hexdigest()[:16]


# ── Stryker-Lauf ─────────────────────────────────────────────────────────────

def _run_stryker(layer: str) -> int:
    """Führt den Layer-spezifischen Stryker-Lauf aus. Gibt Exit-Code zurück."""
    script = _SCRIPTS / ("dotnet-stryker.py" if layer == "backend" else "stryker-frontend.py")
    result = subprocess.run([sys.executable, str(script)])
    return result.returncode


def _find_report(layer: str) -> Path | None:
    subdir = "Backend" if layer == "backend" else "Frontend"
    reports = sorted(Path("StrykerOutput").glob(f"{subdir}/*/reports/mutation-report.json"), reverse=True)
    return reports[0] if reports else None


def _parse_report(report_path: Path) -> tuple[str, str]:
    """Gibt (score_string, report_content_hash) zurück.

    Der Hash wird über eine normalisierte Form berechnet (Mutanten nach id sortiert),
    damit die Reihenfolge im JSON keinen Einfluss hat (StrykerJS ist nicht deterministisch).
    """
    data = json.loads(report_path.read_bytes())
    for file_data in data.get("files", {}).values():
        if "mutants" in file_data:
            file_data["mutants"] = sorted(file_data["mutants"], key=lambda m: str(m.get("id", "")))
    normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    total_tested = total_killed = 0
    for file_data in data.get("files", {}).values():
        for m in file_data.get("mutants", []):
            if m.get("status") in ("Killed", "Survived", "Timeout"):
                total_tested += 1
            if m.get("status") == "Killed":
                total_killed += 1
    score = (total_killed / total_tested * 100) if total_tested > 0 else 0.0
    return f"{score:.1f}%", content_hash


# ── Git-Checks (layer-scoped) ─────────────────────────────────────────────────

def _is_test_file(path: str) -> bool:
    return bool(re.search(r'(\.spec\.ts|Tests\.cs|Test\.cs)$', path))


def check_staged_test_files(layer: str) -> list[str]:
    prefix = _LAYER_PATHS[layer]
    out = _git("diff", "--name-only", "--cached")
    return [f for f in out.splitlines() if f.startswith(prefix) and _is_test_file(f)]


def check_new_suppressions(layer: str) -> list[tuple[str, str]]:
    prefix = _LAYER_PATHS[layer]
    out = _git("diff", "--staged", "-U0")
    findings: list[tuple[str, str]] = []
    current_file = ""
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            if current_file.startswith(prefix) and re.search(r'(Stryker disable|v8 ignore)', line):
                findings.append((current_file, line[1:].strip()))
    return findings


def check_unit_test_patterns(layer: str) -> list[tuple[str, str]]:
    """Verdächtige Unit-Test-Muster die nicht dem erlaubten Test-Typ entsprechen."""
    prefix = _LAYER_PATHS[layer]
    out = _git("diff", "--staged", "-U8")
    findings: list[tuple[str, str]] = []
    current_file = ""
    context: list[str] = []

    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            context = []
        else:
            context.append(line)
            if len(context) > 12:
                context.pop(0)
        if not (line.startswith("+") and not line.startswith("+++") and current_file.startswith(prefix)):
            continue
        content = line[1:]
        ctx = " ".join(context)

        if layer == "backend":
            # [Fact]/[Theory] ohne HTTP-Test-Kontext
            if re.search(r'\[(Fact|Theory)\]', content):
                if "WebApplicationFactory" not in ctx and "HttpClient" not in ctx:
                    findings.append((current_file, content.strip()))
        else:
            # describe()/it() ohne MSW-Setup
            if re.search(r'^\s*(describe|it)\s*\(', content):
                if not re.search(r'(createServer|setupServer|server\.use|msw)', ctx):
                    findings.append((current_file, content.strip()))

    return findings


# ── Test-Struktur ────────────────────────────────────────────────────────────

def check_test_structure(layer: str) -> list[tuple[str, str]]:
    """Prüft ob neue Test-Methoden // Given / // When / // Then Kommentare enthalten."""
    prefix = _LAYER_PATHS[layer]
    out = _git("diff", "--staged", "-U40")
    findings: list[tuple[str, str]] = []
    current_file = ""
    # Collect added lines per test block: (file, trigger_line, [added_lines_in_block])
    blocks: list[tuple[str, str, list[str]]] = []
    current_block: list[str] | None = None
    current_trigger = ""

    if layer == "backend":
        test_marker = re.compile(r'^\+\s*\[(Fact|Theory)\]')
    else:
        test_marker = re.compile(r'^\+\s*it\s*\(')

    for line in out.splitlines():
        if line.startswith("+++ b/"):
            if current_block is not None:
                blocks.append((current_file, current_trigger, current_block))
            current_file = line[6:]
            current_block = None
            current_trigger = ""
        elif not current_file.startswith(prefix) or not _is_test_file(current_file):
            continue
        elif test_marker.match(line):
            if current_block is not None:
                blocks.append((current_file, current_trigger, current_block))
            current_trigger = line[1:].strip()
            current_block = []
        elif current_block is not None and line.startswith("+") and not line.startswith("+++"):
            current_block.append(line[1:])

    if current_block is not None:
        blocks.append((current_file, current_trigger, current_block))

    for filepath, trigger, added_lines in blocks:
        block_text = "\n".join(added_lines)
        missing = [m for m in ("// Given", "// When", "// Then") if m not in block_text]
        if missing:
            findings.append((filepath, f"{trigger}  →  fehlt: {', '.join(missing)}"))

    return findings


# ── ADR-Referenzen ───────────────────────────────────────────────────────────

def check_adr_refs() -> tuple[str, int]:
    """Prüft ob alle // ADR-SXXX-N Kommentare im Code auf existierende ADRs verweisen."""
    script = _SCRIPTS / "decisions.py"
    r = subprocess.run([sys.executable, str(script), "check"], capture_output=True, text=True)
    if r.returncode == 0:
        return r.stdout.strip() or "OK – keine Stale-Referenzen", 0
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    return "\n  ".join(lines) if lines else "FEHLER (kein Output)", r.returncode


# ── Linting ──────────────────────────────────────────────────────────────────

def check_eslint() -> tuple[str, int]:
    staged = _git("diff", "--name-only", "--cached")
    if not any(f.endswith((".ts", ".tsx")) for f in staged.splitlines()):
        return "übersprungen (keine .ts/.tsx Dateien staged)", -1
    script = _SCRIPTS / "eslint-run.py"
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if r.returncode == 0:
        return "OK", 0
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    return f"FEHLER – {lines[-1] if lines else '(kein Output)'}", r.returncode


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QA-Check + Stryker für implementing-scenario")
    parser.add_argument("--layer", choices=["backend", "frontend"], required=True,
                        help="Welche Schicht wird geprüft")
    parser.add_argument("--skip-stryker", action="store_true",
                        help="Stryker nicht ausführen (Orchestrator-Verifikationsmodus: "
                             "liest den bestehenden Report der Subagenten-Ausführung)")
    args = parser.parse_args()

    # ── Stryker ──────────────────────────────────────────────────────────────
    if not args.skip_stryker:
        print(f"[qa-check] Starte Stryker ({args.layer}) …")
        rc = _run_stryker(args.layer)
        if rc != 0:
            print(f"[qa-check] Stryker fehlgeschlagen (Exit {rc}). Abbruch.", file=sys.stderr)
            sys.exit(rc)

    report_path = _find_report(args.layer)
    if report_path is None:
        print("[qa-check] Kein Stryker-Report gefunden.", file=sys.stderr)
        sys.exit(1)

    score, report_hash = _parse_report(report_path)

    # ── Checks ───────────────────────────────────────────────────────────────
    tree           = _staged_tree_fingerprint()
    test_files     = check_staged_test_files(args.layer)
    suppressions   = check_new_suppressions(args.layer)
    unit_tests     = check_unit_test_patterns(args.layer)
    test_structure = check_test_structure(args.layer)
    lint_status, lint_code = check_eslint() if args.layer == "frontend" else ("n/a (backend)", -1)
    adr_status, adr_code   = check_adr_refs()

    # ── Ausgabe ──────────────────────────────────────────────────────────────
    print(f"\n=== STRYKER ({args.layer.upper()}) ===")
    print(f"Score:  {score}")
    print(f"Report: {report_path}")

    print("\n=== CHECK 1: STAGED TEST-DATEIEN ===")
    print("\n".join(test_files) if test_files else "keine")

    print("\n=== CHECK 2: NEUE SUPPRESSIONEN ===")
    if suppressions:
        for f, line in suppressions:
            print(f"  {f}:  {line}")
    else:
        print("keine")

    print("\n=== CHECK 3: UNIT-TEST-MUSTER ===")
    if unit_tests:
        for f, line in unit_tests:
            print(f"  {f}:  {line}")
    else:
        print("keine verdächtigen Treffer")

    if args.layer == "frontend":
        print(f"\n=== CHECK 4: ESLINT ===")
        print(lint_status)

    print("\n=== CHECK 5: TEST-STRUKTUR (Given/When/Then) ===")
    if test_structure:
        for f, msg in test_structure:
            print(f"  {f}:  {msg}")
    else:
        print("alle neuen Tests strukturiert")

    print(f"\n=== CHECK 6: ADR-REFERENZEN ===")
    print(adr_status)

    # ── Hash ─────────────────────────────────────────────────────────────────
    # Bindet Findings an: Report-Inhalt (C3_HASH), gestagten Code-Zustand (TREE),
    # und alle git-basierten Checks. Score-String wird nicht direkt gehasht –
    # stattdessen der Report-Inhalt (fälschungssicher).
    hashable = "|".join([
        f"LAYER:{args.layer}",
        f"TREE:{tree}",
        f"C3_HASH:{report_hash}",
        f"C1:{sorted(test_files)}",
        f"C2:{sorted(str(x) for x in suppressions)}",
        f"C3_PATTERNS:{sorted(str(x) for x in unit_tests)}",
        f"C4:{lint_code}",
        f"C5:{sorted(str(x) for x in test_structure)}",
        f"C6:{adr_code}",
    ])
    h = hashlib.sha256(hashable.encode()).hexdigest()[:16]
    print(f"\n=== VERIFIKATIONS-HASH ===")
    print(h)


if __name__ == "__main__":
    main()

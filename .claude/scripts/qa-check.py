#!/usr/bin/env python3
"""
QA-Check + Stryker-Lauf für den implementing-scenario-Ablauf.

Führt Stryker für die angegebene Schicht aus, liest den frisch erzeugten Report,
und prüft zusätzliche Qualitätsindikatoren (Suppressionen, Linting, Unit-Test-Muster).
Gibt alle Findings strukturiert aus und berechnet einen SHA-256-Hash als
Übergabe-Attestierung.

Der Hash ist manipulationsresistent: er ist über den Report-Inhalt des gerade
ausgeführten Stryker-Laufs und den Working-Tree-Code-Zustand (Datei-INHALT, nicht der
git-Index) berechnet. Der Subagent muss qa-check.py ausführen – er kann weder `touch`
noch manuelle Score-Angaben nutzen, um ihn zu fälschen.

Bewusst index-unabhängig: Der Subagent muss NICHT `git add` ausführen, um einen
Hash zu erzeugen – der Hash hängt am Datei-Inhalt, nicht am Index. Damit ist der echte
Gate „Orchestrator reviewt den ungestageten Test-Diff, staged *dann*, committet". Späteres
Stagen einer freigegebenen Änderung ändert den Content-Hash nicht → kein erneuter
(teurer) Stryker-Lauf nur zur Neu-Attestierung (OBS-S090-2/-4).

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
import time
from pathlib import Path

_SCRIPTS   = Path(__file__).parent
_REPO_ROOT = _SCRIPTS.parent.parent
_CLIENT_DIR = _REPO_ROOT / "Client"

# Dateipfad-Präfixe die zu welcher Schicht gehören
_LAYER_PATHS = {
    "backend":  "Server/",
    "frontend": "Client/src/",
}


# ── Git-Hilfsfunktionen ──────────────────────────────────────────────────────

def _git(*args: str) -> str:
    return subprocess.run(["git"] + list(args), capture_output=True, text=True).stdout


def _porcelain_path(line: str) -> str:
    """Pfad aus einer `git status --porcelain`-Zeile (XY<space>PATH); Rename/Copy → Ziel."""
    if len(line) < 4:
        return ""
    path = line[3:]
    if " -> " in path:               # Rename/Copy: „alt -> neu" → das neue Ziel zählt
        path = path.split(" -> ", 1)[1]
    return path.strip('"')


def _changed_paths(prefix: str) -> list[str]:
    """Sortierte Liste geänderter (modifiziert + neu/untracked) Working-Tree-Pfade unter prefix.

    Index-unabhängig: `git status --porcelain -uall` listet eine geänderte Datei unabhängig
    davon, ob sie gestaged (`M `/`A `) oder ungestaged (` M`/`??`) ist – Stagen ändert die
    Pfad-Menge nicht.
    """
    out = _git("status", "--porcelain", "-uall", "--", prefix)
    paths = (_porcelain_path(line) for line in out.splitlines())
    return sorted(p for p in paths if p and p.startswith(prefix))


def _file_in_head(path: str) -> bool:
    """True wenn der Pfad in HEAD existiert (index-unabhängig – entscheidet neu vs. modifiziert)."""
    r = subprocess.run(["git", "cat-file", "-e", f"HEAD:{path}"], capture_output=True, text=True)
    return r.returncode == 0


def _worktree_content_fingerprint(layer: str) -> str:
    """SHA-256 über den INHALT aller geänderten Working-Tree-Dateien der Schicht.

    Bewusst über den Datei-Inhalt statt den git-Index: Stagen (`git add`) ändert den
    Fingerabdruck NICHT – nur eine echte Inhaltsänderung tut es. Das entkoppelt den
    Übergabe-Hash vom Index und macht Subagent-Stagen für die Attestierung wirkungslos.
    """
    h = hashlib.sha256()
    for path in _changed_paths(_LAYER_PATHS[layer]):
        h.update(path.encode() + b"\0")
        try:
            h.update(Path(path).read_bytes())   # CWD-relativ – wie alle git-Aufrufe (CWD == Repo-Root)
        except OSError:
            h.update(b"<deleted>")   # gelöschte Datei: Pfad zählt, Inhalt entfällt
        h.update(b"\0")
    return h.hexdigest()[:16]


def _worktree_diff(prefix: str, unified: int) -> str:
    """Unified-Diff des Working-Tree gegen HEAD unter prefix, inkl. neuer (untracked) Dateien.

    Ersetzt das frühere `git diff --staged`: erfasst Änderungen index-unabhängig, damit der
    Subagent NICHT stagen muss. Für in HEAD existierende Dateien liefert `git diff HEAD`
    (Working-Tree gegen HEAD) ein staging-invariantes Ergebnis; neue Dateien werden über
    `git diff --no-index /dev/null <datei>` als vollständig hinzugefügt dargestellt – beide
    Formen erzeugen identische `+++ b/…`- und `+`-Zeilen, ob die Datei gestaged ist oder nicht.
    """
    u = f"-U{unified}"
    parts: list[str] = []
    for path in _changed_paths(prefix):
        if _file_in_head(path):
            parts.append(_git("diff", "HEAD", u, "--", path))
        else:
            parts.append(subprocess.run(
                ["git", "diff", "--no-index", u, "/dev/null", path],
                capture_output=True, text=True).stdout)
    return "\n".join(p for p in parts if p)


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


# Kleine Toleranz für mtime-Granularität bei der Freshness-Prüfung.
_FRESHNESS_SLACK_SECONDS = 120


def _is_fresh(report_path: Path, run_started_at: float) -> bool:
    """True, wenn der Report aus dem aktuellen Lauf stammt (mtime >= Lauf-Start − Slack).

    Schützt davor, bei einem fehlgeschlagenen/ohne-Report-Lauf still einen ALTEN Report (aus
    einem früheren erfolgreichen Lauf) als gültige Übergabe auszugeben.
    """
    try:
        return report_path.stat().st_mtime >= (run_started_at - _FRESHNESS_SLACK_SECONDS)
    except OSError:
        return False


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
    # Standard-Mutation-Score (mutation-testing-elements, identisch zum HTML-Report):
    #   detected = Killed + Timeout ; undetected = Survived + NoCoverage.
    # NoCoverage senkt den Score; Ignored/CompileError/RuntimeError zählen nicht in den Nenner.
    counts: dict[str, int] = {}
    for file_data in data.get("files", {}).values():
        for m in file_data.get("mutants", []):
            s = m.get("status")
            counts[s] = counts.get(s, 0) + 1
    detected = counts.get("Killed", 0) + counts.get("Timeout", 0)
    total_valid = detected + counts.get("Survived", 0) + counts.get("NoCoverage", 0)
    score = (detected / total_valid * 100) if total_valid > 0 else 100.0
    return f"{score:.1f}%", content_hash


# ── Git-Checks (layer-scoped) ─────────────────────────────────────────────────

def _is_test_file(path: str) -> bool:
    # Vitest-Unit-Tests (.test.ts/.test.tsx, Frontend-Regelfall unter Client/src/),
    # Playwright-E2E (.spec.ts/.spec.tsx) und Backend-xUnit (…Tests.cs/…Test.cs).
    return bool(re.search(r'(\.test\.tsx?|\.spec\.tsx?|Tests\.cs|Test\.cs)$', path))


def check_changed_test_files(layer: str) -> list[str]:
    prefix = _LAYER_PATHS[layer]
    return [f for f in _changed_paths(prefix) if _is_test_file(f)]


def check_new_suppressions(layer: str) -> list[tuple[str, str]]:
    prefix = _LAYER_PATHS[layer]
    out = _worktree_diff(prefix, 0)
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
    out = _worktree_diff(prefix, 8)
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
    out = _worktree_diff(prefix, 40)
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


# ── Test-Freigabe-Audit ──────────────────────────────────────────────────────

def audit_approved_tests(layer: str, approved: dict[str, str]) -> tuple[int, list[str]]:
    """Vergleicht die aktuellen Test-Datei-Blobs gegen die vom Orchestrator freigegebenen SHAs.

    `approved`: Test-Pfad → git-Blob-SHA aus `git hash-object -w` beim RED-Review (nachdem der
    Orchestrator die Tests inhaltlich freigegeben hat). Der Blob ist content-addressed und
    immutable → gegen Subagent-`git add` immun: der Vergleich greift auch dann, wenn der
    Subagent die Tests nach der Freigabe selbst gestaged hat.

    Kein hartes Gate: Setup-Änderungen an Tests sind nach Freigabe erlaubt, und das Script kann
    Setup ≠ Assertion nicht entscheiden. Es zwingt aber jede Abweichung als Diff ins Sichtfeld,
    damit der Orchestrator urteilt. Rückgabe: (Anzahl Auffälligkeiten, Ausgabe-Zeilen).
    """
    changed = set(check_changed_test_files(layer))
    findings = 0
    lines: list[str] = []
    for f in sorted(changed):
        current = _git("hash-object", f).strip()
        expected = approved.get(f)
        if expected is None:
            findings += 1
            lines.append(f"⚠️  {f}: geändert, aber KEINE Freigabe-SHA übergeben – nie im Test-Review freigegeben?")
        elif current == expected:
            lines.append(f"✅ {f}: unverändert seit Freigabe.")
        else:
            findings += 1
            lines.append(f"⚠️  {f}: seit Freigabe GEÄNDERT – nur Setup (erlaubt) oder auch Assertions (verboten)? "
                         f"Diff freigegeben→aktuell:")
            lines.append(_git("diff", expected, "--", f).rstrip())
    for f in sorted(set(approved) - changed):
        lines.append(f"ℹ️  {f}: freigegeben, taucht aber nicht unter den geänderten Test-Dateien auf "
                     f"(committet/zurückgesetzt?).")
    return findings, lines


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

def check_tsc() -> int:
    """`tsc -b` über das ganze Client-Projekt (npm-Script `typecheck`). Gibt Exit-Code zurück.

    Fast-Fail-Gate als ERSTER Frontend-Schritt: liefert bei einem Typfehler eine klare
    tsc-Diagnose, statt dass der Fehler erst im Stryker-Lauf als kryptisches „kein frischer
    Report" auftaucht. Die *harte* Garantie sitzt weiter bei Stryker (`checkers: typescript`);
    dieser Schritt bringt nur schnelleres, klareres Feedback davor.
    """
    return subprocess.run(["npm", "run", "typecheck"], cwd=str(_CLIENT_DIR)).returncode


def check_eslint(layer: str) -> tuple[str, int]:
    changed = _changed_paths(_LAYER_PATHS[layer])
    if not any(f.endswith((".ts", ".tsx")) for f in changed):
        return "übersprungen (keine .ts/.tsx Dateien geändert)", -1
    script = _SCRIPTS / "eslint-run.py"
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if r.returncode == 0:
        return "OK", 0
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    return f"FEHLER – {lines[-1] if lines else '(kein Output)'}", r.returncode


# ── Hash ─────────────────────────────────────────────────────────────────────

def compute_hash(*, layer: str, tree: str, report_hash: str, test_files, suppressions,
                 unit_tests, lint_code, test_structure, adr_code) -> str:
    """Kanonischer Übergabe-Hash. Bindet Report-Inhalt, Working-Tree-Code-Inhalt und alle Checks.

    Es gibt nur DIESE eine Hash-Form. --skip-stryker gibt bewusst keinen Hash aus, daher ist
    jeder existierende Übergabe-Hash per Konstruktion ein Frisch-Lauf-Hash.
    """
    hashable = "|".join([
        f"LAYER:{layer}",
        f"TREE:{tree}",
        f"C3_HASH:{report_hash}",
        f"C1:{sorted(test_files)}",
        f"C2:{sorted(str(x) for x in suppressions)}",
        f"C3_PATTERNS:{sorted(str(x) for x in unit_tests)}",
        f"C4:{lint_code}",
        f"C5:{sorted(str(x) for x in test_structure)}",
        f"C6:{adr_code}",
    ])
    return hashlib.sha256(hashable.encode()).hexdigest()[:16]


def verify_hash(expected: str, **kwargs) -> bool:
    """True wenn der übergebene Hash dem kanonischen Hash des aktuellen Zustands entspricht."""
    return compute_hash(**kwargs) == expected


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QA-Check + Stryker für implementing-scenario")
    parser.add_argument("--layer", choices=["backend", "frontend"], required=True,
                        help="Welche Schicht wird geprüft")
    parser.add_argument("--skip-stryker", action="store_true",
                        help="Stryker nicht ausführen (Diagnose-Modus: liest den bestehenden "
                             "Report; gibt KEINEN Übergabe-Hash aus)")
    parser.add_argument("--verify", metavar="HASH",
                        help="Übergabe-Hash gegen den aktuellen Zustand prüfen (kein Stryker-Lauf). "
                             "Schlägt fehl, wenn der Hash kein frischer Lauf war oder Code/Report sich änderte.")
    parser.add_argument("--approved-tests", nargs="*", default=[], metavar="PFAD=SHA",
                        help="Vom Orchestrator im Test-Review freigegebene Test-Dateien als "
                             "`pfad=blob-sha` (aus `git hash-object -w <datei>`). qa-check zeigt jede "
                             "Abweichung als Diff freigegeben→aktuell, damit der Orchestrator prüfen "
                             "kann, dass nach der Freigabe nur Setup (erlaubt), keine Assertions geändert "
                             "wurden. Typisch zusammen mit --verify.")
    args = parser.parse_args()

    approved_tests: dict[str, str] = {}
    for token in args.approved_tests:
        path, _, sha = token.partition("=")
        if not sha:
            parser.error(f"--approved-tests erwartet `pfad=sha`, bekam: {token!r}")
        approved_tests[path] = sha

    # verify impliziert keinen frischen Stryker-Lauf (reine Verifikation des bestehenden Reports)
    run_stryker_now = not (args.skip_stryker or args.verify)

    # ── tsc-Gate (Frontend, Fast-Fail vor Stryker) ────────────────────────────
    if run_stryker_now and args.layer == "frontend":
        print("[qa-check] tsc -b (Typecheck) …")
        if check_tsc() != 0:
            print("[qa-check] ❌ tsc -b fehlgeschlagen – Typfehler zuerst beheben. "
                  "Kein Übergabe-Hash (Fast-Fail vor Stryker).", file=sys.stderr)
            sys.exit(1)

    # ── Stryker ──────────────────────────────────────────────────────────────
    stryker_gate_failed = False
    if run_stryker_now:
        print(f"[qa-check] Starte Stryker ({args.layer}) …")
        run_started_at = time.time()
        rc = _run_stryker(args.layer)

        # Build-/Compile-Fehler MÜSSEN als harter Lauf-Fehler durchschlagen –
        # KEIN stiller Fallback auf einen alten Report (sonst ginge eine ungültige Übergabe
        # mit veraltetem Hash durch). Unterscheidung Lauf-Fehler ↔ Score-Gate:
        #   - Score < 100 % (Below-Threshold): Stryker schreibt trotzdem einen FRISCHEN Report
        #     → rc != 0, aber frischer Report vorhanden → nur Score-Gate (Checks + Hash unten).
        #   - Build/Compile-Fehler: KEIN frischer Report → harter Abbruch, kein Hash.
        if rc != 0:
            stryker_gate_failed = True
            fresh = _find_report(args.layer)
            if fresh is None or not _is_fresh(fresh, run_started_at):
                print(
                    f"[qa-check] ❌ Stryker-LAUF fehlgeschlagen (Exit {rc}) und kein frischer Report "
                    f"erzeugt – das deutet auf Build-/Compile-Fehler hin, NICHT auf ein "
                    f"Score-Gate. Harter Lauf-Fehler: kein Übergabe-Hash. Ursache oben im Stryker-"
                    f"Output beheben und neu starten.",
                    file=sys.stderr,
                )
                sys.exit(rc or 1)
            print(
                f"[qa-check] ⚠️  Stryker-Score-Gate fehlgeschlagen (Score < 100 %, Exit {rc}) – "
                f"frischer Report vorhanden, führe restliche Checks dennoch aus.",
                file=sys.stderr,
            )

    report_path = _find_report(args.layer)
    if report_path is None:
        print("[qa-check] Kein Stryker-Report gefunden.", file=sys.stderr)
        sys.exit(1)

    # Auch im --verify/--skip-stryker-Pfad: Ein veralteter Report darf keinen scheinbar gültigen
    # Hash erzeugen. Bei einem frischen Lauf wurde die Frische oben bereits implizit geprüft;
    # hier greift der Schutz für die report-lesenden Modi.
    if run_stryker_now and not _is_fresh(report_path, run_started_at):
        print(
            f"[qa-check] ❌ Gefundener Report ist nicht aus diesem Lauf (veraltet): {report_path}. "
            f"Harter Lauf-Fehler – kein Übergabe-Hash.",
            file=sys.stderr,
        )
        sys.exit(1)

    score, report_hash = _parse_report(report_path)

    # ── Checks ───────────────────────────────────────────────────────────────
    tree           = _worktree_content_fingerprint(args.layer)
    test_files     = check_changed_test_files(args.layer)
    suppressions   = check_new_suppressions(args.layer)
    unit_tests     = check_unit_test_patterns(args.layer)
    test_structure = check_test_structure(args.layer)
    lint_status, lint_code = check_eslint(args.layer) if args.layer == "frontend" else ("n/a (backend)", -1)
    adr_status, adr_code   = check_adr_refs()

    # ── Ausgabe ──────────────────────────────────────────────────────────────
    print(f"\n=== STRYKER ({args.layer.upper()}) ===")
    print(f"Score:  {score}")
    print(f"Report: {report_path}")

    print("\n=== CHECK 1: GEÄNDERTE TEST-DATEIEN ===")
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
    # Bindet Findings an: Report-Inhalt (C3_HASH), Working-Tree-Code-Inhalt (TREE,
    # index-unabhängig) und alle git-basierten Checks (fälschungssicher via SHA-256).
    hash_kwargs = dict(
        layer=args.layer, tree=tree, report_hash=report_hash,
        test_files=test_files, suppressions=suppressions, unit_tests=unit_tests,
        lint_code=lint_code, test_structure=test_structure, adr_code=adr_code,
    )

    if args.verify:
        # Vergessens-Schutz: Sobald ein Verify-Lauf überhaupt Test-Dateien berührt (im TDD-Flow
        # praktisch immer), müssen die im Test-Review freigegebenen Blobs mitkommen – sonst bleibt
        # unbeobachtbar, ob nach der Freigabe Assertions geändert wurden (OBS-S090-4).
        if test_files and not approved_tests:
            print("❌ --verify ohne --approved-tests, obwohl dieser Lauf Test-Dateien ändert. "
                  "Übergib die im Test-Review freigegebenen Blobs (`git hash-object -w <datei>`) via "
                  "--approved-tests <pfad=sha …>, damit prüfbar bleibt, dass nach der Freigabe nur "
                  "Setup (erlaubt) und keine Assertions geändert wurden.", file=sys.stderr)
            sys.exit(1)

        ok = verify_hash(args.verify, **hash_kwargs)
        print(f"\n=== VERIFY ===")
        if not ok:
            print("❌ Hash stimmt NICHT überein – der aktuelle Zustand weicht von dem ab, für den der "
                  "Hash erzeugt wurde (Code/Report seit der Übergabe geändert, falsche Schicht, oder "
                  "ungültiger Hash).", file=sys.stderr)
            sys.exit(1)
        print("✅ Hash verifiziert – frischer Lauf, Code/Report-Zustand stimmt überein.")

        # Test-Freigabe-Audit: zeigt jede Test-Änderung seit der Freigabe als Diff (WAS geändert
        # wurde), damit der Orchestrator Setup (erlaubt) von Assertion-Änderungen (verboten) trennt.
        audit_findings, audit_lines = audit_approved_tests(args.layer, approved_tests)
        print("\n=== TEST-FREIGABE-AUDIT ===")
        print("\n".join(audit_lines) if audit_lines else "keine geänderten Test-Dateien")
        if audit_findings:
            print(f"\n⚠️  {audit_findings} Test-Datei(en) seit Freigabe geändert bzw. ohne Freigabe – "
                  f"obige Diffs prüfen (nur Setup erlaubt).", file=sys.stderr)
        # KEIN early exit: der Score-Gate unten gilt auch hier – ein verifizierter Hash mit
        # Score < 100 % ist trotzdem keine gültige Übergabe. Der Audit ist bewusst kein Exit-Gate
        # (Setup-Änderungen sind erlaubt; nur der Orchestrator kann Setup ≠ Assertion entscheiden).
    else:
        print(f"\n=== VERIFIKATIONS-HASH ===")
        if args.skip_stryker:
            print("(übersprungen – --skip-stryker erzeugt KEINEN Übergabe-Hash. Nur Läufe ohne "
                  "--skip-stryker sind zur Übergabe gültig; Verifikation durch den Orchestrator via --verify <hash>.)")
        else:
            print(compute_hash(**hash_kwargs))

    # ── Gate ─────────────────────────────────────────────────────────────────
    # Score-Gate als Exit-Code – aber erst NACH vollständiger Ausgabe aller Checks + Hash,
    # damit ein zu niedriger Score keine anderen Check-Probleme verdeckt. Der Hash bleibt
    # verifizierbar; der nicht-null Exit-Code signalisiert: keine gültige Übergabe.
    score_value = float(score.rstrip("%"))
    if stryker_gate_failed or score_value < 100.0:
        sys.stdout.flush()  # Checks zuerst, damit die Warnung danach erscheint (stderr ist ungepuffert)
        print(f"\n⚠️  ACHTUNG: Mutation-Score {score} < 100 % – dieser Lauf ist KEINE gültige "
              f"Übergabe. Survivors/NoCoverage oben klären, bevor übergeben wird.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

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
  python3 -m prozesscode.qa-check --layer backend
  python3 -m prozesscode.qa-check --layer frontend

Verwendung (Orchestrator-Verifikation – kein neuer Stryker-Lauf):
  python3 -m prozesscode.qa-check --layer backend --skip-stryker
  python3 -m prozesscode.qa-check --layer frontend --skip-stryker
"""

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from ._cli import Parser
from ._run_lock import LOCK_BUSY_EXIT_CODE
from ._wrapper_output import VERBOSE_HINT
from ._stryker_report import (
    NO_MUTANTS_HINT,
    collect_undetected,
    compute_metrics,
    format_mutant_group,
    format_score,
    format_scope,
    format_status_breakdown,
    has_no_mutants,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CLIENT_DIR = _REPO_ROOT / "Client"

# Dateipfad-Präfixe die zu welcher Schicht gehören. Tupel, weil eine Schicht in mehreren
# Wurzeln liegen kann: Backend-Produktionscode unter Server/, xUnit-Tests unter Server.Tests/.
# (Wäre der Backend-Präfix nur "Server/", fiele Server.Tests/ durch – "Server.Tests/…"
# beginnt NICHT mit "Server/" – und Test-Erkennung, Blob-Anker-Audit UND Übergabe-Hash
# wären für Backend-Testcode blind; OBS-S102-2.)
_LAYER_PATHS: dict[str, tuple[str, ...]] = {
    "backend":  ("Server/", "Server.Tests/"),
    "frontend": ("Client/src/",),
}


# ── Git-Hilfsfunktionen ──────────────────────────────────────────────────────

def _git(*args: str) -> str:
    return subprocess.run(["git"] + list(args), capture_output=True, text=True).stdout


def _porcelain_path(line: str) -> str:
    """Pfad aus einer `git status --porcelain`-Zeile (XY<space>PATH); Rename/Copy → Ziel."""
    path = line[3:]                  # eine zu kurze Zeile ergibt "" und fällt beim Aufrufer heraus
    if " -> " in path:               # Rename/Copy: „alt -> neu" → das neue Ziel zählt
        path = path.split(" -> ", 1)[1]
    return path.strip('"')


def _changed_paths(prefixes: tuple[str, ...]) -> list[str]:
    """Sortierte Liste geänderter (modifiziert + neu/untracked) Working-Tree-Pfade unter prefixes.

    Index-unabhängig: `git status --porcelain -uall` listet eine geänderte Datei unabhängig
    davon, ob sie gestaged (`M `/`A `) oder ungestaged (` M`/`??`) ist – Stagen ändert die
    Pfad-Menge nicht. `prefixes` ist ein Tupel (mehrere Wurzeln je Schicht, z.B. Server/ +
    Server.Tests/); git nimmt mehrere Pathspecs und `str.startswith` ein Tupel direkt.
    """
    out = _git("status", "--porcelain", "-uall", "--", *prefixes)
    paths = (_porcelain_path(line) for line in out.splitlines())
    return sorted(p for p in paths if p and p.startswith(prefixes))


def _file_in_head(path: str) -> bool:
    """True wenn der Pfad in HEAD existiert (index-unabhängig – entscheidet neu vs. modifiziert)."""
    return subprocess.run(["git", "cat-file", "-e", f"HEAD:{path}"], capture_output=True).returncode == 0


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


def _worktree_diff(prefixes: tuple[str, ...], unified: int) -> str:
    """Unified-Diff des Working-Tree gegen HEAD unter prefixes, inkl. neuer (untracked) Dateien.

    Ersetzt das frühere `git diff --staged`: erfasst Änderungen index-unabhängig, damit der
    Subagent NICHT stagen muss. Für in HEAD existierende Dateien liefert `git diff HEAD`
    (Working-Tree gegen HEAD) ein staging-invariantes Ergebnis; neue Dateien werden über
    `git diff --no-index /dev/null <datei>` als vollständig hinzugefügt dargestellt – beide
    Formen erzeugen identische `+++ b/…`- und `+`-Zeilen, ob die Datei gestaged ist oder nicht.
    """
    u = f"-U{unified}"
    parts: list[str] = []
    for path in _changed_paths(prefixes):
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
    modul = "prozesscode." + ("dotnet-stryker" if layer == "backend" else "stryker-frontend")
    # Der Subprozess schreibt ungepuffert auf denselben stdout – ohne Flush erschiene die
    # gesamte qa-check-Vorlaufausgabe erst NACH dessen Output (OBS-S108-4 c).
    sys.stdout.flush()
    result = subprocess.run([sys.executable, "-m", modul], cwd=str(_REPO_ROOT))
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


def _parse_report(report_path: Path) -> tuple[dict, dict, str]:
    """Gibt (files, metrics, report_content_hash) zurück.

    Der Hash wird über eine normalisierte Form berechnet (Mutanten nach id sortiert),
    damit die Reihenfolge im JSON keinen Einfluss hat (StrykerJS ist nicht deterministisch).
    Score/Umfang kommen aus `_stryker_report` – dieselbe Auswertung wie in
    `stryker-summary.py`, damit beide Gates nicht auseinanderdriften können.
    """
    data = json.loads(report_path.read_bytes())
    files = data.get("files", {})
    for file_data in files.values():
        if "mutants" in file_data:
            file_data["mutants"] = sorted(file_data["mutants"], key=lambda m: str(m.get("id", "")))
    normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    return files, compute_metrics(files), content_hash


# ── Git-Checks (layer-scoped) ─────────────────────────────────────────────────

def _is_test_file(path: str) -> bool:
    # Vitest-Unit-Tests (.test.ts/.test.tsx, Frontend-Regelfall unter Client/src/),
    # Playwright-E2E (.spec.ts/.spec.tsx) und Backend-xUnit (…Tests.cs/…Test.cs).
    return bool(re.search(r'(\.test\.tsx?|\.spec\.tsx?|Tests\.cs|Test\.cs)$', path))


def check_changed_test_files(layer: str) -> list[str]:
    prefixes = _LAYER_PATHS[layer]
    return [f for f in _changed_paths(prefixes) if _is_test_file(f)]


def check_new_suppressions(layer: str) -> list[tuple[str, str]]:
    prefixes = _LAYER_PATHS[layer]
    out = _worktree_diff(prefixes, 0)
    findings: list[tuple[str, str]] = []
    current_file = ""
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("+") and not line.startswith("+++") and re.search(r'(Stryker disable|v8 ignore)', line):
            findings.append((current_file, line[1:].strip()))
    return findings


def check_unit_test_patterns(layer: str) -> list[tuple[str, str]]:
    """Verdächtige Unit-Test-Muster die nicht dem erlaubten Test-Typ entsprechen."""
    prefixes = _LAYER_PATHS[layer]
    out = _worktree_diff(prefixes, 8)
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
        if not (line.startswith("+") and not line.startswith("+++")):
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
    prefixes = _LAYER_PATHS[layer]
    out = _worktree_diff(prefixes, 40)
    findings: list[tuple[str, str]] = []
    current_file = ""
    # Hinzugefügte Zeilen je Test-Block: (Datei, Auslöser-Zeile, [hinzugefügte Zeilen im Block]).
    # Ein Block wird beim Auslöser angelegt und danach über `current_block` befüllt.
    blocks: list[tuple[str, str, list[str]]] = []
    current_block: list[str] | None = None

    if layer == "backend":
        test_marker = re.compile(r'^\+\s*\[(Fact|Theory)\]')
    else:
        test_marker = re.compile(r'^\+\s*it\s*\(')

    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            current_block = None
        elif not _is_test_file(current_file):
            continue
        elif test_marker.match(line):
            current_block = []
            blocks.append((current_file, line[1:].strip(), current_block))
        elif current_block is not None and line.startswith("+") and not line.startswith("+++"):
            current_block.append(line[1:])

    for filepath, trigger, added_lines in blocks:
        block_text = "\n".join(added_lines)
        missing = [m for m in ("// Given", "// When", "// Then") if m not in block_text]
        if missing:
            findings.append((filepath, f"{trigger}  →  fehlt: {', '.join(missing)}"))

    return findings


def structure_fast_fail(layer: str) -> str | None:
    """Meldung, wenn neue Tests ohne Given/When/Then dastehen – sonst None.

    Given/When/Then ist Pflicht (CGC-/CGT-given-when-then), ein Befund muss also ohnehin behoben
    werden. Vor Stryker geprüft, weil er sonst erst nach dem minutenlangen Lauf erscheint und einen
    zweiten Lauf kostet.
    """
    findings = check_test_structure(layer)
    if not findings:
        return None
    details = "\n".join(f"  {f}:  {msg}" for f, msg in findings)
    return (f"[qa-check] ❌ Test-Struktur (Given/When/Then) unvollständig – Abbruch vor Stryker, "
            f"kein Übergabe-Hash:\n{details}\n   Kommentare ergänzen, dann qa-check neu starten.")


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
        elif not _git("cat-file", "-t", expected).strip():
            # Ohne -w berechnet: der Diff bliebe still leer und sähe wie „nichts geändert" aus.
            findings += 1
            lines.append(f"⚠️  {f}: seit Freigabe GEÄNDERT – der Freigabe-Blob {expected} liegt nicht in der "
                         f"Objektdatenbank, kein Diff möglich. Anker künftig mit `git hash-object -w <datei>` "
                         f"ablegen; jetzt die Änderung von Hand prüfen.")
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
    r = subprocess.run([sys.executable, "-m", "prozesscode.decisions", "check"],
                       capture_output=True, text=True, cwd=str(_REPO_ROOT))
    if r.returncode == 0:
        return r.stdout.strip() or "OK – keine Stale-Referenzen", 0
    lines = [line for line in (r.stdout + r.stderr).splitlines() if line.strip()]
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


CHECK_ESLINT_TITLE = "CHECK 4: ESLINT"
CHECK_ADR_TITLE = "CHECK 6: ADR-REFERENZEN"

# eslint-run zeigt schon ohne --verbose jede Meldung; --verbose ergänzt nur die npm-Kopfzeilen.
ESLINT_DETAILS_HINT = "  Alle Meldungen samt Warnungen: python3 -m prozesscode.eslint-run"
ESLINT_NO_OUTPUT = "(kein Output)"
ESLINT_INCOMPLETE = "  ⚠️  ESLint zählt {reported} Fehler, erkannt wurden {parsed} – die Liste oben ist unvollständig."

RED_CHECK_HASH_WARNING = (
    "⚠️  Rot: {checks}. Der Hash ist verifizierbar, die Übergabe aber erst gültig, wenn der Check grün "
    "ist – Befund oben beheben und qa-check erneut laufen lassen (oder den Befund im Return begründen).")

# ESLint (stylish) schreibt je Datei eine Kopfzeile mit dem Pfad, darunter eingerückt
# `Zeile:Spalte  error  Meldung  Regel`; Meldung und Regel trennen mindestens zwei Leerzeichen.
# Ein Parsing-Fehler hat keine Regel (`1:23  error  Parsing error: Expression expected`).
_ESLINT_ERROR_LINE = re.compile(r"^\s+(?P<pos>\d+:\d+)\s+error\s+(?P<message>.+?)(?:\s{2,}(?P<rule>\S+))?$")
# ESLints Zusammenfassung, z.B. `✖ 4 problems (2 errors, 2 warnings)` – Gegenprobe zur Zahl der erkannten Fehler.
_ESLINT_SUMMARY_ERRORS = re.compile(r"✖\s*\d+\s+problems?\s*\((\d+)\s+errors?")

# Im Rückfall gezeigte Zeilen: genug für Absturzmeldung und Fehlertext, ohne den Stacktrace.
_ESLINT_FALLBACK_LINES = 5


def check_eslint(layer: str) -> tuple[str, int]:
    changed = _changed_paths(_LAYER_PATHS[layer])
    if not any(f.endswith((".ts", ".tsx")) for f in changed):
        return "übersprungen (keine .ts/.tsx Dateien geändert)", -1
    r = subprocess.run([sys.executable, "-m", "prozesscode.eslint-run"],
                       capture_output=True, text=True, cwd=str(_REPO_ROOT))
    if r.returncode == 0:
        return "OK", 0
    output = r.stdout + r.stderr
    errors = _eslint_errors(output)
    if errors:
        status = f"FEHLER – {len(errors)} Fehler:\n  " + "\n  ".join(errors)
        summary = _ESLINT_SUMMARY_ERRORS.search(output)
        if summary and int(summary.group(1)) != len(errors):
            status += "\n" + ESLINT_INCOMPLETE.format(reported=summary.group(1), parsed=len(errors))
        return f"{status}\n{ESLINT_DETAILS_HINT}", r.returncode
    # Kein Fehler im bekannten Format (z.B. ESLint-Absturz): der Anfang der Ausgabe ist der Befund –
    # ohne die Schlusszeilen des Wrappers, die nur Verdikt und --verbose-Hinweis tragen.
    lines = _without_wrapper_trailer([line for line in output.splitlines() if line.strip()])
    finding = "\n  ".join(lines[:_ESLINT_FALLBACK_LINES]) if lines else ESLINT_NO_OUTPUT
    return f"FEHLER –\n  {finding}\n{ESLINT_DETAILS_HINT}", r.returncode


LINT_FAST_FAIL = ("[qa-check] ❌ ESLint meldet Fehler – Abbruch vor Stryker, kein Übergabe-Hash:\n"
                  "{status}\n   Fehler beheben, dann qa-check neu starten.")


def lint_fast_fail(lint_status: str, lint_code: int) -> str | None:
    """Meldung, wenn Check 4 (ESLint) Fehler meldet – sonst None.

    Ein ESLint-Fehler muss ohnehin behoben werden. Vor Stryker geprüft, weil er sonst erst nach dem
    minutenlangen Lauf erscheint und einen zweiten Lauf kostet; -1 heißt übersprungen.
    """
    return LINT_FAST_FAIL.format(status=lint_status) if lint_code > 0 else None


def _without_wrapper_trailer(lines: list[str]) -> list[str]:
    """Entfernt die Schlusszeilen von `_wrapper_output.emit`: Verdikt und VERBOSE_HINT."""
    if lines and lines[-1] == VERBOSE_HINT:
        return lines[:-2]
    return lines


def _eslint_errors(output: str) -> list[str]:
    """Fehler (keine Warnungen) der ESLint-Ausgabe als `Datei:Zeile:Spalte [Regel] – Meldung`, Datei repo-relativ."""
    errors, current_file = [], ""
    for line in output.splitlines():
        if line and not line[0].isspace():
            current_file = line.removeprefix(f"{_REPO_ROOT}/")
            continue
        match = _ESLINT_ERROR_LINE.match(line)
        if match:
            rule = f" {match['rule']}" if match["rule"] else ""
            errors.append(f"{current_file}:{match['pos']}{rule} – {match['message']}")
    return errors


def red_checks(*, lint_code: int, adr_code: int) -> list[str]:
    """Namen der Checks, die mit Fehler endeten (Exit-Code > 0; -1 heißt übersprungen).

    Nur Check 4 und 6 haben hier einen Fehlerzustand. Check 1–3 sind Auflistungen, die der Orchestrator
    bewertet; Check 5 (Given/When/Then) bricht den Übergabelauf schon vor Stryker ab (`structure_fast_fail`)."""
    return [name for name, code in ((CHECK_ESLINT_TITLE, lint_code), (CHECK_ADR_TITLE, adr_code))
            if code > 0]


def red_check_warning(*, lint_code: int, adr_code: int) -> str | None:
    """Warnzeile zum Hash, wenn ein Check rot ist – sonst None."""
    red = red_checks(lint_code=lint_code, adr_code=adr_code)
    return RED_CHECK_HASH_WARNING.format(checks=", ".join(red)) if red else None


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
    parser = Parser(description="QA-Check + Stryker für implementing-scenario")
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

    # ── Test-Struktur (Fast-Fail vor Stryker) ─────────────────────────────────
    if run_stryker_now:
        message = structure_fast_fail(args.layer)
        if message:
            print(message, file=sys.stderr)
            sys.exit(1)

    # ── ESLint (Fast-Fail vor Stryker; das Ergebnis ist zugleich Check 4) ─────
    # Wie der Stryker-Report misst es den Stand bei Laufbeginn; der Tree-Fingerprint unten entsteht
    # erst danach. Wer während des Laufs Code ändert, bekommt auch ohne ESLint einen Report zum alten
    # Stand – das Fenster ist dasselbe, nicht größer.
    lint_status, lint_code = check_eslint(args.layer) if args.layer == "frontend" else ("n/a (backend)", -1)
    if run_stryker_now:
        message = lint_fast_fail(lint_status, lint_code)
        if message:
            print(message, file=sys.stderr)
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
        if rc == LOCK_BUSY_EXIT_CODE:
            # Lock belegt → Stryker lief gar nicht. Der Report-Fallback unten würde hier den
            # frischen Report des KONKURRIERENDEN Laufs finden (dessen mtime ist naturgemäß
            # aktuell) und dessen Umfang attestieren – auch wenn der aus einem
            # `--mutate`-Einzeldatei-Lauf stammt (OBS-S108-3 c). Darum harter Abbruch.
            print(
                f"[qa-check] ❌ Stryker gar nicht gestartet – ein konkurrierender Lauf hält den Lock "
                f"(Exit {rc}). Kein Übergabe-Hash: ein fremder Report belegt diesen Lauf nicht. "
                f"Konkurrierenden Lauf abwarten und neu starten.",
                file=sys.stderr,
            )
            sys.exit(rc)

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
                sys.exit(rc)   # rc ist hier nie 0
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

    files, metrics, report_hash = _parse_report(report_path)

    # Ein Report ohne validen Mutanten belegt nichts – analog zum veralteten Report oben ein
    # harter Lauf-Fehler VOR dem Hash. Ohne diesen Abbruch entstünde ein formal gültiger
    # Übergabe-Hash über einen Lauf, der nie etwas gemessen hat (OBS-S108-3 a/b).
    if has_no_mutants(metrics):
        print(f"[qa-check] ❌ {NO_MUTANTS_HINT}\n{format_status_breakdown(metrics)}\n"
              f"   Kein Übergabe-Hash. Report: {report_path}", file=sys.stderr)
        sys.exit(1)

    # ── Checks ───────────────────────────────────────────────────────────────
    tree           = _worktree_content_fingerprint(args.layer)
    test_files     = check_changed_test_files(args.layer)
    suppressions   = check_new_suppressions(args.layer)
    unit_tests     = check_unit_test_patterns(args.layer)
    test_structure = check_test_structure(args.layer)
    adr_status, adr_code   = check_adr_refs()

    # ── Ausgabe ──────────────────────────────────────────────────────────────
    print(f"\n=== STRYKER ({args.layer.upper()}) ===")
    print(f"Score:  {format_score(metrics)}")
    print(f"{format_scope(metrics)}")
    print(f"Report: {report_path}")

    # Survivors direkt hier zeigen: der Lauf HAT die Information, sie separat über
    # stryker-summary/stryker-frontend nachzuholen ist ein zweiter Lauf für nichts (OBS-S100-3).
    survivors, nocoverage = collect_undetected(files)
    if survivors:
        print(f"\n⚠️  {metrics['counts']['Survived']} Survivor(s):")
        print("\n".join(format_mutant_group(survivors)))
    if nocoverage:
        print(f"\n⚠️  {metrics['counts']['NoCoverage']} NoCoverage (von keinem Test ausgeführt):")
        print("\n".join(format_mutant_group(nocoverage)))

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
        print(f"\n=== {CHECK_ESLINT_TITLE} ===")
        print(lint_status)

    print("\n=== CHECK 5: TEST-STRUKTUR (Given/When/Then) ===")
    if test_structure:
        for f, msg in test_structure:
            print(f"  {f}:  {msg}")
    else:
        print("alle neuen Tests strukturiert")

    print(f"\n=== {CHECK_ADR_TITLE} ===")
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
        print("\n=== VERIFY ===")
        if not ok:
            print("❌ Hash stimmt NICHT überein – der aktuelle Zustand weicht von dem ab, für den der "
                  "Hash erzeugt wurde (Code/Report seit der Übergabe geändert, falsche Schicht, oder "
                  "ungültiger Hash).", file=sys.stderr)
            sys.exit(1)
        print("✅ Hash verifiziert – frischer Lauf, Code/Report-Zustand stimmt überein.")
        # Auch hier: der Orchestrator entscheidet über die Übergabe und soll den roten Check nicht übersehen.
        warning = red_check_warning(lint_code=lint_code, adr_code=adr_code)
        if warning:
            print(warning)

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
        print("\n=== VERIFIKATIONS-HASH ===")
        if args.skip_stryker:
            print("(übersprungen – --skip-stryker erzeugt KEINEN Übergabe-Hash. Nur Läufe ohne "
                  "--skip-stryker sind zur Übergabe gültig; Verifikation durch den Orchestrator via --verify <hash>.)")
        else:
            print(compute_hash(**hash_kwargs))
            warning = red_check_warning(lint_code=lint_code, adr_code=adr_code)
            if warning:
                print(warning)

    # ── Gate ─────────────────────────────────────────────────────────────────
    # Score-Gate als Exit-Code – aber erst NACH vollständiger Ausgabe aller Checks + Hash,
    # damit ein zu niedriger Score keine anderen Check-Probleme verdeckt. Der Hash bleibt
    # verifizierbar; der nicht-null Exit-Code signalisiert: keine gültige Übergabe.
    if stryker_gate_failed or metrics["score"] < 100.0:
        sys.stdout.flush()  # Checks zuerst, damit die Warnung danach erscheint (stderr ist ungepuffert)
        print(f"\n⚠️  ACHTUNG: Mutation-Score {format_score(metrics)} < 100 % – dieser Lauf ist KEINE "
              f"gültige Übergabe. Survivors/NoCoverage oben klären, bevor übergeben wird – "
              f"außer solche, die laut „Welcher Survivor bekommt welche Reaktion?“ "
              f"(docs/process/tdd-process.md#TDD-survivor-entscheidung) an den Orchestrator "
              f"gemeldet werden: dann übergeben und jeden einzeln im Return aufführen.",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): E2E-Szenario-Verweise (ADR-S041-7).

Hält Feature-Szenario-Titel und E2E-`// Szenario:`-Kommentare titelgleich, damit next_run.py
nie auf ein nicht existierendes Szenario zeigt. Beide Richtungen:
- Edit an `Client/e2e/**/*.spec.ts`: jeder Testfall braucht einen `// Szenario:`-Kommentar (Präsenz),
  jeder Kommentar matcht ein Feature-Szenario (Gültigkeit) und ist über Specs hinweg eindeutig.
- Edit an `**/*.feature`: blockt, wenn die Änderung einen bestehenden `// Szenario:`-Kommentar
  verwaisen lässt (Umbenennung/Entfernung eines bereits implementierten Szenarios).

Mechanik: PreToolUse läuft VOR der Anwendung – die Datei auf Platte ist noch der Vor-Edit-Stand.
Der Hook simuliert den Post-Edit-Inhalt (Datei lesen + Edit anwenden bzw. Write-Content) und
prüft diesen. Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from next_run import scenario_comment_titles, parse_scenarios  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FEATURES_DIR = _REPO_ROOT / "features"
_E2E_DIR = _REPO_ROOT / "Client" / "e2e"
_E2E_SPEC_RE = re.compile(r"e2e[/\\].*\.spec\.ts$")
_FEATURE_RE = re.compile(r"\.feature$")
# Eine Playwright-Test-Definition (Testfall): test( / test.only( / test.skip( / test.fixme(
# – bewusst NICHT test.describe(, test.beforeEach( usw. (das sind Gruppen/Hooks, keine Szenarien).
_TEST_CASE_RE = re.compile(r"^\s*test(?:\.(?:only|skip|fixme))?\s*\(")
_TEST_NAME_RE = re.compile(r"""test(?:\.(?:only|skip|fixme))?\s*\(\s*(['"`])(.+?)\1""")
_SZENARIO_LINE_RE = re.compile(r"//\s*Szenario:")


def is_e2e_spec(file_path: str) -> bool:
    return bool(_E2E_SPEC_RE.search(file_path))


def is_feature(file_path: str) -> bool:
    return bool(_FEATURE_RE.search(file_path))


def tests_missing_comment(post_content: str) -> list[str]:
    """Namen der Testfälle, über denen kein `// Szenario:`-Kommentar steht."""
    lines = post_content.splitlines()
    missing: list[str] = []
    for i, line in enumerate(lines):
        if not _TEST_CASE_RE.match(line):
            continue
        if _has_szenario_comment_above(lines, i):
            continue
        name_match = _TEST_NAME_RE.search(line)
        missing.append(name_match.group(2) if name_match else f"Zeile {i + 1}")
    return missing


def _has_szenario_comment_above(lines: list[str], index: int) -> bool:
    """Läuft ab `index` rückwärts über Leerzeilen/Kommentare; True bei `// Szenario:`."""
    j = index - 1
    while j >= 0:
        stripped = lines[j].strip()
        if stripped == "" or stripped.startswith("//"):
            if _SZENARIO_LINE_RE.search(lines[j]):
                return True
            j -= 1
            continue
        break  # erste Nicht-Kommentar-/Nicht-Leerzeile → Kommentarblock zu Ende
    return False


def compute_post_content(tool: str, file_path: str, tool_input: dict) -> str | None:
    """Simuliert den Datei-Inhalt nach Anwendung des Edits/Writes."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        path = Path(file_path)
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if old and old in current:
            if tool_input.get("replace_all"):
                return current.replace(old, new)
            return current.replace(old, new, 1)
        return current  # old_string nicht gefunden → echter Edit schlägt ohnehin fehl
    return None


def validate(
    post_content: str, feature_titles: set[str], other_spec_titles: frozenset[str] = frozenset()
) -> list[str]:
    """Verstoß-Meldungen für den Post-Edit-Inhalt (dedupliziert).

    (a) Vollständigkeit: jeder Testfall hat einen `// Szenario:`-Kommentar.
    (b) Gültigkeit: jeder Kommentar matcht ein Feature-Szenario.
    (c) Eindeutigkeit: kein Titel doppelt über E2E-Specs hinweg.
    """
    violations: dict[str, None] = {}
    for test_name in tests_missing_comment(post_content):
        violations[f"Test „{test_name}“ hat keinen `// Szenario:`-Kommentar (für DONE-Erkennung nötig)."] = None
    for title in scenario_comment_titles(post_content):
        if title not in feature_titles:
            violations[f"// Szenario: „{title}“ verweist auf kein Szenario in features/."] = None
        elif title in other_spec_titles:
            violations[f"// Szenario: „{title}“ ist bereits in einer anderen E2E-Spec vergeben (doppelt)."] = None
    return list(violations)


def validate_feature(
    post_feature_content: str, other_feature_titles: frozenset[str], spec_titles: set[str]
) -> list[str]:
    """Verstöße, wenn ein Feature-Edit bestehende `// Szenario:`-Kommentare verwaisen lässt."""
    valid = {s["title"] for s in parse_scenarios(post_feature_content)} | set(other_feature_titles)
    orphaned = [t for t in spec_titles if t not in valid]
    return [
        f"Umbenennung/Entfernung verwaist den E2E-Kommentar „{t}“ – kein gleichnamiges Szenario in features/ mehr."
        for t in dict.fromkeys(sorted(orphaned))
    ]


def _feature_titles() -> set[str]:
    titles: set[str] = set()
    if _FEATURES_DIR.exists():
        for path in _FEATURES_DIR.glob("**/*.feature"):
            titles |= {s["title"] for s in parse_scenarios(path.read_text(encoding="utf-8"))}
    return titles


def _other_spec_titles(edited_path: str) -> frozenset[str]:
    edited = Path(edited_path).resolve()
    titles: set[str] = set()
    if _E2E_DIR.exists():
        for path in _E2E_DIR.glob("**/*.spec.ts"):
            if path.resolve() == edited:
                continue
            titles.update(scenario_comment_titles(path.read_text(encoding="utf-8")))
    return frozenset(titles)


def _other_feature_titles(edited_path: str) -> frozenset[str]:
    edited = Path(edited_path).resolve()
    titles: set[str] = set()
    if _FEATURES_DIR.exists():
        for path in _FEATURES_DIR.glob("**/*.feature"):
            if path.resolve() == edited:
                continue
            titles |= {s["title"] for s in parse_scenarios(path.read_text(encoding="utf-8"))}
    return frozenset(titles)


def _all_spec_titles() -> set[str]:
    titles: set[str] = set()
    if _E2E_DIR.exists():
        for path in _E2E_DIR.glob("**/*.spec.ts"):
            titles.update(scenario_comment_titles(path.read_text(encoding="utf-8")))
    return titles


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # kein parsbarer Input → nichts blocken

    try:
        tool = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if tool not in ("Edit", "Write"):
            sys.exit(0)

        post = compute_post_content(tool, file_path, tool_input)
        if post is None:
            sys.exit(0)

        if is_e2e_spec(file_path):
            violations = validate(post, _feature_titles(), _other_spec_titles(file_path))
        elif is_feature(file_path):
            violations = validate_feature(post, _other_feature_titles(file_path), _all_spec_titles())
        else:
            sys.exit(0)

        if violations:
            print("❌ E2E-Szenario-Mapping (Poka-Yoke):", file=sys.stderr)
            for v in violations:
                print(f"  - {v}", file=sys.stderr)
            print(
                "  Feature-Szenario-Titel und E2E-`// Szenario:`-Kommentare müssen gleich sein "
                "(Szenario via /gherkin-workshop anlegen/umbenennen; seltenen Rename-Deadlock per Hand-Edit lösen).",
                file=sys.stderr,
            )
            sys.exit(2)  # exit 2 = Edit blockieren
    except Exception as exc:  # noqa: BLE001 – Hook-Fehler darf nie einen Edit blockieren (fail-open)
        print(f"check-e2e-scenario-ref: Fehler ({exc}) – Edit nicht blockiert.", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()

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
prüft diesen. Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import re
from pathlib import Path

from ._hook_io import edit_zustand
from ..next_run import scenario_comment_titles, parse_scenarios

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
    for zeile in reversed(lines[:index]):
        stripped = zeile.strip()
        if stripped and not stripped.startswith("//"):
            return False  # erste Nicht-Kommentar-/Nicht-Leerzeile → Kommentarblock zu Ende
        if _SZENARIO_LINE_RE.search(zeile):
            return True
    return False


def validate(
    post_content: str, feature_titles: set[str], other_spec_titles: frozenset[str] = frozenset()
) -> list[str]:
    """Verstoß-Meldungen für den Post-Edit-Inhalt (dedupliziert).

    (a) Vollständigkeit: jeder Testfall hat einen `// Szenario:`-Kommentar.
    (b) Gültigkeit: jeder Kommentar matcht ein Feature-Szenario.
    (c) Eindeutigkeit: kein Titel doppelt über E2E-Specs hinweg.
    """
    violations = [_OHNE_KOMMENTAR.format(test=name) for name in tests_missing_comment(post_content)]
    for title in scenario_comment_titles(post_content):
        if title not in feature_titles:
            violations.append(_OHNE_SZENARIO.format(titel=title))
        elif title in other_spec_titles:
            violations.append(_DOPPELT.format(titel=title))
    return list(dict.fromkeys(violations))


def validate_feature(
    post_feature_content: str, other_feature_titles: frozenset[str], spec_titles: set[str]
) -> list[str]:
    """Verstöße, wenn ein Feature-Edit bestehende `// Szenario:`-Kommentare verwaisen lässt."""
    valid = {s["title"] for s in parse_scenarios(post_feature_content)} | set(other_feature_titles)
    return [_VERWAIST.format(titel=t) for t in sorted(set(spec_titles) - valid)]


def _texte(verzeichnis: Path, muster: str, ausser: str | None) -> list[str]:
    """Inhalt jeder Datei nach `muster` unter `verzeichnis` – ohne die bearbeitete (`ausser`):
    Deren Stand vor dem Edit stünde sonst neben dem neuen."""
    if not verzeichnis.exists():
        return []
    ausgenommen = Path(ausser).resolve() if ausser else None
    return [p.read_text(encoding="utf-8") for p in sorted(verzeichnis.glob(muster))
            if p.resolve() != ausgenommen]


def _feature_titles(ausser: str | None = None) -> set[str]:
    return {s["title"] for text in _texte(_FEATURES_DIR, "**/*.feature", ausser)
            for s in parse_scenarios(text)}


def _spec_titles(ausser: str | None = None) -> set[str]:
    return {t for text in _texte(_E2E_DIR, "**/*.spec.ts", ausser)
            for t in scenario_comment_titles(text)}


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py.

    Fail-open (Exception → None) liegt beim Dispatcher, damit ein Hook-Fehler
    nie einen Edit blockiert.
    """
    zustand = edit_zustand(data)
    if zustand is None:
        return None
    file_path, _pre, post = zustand

    if is_e2e_spec(file_path):
        violations = validate(post, _feature_titles(), _spec_titles(ausser=file_path))
    elif is_feature(file_path):
        violations = validate_feature(post, _feature_titles(ausser=file_path), _spec_titles())
    else:
        return None

    if not violations:
        return None

    lines = "\n".join(f"  - {v}" for v in violations)
    return f"{_KOPF}{lines}\n{_HINWEIS}"


_OHNE_KOMMENTAR = "Test „{test}“ hat keinen `// Szenario:`-Kommentar (für DONE-Erkennung nötig)."
_OHNE_SZENARIO = "// Szenario: „{titel}“ verweist auf kein Szenario in features/."
_DOPPELT = "// Szenario: „{titel}“ ist bereits in einer anderen E2E-Spec vergeben (doppelt)."
_VERWAIST = ("Umbenennung/Entfernung verwaist den E2E-Kommentar „{titel}“ – kein gleichnamiges "
             "Szenario in features/ mehr.")
_KOPF = "❌ E2E-Szenario-Mapping (Poka-Yoke):\n"
_HINWEIS = (
    "  Feature-Szenario-Titel und E2E-`// Szenario:`-Kommentare müssen gleich sein "
    "(Szenario via /gherkin-workshop anlegen/umbenennen; seltenen Rename-Deadlock per Hand-Edit lösen)."
)

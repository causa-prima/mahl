#!/usr/bin/env python3
"""
next_scenario.py – Szenario-Resolver für AGENT_MEMORY.md.

Löst den Platzhalter `{{NEXT_SCENARIO}}` zum nächsten unimplementierten Gherkin-Szenario
der aktuellen Story auf. Mapping Feature-Datei ↔ E2E-Test über `// Szenario: <Titel>`-
Kommentare in den Playwright-Specs (ADR-S041-7, Bidirektionale Traceability).

Modi:
  --render <memory.md>   Liest AGENT_MEMORY, ersetzt {{NEXT_SCENARIO}} durch das aufgelöste
                         Szenario und gibt den vollständigen Text auf stdout aus.
                         Bricht nie ab – bei Problemen Platzhalter→lesbare Notiz + stderr-Warnung.
  --check                Mapping-Integritäts-Guard: jeder // Szenario:-Kommentar matcht genau
                         einen Feature-Titel, keine Duplikate. Exit 1 bei Verstoß (für qa-check).

Story-Bestimmung: `Aktuelle Story: US-NNN` aus AGENT_MEMORY → Feature-Datei mit Top-Level-Tag
`@US-NNN`. „Erstes unimplementiertes" = erstes Szenario in Datei-Reihenfolge, dessen Titel in
keinem Spec-Kommentar steht.
"""
import argparse
import re
import sys
from pathlib import Path

from _feature import parse_feature

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FEATURES_DIR = _REPO_ROOT / "features"
_E2E_DIR = _REPO_ROOT / "Client" / "e2e"

_TOKEN = "{{NEXT_SCENARIO}}"
_STORY_RE = re.compile(r"Aktuelle Story:\*\*\s*(US-\d+)")
_SCENARIO_COMMENT_RE = re.compile(r"^\s*//\s*Szenario:\s*(.+?)\s*$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Reine Funktionen (textbasiert, ohne Dateisystem)
# ---------------------------------------------------------------------------

def extract_story(memory_text: str) -> str | None:
    """Liest die aktuelle Story-ID (z.B. 'US-904') aus dem AGENT_MEMORY-Text."""
    match = _STORY_RE.search(memory_text)
    return match.group(1) if match else None


def feature_tags(text: str) -> set[str]:
    """Top-Level-Tags der Feature (vor der `Feature:`-Zeile)."""
    return parse_feature(text)[0]


def parse_scenarios(text: str) -> list[dict]:
    """Geordnete Szenario-Liste; jedes {'tags': set[str], 'title': str}."""
    return parse_feature(text)[2]


def scenario_comment_titles(text: str) -> list[str]:
    """Alle `// Szenario: <Titel>`-Titel eines Texts in Reihenfolge (inkl. Duplikate)."""
    return [m.strip() for m in _SCENARIO_COMMENT_RE.findall(text)]


def implemented_titles_from_text(spec_text: str) -> set[str]:
    """Szenario-Titel aus `// Szenario: <Titel>`-Kommentaren eines Spec-Texts (dedupliziert)."""
    return set(scenario_comment_titles(spec_text))


def next_scenario(
    scenarios: list[dict], implemented: set[str], exclude_tags: frozenset[str] = frozenset()
) -> dict | None:
    """Erstes Szenario in Reihenfolge, das nicht implementiert und nicht ausgeschlossen ist."""
    for scenario in scenarios:
        if scenario["title"] in implemented:
            continue
        if scenario["tags"] & set(exclude_tags):
            continue
        return scenario
    return None


def open_scenarios(
    scenarios: list[dict], implemented: set[str], exclude_tags: frozenset[str] = frozenset()
) -> list[dict]:
    """Alle nicht-implementierten, nicht-ausgeschlossenen Szenarien in Reihenfolge."""
    return [
        s for s in scenarios
        if s["title"] not in implemented and not (s["tags"] & set(exclude_tags))
    ]


def done_scenarios(scenarios: list[dict], implemented: set[str]) -> list[dict]:
    """Alle implementierten Szenarien in Feature-Reihenfolge."""
    return [s for s in scenarios if s["title"] in implemented]


def format_scenario(scenario: dict) -> str:
    """Formatiert ein Szenario als `@tag` „Titel" für die Prioritätenliste."""
    tags = " ".join(sorted(scenario["tags"]))
    return f'`{tags}` „{scenario["title"]}"'


def check_integrity(feature_texts: list[str], spec_texts: list[str]) -> list[str]:
    """Prüft die Mapping-Integrität. Gibt eine Liste von Verstoß-Meldungen zurück (leer = ok).

    (i)  Jeder `// Szenario:`-Kommentar matcht genau einen Feature-Titel.
    (ii) Kein Titel doppelt über alle Specs hinweg.
    """
    all_titles: set[str] = set()
    for text in feature_texts:
        all_titles |= {s["title"] for s in parse_scenarios(text)}

    violations: list[str] = []
    seen: set[str] = set()
    for spec_text in spec_texts:
        for title in scenario_comment_titles(spec_text):
            if title not in all_titles:
                violations.append(
                    f"// Szenario: „{title}“ matcht kein Szenario in features/ "
                    f"(Titel exakt aus der Feature-Datei übernehmen)."
                )
            if title in seen:
                violations.append(f"// Szenario: „{title}“ ist doppelt über E2E-Specs vergeben.")
            seen.add(title)
    return violations


def render(
    memory_text: str,
    feature_texts: list[str],
    implemented: set[str],
    exclude_tags: frozenset[str] = frozenset(),
) -> str:
    """Ersetzt {{NEXT_SCENARIO}} im Memory-Text. Bricht nie ab – Fallback = lesbare Notiz."""
    if _TOKEN not in memory_text:
        return memory_text

    replacement, warning = _resolve_replacement(memory_text, feature_texts, implemented, exclude_tags)
    if warning:
        print(f"⚠️  next_scenario: {warning}", file=sys.stderr)
    return memory_text.replace(_TOKEN, replacement)


def _resolve_replacement(
    memory_text: str,
    feature_texts: list[str],
    implemented: set[str],
    exclude_tags: frozenset[str],
) -> tuple[str, str | None]:
    story = extract_story(memory_text)
    if story is None:
        return ("⚠️ nächstes Szenario nicht ermittelbar (keine „Aktuelle Story“ gefunden)", "keine Story im Memory")

    story_tag = f"@{story}"
    matching = [t for t in feature_texts if story_tag in feature_tags(t)]
    if len(matching) != 1:
        return (
            f"⚠️ nächstes Szenario nicht ermittelbar (Feature für {story}: {len(matching)} Treffer)",
            f"{len(matching)} Feature-Dateien mit {story_tag}",
        )

    scenario = next_scenario(parse_scenarios(matching[0]), implemented, exclude_tags)
    if scenario is None:
        return (f"(alle Szenarien der Story {story} implementiert)", None)
    return (format_scenario(scenario), None)


# ---------------------------------------------------------------------------
# Dateisystem-Anbindung
# ---------------------------------------------------------------------------

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _feature_files() -> list[Path]:
    if not _FEATURES_DIR.exists():
        return []
    return sorted(_FEATURES_DIR.glob("**/*.feature"))


def _feature_texts() -> list[str]:
    return [_read(p) for p in _feature_files()]


def _spec_texts() -> list[str]:
    if not _E2E_DIR.exists():
        return []
    return [_read(p) for p in sorted(_E2E_DIR.glob("**/*.spec.ts"))]


def _gather_implemented() -> set[str]:
    titles: set[str] = set()
    for spec in _spec_texts():
        titles |= implemented_titles_from_text(spec)
    return titles


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_render(memory_path: str) -> int:
    path = Path(memory_path)
    try:
        memory_text = _read(path)
    except OSError as exc:
        print(f"WARNUNG: AGENT_MEMORY ({memory_path}) nicht lesbar: {exc}", file=sys.stderr)
        return 1
    try:
        out = render(memory_text, _feature_texts(), _gather_implemented())
    except Exception as exc:  # noqa: BLE001 – Memory darf nie wegen Resolver wegbrechen
        print(f"⚠️  next_scenario: unerwarteter Fehler ({exc}); Memory unverändert.", file=sys.stderr)
        out = memory_text
    sys.stdout.write(out)
    return 0


def _cmd_list(only_open: bool) -> int:
    """Listet offene bzw. erledigte Szenarien je Feature-Datei – ohne die Datei öffnen zu müssen."""
    implemented = _gather_implemented()
    label = "offen" if only_open else "erledigt"
    any_output = False
    for path in _feature_files():
        text = _read(path)
        scenarios = open_scenarios(parse_scenarios(text), implemented) if only_open \
            else done_scenarios(parse_scenarios(text), implemented)
        if not scenarios:
            continue
        any_output = True
        ftags = " ".join(sorted(feature_tags(text)))
        header = f"=== {path.name}" + (f" ({ftags})" if ftags else "") + " ==="
        print(header)
        for s in scenarios:
            print(f"  {format_scenario(s)}")
    if not any_output:
        print(f"(keine {label}en Szenarien)")
    return 0


def _cmd_check() -> int:
    violations = check_integrity(_feature_texts(), _spec_texts())
    if violations:
        print("❌  E2E-Szenario-Mapping verletzt (// Szenario:-Kommentare):", file=sys.stderr)
        for v in violations:
            print(f"   - {v}", file=sys.stderr)
        return 1
    print("✅  E2E-Szenario-Mapping konsistent.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--render", metavar="MEMORY_MD", help="Platzhalter im Memory-Text auflösen")
    group.add_argument("--check", action="store_true", help="Mapping-Integritäts-Guard")
    group.add_argument("--open", action="store_true", help="offene Szenarien je Feature listen")
    group.add_argument("--done", action="store_true", help="erledigte Szenarien je Feature listen")
    args = parser.parse_args()

    if args.render:
        return _cmd_render(args.render)
    if args.open:
        return _cmd_list(only_open=True)
    if args.done:
        return _cmd_list(only_open=False)
    return _cmd_check()


if __name__ == "__main__":
    sys.exit(main())

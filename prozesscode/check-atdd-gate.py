#!/usr/bin/env python3
"""
ATDD-Gate: Prüft ob ein Gherkin-Szenario-Tag bzw. ein Implementierungs-Lauf in features/ existiert.
Gibt bei Treffer den Background + alle passenden Szenario-Blöcke aus, im Lauf-Modus dazu die
Kopf-Regeln, die ein Vermerk `→ <Absicherung> · run-N` dem Lauf zuordnet.

Verwendung (Einzel-Szenario, Tag+optionaler Titel):
  python3 -m prozesscode.check-atdd-gate @US-904-happy-path
  python3 -m prozesscode.check-atdd-gate @US-904-happy-path "Zutat anlegen"

Verwendung (Lauf, siehe .claude/skills/gherkin-workshop/references/scenario-clustering.md):
  python3 -m prozesscode.check-atdd-gate @US-904 run-3

Exit-Code 0 wenn gefunden, 1 wenn nicht gefunden.
"""
import re
import sys
from pathlib import Path

from ._feature import parse_feature, parse_header_rules

_FEATURES_DIR = Path(__file__).parent.parent / "features"
_RUN_ARG_RE = re.compile(r"^run-(\d+)$", re.IGNORECASE)
_HEADER_RULES_TITLE = "─── {file} · Kopf-Regeln ohne Szenario, per Test abzusichern ───"
_HEADER_RULES_COUNT = ", dazu {count} Kopf-Regel(n)"


def _print_scenario(feature_file: Path, background: list[str], scenario: dict) -> None:
    print(f"─── {feature_file.name} ───")
    if background:
        print("\n".join(background))
        print()
    print(" ".join(sorted(scenario["tags"])))
    print("\n".join(scenario["lines"]))
    print()


def _print_header_rules(feature_file: Path, rules: list[dict]) -> None:
    """Die Kopf-Regeln des Laufs, die Überschrift einmal je Gruppe aufeinanderfolgender Regeln."""
    print(_HEADER_RULES_TITLE.format(file=feature_file.name))
    # Startwert gleichwertig zu jedem anderen Nicht-Listen-Wert: verglichen wird per Identität.
    shown_heading: list[str] | None = None  # pragma: no mutate
    for rule in rules:
        if rule["heading"] is not None and rule["heading"] is not shown_heading:
            print("\n".join(rule["heading"]))
        shown_heading = rule["heading"]
        print("\n".join(rule["lines"]))
    print()


def _run_mode(story_tag: str, run_number: int) -> None:
    matches: list[tuple[Path, list[str], dict]] = []
    header_rules: list[tuple[Path, list[dict]]] = []

    for feature_file in sorted(_FEATURES_DIR.glob("**/*.feature")):
        text = feature_file.read_text(encoding="utf-8")
        feature_tags, background, scenarios = parse_feature(text)
        if story_tag not in feature_tags:
            continue
        for scenario in scenarios:
            if scenario["run"] is not None and scenario["run"]["number"] == run_number:
                matches.append((feature_file, background, scenario))
        rules = [rule for rule in parse_header_rules(text) if run_number in rule["runs"]]
        if rules:
            header_rules.append((feature_file, rules))

    if not matches:
        print(f"❌  Kein Szenario mit run-{run_number} unter Feature-Tag {story_tag} in features/ gefunden.")
        print("   Bitte zuerst /gherkin-workshop (Szenario-Clustering) für diese Story ausführen.")
        sys.exit(1)

    run_meta = matches[0][2]["run"]
    singleton_note = " · Singleton" if run_meta["singleton"] else ""
    rule_count = sum(len(rules) for _file, rules in header_rules)
    rule_note = _HEADER_RULES_COUNT.format(count=rule_count) if rule_count else ""
    print(
        f"✅  run-{run_number} „{run_meta['label']}\" ({run_meta['layer']}{singleton_note}) "
        f"– {len(matches)} Szenario(s) gefunden{rule_note}:\n"
    )
    for feature_file, background, scenario in matches:
        _print_scenario(feature_file, background, scenario)
    for feature_file, rules in header_rules:
        _print_header_rules(feature_file, rules)


def _tag_mode(tag: str, title_filter: str | None) -> None:
    matches: list[tuple[Path, list[str], dict]] = []

    for feature_file in sorted(_FEATURES_DIR.glob("**/*.feature")):
        text = feature_file.read_text(encoding="utf-8")
        _feature_tags, background, scenarios = parse_feature(text)
        for scenario in scenarios:
            if tag not in scenario["tags"]:
                continue
            if title_filter and title_filter not in scenario["title"].lower():
                continue
            matches.append((feature_file, background, scenario))

    if not matches:
        if title_filter:
            print(f"❌  Kein Szenario mit Tag {tag} und Titel '{title_filter}' in features/ gefunden.")
        else:
            print(f"❌  Kein Szenario mit Tag {tag} in features/ gefunden.")
        print("   Bitte zuerst /gherkin-workshop für die betreffende User Story ausführen.")
        sys.exit(1)

    print(f"✅  {len(matches)} Szenario(s) mit Tag {tag} gefunden:\n")
    for feature_file, background, scenario in matches:
        _print_scenario(feature_file, background, scenario)


def main() -> None:
    if len(sys.argv) < 2:
        print("Verwendung: check-atdd-gate.py <@tag> [Szenario-Titel] | <@story-tag> run-N", file=sys.stderr)
        sys.exit(1)

    if not _FEATURES_DIR.exists():
        print(f"❌  features/-Verzeichnis nicht gefunden: {_FEATURES_DIR}", file=sys.stderr)
        sys.exit(1)

    tag = sys.argv[1] if sys.argv[1].startswith("@") else f"@{sys.argv[1]}"

    run_match = _RUN_ARG_RE.match(sys.argv[2]) if len(sys.argv) > 2 else None
    if run_match:
        _run_mode(tag, int(run_match.group(1)))
        return

    title_filter = sys.argv[2].lower() if len(sys.argv) > 2 else None
    _tag_mode(tag, title_filter)


if __name__ == "__main__":
    main()

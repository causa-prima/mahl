#!/usr/bin/env python3
"""
ATDD-Gate: Prüft ob ein Gherkin-Szenario-Tag in features/ existiert.
Gibt bei Treffer den Background + alle passenden Szenario-Blöcke aus.

Verwendung:
  python3 .claude/scripts/check-atdd-gate.py @US-904-happy-path
  python3 .claude/scripts/check-atdd-gate.py @US-904-happy-path "Zutat anlegen"

Exit-Code 0 wenn gefunden, 1 wenn nicht gefunden.
"""
import sys
from pathlib import Path

from _feature import parse_feature

_FEATURES_DIR = Path(__file__).parent.parent.parent / "features"


def main() -> None:
    if len(sys.argv) < 2:
        print("Verwendung: check-atdd-gate.py <@tag> [Szenario-Titel]", file=sys.stderr)
        sys.exit(1)

    tag = sys.argv[1] if sys.argv[1].startswith("@") else f"@{sys.argv[1]}"
    title_filter = sys.argv[2].lower() if len(sys.argv) > 2 else None

    if not _FEATURES_DIR.exists():
        print(f"❌  features/-Verzeichnis nicht gefunden: {_FEATURES_DIR}", file=sys.stderr)
        sys.exit(1)

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
        print(f"   Bitte zuerst /gherkin-workshop für die betreffende User Story ausführen.")
        sys.exit(1)

    print(f"✅  {len(matches)} Szenario(s) mit Tag {tag} gefunden:\n")

    for feature_file, background, scenario in matches:
        print(f"─── {feature_file.name} ───")
        if background:
            print("\n".join(background))
            print()
        print(f"  @{tag.lstrip('@')}")
        print("\n".join(scenario["lines"]))
        print()


if __name__ == "__main__":
    main()

"""Geteilter Gherkin-Feature-Parser für .claude/scripts/.

Single Source of Truth für das Parsen von `features/*.feature`-Dateien.
Genutzt von check-atdd-gate.py (ATDD-Gate) und next_scenario.py (Szenario-Resolver).
"""


def parse_feature(text: str) -> tuple[set[str], list[str], list[dict]]:
    """Parst eine Gherkin-Feature-Datei.

    Gibt (feature_tags, background_lines, scenarios) zurück:
      - feature_tags: Tags direkt vor der `Feature:`-Zeile (z.B. {"@US-904"}).
      - background_lines: Zeilen des Background-Blocks.
      - scenarios: geordnete Liste, jedes {"tags": set[str], "title": str, "lines": list[str]}.
        Szenario-Tags enthalten NICHT die Feature-Tags (die sind separat in feature_tags).
    """
    lines = text.splitlines()
    feature_tags: set[str] = set()
    background: list[str] = []
    scenarios: list[dict] = []
    in_background = False
    current_tags: set[str] = set()
    current: dict | None = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("@"):
            # Tag-Zeile – schließt ggf. vorheriges Szenario ab
            if current is not None:
                scenarios.append(current)
                current = None
            in_background = False
            for tag in stripped.split():
                if tag.startswith("@"):
                    current_tags.add(tag)

        elif stripped.startswith("Feature:"):
            # Akkumulierte Tags gehören zur Feature, nicht zum ersten Szenario
            feature_tags |= current_tags
            current_tags = set()
            in_background = False

        elif stripped.startswith("Background:"):
            in_background = True
            background.append(line)

        elif stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
            if current is not None:
                scenarios.append(current)
            title = stripped.split(":", 1)[1].strip()
            current = {"tags": set(current_tags), "title": title, "lines": [line]}
            current_tags = set()
            in_background = False

        elif in_background:
            if stripped and not stripped.startswith("Feature:"):
                background.append(line)

        elif current is not None:
            current["lines"].append(line)

        # Kommentare / leere Zeilen zwischen Szenarien überspringen

    if current is not None:
        scenarios.append(current)

    return feature_tags, background, scenarios

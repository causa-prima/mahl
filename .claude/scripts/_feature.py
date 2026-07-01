"""Geteilter Gherkin-Feature-Parser für .claude/scripts/.

Single Source of Truth für das Parsen von `features/*.feature`-Dateien.
Genutzt von check-atdd-gate.py (ATDD-Gate) und next_run.py (Lauf-Resolver).
"""
import re

# Format (scenario-clustering.md): `# @run-<N> · <Cluster-Label> · <Frontend-only|Full-Stack>[ · Singleton]`
_RUN_COMMENT_RE = re.compile(
    r"^#\s*@run-(\d+)\s*·\s*(.+?)\s*·\s*(Frontend-only|Full-Stack)(?:\s*·\s*(Singleton))?\s*$"
)
# Lockere Erkennung für Format-Validierung: alles, was wie ein Run-Tag gemeint war (enthält
# "@run-N"), aber nicht exakt das strikte Format oben trifft (Tippfehler bei Schicht-Bezeichnung,
# falsches Trennzeichen o.ä.). parse_feature() ignoriert solche Zeilen stillschweigend als
# gewöhnlichen Kommentar – find_malformed_run_comments() macht diesen stillen Fehlschlag sichtbar.
_RUN_COMMENT_LOOSE_RE = re.compile(r"^#.*@run-\d+")


def find_malformed_run_comments(text: str) -> list[str]:
    """Zeilen, die wie ein Run-Tag aussehen, aber nicht exakt das Format
    `# @run-N · Label · Frontend-only|Full-Stack[ · Singleton]` treffen."""
    violations: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if _RUN_COMMENT_LOOSE_RE.match(stripped) and not _RUN_COMMENT_RE.match(stripped):
            violations.append(
                f"Zeile {lineno}: sieht wie ein Run-Tag aus, matcht aber nicht das Format "
                f"(wird als normaler Kommentar behandelt, Szenario verliert den Run-Tag): {stripped!r}"
            )
    return violations


def parse_feature(text: str) -> tuple[set[str], list[str], list[dict]]:
    """Parst eine Gherkin-Feature-Datei.

    Gibt (feature_tags, background_lines, scenarios) zurück:
      - feature_tags: Tags direkt vor der `Feature:`-Zeile (z.B. {"@US-904"}).
      - background_lines: Zeilen des Background-Blocks.
      - scenarios: geordnete Liste, jedes {"tags": set[str], "title": str, "lines": list[str],
        "run": dict|None}. Szenario-Tags enthalten NICHT die Feature-Tags (die sind separat in
        feature_tags). "run" ist {"number": int, "label": str, "layer": str, "singleton": bool}
        aus dem `# @run-N · ...`-Kommentar direkt oberhalb des Szenarios, sonst None.

    Kommentar-/Leerzeilen werden gepuffert und erst aufgelöst, wenn klar ist, WAS als Nächstes
    kommt: folgt eine `@`-Tag- oder `Scenario:`-Zeile, ist der Puffer die Lücke zwischen zwei
    Szenarien (dort werden `# @run-N`-Kommentare als Run-Tag ausgewertet, alles andere verworfen);
    folgt irgendetwas anderes (z.B. ein weiterer Gherkin-Step), gehört der Puffer zum aktuellen
    Kontext (Background oder laufender Szenario-Body) und wird dort wie jede normale Zeile
    übernommen. Ohne dieses Lookahead ließe sich ein Kommentar mitten im Szenario-Body (z.B. eine
    Erklärung zwischen zwei Steps) nicht von einem echten Run-Tag-Kommentar unterscheiden – beide
    stehen zum Zeitpunkt des Lesens im selben Zustand (`current` ist noch das laufende Szenario,
    es wird erst bei der nächsten Tag-/Scenario-Zeile geschlossen).
    """
    lines = text.splitlines()
    feature_tags: set[str] = set()
    background: list[str] = []
    scenarios: list[dict] = []
    in_background = False
    current_tags: set[str] = set()
    current: dict | None = None
    pending_run: dict | None = None
    buffer: list[str] = []

    def flush_as_body_lines() -> None:
        for buffered in buffer:
            if in_background:
                if buffered.strip():
                    background.append(buffered)
            elif current is not None:
                current["lines"].append(buffered)
        buffer.clear()

    def flush_as_run_tag_candidates() -> None:
        nonlocal pending_run
        for buffered in buffer:
            stripped_buffered = buffered.strip()
            if not stripped_buffered.startswith("#"):
                continue
            match = _RUN_COMMENT_RE.match(stripped_buffered)
            if match:
                number, label, layer, singleton = match.groups()
                pending_run = {
                    "number": int(number),
                    "label": label,
                    "layer": layer,
                    "singleton": singleton is not None,
                }
            # sonstige Erklär-Kommentare zwischen Szenarien: ignorieren (pending_run bleibt erhalten)
        buffer.clear()

    for line in lines:
        stripped = line.strip()

        if stripped == "" or stripped.startswith("#"):
            buffer.append(line)
            continue

        is_scenario_boundary = (
            stripped.startswith("@")
            or stripped.startswith("Scenario:")
            or stripped.startswith("Scenario Outline:")
        )
        if is_scenario_boundary:
            flush_as_run_tag_candidates()
        else:
            flush_as_body_lines()

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
            current = {"tags": set(current_tags), "title": title, "lines": [line], "run": pending_run}
            current_tags = set()
            pending_run = None
            in_background = False

        elif in_background:
            if stripped and not stripped.startswith("Feature:"):
                background.append(line)

        elif current is not None:
            current["lines"].append(line)

    # Rest-Puffer am Dateiende (z.B. Trailing-Kommentare nach dem letzten Szenario) gehört
    # zu keinem folgenden Szenario mehr – als Body-Zeilen des noch offenen Kontexts behandeln.
    flush_as_body_lines()

    if current is not None:
        scenarios.append(current)

    return feature_tags, background, scenarios

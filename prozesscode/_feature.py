"""Geteilter Gherkin-Feature-Parser für den Prozess-Code.

Single Source of Truth für das Parsen von `features/*.feature`-Dateien.
Genutzt von check-atdd-gate.py (ATDD-Gate) und next_run.py (Lauf-Resolver).
"""
import re

# Projekt-Phasen in ihrer Reihenfolge. Ein Lauf ist frühestens fällig, wenn das Projekt seine
# Phase erreicht hat; `next_run.py` vergleicht darüber, `td_anchors.py` prüft nur auf Gleichheit.
PHASEN = ("SKELETON", "MVP", "V1")

# Format (scenario-clustering.md):
# `# @run-<N> · <Cluster-Label> · <Frontend-only|Full-Stack>[ · Singleton][ · Phase:<P>][ · braucht:<refs>]`
_RUN_COMMENT_RE = re.compile(
    r"^#\s*@run-(\d+)\s*·\s*(.+?)\s*·\s*(Frontend-only|Full-Stack)"
    r"(?:\s*·\s*(Singleton))?"
    r"(?:\s*·\s*Phase:\s*([A-Za-z0-9_]+))?"
    r"(?:\s*·\s*braucht:\s*([A-Za-z0-9_/,\-]+))?\s*$"
)
# Datei-weite Direktiven im Feature-Header – Default für alle Läufe der Datei. Nötig, weil
# querschnittliche Feature-Dateien (resilience/interaction) gar keine Run-Tags tragen und ihre
# Phase sonst nirgends anschreiben könnten.
_PHASE_DIRECTIVE_RE = re.compile(r"^#\s*@phase:\s*([A-Za-z0-9_]+)\s*$")
_NEEDS_DIRECTIVE_RE = re.compile(r"^#\s*@braucht:\s*([A-Za-z0-9_/,\-]+)\s*$")
_DIRECTIVE_LOOSE_RE = re.compile(r"^#.*@(phase|braucht):")
_HEADER_END_RE = re.compile(r"^(Background:|Scenario:|Scenario Outline:)")


def phasen_rang(name: str) -> int:
    """Rang einer Phase in der Projekt-Reihenfolge (SKELETON < MVP < V1).

    Eine unbekannte Phase sortiert hinter alle bekannten, statt zu werfen: Der Resolver soll an
    einem Vertipper nicht wegbrechen, sondern den Lauf zurückstellen – gemeldet wird er ohnehin
    von find_malformed_run_comments().
    """
    upper = name.upper()
    return PHASEN.index(upper) if upper in PHASEN else len(PHASEN)


def _split_refs(raw: str | None) -> tuple[str, ...] | None:
    """Kommaseparierte `braucht:`-Referenzen; None wenn gar nichts angegeben war."""
    if raw is None:
        return None
    return tuple(ref.strip() for ref in raw.split(",") if ref.strip())


def parse_directives(text: str) -> tuple[str | None, tuple[str, ...]]:
    """Datei-weite Direktiven aus dem Feature-Header: (phase, needs).

    Header = alles vor der ersten `Background:`/`Scenario:`-Zeile. Weiter unten stehende
    Direktiven werden hier ignoriert und von find_malformed_run_comments() gemeldet – sie sähen
    lokal aus, wirkten aber global.
    """
    phase: str | None = None
    needs: tuple[str, ...] = ()
    for line in text.splitlines():
        stripped = line.strip()
        if _HEADER_END_RE.match(stripped):
            break
        phase_match = _PHASE_DIRECTIVE_RE.match(stripped)
        if phase_match:
            phase = phase_match.group(1).upper()
        needs_match = _NEEDS_DIRECTIVE_RE.match(stripped)
        if needs_match:
            needs = _split_refs(needs_match.group(1)) or ()
    return phase, needs
# Lockere Erkennung für Format-Validierung: alles, was wie ein Run-Tag gemeint war (enthält
# "@run-N"), aber nicht exakt das strikte Format oben trifft (Tippfehler bei Schicht-Bezeichnung,
# falsches Trennzeichen o.ä.). parse_feature() ignoriert solche Zeilen stillschweigend als
# gewöhnlichen Kommentar – find_malformed_run_comments() macht diesen stillen Fehlschlag sichtbar.
_RUN_COMMENT_LOOSE_RE = re.compile(r"^#.*@run-\d+")


def _header_end_lineno(text: str) -> int:
    """1-basierte Zeile der ersten `Background:`/`Scenario:`-Zeile (Ende des Feature-Headers)."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _HEADER_END_RE.match(line.strip()):
            return lineno
    return len(text.splitlines()) + 1


def _check_run_comment(lineno: int, stripped: str) -> str | None:
    match = _RUN_COMMENT_RE.match(stripped)
    if match is None:
        return (
            f"Zeile {lineno}: sieht wie ein Run-Tag aus, matcht aber nicht das Format "
            f"(wird als normaler Kommentar behandelt, Szenario verliert den Run-Tag): {stripped!r}"
        )
    phase = match.group(5)
    if phase and phase.upper() not in PHASEN:
        return f"Zeile {lineno}: unbekannte Phase {phase!r} (bekannt: {', '.join(PHASEN)})."
    return None


def _check_directive(lineno: int, stripped: str, header_end: int) -> str | None:
    if lineno >= header_end:
        return (
            f"Zeile {lineno}: Datei-Direktive steht unterhalb des Feature-Headers. Sie gilt für "
            f"die ganze Datei – dort sähe sie lokal aus. Nach oben vor `Background:` verschieben."
        )
    phase_match = _PHASE_DIRECTIVE_RE.match(stripped)
    if phase_match:
        phase = phase_match.group(1)
        if phase.upper() not in PHASEN:
            return f"Zeile {lineno}: unbekannte Phase {phase!r} (bekannt: {', '.join(PHASEN)})."
        return None
    if _NEEDS_DIRECTIVE_RE.match(stripped):
        return None
    return (
        f"Zeile {lineno}: sieht wie eine Datei-Direktive aus, matcht aber nicht das Format "
        f"(`# @phase: <PHASE>` bzw. `# @braucht: <ref>[,<ref>]`): {stripped!r}"
    )


def find_malformed_run_comments(text: str) -> list[str]:
    """Zeilen, die wie ein Run-Tag oder eine Datei-Direktive aussehen, das jeweilige Format aber
    nicht treffen – inklusive unbekannter Phasen-Werte und Direktiven unterhalb des Headers.

    Alle drei Fälle wären sonst still: `parse_feature()` behandelt sie als gewöhnlichen Kommentar,
    das Szenario verliert seinen Tag bzw. seine Phase, und nichts schlägt fehl.
    """
    header_end = _header_end_lineno(text)
    violations: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if _RUN_COMMENT_LOOSE_RE.match(stripped):
            violation = _check_run_comment(lineno, stripped)
        elif _DIRECTIVE_LOOSE_RE.match(stripped):
            violation = _check_directive(lineno, stripped, header_end)
        else:
            continue
        if violation:
            violations.append(violation)
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
    pending_phase: str | None = None
    pending_needs: tuple[str, ...] | None = None
    file_phase, file_needs = parse_directives(text)
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
        nonlocal pending_run, pending_phase, pending_needs
        for buffered in buffer:
            stripped_buffered = buffered.strip()
            if not stripped_buffered.startswith("#"):
                continue
            match = _RUN_COMMENT_RE.match(stripped_buffered)
            if match:
                number, label, layer, singleton, phase, needs = match.groups()
                pending_run = {
                    "number": int(number),
                    "label": label,
                    "layer": layer,
                    "singleton": singleton is not None,
                }
                pending_phase = phase.upper() if phase else None
                pending_needs = _split_refs(needs)
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
            current = {
                "tags": set(current_tags), "title": title, "lines": [line], "run": pending_run,
                "phase": pending_phase or file_phase,
                "needs": file_needs if pending_needs is None else pending_needs,
            }
            current_tags = set()
            pending_run = None
            pending_phase = None
            pending_needs = None
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

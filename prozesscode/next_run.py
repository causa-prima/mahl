#!/usr/bin/env python3
"""
next_run.py – Lauf-Resolver für AGENT_MEMORY.md.

Löst den Platzhalter `{{NEXT_RUN}}` zum nächsten **fälligen** Implementierungs-Lauf auf. Ein Lauf
ist ein oder mehrere Szenarien mit demselben `# @run-N`-Kommentar-Tag (Algorithmus + Format:
`.claude/skills/gherkin-workshop/references/scenario-clustering.md`). Szenarien ohne Run-Tag bilden
ihren eigenen Einzel-Lauf – rückwärtskompatibel zu Storys, die noch nicht per
gherkin-workshop-Szenario-Clustering geclustert wurden. Mapping Feature-Datei ↔ E2E-Test über
`// Szenario: <Titel>`-Kommentare in den Playwright-Specs (ADR-S041-7, Bidirektionale
Traceability).

Fälligkeit hat zwei Bedingungen (ADR-S131-1):
  - **Phase** – der Lauf trägt eine Phase (`# @phase:` im Feature-Header, `· Phase:<P>` am
    Run-Tag), und das Projekt hat sie laut `**Phase:**` in AGENT_MEMORY erreicht.
  - **Kanten** – alle in `· braucht:<refs>` genannten Vorgänger-Läufe sind vollständig
    implementiert. Die Phase allein kann die Reihenfolge nicht leisten: Sie hat drei Stufen, in
    denen praktisch alles gleichzeitig liegt.
Die Auflösung geht über **alle** Feature-Dateien, nicht nur die der aktuellen Story – sonst
erreicht sie querschnittliche Dateien (`@CROSS-…`, `@NFR-…`) strukturell nie. Die aktuelle Story
kommt in der Sortierung trotzdem zuerst, damit eine Story am Stück gebaut wird.

Modi:
  --render <memory.md>   Liest AGENT_MEMORY, ersetzt {{NEXT_RUN}} durch den aufgelösten
                         Lauf und gibt den vollständigen Text auf stdout aus.
                         Bricht nie ab – bei Problemen Platzhalter→lesbare Notiz + stderr-Warnung.
  --check                Mapping-Integritäts-Guard: jeder // Szenario:-Kommentar matcht genau
                         einen Feature-Titel, keine Duplikate; jede Run-Tag-Zeile ist syntaktisch
                         gültig; alle Szenarien derselben Run-Nummer tragen identische Metadaten
                         (Label/Schicht/Singleton/Phase/Kanten); jeder Lauf hat eine Phase, jede
                         braucht:-Kante ein Ziel, keine Kante bildet einen Zyklus.
                         Exit 1 bei Verstoß. Manuelle Bestandsprüfung – im Moment der
                         Entstehung greift der Hook `check-feature-plan.py`.
  --open / --done         Offene bzw. erledigte Läufe je Feature-Datei listen (ein Lauf gilt als
                         "erledigt", wenn alle seine Szenarien implementiert sind).
  --story US-NNN          Nur mit --open/--done: auf die Feature-Datei(en) dieser Story
                         eingrenzen (z.B. Sibling-Läufe-Überblick ohne Rauschen aus anderen
                         Storys/NFR-Features).

Story-Bestimmung: `Aktuelle Story: US-NNN` aus AGENT_MEMORY → Feature-Datei mit Top-Level-Tag
`@US-NNN`. „Nächster offener Lauf" = der Lauf mit der **niedrigsten Run-Nummer** (= vorgesehene
Build-Reihenfolge, siehe scenario-clustering.md – NICHT die Position in der Feature-Datei, die
der Erzähl-/Lesereihenfolge folgt), der mindestens ein nicht-implementiertes, nicht-
ausgeschlossenes Szenario enthält.
"""
import argparse
import re
import sys
from pathlib import Path

from ._feature import PHASEN, find_malformed_run_comments, parse_feature, phasen_rang

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FEATURES_DIR = _REPO_ROOT / "features"
_E2E_DIR = _REPO_ROOT / "Client" / "e2e"

_TOKEN = "{{NEXT_RUN}}"
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
    """Geordnete Szenario-Liste; jedes {'tags': set[str], 'title': str, 'run': dict|None}."""
    return parse_feature(text)[2]


def scenario_comment_titles(text: str) -> list[str]:
    """Alle `// Szenario: <Titel>`-Titel eines Texts in Reihenfolge (inkl. Duplikate)."""
    return [m.strip() for m in _SCENARIO_COMMENT_RE.findall(text)]


def implemented_titles_from_text(spec_text: str) -> set[str]:
    """Szenario-Titel aus `// Szenario: <Titel>`-Kommentaren eines Spec-Texts (dedupliziert)."""
    return set(scenario_comment_titles(spec_text))


def group_runs(scenarios: list[dict]) -> list[dict]:
    """Gruppiert Szenarien zu Läufen, sortiert nach **Run-Nummer** (= vorgesehene Build-
    Reihenfolge laut scenario-clustering.md), NICHT nach der Position in der Feature-Datei
    (die folgt der Erzähl-/Lesereihenfolge, nicht der Implementierungsreihenfolge – z.B. steht
    der Lese-Lauf oft ganz oben, obwohl er erst nach dem Anlegen-Endpoint sinnvoll ist).

    Jede Gruppe: {"number": int|None, "label": str|None, "layer": str|None,
    "singleton": bool, "scenarios": [scenario, ...]}. Ein Szenario ohne `run`-Tag
    bildet einen eigenen Einzel-Lauf ("number": None) statt in einen gemeinsamen
    Rest-Cluster zu fallen – das entspricht der Clustering-Regel, dass ungetaggte
    Läufe (z.B. bei noch nicht geclusterten Storys) je für sich stehen. Ungetaggte
    Einzel-Läufe behalten ihre Datei-Reihenfolge und werden hinter alle getaggten
    Läufe einsortiert (Anomalie-Fall: eigentlich sollte in einer geclusterten Story
    jedes Szenario einen Run-Tag tragen).
    """
    numbered: dict[int, dict] = {}
    untagged: list[dict] = []
    order: list[int] = []
    for scenario in scenarios:
        run = scenario["run"]
        if run is None:
            untagged.append({
                "number": None, "label": None, "layer": None, "singleton": True,
                "scenarios": [scenario],
            })
            continue
        group = numbered.get(run["number"])
        if group is None:
            group = {
                "number": run["number"], "label": run["label"], "layer": run["layer"],
                "singleton": run["singleton"], "scenarios": [],
            }
            numbered[run["number"]] = group
            order.append(run["number"])
        group["scenarios"].append(scenario)
    return [numbered[n] for n in sorted(order)] + untagged


def _group_is_open(group: dict, implemented: set[str], exclude_tags: frozenset[str]) -> bool:
    return any(
        s["title"] not in implemented and not (s["tags"] & set(exclude_tags))
        for s in group["scenarios"]
    )


def collect_runs(feature_texts: list[str]) -> list[dict]:
    """Alle Läufe **aller** Feature-Dateien, angereichert um Phase, Kanten und Herkunft.

    Der dateiübergreifende Blick ist nötig, weil Run-Nummern datei-lokal vergeben werden und eine
    `braucht:`-Kante über Dateigrenzen zeigen darf (`US-904/run-8`). Phase und Kanten stehen je
    Szenario schon aufgelöst im Parser (Run-Tag schlägt Datei-Direktive); ein Lauf übernimmt sie
    von seinem ersten Szenario – dass alle Szenarien eines Laufs darin übereinstimmen, prüft
    check_run_consistency().
    """
    groups: list[dict] = []
    for file_index, text in enumerate(feature_texts):
        tags = feature_tags(text)
        for group in group_runs(parse_scenarios(text)):
            first = group["scenarios"][0]
            groups.append({
                **group, "tags": tags, "file_index": file_index,
                "phase": first["phase"], "needs": first["needs"],
            })
    return groups


def run_label(group: dict) -> str:
    """Kurzbezeichnung eines Laufs für Meldungen (`US-904/run-8` bzw. Titel bei ungetaggtem Lauf)."""
    tag = sorted(group["tags"])[0].lstrip("@") if group["tags"] else "?"
    if group["number"] is None:
        return f'{tag}/„{group["scenarios"][0]["title"]}"'
    return f'{tag}/run-{group["number"]}'


def matches_ref(group: dict, ref: str, from_file_index: int) -> bool:
    """Trifft `ref` (`run-8` datei-intern, `US-904/run-8` datei-übergreifend) diesen Lauf?"""
    if "/" in ref:
        tag, run_part = ref.split("/", 1)
        if f"@{tag}" not in group["tags"]:
            return False
    else:
        run_part = ref
        if group["file_index"] != from_file_index:
            return False
    return group["number"] is not None and run_part == f"run-{group['number']}"


def _is_done(group: dict, implemented: set[str]) -> bool:
    return all(s["title"] in implemented for s in group["scenarios"])


def _needs_satisfied(group: dict, groups: list[dict], implemented: set[str]) -> bool:
    """Sind alle Vorgänger dieses Laufs erledigt?

    Ein Verweis ohne Ziel gilt als **nicht** erfüllt: Ein Vertipper soll den Lauf sichtbar
    zurückhalten (check_dependencies nennt ihn), statt still durchzulassen – ein durchgelassener
    toter Verweis wäre genau der stumme Ausfall, den niemand bemerkt.
    """
    for ref in group["needs"]:
        targets = [g for g in groups if matches_ref(g, ref, group["file_index"])]
        if not targets or not all(_is_done(t, implemented) for t in targets):
            return False
    return True


def next_run_global(
    groups: list[dict],
    implemented: set[str],
    phase: str | None,
    story: str | None,
    exclude_tags: frozenset[str] = frozenset(),
) -> dict | None:
    """Nächster fälliger Lauf über alle Feature-Dateien.

    Fällig ist ein Lauf, dessen Phase das Projekt erreicht hat und dessen Vorgänger erledigt sind.
    Sortierung: aktuelle Story zuerst (erhält die Arbeitsweise „eine Story am Stück"), dann
    Phasen-Rang, dann Feature-Datei, dann Run-Nummer.
    """
    max_rang = phasen_rang(phase) if phase else len(PHASEN)
    candidates = [
        g for g in groups
        if _group_is_open(g, implemented, exclude_tags)
        and (g["phase"] is None or phasen_rang(g["phase"]) <= max_rang)
        and _needs_satisfied(g, groups, implemented)
    ]
    if not candidates:
        return None
    story_tag = f"@{story}" if story else None
    return min(candidates, key=lambda g: (
        0 if story_tag and story_tag in g["tags"] else 1,
        phasen_rang(g["phase"]) if g["phase"] else len(PHASEN),
        g["file_index"],
        g["number"] if g["number"] is not None else 10**6,
    ))


def open_runs(
    scenarios: list[dict], implemented: set[str], exclude_tags: frozenset[str] = frozenset()
) -> list[dict]:
    """Alle Läufe mit mindestens einem offenen Szenario, in Reihenfolge."""
    return [g for g in group_runs(scenarios) if _group_is_open(g, implemented, exclude_tags)]


def done_runs(scenarios: list[dict], implemented: set[str]) -> list[dict]:
    """Alle Läufe, deren Szenarien vollständig implementiert sind, in Reihenfolge."""
    return [
        g for g in group_runs(scenarios)
        if all(s["title"] in implemented for s in g["scenarios"])
    ]


def format_run(group: dict) -> str:
    """Formatiert einen Lauf für die Prioritätenliste.

    Ohne Run-Tag (number None): wie das bisherige Einzel-Szenario-Format, damit
    ungeclusterte Storys unverändert lesbar bleiben.
    """
    if group["number"] is None:
        scenario = group["scenarios"][0]
        tags = " ".join(sorted(scenario["tags"]))
        return f'`{tags}` „{scenario["title"]}"'

    titles = ", ".join(f'„{s["title"]}"' for s in group["scenarios"])
    singleton_note = " · Singleton" if group["singleton"] else ""
    return f'`run-{group["number"]}` „{group["label"]}" ({group["layer"]}{singleton_note}): {titles}'


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


def check_run_consistency(scenarios: list[dict]) -> list[str]:
    """Prüft, dass alle Szenarien derselben Run-Nummer identische Metadaten (Label/Schicht/
    Singleton) tragen. Ohne diesen Check übernimmt die Gruppierung stillschweigend nur die
    Metadaten des ERSTEN Treffers (z.B. wenn beim Umbenennen eines Laufs nicht alle Kommentare
    aktualisiert wurden)."""
    seen: dict[int, tuple] = {}
    violations: list[str] = []
    for scenario in scenarios:
        run = scenario["run"]
        if run is None:
            continue
        meta = (run["label"], run["layer"], run["singleton"], scenario["phase"], scenario["needs"])
        if run["number"] not in seen:
            seen[run["number"]] = meta
        elif seen[run["number"]] != meta:
            violations.append(
                f'run-{run["number"]}: uneinheitliche Metadaten – „{scenario["title"]}“ hat '
                f'{meta}, ein früheres Szenario dieses Laufs hatte {seen[run["number"]]}.'
            )
    return violations


def _edge_map(groups: list[dict]) -> dict[int, list[int]]:
    """Index eines Laufs → Indizes der Läufe, die er laut `braucht:` voraussetzt."""
    return {
        i: [
            j for j, target in enumerate(groups)
            for ref in g["needs"] if matches_ref(target, ref, g["file_index"])
        ]
        for i, g in enumerate(groups)
    }


def _find_cycles(groups: list[dict]) -> list[str]:
    """Läufe, die sich über ihre `braucht:`-Kanten selbst voraussetzen (je Teilnehmer eine
    Meldung – wer im Zyklus steckt, ist die eigentliche Information)."""
    edges = _edge_map(groups)
    violations: list[str] = []
    for start, direct in edges.items():
        seen: set[int] = set()
        stack = list(direct)
        while stack:
            current = stack.pop()
            if current == start:
                violations.append(
                    f"{run_label(groups[start])}: Zyklus in den `braucht:`-Kanten – keiner der "
                    f"beteiligten Läufe kann je fällig werden. Eine Kante entfernen; setzen "
                    f"sich zwei Läufe gegenseitig voraus, gehören sie zusammengelegt "
                    f"(scenario-clustering.md, Schritt Zustands-Abhängigkeiten auflösen)."
                )
                break
            if current not in seen:
                seen.add(current)
                stack.extend(edges[current])
    return violations


def check_dependencies(groups: list[dict]) -> list[str]:
    """Prüft Phasen-Anker und Abhängigkeitskanten über alle Feature-Dateien.

    Drei Verstöße, alle sonst still: ein Lauf ohne Phase wird nie durch einen Phasenwechsel
    fällig, ein Verweis ohne Ziel hält seinen Lauf dauerhaft zurück, und ein Zyklus lässt keinen
    seiner Teilnehmer je an die Reihe kommen.
    """
    violations: list[str] = []
    for group in groups:
        if group["phase"] is None:
            violations.append(
                f"{run_label(group)}: ohne Phase – ergänze `# @phase: <PHASE>` im Feature-Header "
                f"oder `· Phase:<PHASE>` am Run-Tag."
            )
        for ref in group["needs"]:
            if not any(matches_ref(t, ref, group["file_index"]) for t in groups):
                violations.append(
                    f"{run_label(group)}: `braucht:{ref}` zeigt auf keinen existierenden Lauf."
                )
    return violations + _find_cycles(groups)


def render(
    memory_text: str,
    feature_texts: list[str],
    implemented: set[str],
    exclude_tags: frozenset[str] = frozenset(),
) -> str:
    """Ersetzt {{NEXT_RUN}} im Memory-Text. Bricht nie ab – Fallback = lesbare Notiz."""
    if _TOKEN not in memory_text:
        return memory_text

    replacement, warning = _resolve_replacement(memory_text, feature_texts, implemented, exclude_tags)
    if warning:
        print(f"⚠️  next_run: {warning}", file=sys.stderr)
    return memory_text.replace(_TOKEN, replacement)


def _resolve_replacement(
    memory_text: str,
    feature_texts: list[str],
    implemented: set[str],
    exclude_tags: frozenset[str],
) -> tuple[str, str | None]:
    from .td_anchors import phase_aus_memory  # lokal: td_anchors importiert next_run seinerseits

    story = extract_story(memory_text)
    phase = phase_aus_memory(memory_text)
    groups = collect_runs(feature_texts)

    group = next_run_global(groups, implemented, phase, story, exclude_tags)
    if group is None:
        return (_blocked_note(groups, implemented, phase, exclude_tags), None)
    return (format_run(group), None)


def _blocked_note(
    groups: list[dict], implemented: set[str], phase: str | None, exclude_tags: frozenset[str]
) -> str:
    """Notiz, wenn kein Lauf fällig ist – mit dem **Grund**, nicht mit einem Befehl.

    Ein Verweis auf `--check` wäre hier irreführend: Ein Lauf, den seine Phase oder eine erfüllte
    Kante korrekt zurückhält, ist kein Verstoß, der Guard bliebe also grün.
    """
    offen = [g for g in groups if _group_is_open(g, implemented, exclude_tags)]
    if not offen:
        return "(alle Läufe implementiert)"

    max_rang = phasen_rang(phase) if phase else len(PHASEN)
    zu_frueh = [g for g in offen if g["phase"] and phasen_rang(g["phase"]) > max_rang]
    if len(zu_frueh) == len(offen):
        naechste = min((g["phase"] for g in zu_frueh), key=phasen_rang)
        return (
            f"(kein Lauf in Phase {phase} fällig – {len(offen)} offen, "
            f"frühester ab Phase {naechste})"
        )
    wartend = [g for g in offen if g not in zu_frueh]
    kanten = sorted({ref for g in wartend for ref in g["needs"]})
    return (
        f"(kein Lauf fällig – {len(offen)} offen; {len(wartend)} warten auf "
        f"`braucht:{','.join(kanten)}`)"
    )


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
        print(f"⚠️  next_run: unerwarteter Fehler ({exc}); Memory unverändert.", file=sys.stderr)
        out = memory_text
    sys.stdout.write(out)
    return 0


def matches_story(text: str, story: str) -> bool:
    """True, wenn die Feature-Datei den Top-Level-Tag der gegebenen Story trägt (z.B. 'US-904')."""
    story_tag = story if story.startswith("@") else f"@{story}"
    return story_tag in feature_tags(text)


def _cmd_list(only_open: bool, story: str | None = None) -> int:
    """Listet offene bzw. erledigte Läufe je Feature-Datei – ohne die Datei öffnen zu müssen.

    Mit `story` auf die Feature-Datei(en) dieser Story eingegrenzt (z.B. für den Sibling-Läufe-
    Überblick im Architektur-Check von `implementing-scenario` – andere Storys/NFR-Features sind dort nur
    Rauschen und unnötige Tokenkosten)."""
    implemented = _gather_implemented()
    label = "offene" if only_open else "erledigte"
    any_output = False
    for path in _feature_files():
        text = _read(path)
        if story is not None and not matches_story(text, story):
            continue
        groups = open_runs(parse_scenarios(text), implemented) if only_open \
            else done_runs(parse_scenarios(text), implemented)
        if not groups:
            continue
        any_output = True
        ftags = " ".join(sorted(feature_tags(text)))
        header = f"=== {path.name}" + (f" ({ftags})" if ftags else "") + " ==="
        print(header)
        for g in groups:
            print(f"  {format_run(g)}")
    if not any_output:
        print(f"(keine {label}n Läufe)")
    return 0


def _cmd_check() -> int:
    violations = check_integrity(_feature_texts(), _spec_texts())

    run_violations: list[str] = []
    for path in _feature_files():
        text = _read(path)
        for v in find_malformed_run_comments(text):
            run_violations.append(f"{path.name}: {v}")
        for v in check_run_consistency(parse_scenarios(text)):
            run_violations.append(f"{path.name}: {v}")
    run_violations.extend(check_dependencies(collect_runs(_feature_texts())))

    if violations or run_violations:
        print("❌  E2E-Szenario-Mapping verletzt:", file=sys.stderr)
        for v in violations:
            print(f"   - {v}", file=sys.stderr)
        for v in run_violations:
            print(f"   - {v}", file=sys.stderr)
        return 1
    print("✅  E2E-Szenario-Mapping konsistent.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--render", metavar="MEMORY_MD", help="Platzhalter im Memory-Text auflösen")
    group.add_argument("--check", action="store_true", help="Mapping-Integritäts-Guard")
    group.add_argument("--open", action="store_true", help="offene Läufe je Feature listen")
    group.add_argument("--done", action="store_true", help="erledigte Läufe je Feature listen")
    parser.add_argument("--story", metavar="US-NNN", help="nur diese Story (mit --open/--done)")
    args = parser.parse_args(argv)

    if args.render:
        return _cmd_render(args.render)
    if args.open:
        return _cmd_list(only_open=True, story=args.story)
    if args.done:
        return _cmd_list(only_open=False, story=args.story)
    return _cmd_check()


if __name__ == "__main__":
    sys.exit(main())

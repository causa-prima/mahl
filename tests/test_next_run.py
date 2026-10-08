"""Tests für next_run.py – Lauf-Resolver + Mapping-Integritäts-Guard."""
import textwrap

import pytest

from prozesscode import next_run as nr  # noqa: E402


FEATURE = textwrap.dedent("""\
    @US-904
    Feature: Zutaten verwalten

      Background:
        Given die Anwendung ist gestartet

      @US-904-happy-path
      Scenario: Erstes Szenario
        When a
        Then b

      @US-904-happy-path
      Scenario: Zweites Szenario
        When a
        Then b

      @US-904-error
      Scenario: Drittes Szenario
        When a
        Then b
    """)

FEATURE_WITH_RUNS = textwrap.dedent("""\
    @US-904
    Feature: Zutaten verwalten

      Background:
        Given die Anwendung ist gestartet

      # @run-1 · Anlegen·Success · Full-Stack
      @US-904-happy-path
      Scenario: Zutat anlegen
        When a
        Then b

      # @run-2 · Anlegen·Validierung · Full-Stack
      @US-904-error
      Scenario: Leerer Name
        When a
        Then b

      # @run-2 · Anlegen·Validierung · Full-Stack
      @US-904-error
      Scenario: Leere Einheit
        When a
        Then b

      # @run-3 · Mehrfeld · Full-Stack · Singleton
      @US-904-error
      Scenario: Beide leer
        When a
        Then b
    """)

# Regression: Datei-Reihenfolge weicht von Run-Reihenfolge ab (wie im echten ingredients.feature,
# wo der Lese-Lauf run-7 als erstes Szenario in der Datei steht, aber erst nach run-1 gebaut wird).
FEATURE_RUN_ORDER_DIVERGES_FROM_FILE_ORDER = textwrap.dedent("""\
    @US-904
    Feature: Zutaten verwalten

      Background:
        Given die Anwendung ist gestartet

      # @run-7 · Liste · Full-Stack
      @US-904-happy-path
      Scenario: Leere Liste
        When a
        Then b

      # @run-1 · Anlegen·Success · Full-Stack
      @US-904-happy-path
      Scenario: Zutat anlegen
        When a
        Then b

      # @run-7 · Liste · Full-Stack
      @US-904-happy-path
      Scenario: Sortierte Liste
        When a
        Then b
    """)


# --- extract_story -----------------------------------------------------------
def test_extract_story():
    mem = "**Aktuelle Story:** US-904 (Zutaten) → `features/ingredients.feature`"
    assert nr.extract_story(mem) == "US-904"


def test_extract_story_none_when_absent():
    assert nr.extract_story("kein Story-Feld hier") is None


# --- feature_tags / parse_scenarios ------------------------------------------
def test_feature_tags_detected_not_on_first_scenario():
    assert "@US-904" in nr.feature_tags(FEATURE)
    scenarios = nr.parse_scenarios(FEATURE)
    # Feature-Tag darf nicht ans erste Szenario gehängt werden
    assert scenarios[0]["tags"] == {"@US-904-happy-path"}


def test_parse_scenarios_order():
    titles = [s["title"] for s in nr.parse_scenarios(FEATURE)]
    assert titles == ["Erstes Szenario", "Zweites Szenario", "Drittes Szenario"]


# --- implemented_titles_from_text --------------------------------------------
def test_implemented_titles_parses_comments():
    spec = "// Szenario: Erstes Szenario\ntest('foo', ...)\n//  Szenario:  Zweites Szenario  \n"
    assert nr.implemented_titles_from_text(spec) == {"Erstes Szenario", "Zweites Szenario"}


def test_implemented_titles_empty_when_no_comments():
    assert nr.implemented_titles_from_text("test('foo')") == set()


# --- group_runs ----------------------------------------------------------------
def test_group_runs_without_run_tags_are_singletons():
    scenarios = nr.parse_scenarios(FEATURE)
    groups = nr.group_runs(scenarios)
    assert [g["number"] for g in groups] == [None, None, None]
    assert [g["scenarios"][0]["title"] for g in groups] == \
        ["Erstes Szenario", "Zweites Szenario", "Drittes Szenario"]


def test_group_runs_collects_same_run_number():
    scenarios = nr.parse_scenarios(FEATURE_WITH_RUNS)
    groups = nr.group_runs(scenarios)
    assert [g["number"] for g in groups] == [1, 2, 3]
    run2 = groups[1]
    assert [s["title"] for s in run2["scenarios"]] == ["Leerer Name", "Leere Einheit"]
    assert run2["label"] == "Anlegen·Validierung"
    assert groups[2]["singleton"] is True


def test_group_runs_orders_by_run_number_not_file_position():
    # run-7 steht als erstes Szenario in der Datei, aber run-1 hat die niedrigere Nummer
    # und muss zuerst gebaut werden (Success-Endpoint vor der Liste, die ihn nutzt).
    scenarios = nr.parse_scenarios(FEATURE_RUN_ORDER_DIVERGES_FROM_FILE_ORDER)
    groups = nr.group_runs(scenarios)
    assert [g["number"] for g in groups] == [1, 7]


def test_next_run_respects_run_number_order_over_file_order():
    groups = nr.collect_runs([FEATURE_RUN_ORDER_DIVERGES_FROM_FILE_ORDER])
    nxt = nr.next_run_global(groups, implemented=set(), phase=None, story="US-904")
    assert nxt["number"] == 1


# --- next_run_global ------------------------------------------------------------
def test_next_run_returns_first_unimplemented_singleton_run():
    groups = nr.collect_runs([FEATURE])
    nxt = nr.next_run_global(groups, implemented={"Erstes Szenario"}, phase=None, story="US-904")
    assert nxt["scenarios"][0]["title"] == "Zweites Szenario"


def test_next_run_none_when_all_done():
    groups = nr.collect_runs([FEATURE])
    done = {"Erstes Szenario", "Zweites Szenario", "Drittes Szenario"}
    assert nr.next_run_global(groups, implemented=done, phase=None, story="US-904") is None


def test_next_run_skips_excluded_tags():
    groups = nr.collect_runs([FEATURE])
    done = {"Erstes Szenario", "Zweites Szenario"}
    # Einziges verbleibendes ist @US-904-error → ausgeschlossen → None
    nxt = nr.next_run_global(
        groups, implemented=done, phase=None, story="US-904",
        exclude_tags=frozenset({"@US-904-error"}),
    )
    assert nxt is None


def test_next_run_returns_whole_run_if_any_scenario_open():
    groups = nr.collect_runs([FEATURE_WITH_RUNS])
    # run-1 komplett erledigt, run-2 hat noch ein offenes Szenario
    done = {"Zutat anlegen", "Leerer Name"}
    nxt = nr.next_run_global(groups, implemented=done, phase=None, story="US-904")
    assert nxt["number"] == 2
    assert [s["title"] for s in nxt["scenarios"]] == ["Leerer Name", "Leere Einheit"]


# --- open_runs / done_runs -----------------------------------------------------
def test_open_runs_in_order():
    scenarios = nr.parse_scenarios(FEATURE)
    opened = nr.open_runs(scenarios, implemented={"Erstes Szenario"})
    assert [g["scenarios"][0]["title"] for g in opened] == ["Zweites Szenario", "Drittes Szenario"]


def test_open_runs_respects_exclude_tags():
    scenarios = nr.parse_scenarios(FEATURE)
    opened = nr.open_runs(scenarios, implemented=set(), exclude_tags={"@US-904-error"})
    assert "Drittes Szenario" not in [g["scenarios"][0]["title"] for g in opened]


def test_done_runs_requires_all_scenarios_done():
    scenarios = nr.parse_scenarios(FEATURE_WITH_RUNS)
    done = {"Zutat anlegen", "Leerer Name"}  # run-2 nur teilweise
    done_groups = nr.done_runs(scenarios, implemented=done)
    assert [g["number"] for g in done_groups] == [1]


def test_done_runs_in_order():
    scenarios = nr.parse_scenarios(FEATURE)
    done = nr.done_runs(scenarios, implemented={"Erstes Szenario", "Drittes Szenario"})
    assert [g["scenarios"][0]["title"] for g in done] == ["Erstes Szenario", "Drittes Szenario"]


# --- format_run -----------------------------------------------------------------
def test_format_run_without_run_tag_matches_legacy_format():
    group = {"number": None, "label": None, "layer": None, "singleton": True,
             "scenarios": [{"tags": {"@US-904-error"}, "title": "Drittes Szenario"}]}
    assert nr.format_run(group) == '`@US-904-error` „Drittes Szenario"'


def test_format_run_with_run_tag_lists_all_titles():
    scenarios = nr.parse_scenarios(FEATURE_WITH_RUNS)
    groups = nr.group_runs(scenarios)
    formatted = nr.format_run(groups[1])
    assert formatted == '`run-2` „Anlegen·Validierung" (Full-Stack): „Leerer Name", „Leere Einheit"'


def test_format_run_singleton_note():
    scenarios = nr.parse_scenarios(FEATURE_WITH_RUNS)
    groups = nr.group_runs(scenarios)
    formatted = nr.format_run(groups[2])
    assert "Singleton" in formatted


# --- check_integrity ---------------------------------------------------------
def test_check_integrity_clean():
    assert nr.check_integrity([FEATURE], ["// Szenario: Erstes Szenario\n"]) == []


def test_check_integrity_orphan_comment():
    violations = nr.check_integrity([FEATURE], ["// Szenario: Gibt es nicht\n"])
    assert len(violations) == 1
    assert "Gibt es nicht" in violations[0]


def test_check_integrity_duplicate():
    spec_a = "// Szenario: Erstes Szenario\n"
    spec_b = "// Szenario: Erstes Szenario\n"
    violations = nr.check_integrity([FEATURE], [spec_a, spec_b])
    assert any("Erstes Szenario" in v and "doppelt" in v.lower() for v in violations)


# --- check_run_consistency ----------------------------------------------------
def test_check_run_consistency_clean_when_metadata_matches():
    scenarios = nr.parse_scenarios(FEATURE_WITH_RUNS)
    assert nr.check_run_consistency(scenarios) == []


def _scenario(title, number, label="X", layer="Full-Stack", phase="SKELETON", needs=()):
    return {
        "tags": set(), "title": title, "phase": phase, "needs": needs,
        "run": {"number": number, "label": label, "layer": layer, "singleton": False},
    }


def test_check_run_consistency_flags_mismatched_label():
    scenarios = [
        _scenario("A", 2, label="Anlegen·Validierung"),
        _scenario("B", 2, label="Anlegen·Validierung TYPO"),
    ]
    violations = nr.check_run_consistency(scenarios)
    assert len(violations) == 1
    assert "run-2" in violations[0]


def test_check_run_consistency_flags_mismatched_layer():
    scenarios = [_scenario("A", 3), _scenario("B", 3, layer="Frontend-only")]
    assert len(nr.check_run_consistency(scenarios)) == 1


def test_check_run_consistency_flags_mismatched_phase():
    # Ein Lauf mit zwei Phasen wäre still: collect_runs() nähme die des ERSTEN Szenarios.
    scenarios = [_scenario("A", 4), _scenario("B", 4, phase="MVP")]
    assert len(nr.check_run_consistency(scenarios)) == 1


def test_check_run_consistency_flags_mismatched_needs():
    scenarios = [_scenario("A", 5), _scenario("B", 5, needs=("run-1",))]
    assert len(nr.check_run_consistency(scenarios)) == 1


# --- matches_story -------------------------------------------------------------
def test_matches_story_true_for_matching_tag():
    assert nr.matches_story(FEATURE, "US-904") is True


def test_matches_story_false_for_other_story():
    assert nr.matches_story(FEATURE, "US-999") is False


def test_matches_story_accepts_at_prefix():
    assert nr.matches_story(FEATURE, "@US-904") is True


# --- render ------------------------------------------------------------------
def test_render_substitutes_token():
    memory = "**Aktuelle Story:** US-904\n\n- US-904: {{NEXT_RUN}}\n"
    out = nr.render(memory, feature_texts=[FEATURE], implemented=set())
    assert "{{NEXT_RUN}}" not in out
    assert "`@US-904-happy-path` „Erstes Szenario\"" in out


def test_render_substitutes_token_with_run_group():
    memory = "**Aktuelle Story:** US-904\n\n- US-904: {{NEXT_RUN}}\n"
    out = nr.render(memory, feature_texts=[FEATURE_WITH_RUNS], implemented=set())
    assert "`run-1`" in out


def test_render_fallback_when_story_missing():
    memory = "kein Story-Feld\n\n- {{NEXT_RUN}}\n"
    out = nr.render(memory, feature_texts=[FEATURE], implemented=set())
    # Token wird durch eine lesbare Notiz ersetzt, Memory bleibt intakt
    assert "{{NEXT_RUN}}" not in out
    assert "kein Story-Feld" in out


def test_render_all_done_note():
    memory = "**Aktuelle Story:** US-904\n\n- {{NEXT_RUN}}\n"
    done = {"Erstes Szenario", "Zweites Szenario", "Drittes Szenario"}
    out = nr.render(memory, feature_texts=[FEATURE], implemented=done)
    assert "{{NEXT_RUN}}" not in out


# --- Phasen und Abhängigkeitskanten -------------------------------------------
STORY_FEATURE = textwrap.dedent("""\
    @US-904
    Feature: Zutaten verwalten

      # @phase: SKELETON

      Background:
        Given die Anwendung ist gestartet

      # @run-1 · Anlegen · Full-Stack
      @US-904-happy-path
      Scenario: Zutat anlegen
        When a
        Then b

      # @run-8 · Löschen · Full-Stack
      @US-904-happy-path
      Scenario: Zutat löschen
        When a
        Then b

      # @run-9 · Bearbeiten · Full-Stack · Phase:MVP
      @US-904-happy-path
      Scenario: Zutat bearbeiten
        When a
        Then b
    """)

CROSS_FEATURE = textwrap.dedent("""\
    @CROSS-interaction
    Feature: Querschnittliches Interaktionsverhalten

      # @phase: SKELETON
      # @braucht: US-904/run-8

      @CROSS-interaction-happy-path
      Scenario: Der Undo-Toast lässt sich manuell schließen
        When a
        Then b
    """)

ALL_TEXTS = [STORY_FEATURE, CROSS_FEATURE]


def _collect(texts=None):
    return nr.collect_runs(texts if texts is not None else ALL_TEXTS)


def test_collect_runs_carries_phase_and_needs():
    groups = _collect()
    anlegen = next(g for g in groups if g["number"] == 1)
    assert anlegen["phase"] == "SKELETON"
    assert anlegen["needs"] == ()


def test_collect_runs_takes_run_level_phase_over_file_default():
    groups = _collect()
    bearbeiten = next(g for g in groups if g["number"] == 9)
    assert bearbeiten["phase"] == "MVP"


def test_collect_runs_carries_needs_for_untagged_cross_scenario():
    groups = _collect()
    cross = next(g for g in groups if g["number"] is None)
    assert cross["needs"] == ("US-904/run-8",)


def test_run_out_of_phase_is_not_a_candidate():
    # run-9 ist MVP, das Projekt steht auf SKELETON – er darf nicht vorgeschlagen werden.
    group = nr.next_run_global(_collect(), implemented=set(), phase="SKELETON", story="US-904")
    assert group["number"] == 1


def test_run_becomes_candidate_once_phase_is_reached():
    done = {"Zutat anlegen", "Zutat löschen", "Der Undo-Toast lässt sich manuell schließen"}
    group = nr.next_run_global(_collect(), implemented=done, phase="MVP", story="US-904")
    assert group["number"] == 9


def test_dependency_blocks_run_until_predecessor_done():
    # Das CROSS-Szenario braucht US-904/run-8 (Löschen) – solange offen, ist es kein Kandidat.
    group = nr.next_run_global(_collect(), implemented=set(), phase="SKELETON", story="US-904")
    assert group["number"] == 1
    assert "CROSS" not in " ".join(group["tags"])


def test_dependency_released_when_predecessor_done():
    done = {"Zutat anlegen", "Zutat löschen"}
    group = nr.next_run_global(_collect(), implemented=done, phase="SKELETON", story="US-904")
    assert group["scenarios"][0]["title"] == "Der Undo-Toast lässt sich manuell schließen"


def test_current_story_wins_over_other_features():
    # Beide fällig und unblockiert: die aktuelle Story kommt zuerst (Arbeitsweise „eine Story am Stück").
    cross_ohne_kante = CROSS_FEATURE.replace("  # @braucht: US-904/run-8\n", "")
    groups = nr.collect_runs([STORY_FEATURE, cross_ohne_kante])
    group = nr.next_run_global(groups, implemented=set(), phase="SKELETON", story="US-904")
    assert group["number"] == 1


def test_other_feature_reached_once_story_is_exhausted():
    # Genau die Sackgasse aus OBS-S117-1: Story fertig, querschnittliche Szenarien bleiben offen.
    done = {"Zutat anlegen", "Zutat löschen"}
    group = nr.next_run_global(_collect(), implemented=done, phase="SKELETON", story="US-904")
    assert group is not None
    assert group["scenarios"][0]["title"] == "Der Undo-Toast lässt sich manuell schließen"


def test_dead_dependency_reference_blocks_instead_of_passing_silently():
    text = CROSS_FEATURE.replace("US-904/run-8", "US-904/run-99")
    groups = nr.collect_runs([STORY_FEATURE, text])
    done = {"Zutat anlegen", "Zutat löschen"}
    group = nr.next_run_global(groups, implemented=done, phase="SKELETON", story="US-904")
    assert group is None


# --- Guard: Phasen und Kanten --------------------------------------------------
def test_check_dependencies_clean():
    assert nr.check_dependencies(_collect()) == []


def test_check_dependencies_flags_dead_reference():
    groups = nr.collect_runs([STORY_FEATURE, CROSS_FEATURE.replace("run-8", "run-99")])
    violations = nr.check_dependencies(groups)
    assert len(violations) == 1
    assert "run-99" in violations[0]


def test_check_dependencies_flags_cycle():
    a = STORY_FEATURE.replace(
        "# @run-1 · Anlegen · Full-Stack",
        "# @run-1 · Anlegen · Full-Stack · braucht:run-8",
    ).replace(
        "# @run-8 · Löschen · Full-Stack",
        "# @run-8 · Löschen · Full-Stack · braucht:run-1",
    )
    violations = nr.check_dependencies(nr.collect_runs([a]))
    assert any("Zyklus" in v for v in violations)


def test_check_dependencies_flags_missing_phase():
    violations = nr.check_dependencies(nr.collect_runs([FEATURE_WITH_RUNS]))
    assert any("ohne Phase" in v for v in violations)


def test_check_dependencies_accepts_intra_file_reference():
    text = STORY_FEATURE.replace(
        "# @run-8 · Löschen · Full-Stack",
        "# @run-8 · Löschen · Full-Stack · braucht:run-1",
    )
    assert nr.check_dependencies(nr.collect_runs([text])) == []


# --- render mit Phase ----------------------------------------------------------
def test_render_uses_phase_from_memory():
    memory = "**Phase:** SKELETON 🔄\n**Aktuelle Story:** US-904\n\n- {{NEXT_RUN}}\n"
    out = nr.render(memory, feature_texts=ALL_TEXTS, implemented=set())
    assert "`run-1`" in out


def test_render_names_the_next_phase_when_only_the_phase_blocks():
    # Sonst verweist die Notiz auf --check, der hier grün ist: korrekt zurückgehaltene Läufe
    # sind kein Verstoß. Der Leser braucht den Grund, nicht einen Befehl ohne Befund.
    memory = "**Phase:** SKELETON 🔄\n**Aktuelle Story:** US-904\n\n- {{NEXT_RUN}}\n"
    done = {"Zutat anlegen", "Zutat löschen", "Der Undo-Toast lässt sich manuell schließen"}
    out = nr.render(memory, feature_texts=ALL_TEXTS, implemented=done)
    assert "Phase MVP" in out


def test_render_says_when_a_dependency_blocks():
    memory = "**Phase:** SKELETON 🔄\n**Aktuelle Story:** US-904\n\n- {{NEXT_RUN}}\n"
    done = {"Zutat anlegen"}
    out = nr.render(memory, feature_texts=[CROSS_FEATURE], implemented=done)
    assert "braucht:US-904/run-8" in out


def test_render_reaches_cross_feature_when_story_done():
    memory = "**Phase:** SKELETON 🔄\n**Aktuelle Story:** US-904\n\n- {{NEXT_RUN}}\n"
    done = {"Zutat anlegen", "Zutat löschen"}
    out = nr.render(memory, feature_texts=ALL_TEXTS, implemented=done)
    assert "Der Undo-Toast lässt sich manuell schließen" in out


# --- Stories ohne Workshop und Phasen-Abschluss ---------------------------------
# Der Resolver kennt nur Läufe. Eine Story der erreichten Phase, für die noch kein Workshop lief,
# hat keine – und die Notiz meldete dann „kein Lauf in Phase SKELETON fällig", als sei die Phase
# fertig. Die Fixture hat die Form von `docs/stories/szenario_*.md`: Inhaltsliste mit Phasen-Tag,
# darunter die Detailzeile derselben Story, die nicht doppelt zählen darf.
STORY_FILE = textwrap.dedent("""\
    # Szenario 8 – Die Resteverwertung (Planung)

    > Teil von [docs/stories/user-stories.md](../docs/stories/user-stories.md).

    ## Inhalt

    - Szenario-Narrativ (Rezept-Liste, Suche, Plan-Anpassung)
    - US-801 (Rezept-Liste) [MVP]
    - US-803 (Manuelle Plan-Anpassung) [SKELETON]
    - US-804 (Kategorisierte Übersicht) [V2]
    - US-805 (Reste-Idee (vage)) [PARKING]

    ---

    *   **US-803 (Manuelle Plan-Anpassung) [SKELETON]:** Als *Feierabend-Planer* möchte ich …
    """)

STORY_FILE_904 = textwrap.dedent("""\
    ## Inhalt

    - US-904 (Zutaten-Verwaltung) [SKELETON]
    """)

STORY_TEXTS = [STORY_FILE, STORY_FILE_904]
SKELETON_DONE = {"Zutat anlegen", "Zutat löschen", "Der Undo-Toast lässt sich manuell schließen"}
MEMORY = "**Phase:** SKELETON 🔄\n**Aktuelle Story:** US-904\n\n- {{NEXT_RUN}}\n"


def test_story_of_reached_phase_without_feature_is_reported():
    assert nr.open_story_stages(STORY_TEXTS, ALL_TEXTS, "SKELETON") == ["US-803"]


def test_story_with_feature_is_not_reported():
    feature_803 = STORY_FEATURE.replace("@US-904", "@US-803")
    assert nr.open_story_stages(STORY_TEXTS, [STORY_FEATURE, feature_803], "SKELETON") == []


def test_stories_of_earlier_phases_count_too():
    assert nr.open_story_stages(STORY_TEXTS, ALL_TEXTS, "MVP") == ["US-801", "US-803"]


def test_stories_outside_the_known_phases_are_never_reported():
    # V2 und PARKING kennt der Resolver nicht als Phase – sie werden nie „erreicht".
    assert nr.open_story_stages(STORY_TEXTS, ALL_TEXTS, "V1") == ["US-801", "US-803"]


def test_unreadable_story_line_fails_loudly():
    # Verschwände die Story still, meldete der Resolver am Ende eine fertige Phase.
    text = STORY_FILE.replace("[SKELETON]\n", "[SKELETON] ← Walking Skeleton\n", 1)
    with pytest.raises(ValueError, match="US-803"):
        nr.open_story_stages([text], ALL_TEXTS, "SKELETON")


def test_no_phase_means_no_story_finding():
    assert nr.open_story_stages(STORY_TEXTS, ALL_TEXTS, None) == []


def test_render_names_stories_without_feature_instead_of_a_finished_phase():
    out = nr.render(MEMORY, feature_texts=ALL_TEXTS, implemented=SKELETON_DONE,
                    story_texts=STORY_TEXTS)
    assert "US-803" in out and "gherkin-workshop" in out
    assert "abgeschlossen" not in out


def test_a_due_run_comes_before_a_missing_feature():
    out = nr.render(MEMORY, feature_texts=ALL_TEXTS, implemented=set(), story_texts=STORY_TEXTS)
    assert "`run-1`" in out and "US-803" not in out


def test_render_announces_the_finished_phase():
    out = nr.render(MEMORY, feature_texts=ALL_TEXTS, implemented=SKELETON_DONE,
                    story_texts=[STORY_FILE_904])
    assert "Phase SKELETON abgeschlossen" in out
    assert "Phasen-Review" in out
    assert "Phase MVP" in out  # was danach kommt, bleibt sichtbar


def test_phase_status_is_silent_while_a_run_is_due():
    assert nr.phase_status(MEMORY, ALL_TEXTS, set(), STORY_TEXTS) is None


def test_phase_status_is_silent_while_a_dependency_blocks():
    # Ein Lauf der Phase ist offen und wartet nur auf seine Kante: kein Befund über die Phase.
    status = nr.phase_status(MEMORY, [CROSS_FEATURE], {"Zutat anlegen"}, story_texts=[])
    assert status is None


def test_phase_status_reports_missing_features_and_finished_phase():
    luecke = nr.phase_status(MEMORY, ALL_TEXTS, SKELETON_DONE, STORY_TEXTS)
    fertig = nr.phase_status(MEMORY, ALL_TEXTS, SKELETON_DONE, [STORY_FILE_904])
    assert "US-803" in luecke
    assert "abgeschlossen" in fertig


# --- Stufen einer Story ----------------------------------------------------------
# Eine Story hat Akzeptanzkriterien je Stufe. Galt sie mit ihrer ersten Feature-Datei als
# erledigt, waren spätere Stufen unsichtbar (bei US-904 und US-602 nur per Hand in AGENT_MEMORY
# überbrückt). Die Fixture trägt die Kopf-Varianten des Bestands.
STORY_FILE_STUFEN = textwrap.dedent("""\
    ## Inhalt

    - US-904 (Zutaten-Verwaltung) [SKELETON]
    - US-602 (Manuelle Erfassung) [SKELETON]
    - US-607 (Zutaten-Zuordnung) [MVP]
    - US-701 (Regeln) [MVP]

    ---

    *   **US-904 (Zutaten-Verwaltung) [SKELETON]:** Als *Rezept-Sammler* …
        *   **Akzeptanzkriterien (SKELETON-Version):**
            *   Anlegen.
        *   **Akzeptanzkriterien (MVP-Version – Bearbeiten + Modifier):**
            *   Bearbeiten.
        *   **Akzeptanzkriterien (V1-Version – Tags):**
            *   Tags.

    *   **US-602 (Manuelle Erfassung) [SKELETON]:** Als *Rezept-Sammler* …
        *   **Akzeptanzkriterien (SKELETON):**
            *   Formular.
        *   **Akzeptanzkriterien (MVP – Bild-Upload, Basis-Portion):**
            *   Upload.

    *   **US-607 (Zutaten-Zuordnung) [MVP]:** Als *Rezept-Sammler* …
        *   **Akzeptanzkriterien (MVP – manuelle Erfassung):**
            *   Je Schritt.
        *   **Akzeptanzkriterien (MVP – Zutatenzeile):**
            *   Brüche.
        *   **Akzeptanzkriterien (V2 – Import-Workflow):**
            *   Import.

    *   **US-701 (Regeln) [MVP]:** Als *Feierabend-Planer* …
        *   **Akzeptanzkriterien:**
            *   Regel.
    """)

FEATURE_602 = textwrap.dedent("""\
    @US-602
    Feature: Rezepte erfassen

      # @phase: SKELETON

      Scenario: Rezept anlegen
        When a
        Then b
    """)
FEATURE_607 = FEATURE_602.replace("@US-602", "@US-607").replace("SKELETON", "MVP")
FEATURE_701 = FEATURE_602.replace("@US-602", "@US-701").replace("SKELETON", "MVP")
STUFEN_FEATURES = [STORY_FEATURE, FEATURE_602, FEATURE_607, FEATURE_701]


def test_story_stages_come_from_the_acceptance_headers():
    stages = nr.story_stages([STORY_FILE_STUFEN])
    assert stages["US-904"] == ("SKELETON", "MVP", "V1")
    assert stages["US-602"] == ("SKELETON", "MVP")
    assert stages["US-607"] == ("MVP", "V2")  # zwei MVP-Blöcke sind eine Stufe
    assert stages["US-701"] == ("MVP",)  # Block ohne Phase: die Phase der Story


def test_story_without_detail_section_has_its_listed_phase():
    assert nr.story_stages(STORY_TEXTS)["US-801"] == ("MVP",)


def test_later_stage_of_a_story_with_feature_is_reported_once_reached():
    assert nr.open_story_stages([STORY_FILE_STUFEN], STUFEN_FEATURES, "SKELETON") == []
    assert nr.open_story_stages([STORY_FILE_STUFEN], STUFEN_FEATURES, "MVP") == [
        "US-602 (MVP)", "US-904 (MVP)"]


def test_stage_named_in_stufen_counts_as_done():
    feature = FEATURE_602.replace("# @phase: SKELETON", "# @phase: SKELETON\n  # @stufen: SKELETON, MVP")
    features = [STORY_FEATURE, feature, FEATURE_607, FEATURE_701]
    assert nr.open_story_stages([STORY_FILE_STUFEN], features, "MVP") == ["US-904 (MVP)"]


def test_stufen_replaces_the_file_phase():
    # Nennt @stufen nur MVP, ist SKELETON offen – @stufen ist die vollständige Angabe.
    feature = FEATURE_602.replace("# @phase: SKELETON", "# @phase: SKELETON\n  # @stufen: MVP")
    features = [STORY_FEATURE, feature, FEATURE_607, FEATURE_701]
    assert nr.open_story_stages([STORY_FILE_STUFEN], features, "SKELETON") == ["US-602 (SKELETON)"]


def test_story_without_feature_is_still_named_without_stage():
    assert nr.open_story_stages([STORY_FILE_STUFEN], [STORY_FEATURE], "MVP") == [
        "US-602", "US-607", "US-701", "US-904 (MVP)"]


def test_stages_beyond_the_known_phases_are_never_reported():
    assert "US-607 (V2)" not in nr.open_story_stages([STORY_FILE_STUFEN], STUFEN_FEATURES, "V1")


def test_unreadable_acceptance_header_fails_loudly():
    # Ein Kopf, dessen Phase nicht lesbar ist, ließe die Stufe still verschwinden.
    text = STORY_FILE_STUFEN.replace("(MVP – Bild-Upload, Basis-Portion)", "(Erweiterung)")
    with pytest.raises(ValueError, match="US-602"):
        nr.story_stages([text])


def test_real_story_files_parse():
    # Echtes Artefakt: Jeder Akzeptanzkriterien-Kopf im Bestand muss lesbar sein.
    stages = nr.story_stages(nr._story_texts())
    assert stages and all(stage for stage in stages.values())


def test_render_names_the_open_stage():
    memory = MEMORY.replace("SKELETON", "MVP")
    out = nr.render(memory, feature_texts=STUFEN_FEATURES,
                    implemented=SKELETON_DONE | {"Zutat bearbeiten", "Rezept anlegen"},
                    story_texts=[STORY_FILE_STUFEN])
    assert "US-904 (MVP)" in out and "gherkin-workshop" in out


def test_check_flags_stufen_the_story_does_not_have():
    feature = FEATURE_602.replace("# @phase: SKELETON", "# @phase: SKELETON\n  # @stufen: SKELETON, V1")
    violations = nr.check_stufen([feature], [STORY_FILE_STUFEN])
    assert len(violations) == 1 and "US-602" in violations[0] and "V1" in violations[0]


def test_check_accepts_stufen_the_story_has():
    feature = FEATURE_602.replace("# @phase: SKELETON", "# @phase: SKELETON\n  # @stufen: SKELETON, MVP")
    assert nr.check_stufen([feature], [STORY_FILE_STUFEN]) == []


# --- Aufrufpfad: die CLI liest die Story-Dateien wirklich -------------------------
def _bestand(tmp_path, monkeypatch, story_texts):
    features, stories = tmp_path / "features", tmp_path / "stories"
    features.mkdir()
    stories.mkdir()
    for i, text in enumerate(ALL_TEXTS):
        (features / f"f{i}.feature").write_text(text, encoding="utf-8")
    for i, text in enumerate(story_texts):
        (stories / f"szenario_{i}_x.md").write_text(text, encoding="utf-8")
    (stories / "user-stories.md").write_text("- US-999 (Index) [SKELETON]\n", encoding="utf-8")
    memory = tmp_path / "AGENT_MEMORY.md"
    memory.write_text(MEMORY, encoding="utf-8")
    monkeypatch.setattr(nr, "_FEATURES_DIR", features)
    monkeypatch.setattr(nr, "_STORIES_DIR", stories)
    monkeypatch.setattr(nr, "_gather_implemented", lambda: SKELETON_DONE)
    # Hermetisch: ohne diese beiden läse --render die echten Tracker des Repos.
    monkeypatch.setattr(nr, "_TD_FILE", tmp_path / "tech-debt.md")
    monkeypatch.setattr(nr, "_OQ_FILE", tmp_path / "open-questions.md")
    return str(memory)


def test_cli_render_reads_the_story_files(tmp_path, monkeypatch, capsys):
    memory = _bestand(tmp_path, monkeypatch, STORY_TEXTS)
    assert nr.main(["--render", memory]) == 0
    out = capsys.readouterr().out
    assert "US-803" in out
    assert "US-999" not in out  # der Index ist keine Story-Datei


def test_cli_phase_status_prints_the_finding(tmp_path, monkeypatch, capsys):
    memory = _bestand(tmp_path, monkeypatch, [STORY_FILE_904])
    assert nr.main(["--phase-status", memory]) == 0
    assert "Phase SKELETON abgeschlossen" in capsys.readouterr().out


def test_cli_phase_status_prints_nothing_while_a_run_is_due(tmp_path, monkeypatch, capsys):
    memory = _bestand(tmp_path, monkeypatch, STORY_TEXTS)
    monkeypatch.setattr(nr, "_gather_implemented", set)
    assert nr.main(["--phase-status", memory]) == 0
    assert capsys.readouterr().out == ""


def test_cli_check_reports_wrong_stufen(tmp_path, monkeypatch, capsys):
    features, stories, e2e = tmp_path / "features", tmp_path / "stories", tmp_path / "e2e"
    for d in (features, stories, e2e):
        d.mkdir()
    feature = FEATURE_602.replace("# @phase: SKELETON", "# @phase: SKELETON\n  # @stufen: SKELETON, V1")
    (features / "recipes.feature").write_text(feature, encoding="utf-8")
    (stories / "szenario_6_x.md").write_text(STORY_FILE_STUFEN, encoding="utf-8")
    monkeypatch.setattr(nr, "_FEATURES_DIR", features)
    monkeypatch.setattr(nr, "_STORIES_DIR", stories)
    monkeypatch.setattr(nr, "_E2E_DIR", e2e)
    assert nr.main(["--check"]) == 1
    assert "V1" in capsys.readouterr().err


# --- Laufanhang: Einträge, deren Fälligkeit an einem Szenario des Laufs hängt --------
# Fixtures in Bestandsform (tech-debt.md, open-questions.md, AGENT_MEMORY.md).
TD_TEXT = textwrap.dedent("""\
    ## TD-S120-4 — Kein Test-Data-Builder für `IngredientDbType`
    **Fällig:** Szenario:„Leerer Name", Phase:MVP – die nächste Entität mit eigenen Tests.
    **Problem:** p
    **Behebung:** b

    ## TD-S108-2 — Frontend: kein Fokus-Management nach Löschen
    **Fällig:** Szenario:„Zutat anlegen", Phase:V1 – erster Navigationsschritt.
    **Problem:** p
    **Behebung:** b

    ## TD-S135-1 — Ausgaben unbegrenzt lang
    **Fällig:** Phase:MVP – Querschnitt.
    **Problem:** p
    **Behebung:** b
    """)

OQ_TEXT = textwrap.dedent("""\
    ## OQ-S135-2 — Zutatenzeile zerlegen: unscharfe Zuordnung
    **Frage:** Wie ordnet der Parser zu?
    **Fällig:** Szenario:"Leere Einheit", Phase:MVP – im Workshop der MVP-Stufe.
    **Hintergrund:** h
    """)

MEMORY_MIT_PRIORITAET = MEMORY + textwrap.dedent("""\

    ## Nächste Prioritäten

    - **Guideline erweitern** — `Fällig: Szenario:„Leerer Name", Phase:MVP` · Quelle: x · Done: y
    - **Ohne Szenario** — `Fällig: Phase:MVP` · Quelle: x · Done: y
    """)


def _run(feature_text: str, number: int) -> dict:
    return next(g for g in nr.group_runs(nr.parse_scenarios(feature_text)) if g["number"] == number)


def test_tracker_eintraege_liest_td_oq_und_prioritaeten_in_bestandsform():
    eintraege = nr.tracker_eintraege(TD_TEXT, OQ_TEXT, MEMORY_MIT_PRIORITAET)
    kennungen = [e[0] for e in eintraege]
    assert kennungen == ["TD-S120-4", "TD-S108-2", "TD-S135-1", "OQ-S135-2", "Priorität", "Priorität"]
    assert eintraege[0][1] == "Kein Test-Data-Builder für `IngredientDbType`"
    assert eintraege[3][1] == "Zutatenzeile zerlegen: unscharfe Zuordnung"
    assert eintraege[4][1] == "Guideline erweitern"


def test_laufanhang_nennt_jeden_eintrag_mit_seinem_szenario():
    eintraege = nr.tracker_eintraege(TD_TEXT, OQ_TEXT, MEMORY_MIT_PRIORITAET)
    block = nr.laufanhang(_run(FEATURE_WITH_RUNS, 2), eintraege)
    assert "**Teil dieses Laufs**" in block
    assert "TD-S120-4 „Kein Test-Data-Builder für `IngredientDbType`\" – an „Leerer Name\"" in block
    assert "OQ-S135-2 „Zutatenzeile zerlegen: unscharfe Zuordnung\" – an „Leere Einheit\"" in block
    assert "Priorität „Guideline erweitern\" – an „Leerer Name\"" in block


def test_laufanhang_laesst_eintraege_anderer_laeufe_und_ohne_szenario_weg():
    eintraege = nr.tracker_eintraege(TD_TEXT, OQ_TEXT, MEMORY_MIT_PRIORITAET)
    block = nr.laufanhang(_run(FEATURE_WITH_RUNS, 2), eintraege)
    assert "TD-S108-2" not in block       # hängt an „Zutat anlegen" = run-1
    assert "TD-S135-1" not in block       # nur Phase – kommt über td-due, nicht hier
    assert "Ohne Szenario" not in block


def test_laufanhang_ist_leer_ohne_treffer():
    assert nr.laufanhang(_run(FEATURE_WITH_RUNS, 3), nr.tracker_eintraege(TD_TEXT, OQ_TEXT, "")) == ""


def test_laufanhang_ist_eingerueckt_damit_er_zur_lauf_zeile_gehoert():
    block = nr.laufanhang(_run(FEATURE_WITH_RUNS, 1), nr.tracker_eintraege(TD_TEXT, "", ""))
    assert block and all(zeile.startswith("  ") for zeile in block.splitlines())


def test_render_haengt_den_block_an_den_naechsten_lauf():
    memory = "**Aktuelle Story:** US-904\n**Nächster Lauf:** {{NEXT_RUN}}\n"
    out = nr.render(memory, feature_texts=[FEATURE_WITH_RUNS], implemented=set(),
                    eintraege=nr.tracker_eintraege(TD_TEXT, OQ_TEXT, ""))
    zeilen = out.splitlines()
    lauf = next(i for i, z in enumerate(zeilen) if z.startswith("**Nächster Lauf:** `run-1`"))
    assert "**Teil dieses Laufs**" in zeilen[lauf + 1]
    assert "TD-S108-2" in zeilen[lauf + 2]
    assert "TD-S120-4" not in out          # gehört zu run-2, nicht zum nächsten Lauf


def test_cli_render_liest_tracker_dateien(tmp_path, monkeypatch, capsys):
    memory = _bestand(tmp_path, monkeypatch, STORY_TEXTS)
    (tmp_path / "tech-debt.md").write_text(
        "## TD-S120-4 — Builder fehlt\n**Fällig:** Szenario:„Zutat anlegen\", Phase:MVP – x\n"
        "**Problem:** p\n**Behebung:** b\n", encoding="utf-8")
    monkeypatch.setattr(nr, "_gather_implemented", set)
    assert nr.main(["--render", memory]) == 0
    out = capsys.readouterr().out
    assert "**Teil dieses Laufs**" in out
    assert "TD-S120-4 „Builder fehlt\" – an „Zutat anlegen\"" in out

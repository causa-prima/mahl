"""Tests für next_run.py – Lauf-Resolver + Mapping-Integritäts-Guard."""
import textwrap

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

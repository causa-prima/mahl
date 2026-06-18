"""Tests für next_scenario.py – Szenario-Resolver + Mapping-Integritäts-Guard."""
import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import next_scenario as ns  # noqa: E402


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


# --- extract_story -----------------------------------------------------------
def test_extract_story():
    mem = "**Aktuelle Story:** US-904 (Zutaten) → `features/ingredients.feature`"
    assert ns.extract_story(mem) == "US-904"


def test_extract_story_none_when_absent():
    assert ns.extract_story("kein Story-Feld hier") is None


# --- feature_tags / parse_scenarios ------------------------------------------
def test_feature_tags_detected_not_on_first_scenario():
    assert "@US-904" in ns.feature_tags(FEATURE)
    scenarios = ns.parse_scenarios(FEATURE)
    # Feature-Tag darf nicht ans erste Szenario gehängt werden
    assert scenarios[0]["tags"] == {"@US-904-happy-path"}


def test_parse_scenarios_order():
    titles = [s["title"] for s in ns.parse_scenarios(FEATURE)]
    assert titles == ["Erstes Szenario", "Zweites Szenario", "Drittes Szenario"]


# --- implemented_titles_from_text --------------------------------------------
def test_implemented_titles_parses_comments():
    spec = "// Szenario: Erstes Szenario\ntest('foo', ...)\n//  Szenario:  Zweites Szenario  \n"
    assert ns.implemented_titles_from_text(spec) == {"Erstes Szenario", "Zweites Szenario"}


def test_implemented_titles_empty_when_no_comments():
    assert ns.implemented_titles_from_text("test('foo')") == set()


# --- next_scenario -----------------------------------------------------------
def test_next_scenario_returns_first_unimplemented():
    scenarios = ns.parse_scenarios(FEATURE)
    nxt = ns.next_scenario(scenarios, implemented={"Erstes Szenario"})
    assert nxt["title"] == "Zweites Szenario"


def test_next_scenario_none_when_all_done():
    scenarios = ns.parse_scenarios(FEATURE)
    done = {"Erstes Szenario", "Zweites Szenario", "Drittes Szenario"}
    assert ns.next_scenario(scenarios, implemented=done) is None


def test_next_scenario_skips_excluded_tags():
    scenarios = ns.parse_scenarios(FEATURE)
    done = {"Erstes Szenario", "Zweites Szenario"}
    # Einziges verbleibendes ist @US-904-error → ausgeschlossen → None
    assert ns.next_scenario(scenarios, implemented=done, exclude_tags={"@US-904-error"}) is None


# --- open_scenarios / done_scenarios -----------------------------------------
def test_open_scenarios_in_order():
    scenarios = ns.parse_scenarios(FEATURE)
    opened = ns.open_scenarios(scenarios, implemented={"Erstes Szenario"})
    assert [s["title"] for s in opened] == ["Zweites Szenario", "Drittes Szenario"]


def test_open_scenarios_respects_exclude_tags():
    scenarios = ns.parse_scenarios(FEATURE)
    opened = ns.open_scenarios(scenarios, implemented=set(), exclude_tags={"@US-904-error"})
    assert "Drittes Szenario" not in [s["title"] for s in opened]


def test_done_scenarios_in_order():
    scenarios = ns.parse_scenarios(FEATURE)
    done = ns.done_scenarios(scenarios, implemented={"Erstes Szenario", "Drittes Szenario"})
    assert [s["title"] for s in done] == ["Erstes Szenario", "Drittes Szenario"]


# --- format_scenario ---------------------------------------------------------
def test_format_scenario():
    s = {"tags": {"@US-904-error"}, "title": "Drittes Szenario"}
    assert ns.format_scenario(s) == '`@US-904-error` „Drittes Szenario"'


# --- check_integrity ---------------------------------------------------------
def test_check_integrity_clean():
    assert ns.check_integrity([FEATURE], ["// Szenario: Erstes Szenario\n"]) == []


def test_check_integrity_orphan_comment():
    violations = ns.check_integrity([FEATURE], ["// Szenario: Gibt es nicht\n"])
    assert len(violations) == 1
    assert "Gibt es nicht" in violations[0]


def test_check_integrity_duplicate():
    spec_a = "// Szenario: Erstes Szenario\n"
    spec_b = "// Szenario: Erstes Szenario\n"
    violations = ns.check_integrity([FEATURE], [spec_a, spec_b])
    assert any("Erstes Szenario" in v and "doppelt" in v.lower() for v in violations)


# --- render ------------------------------------------------------------------
def test_render_substitutes_token():
    memory = "**Aktuelle Story:** US-904\n\n- US-904: {{NEXT_SCENARIO}}\n"
    out = ns.render(memory, feature_texts=[FEATURE], implemented=set())
    assert "{{NEXT_SCENARIO}}" not in out
    assert "`@US-904-happy-path` „Erstes Szenario\"" in out


def test_render_fallback_when_story_missing():
    memory = "kein Story-Feld\n\n- {{NEXT_SCENARIO}}\n"
    out = ns.render(memory, feature_texts=[FEATURE], implemented=set())
    # Token wird durch eine lesbare Notiz ersetzt, Memory bleibt intakt
    assert "{{NEXT_SCENARIO}}" not in out
    assert "kein Story-Feld" in out


def test_render_all_done_note():
    memory = "**Aktuelle Story:** US-904\n\n- {{NEXT_SCENARIO}}\n"
    done = {"Erstes Szenario", "Zweites Szenario", "Drittes Szenario"}
    out = ns.render(memory, feature_texts=[FEATURE], implemented=done)
    assert "{{NEXT_SCENARIO}}" not in out

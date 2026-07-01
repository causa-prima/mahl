"""Tests für _feature.py – insbesondere das Parsen der `# @run-N`-Lauf-Kommentare."""
import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from _feature import find_malformed_run_comments, parse_feature  # noqa: E402


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

      # @run-2 · Anlegen·Dialog-Verhalten · Frontend-only
      @US-904-happy-path
      Scenario: Felder sind beim Öffnen des Dialogs leer
        When a
        Then b

      # @run-2 · Anlegen·Dialog-Verhalten · Frontend-only
      @US-904-happy-path
      Scenario: Abbrechen schließt Dialog
        When a
        Then b

      # @run-5 · Anlegen·Mehrfeld-Validierung · Full-Stack · Singleton
      @US-904-error
      Scenario: Beide Pflichtfelder leer
        When a
        Then b

      @US-904-error
      Scenario: Ohne Run-Tag
        When a
        Then b
    """)


def test_scenario_carries_run_metadata():
    _, _, scenarios = parse_feature(FEATURE_WITH_RUNS)
    run = scenarios[0]["run"]
    assert run == {"number": 1, "label": "Anlegen·Success", "layer": "Full-Stack", "singleton": False}


def test_run_singleton_flag_detected():
    _, _, scenarios = parse_feature(FEATURE_WITH_RUNS)
    singleton_scenario = next(s for s in scenarios if s["title"] == "Beide Pflichtfelder leer")
    assert singleton_scenario["run"]["singleton"] is True


def test_multiple_scenarios_share_same_run():
    _, _, scenarios = parse_feature(FEATURE_WITH_RUNS)
    run2_titles = [s["title"] for s in scenarios if s["run"] and s["run"]["number"] == 2]
    assert run2_titles == ["Felder sind beim Öffnen des Dialogs leer", "Abbrechen schließt Dialog"]


def test_scenario_without_run_comment_has_none():
    _, _, scenarios = parse_feature(FEATURE_WITH_RUNS)
    last = scenarios[-1]
    assert last["title"] == "Ohne Run-Tag"
    assert last["run"] is None


def test_run_does_not_leak_into_next_scenario_without_comment():
    # Ohne-Run-Tag-Szenario folgt direkt auf ein getaggtes – pending_run darf nicht übernommen werden.
    _, _, scenarios = parse_feature(FEATURE_WITH_RUNS)
    assert scenarios[-2]["run"]["number"] == 5
    assert scenarios[-1]["run"] is None


def test_frontend_only_layer_string():
    _, _, scenarios = parse_feature(FEATURE_WITH_RUNS)
    run2 = scenarios[1]["run"]
    assert run2["layer"] == "Frontend-only"


# --- Kommentare außerhalb der Zwischen-Szenario-Lücke -------------------------
# Regression: die "#"-Sonderbehandlung darf NUR zwischen Szenarien greifen. Kommentare im
# Background-Block oder mitten im Szenario-Body müssen wie zuvor als normale Zeilen erhalten
# bleiben – sonst verschwinden Erklär-Kommentare dort silently, oder ein zufällig zum Run-Tag-
# Muster passender Kommentar würde fälschlich dem NÄCHSTEN Szenario als Run-Tag zugeordnet.

FEATURE_COMMENT_IN_BACKGROUND = textwrap.dedent("""\
    @US-904
    Feature: Zutaten verwalten

      Background:
        Given die Anwendung ist gestartet
        # Hinweis: gilt für alle Szenarien dieser Story
        And ich navigiere zur Zutaten-Seite

      @US-904-happy-path
      Scenario: Erstes Szenario
        When a
        Then b
    """)

FEATURE_COMMENT_IN_SCENARIO_BODY = textwrap.dedent("""\
    @US-904
    Feature: Zutaten verwalten

      Background:
        Given die Anwendung ist gestartet

      # @run-1 · Anlegen·Success · Full-Stack
      @US-904-happy-path
      Scenario: Erstes Szenario
        When a
        # @run-9 · Sollte NICHT als Run-Tag zählen · Full-Stack
        Then b

      @US-904-happy-path
      Scenario: Zweites Szenario
        When a
        Then b
    """)


def test_comment_inside_background_is_preserved():
    _, background, _ = parse_feature(FEATURE_COMMENT_IN_BACKGROUND)
    assert any("Hinweis" in line for line in background)


def test_comment_inside_scenario_body_is_preserved_not_dropped():
    _, _, scenarios = parse_feature(FEATURE_COMMENT_IN_SCENARIO_BODY)
    first = scenarios[0]
    assert any("Sollte NICHT als Run-Tag zählen" in line for line in first["lines"])


def test_comment_inside_scenario_body_does_not_leak_as_run_tag_for_next_scenario():
    _, _, scenarios = parse_feature(FEATURE_COMMENT_IN_SCENARIO_BODY)
    assert scenarios[0]["run"]["number"] == 1
    # Das zweite Szenario hat keinen eigenen Run-Tag-Kommentar – der irrtümlich im ersten
    # Szenario-Body stehende "@run-9"-Kommentar darf hier NICHT ankommen.
    assert scenarios[1]["run"] is None


# --- find_malformed_run_comments ----------------------------------------------
def test_malformed_run_comment_wrong_layer_spelling_detected():
    text = "  # @run-3 · Anlegen·Erfolg · Fullstack\n  @US-904-x\n  Scenario: Foo\n"
    violations = find_malformed_run_comments(text)
    assert len(violations) == 1
    assert "Zeile 1" in violations[0]


def test_malformed_run_comment_wrong_separator_detected():
    text = "  # @run-3 - Anlegen·Erfolg - Full-Stack\n"
    assert len(find_malformed_run_comments(text)) == 1


def test_well_formed_run_comment_not_flagged():
    text = "  # @run-3 · Anlegen·Erfolg · Full-Stack\n"
    assert find_malformed_run_comments(text) == []


def test_unrelated_comment_not_flagged():
    text = "  # Ein ganz normaler Erklär-Kommentar ohne Run-Tag\n"
    assert find_malformed_run_comments(text) == []


def test_malformed_run_comment_silently_drops_run_tag_in_parse_feature():
    # Dokumentiert das stille Verhalten, das find_malformed_run_comments sichtbar macht:
    # parse_feature() selbst wirft keinen Fehler, das Szenario verliert einfach seinen Run-Tag.
    text = textwrap.dedent("""\
        @US-904
        Feature: X

          Background:
            Given a

          # @run-3 · Foo · Fullstack
          @US-904-x
          Scenario: Bar
            When a
            Then b
        """)
    _, _, scenarios = parse_feature(text)
    assert scenarios[0]["run"] is None

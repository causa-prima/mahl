"""Tests für check-feature-plan.py – Poka-Yoke für Phasen-Anker und `braucht:`-Kanten.

Abgrenzung zu test_e2e_scenario_ref.py: Dort geht es um das Mapping Feature ↔ E2E-Spec, hier um
die Bauplan-Konsistenz *innerhalb* der Feature-Dateien (ADR-S131-1).
"""
from importlib import import_module

import pytest

hook = import_module("prozesscode.hooks.check-feature-plan")


FEATURE_OK = (
    "@US-904\nFeature: Zutaten\n\n  # @phase: SKELETON\n\n"
    "  # @run-1 · Anlegen · Full-Stack\n  @US-904-happy-path\n  Scenario: Zutat anlegen\n"
    "    When a\n    Then b\n\n"
    "  # @run-2 · Löschen · Full-Stack · braucht:run-1\n  @US-904-happy-path\n"
    "  Scenario: Zutat löschen\n    When a\n    Then b\n"
)


def _daten(pfad: str, inhalt: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": pfad, "content": inhalt}}


# --- Zuständigkeit ------------------------------------------------------------
def test_ignores_non_feature_files():
    assert hook.check(_daten("Client/e2e/ingredients.spec.ts", "irgendwas")) is None


def test_clean_feature_passes():
    assert hook.check(_daten("features/ingredients.feature", FEATURE_OK)) is None


# --- Phasen-Anker -------------------------------------------------------------
@pytest.mark.aufrufpfad("check-feature-plan")
def test_blocks_run_without_any_phase():
    ohne_phase = FEATURE_OK.replace("  # @phase: SKELETON\n\n", "")
    grund = hook.check(_daten("features/ingredients.feature", ohne_phase))
    assert grund is not None and "ohne Phase" in grund


def test_blocks_unknown_phase_value():
    falsch = FEATURE_OK.replace("# @phase: SKELETON", "# @phase: PROTOTYP")
    grund = hook.check(_daten("features/ingredients.feature", falsch))
    assert grund is not None and "PROTOTYP" in grund


def test_blocks_directive_below_the_header():
    verschoben = FEATURE_OK.replace("  # @phase: SKELETON\n\n", "") + "\n  # @phase: MVP\n"
    grund = hook.check(_daten("features/ingredients.feature", verschoben))
    assert grund is not None and "unterhalb" in grund


# --- Abhängigkeitskanten ------------------------------------------------------
def test_blocks_dead_dependency_reference():
    tot = FEATURE_OK.replace("braucht:run-1", "braucht:run-99")
    grund = hook.check(_daten("features/ingredients.feature", tot))
    assert grund is not None and "run-99" in grund


def test_blocks_cycle():
    zyklus = FEATURE_OK.replace(
        "# @run-1 · Anlegen · Full-Stack", "# @run-1 · Anlegen · Full-Stack · braucht:run-2"
    )
    grund = hook.check(_daten("features/ingredients.feature", zyklus))
    assert grund is not None and "Zyklus" in grund


def test_message_names_the_way_out():
    ohne_phase = FEATURE_OK.replace("  # @phase: SKELETON\n\n", "")
    grund = hook.check(_daten("features/ingredients.feature", ohne_phase))
    assert "# @phase:" in grund


# --- Registrierung ------------------------------------------------------------
def test_check_is_registered_in_the_dispatcher():
    # Ein Guard, der nicht registriert ist, läuft nie – und sein Ausfall löst nichts aus.
    dispatcher = import_module("prozesscode.hooks.dispatch-edit-write")
    assert "check-feature-plan" in dispatcher.CHECKS

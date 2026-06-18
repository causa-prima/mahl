"""Tests für check-e2e-scenario-ref.py – PreToolUse-Poka-Yoke für // Szenario:-Verweise."""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
hook = import_module("check-e2e-scenario-ref")


FEATURE_TITLES = {"Zutat anlegen", "Zutat löschen"}

FEATURE_SRC = (
    "@US-904\nFeature: Zutaten\n\n"
    "  @US-904-happy-path\n  Scenario: Zutat anlegen\n    When a\n    Then b\n\n"
    "  @US-904-happy-path\n  Scenario: Zutat löschen\n    When a\n    Then b\n"
)


# --- is_e2e_spec / is_feature ------------------------------------------------
def test_is_e2e_spec_matches_e2e_specs():
    assert hook.is_e2e_spec("Client/e2e/ingredients.spec.ts")


def test_is_e2e_spec_ignores_unit_tests_and_other_files():
    assert not hook.is_e2e_spec("Client/src/pages/IngredientsPage.test.tsx")
    assert not hook.is_e2e_spec("Server/Domain/Ingredient.cs")


def test_is_feature_matches_feature_files():
    assert hook.is_feature("features/ingredients.feature")
    assert not hook.is_feature("Client/e2e/ingredients.spec.ts")


# --- validate_feature (Test→Spec-Richtung: verwaiste Kommentare) --------------
def test_validate_feature_flags_orphan_after_retitle():
    post = FEATURE_SRC.replace("Scenario: Zutat anlegen", "Scenario: Zutat erstellen")
    violations = hook.validate_feature(post, other_feature_titles=frozenset(), spec_titles={"Zutat anlegen"})
    assert len(violations) == 1
    assert "Zutat anlegen" in violations[0]


def test_validate_feature_ok_when_renaming_unimplemented_scenario():
    # "Zutat löschen" hat keinen Spec-Kommentar → Umbenennen ist erlaubt
    post = FEATURE_SRC.replace("Scenario: Zutat löschen", "Scenario: Zutat entfernen")
    assert hook.validate_feature(post, other_feature_titles=frozenset(), spec_titles={"Zutat anlegen"}) == []


def test_validate_feature_ok_when_title_lives_in_other_feature():
    post = FEATURE_SRC.replace("Scenario: Zutat anlegen", "Scenario: Zutat erstellen")
    assert hook.validate_feature(post, other_feature_titles=frozenset({"Zutat anlegen"}), spec_titles={"Zutat anlegen"}) == []


# --- compute_post_content ----------------------------------------------------
def test_compute_post_content_write_returns_content():
    inp = {"file_path": "x.spec.ts", "content": "// Szenario: Zutat anlegen\n"}
    assert hook.compute_post_content("Write", "x.spec.ts", inp) == "// Szenario: Zutat anlegen\n"


def test_compute_post_content_edit_applies_replacement(tmp_path):
    f = tmp_path / "ingredients.spec.ts"
    f.write_text("test('foo')\n", encoding="utf-8")
    inp = {"file_path": str(f), "old_string": "test('foo')", "new_string": "// Szenario: Zutat anlegen\ntest('foo')"}
    out = hook.compute_post_content("Edit", str(f), inp)
    assert "// Szenario: Zutat anlegen" in out
    assert "test('foo')" in out


def test_compute_post_content_edit_missing_old_string_returns_current(tmp_path):
    f = tmp_path / "ingredients.spec.ts"
    f.write_text("test('foo')\n", encoding="utf-8")
    inp = {"file_path": str(f), "old_string": "NICHT VORHANDEN", "new_string": "x"}
    assert hook.compute_post_content("Edit", str(f), inp) == "test('foo')\n"


# --- validate ----------------------------------------------------------------
def test_validate_clean():
    post = "// Szenario: Zutat anlegen\ntest('a')\n"
    assert hook.validate(post, FEATURE_TITLES) == []


def test_validate_flags_orphan_comment():
    post = "// Szenario: Gibt es nicht\ntest('a')\n"
    violations = hook.validate(post, FEATURE_TITLES)
    assert len(violations) == 1
    assert "Gibt es nicht" in violations[0]


def test_validate_flags_cross_file_duplicate():
    post = "// Szenario: Zutat anlegen\ntest('a')\n"
    violations = hook.validate(post, FEATURE_TITLES, other_spec_titles={"Zutat anlegen"})
    assert any("doppelt" in v.lower() for v in violations)


def test_validate_dedupes_repeated_orphan():
    post = "// Szenario: Gibt es nicht\n// Szenario: Gibt es nicht\n"
    assert len(hook.validate(post, FEATURE_TITLES)) == 1


# --- Vollständigkeit: jeder Test braucht einen // Szenario:-Kommentar ---------
def test_validate_flags_test_without_comment():
    post = "test('macht irgendwas', async () => {})\n"
    violations = hook.validate(post, FEATURE_TITLES)
    assert any("macht irgendwas" in v and "Szenario" in v for v in violations)


def test_validate_accepts_test_with_comment():
    post = "// Szenario: Zutat anlegen\ntest('CreateIngredient', async () => {})\n"
    assert hook.validate(post, FEATURE_TITLES) == []


def test_validate_ignores_describe_and_hooks():
    post = (
        "test.describe('Gruppe', () => {\n"
        "  test.beforeEach(async () => {})\n"
        "  // Szenario: Zutat anlegen\n"
        "  test('CreateIngredient', async () => {})\n"
        "})\n"
    )
    assert hook.validate(post, FEATURE_TITLES) == []


def test_validate_flags_only_the_uncommented_test():
    post = (
        "// Szenario: Zutat anlegen\n"
        "test('A', async () => {})\n"
        "test('B', async () => {})\n"
    )
    violations = hook.validate(post, FEATURE_TITLES)
    assert any("'B'" in v or "B" in v for v in violations)
    assert not any("'A'" in v for v in violations)

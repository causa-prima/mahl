"""Tests für check-e2e-scenario-ref.py – PreToolUse-Poka-Yoke für // Szenario:-Verweise."""
from importlib import import_module

import pytest

hook = import_module("prozesscode.hooks.check-e2e-scenario-ref")


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


# Die compute_post_content-Tests standen bis S128 hier und prüften eine LOKALE Kopie mit
# eigener Signatur – zusammen mit der in check-ref-direction.py war das der größte Python-Clone
# (18 Zeilen). Beide Kopien sind entfallen, geprüft wird die Simulation in test_hook_io.py.


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


# --- Einstieg über den Dispatcher-Weg (gegen die echten features/) ------------
def _spec_write(inhalt: str) -> dict:
    return {"tool_name": "Write",
            "tool_input": {"file_path": "Client/e2e/aufrufpfad-probe.spec.ts", "content": inhalt}}


@pytest.mark.aufrufpfad("check-e2e-scenario-ref")
def test_check_blockt_verweis_auf_ein_szenario_das_es_nicht_gibt():
    grund = hook.check(_spec_write("// Szenario: Dieses Szenario gibt es in keinem Feature\n"
                                   "test('x', () => {})\n"))
    assert grund and "Dieses Szenario gibt es in keinem Feature" in grund


def test_check_ignoriert_dateien_ausserhalb_von_specs_und_features():
    daten = {"tool_name": "Write",
             "tool_input": {"file_path": "Client/src/x.ts", "content": "// Szenario: egal\n"}}
    assert hook.check(daten) is None


# --- Kommentar über dem Testfall ---------------------------------------------------
@pytest.mark.parametrize("quelle, fehlt", [
    # Leerzeilen und weitere Kommentare dazwischen sind erlaubt.
    ("// Szenario: Zutat anlegen\n// noch ein Kommentar\n\ntest('a', () => {})\n", []),
    # Code dazwischen beendet den Kommentarblock.
    ("// Szenario: Zutat anlegen\nconst x = 1\ntest('a', () => {})\n", ["a"]),
    # Ohne lesbaren Namen nennt die Meldung die Zeile.
    ("const n = 'a'\n\ntest(n, () => {})\n", ["Zeile 3"]),
])
def test_kommentarblock_ueber_dem_testfall(quelle, fehlt):
    assert hook.tests_missing_comment(quelle) == fehlt


# --- Titel aus den Verzeichnissen ---------------------------------------------------
@pytest.fixture
def repo(tmp_path, monkeypatch):
    features, e2e = tmp_path / "features", tmp_path / "Client" / "e2e"
    (features / "sub").mkdir(parents=True)
    e2e.mkdir(parents=True)
    (features / "sub" / "zutaten.feature").write_text(FEATURE_SRC, encoding="utf-8")
    (features / "andere.feature").write_text(
        "Feature: X\n\n  Scenario: Rezept anlegen\n    When a\n", encoding="utf-8")
    (e2e / "zutaten.spec.ts").write_text(
        "// Szenario: Zutat anlegen\ntest('a', () => {})\n", encoding="utf-8")
    (e2e / "rezept.spec.ts").write_text(
        "// Szenario: Rezept anlegen\ntest('b', () => {})\n", encoding="utf-8")
    monkeypatch.setattr(hook, "_FEATURES_DIR", features)
    monkeypatch.setattr(hook, "_E2E_DIR", e2e)
    return tmp_path


def test_titel_aus_allen_dateien_oder_ohne_die_bearbeitete(repo):
    assert hook._feature_titles() == FEATURE_TITLES | {"Rezept anlegen"}
    assert hook._feature_titles(ausser=str(repo / "features" / "andere.feature")) == FEATURE_TITLES
    assert hook._spec_titles() == {"Zutat anlegen", "Rezept anlegen"}
    assert hook._spec_titles(ausser=str(repo / "Client" / "e2e" / "rezept.spec.ts")) == {"Zutat anlegen"}


def test_ohne_verzeichnisse_keine_titel(tmp_path, monkeypatch):
    monkeypatch.setattr(hook, "_FEATURES_DIR", tmp_path / "fehlt")
    monkeypatch.setattr(hook, "_E2E_DIR", tmp_path / "fehlt")
    assert hook._feature_titles() == hook._spec_titles() == set()


def test_check_feature_umbenennung_verwaist_einen_e2e_kommentar(repo):
    ziel = repo / "features" / "andere.feature"
    grund = hook.check({"tool_name": "Write", "tool_input": {
        "file_path": str(ziel), "content": "Feature: X\n\n  Scenario: Rezept neu\n    When a\n"}})
    assert grund == (f"{hook._KOPF}  - {hook._VERWAIST.format(titel='Rezept anlegen')}\n"
                     f"{hook._HINWEIS}")


def test_check_feature_ohne_folgen_fuer_e2e_passiert(repo):
    ziel = repo / "features" / "andere.feature"
    inhalt = "Feature: X\n\n  Scenario: Rezept anlegen\n    When b\n"
    assert hook.check({"tool_name": "Write",
                       "tool_input": {"file_path": str(ziel), "content": inhalt}}) is None


def test_check_spec_doppelter_titel_aus_einer_anderen_spec(repo):
    ziel = repo / "Client" / "e2e" / "neu.spec.ts"
    inhalt = "// Szenario: Zutat anlegen\ntest('c', () => {})\n"
    grund = hook.check({"tool_name": "Write",
                        "tool_input": {"file_path": str(ziel), "content": inhalt}})
    assert grund == f"{hook._KOPF}  - {hook._DOPPELT.format(titel='Zutat anlegen')}\n{hook._HINWEIS}"


def test_check_spec_eigener_titel_ist_kein_doppel(repo):
    """Die bearbeitete Spec zählt nicht gegen sich selbst."""
    ziel = repo / "Client" / "e2e" / "zutaten.spec.ts"
    inhalt = "// Szenario: Zutat anlegen\ntest('a2', () => {})\n"
    assert hook.check({"tool_name": "Write",
                       "tool_input": {"file_path": str(ziel), "content": inhalt}}) is None

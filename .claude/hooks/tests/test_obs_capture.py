"""Tests für check-obs-capture.py – PreToolUse-Poka-Yoke gegen Lösungskandidaten bei OBS-Erfassung.

Regel: Ein **neu** in `docs/kaizen/observations.md` erfasster OBS-Eintrag muss im Feld
`- Entscheidung/Maßnahme:` mit dem Kanon-Token `offen` beginnen. Ein bereits bei der Erfassung
notierter Lösungskandidat ankert den bewusst frischen Drain-Agenten (Anchoring-Bias).
Bestehende Einträge sind frei änderbar (genau das tut der Drain); Zeilen mit `obs-ok`-Marker
sind ausgenommen.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
hook = import_module("check-obs-capture")


def _obs(
    oid: str,
    decision: str | None = "offen",
    beobachtung: str = "irgendwas fiel auf",
    extra: str = "",
    bezug: str | None = "–",
) -> str:
    """Minimaler, formatgetreuer OBS-Block."""
    entscheidung = "" if decision is None else f"- Entscheidung/Maßnahme: {decision}\n"
    return (
        f"## {oid} – Kurztitel\n"
        "- Quelle: Orchestrator\n"
        "- Status: NEU\n"
        "- Impact: MITTEL    Häufigkeit: gelegentlich\n"
        "- Kategorie: PROZESS    Kontext: Skill-Nutzung\n"
        f"- Beobachtung: {beobachtung}\n"
        f"{entscheidung}"
        f"{extra}"
        + ("" if bezug is None else f"- Bezug: {bezug}\n")
        + "\n"
    )


# --- is_obs_file -------------------------------------------------------------
def test_matches_the_observations_backlog():
    assert hook.is_obs_file("docs/kaizen/observations.md")


def test_matches_absolute_path_to_the_backlog():
    assert hook.is_obs_file("/home/kieritz/repos/mahl/docs/kaizen/observations.md")


def test_ignores_other_kaizen_files():
    assert not hook.is_obs_file("docs/kaizen/lessons_learned.md")
    assert not hook.is_obs_file("docs/kaizen/countermeasures.md")
    assert not hook.is_obs_file("docs/kaizen/archive/observations_archive.md")


# --- parse_obs_decisions -----------------------------------------------------
def test_parses_decision_per_entry():
    content = _obs("OBS-S100-1", "offen") + _obs("OBS-S100-2", "Aufgeschoben bis S110")
    assert hook.parse_obs_decisions(content) == {
        "OBS-S100-1": "offen",
        "OBS-S100-2": "Aufgeschoben bis S110",
    }


def test_missing_decision_field_yields_none():
    assert hook.parse_obs_decisions(_obs("OBS-S100-1", None)) == {"OBS-S100-1": None}


def test_ignores_prose_outside_entries():
    content = "# Observations\n\nBeliebiger Header-Text\n\n---\n\n" + _obs("OBS-S100-1")
    assert hook.parse_obs_decisions(content) == {"OBS-S100-1": "offen"}


# --- is_canonical_open -------------------------------------------------------
# Zulässig sind bei der Erfassung GENAU zwei Werte – freie Prosa hinter `offen` ist der
# Schlupfweg, über den der Kandidat sonst doch wieder im Feld landet.
def test_bare_canon_value_is_accepted():
    assert hook.is_canonical_open("offen")


def test_long_canon_value_is_accepted():
    assert hook.is_canonical_open("offen - beim Drain Kandidaten erstellen und bewerten")


def test_typographic_noise_does_not_matter():
    # Gedankenstrich, Groß-/Kleinschreibung und Mehrfach-Leerzeichen tragen keine Bedeutung
    assert hook.is_canonical_open("Offen – beim  Drain Kandidaten erstellen und bewerten")
    assert hook.is_canonical_open("  offen  ")


def test_candidate_behind_the_token_is_rejected():
    assert not hook.is_canonical_open("offen - Kandidat: Poka-Yoke-Hook bauen")
    assert not hook.is_canonical_open("offen, aber vermutlich brauchen wir dafür einen Hook")


def test_open_question_is_rejected():
    # Offene Fragen gehören nicht in dieses Feld
    assert not hook.is_canonical_open("offen: brauchen wir dafür einen Hook?")


def test_anything_appended_to_the_long_value_is_rejected():
    assert not hook.is_canonical_open("offen - beim Drain Kandidaten erstellen und bewerten (evtl. Hook)")


def test_solution_candidate_is_rejected():
    assert not hook.is_canonical_open("Poka-Yoke-Hook bauen, der das syntaktisch erzwingt")


def test_deferral_is_rejected():
    assert not hook.is_canonical_open("Aufgeschoben (S107-Retro) bis zum 2. Vorkommen")


def test_prefix_of_the_token_is_rejected():
    assert not hook.is_canonical_open("offene Frage: bauen wir dafür einen Hook?")


def test_empty_and_missing_are_rejected():
    assert not hook.is_canonical_open("")
    assert not hook.is_canonical_open(None)


# --- find_violations ---------------------------------------------------------
def test_new_entry_with_canon_value_passes():
    pre = _obs("OBS-S100-1", "offen")
    post = pre + _obs("OBS-S100-2", "offen - beim Drain Kandidaten erstellen und bewerten")
    assert hook.find_violations(pre, post) == []


def test_new_entry_with_solution_candidate_is_blocked():
    pre = _obs("OBS-S100-1", "offen")
    post = pre + _obs("OBS-S100-2", "Hook bauen, der das erzwingt")
    assert [v[0] for v in hook.find_violations(pre, post)] == ["OBS-S100-2"]


def test_new_entry_with_candidate_behind_the_token_is_blocked():
    post = _obs("OBS-S100-1", "offen – Richtung: Poka-Yoke-Hook")
    assert [v[0] for v in hook.find_violations("", post)] == ["OBS-S100-1"]


def test_new_entry_without_decision_field_is_blocked():
    post = _obs("OBS-S100-1", None)
    assert [v[0] for v in hook.find_violations("", post)] == ["OBS-S100-1"]


def test_drain_may_fill_the_decision_of_an_existing_entry():
    pre = _obs("OBS-S100-1", "offen")
    post = _obs("OBS-S100-1", "Umgesetzt: Hook gebaut, weil Lese-Disziplin nicht reicht")
    assert hook.find_violations(pre, post) == []


def test_unchanged_content_yields_no_violations():
    content = _obs("OBS-S100-1", "Aufgeschoben bis S110")
    assert hook.find_violations(content, content) == []


def test_obs_ok_marker_exempts_a_new_entry():
    post = _obs("OBS-S100-1", "Umnummeriert aus OBS-S099-4 <!-- obs-ok -->")
    assert hook.find_violations("", post) == []


def test_violation_names_the_entry_and_the_offending_value():
    oid, reason = hook.find_violations("", _obs("OBS-S100-1", "Hook bauen"))[0]
    assert oid == "OBS-S100-1"
    assert "Hook bauen" in reason


# --- Ausweich-Wege: Kandidat wandert in ein anderes Feld ---------------------
# Der Wasserbett-Effekt: sperrt man `- Entscheidung/Maßnahme:`, landet die Lösung sonst
# in einem erfundenen Feld oder in der Beobachtungs-Prosa.
def test_invented_field_in_a_new_entry_is_blocked():
    post = _obs("OBS-S100-1", extra="- Kandidaten: A) Hook bauen B) Guideline schärfen\n")
    assert [v[0] for v in hook.find_violations("", post)] == ["OBS-S100-1"]


def test_drain_may_add_fields_to_an_existing_entry():
    # Beim Drain entsteht legitim ein `- Kandidaten:`-Feld – nur Neu-Erfassung ist reglementiert
    pre = _obs("OBS-S100-1")
    post = _obs("OBS-S100-1", "Umgesetzt: X", extra="- Kandidaten: A) … B) …\n")
    assert hook.find_violations(pre, post) == []


def test_missing_mandatory_field_is_blocked():
    post = _obs("OBS-S100-1").replace("- Beobachtung: irgendwas fiel auf\n", "")
    assert [v[0] for v in hook.find_violations("", post)] == ["OBS-S100-1"]


def test_bezug_is_optional():
    assert hook.find_violations("", _obs("OBS-S100-1", bezug=None)) == []


def test_indented_sub_bullets_are_prose_not_fields():
    post = _obs("OBS-S100-1", beobachtung="zwei Dinge:\n  - Erstens: A\n  - Zweitens: B")
    assert hook.find_violations("", post) == []


def test_explicit_proposal_marker_in_the_observation_is_blocked():
    post = _obs("OBS-S100-1", beobachtung="Kostete eine Design-Runde. Lösungsvorschlag: Hook bauen.")
    assert [v[0] for v in hook.find_violations("", post)] == ["OBS-S100-1"]


def test_idea_marker_in_the_observation_is_blocked():
    post = _obs("OBS-S100-1", beobachtung="Fiel auf. Idee: das schon in Schritt 0 festhalten.")
    assert [v[0] for v in hook.find_violations("", post)] == ["OBS-S100-1"]


def test_modal_wording_in_the_observation_is_allowed():
    # „könnte/sollte" beschreibt meist ein Risiko, keinen Vorschlag – am Bestand ~50 % Fehlalarm,
    # deshalb bewusst NICHT reglementiert.
    post = _obs("OBS-S100-1", beobachtung="Ein Subagent könnte ungeprüfte Assertions stagen.")
    assert hook.find_violations("", post) == []


def test_canonical_decision_does_not_trip_the_proposal_marker():
    # „…Kandidaten erstellen und bewerten" enthält das Wort, aber nicht die Marker-Form
    assert hook.find_violations("", _obs("OBS-S100-1", "offen - beim Drain Kandidaten erstellen und bewerten")) == []


def test_obs_ok_marker_exempts_the_whole_entry():
    post = _obs("OBS-S100-1", "Kandidat notiert <!-- obs-ok -->", extra="- Lösungsidee: Hook\n")
    assert hook.find_violations("", post) == []


# --- pre/post-Inhalt ---------------------------------------------------------
def test_pre_content_is_the_file_on_disk(tmp_path):
    f = tmp_path / "observations.md"
    f.write_text(_obs("OBS-S100-1", "offen"), encoding="utf-8")
    assert hook.read_file_text(str(f)) == _obs("OBS-S100-1", "offen")


def test_pre_content_of_a_missing_file_is_empty(tmp_path):
    assert hook.read_file_text(str(tmp_path / "gibtsnicht.md")) == ""


def test_write_post_content_is_the_new_file_content():
    post = _obs("OBS-S100-1", "offen")
    assert hook.compute_post_content("Write", {"content": post}, "alt") == post


def test_edit_post_content_applies_the_replacement():
    pre = _obs("OBS-S100-1", "offen")
    inp = {"old_string": "offen", "new_string": "Umgesetzt: Hook gebaut"}
    assert "- Entscheidung/Maßnahme: Umgesetzt: Hook gebaut" in hook.compute_post_content("Edit", inp, pre)


def test_edit_with_unfindable_old_string_leaves_content_unchanged():
    pre = _obs("OBS-S100-1", "offen")
    inp = {"old_string": "kommt so nicht vor", "new_string": "egal"}
    assert hook.compute_post_content("Edit", inp, pre) == pre

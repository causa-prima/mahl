"""Tests für _session_logs.py – Session-Erkennung und Read-Extraktion aus den Claude-Code-Logs.

Kern der Klassifikation: `attributionSkill` als Primärsignal, kuratierte Mapping-Datei mit
Vorrang, Edit-Heuristik als Fallback. Die Heuristik rechnet vorher die Dateien heraus, die
`closing-session` in jeder Session anfasst – ohne das gälte jede Session als Drain (wegen
`observations.md`) oder als Retro (wegen `lessons_learned.md`).
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

import _session_logs as sl


# --- categorize --------------------------------------------------------------
def test_categorizes_by_first_matching_prefix():
    assert sl.categorize("docs/guidelines/coding-guideline-csharp.md") == "docs/guidelines (Pflichtlektüre)"
    assert sl.categorize("/home/x/repo/docs/kaizen/observations.md") == "docs/kaizen"
    assert sl.categorize("Client/src/pages/IngredientsPage.tsx") == "Client/ (Frontend-Code)"
    assert sl.categorize("Server.Tests/IngredientsEndpointsTests.cs") == "Server/ (Backend-Code)"


def test_more_specific_claude_paths_win_over_the_catchall():
    assert sl.categorize(".claude/skills/kaizen/SKILL.md") == ".claude/skills"
    assert sl.categorize(".claude/settings.json") == ".claude/ (sonstige)"


def test_unknown_paths_fall_back():
    assert sl.categorize("/tmp/irgendwas.txt") == "sonstiges"


def test_relative_path_strips_the_repo_prefix():
    assert sl.relative_path("/home/kieritz/repos/mahl/docs/tech-debt.md") == "docs/tech-debt.md"
    assert sl.relative_path("docs/tech-debt.md") == "docs/tech-debt.md"


# --- Rauschen & Heuristik ----------------------------------------------------
def test_removes_files_touched_in_every_session():
    paths = {
        "docs/kaizen/observations.md",
        "docs/kaizen/lessons_learned.md",
        "docs/history/sessions/session_113.md",
        "docs/AGENT_MEMORY.md",
        "Client/src/App.tsx",
    }
    assert sl.ohne_rauschen(paths) == {"Client/src/App.tsx"}


def test_session_that_only_touched_closing_files_is_an_abschluss():
    assert sl.type_from_edits({"docs/kaizen/observations.md", "docs/AGENT_MEMORY.md"}) == "abschluss"


def test_no_edits_at_all_yields_no_guess():
    assert sl.type_from_edits(set()) is None


def test_observations_alone_does_not_make_it_a_drain():
    """Der Fehler, den die Rausch-Liste verhindert: `closing-session` schreibt dort immer."""
    paths = {"docs/kaizen/observations.md", "Client/src/App.tsx"}
    assert sl.type_from_edits(paths) == "implementierung"


def test_built_artifacts_win_over_the_archive_marker():
    """Eine Tooling-Session, die nebenher OBS archiviert, bleibt Tooling."""
    paths = {".claude/scripts/obs-drain.py", "docs/kaizen/archive/observations_archive.md"}
    assert sl.type_from_edits(paths) == "tooling"


def test_archive_marks_a_drain_when_nothing_was_built():
    assert sl.type_from_edits({"docs/kaizen/archive/observations_archive.md"}) == "drain"


def test_lessons_learned_archive_marks_a_retro():
    assert sl.type_from_edits({"docs/kaizen/archive/lessons_learned_S100.md"}) == "retro"


# --- Mapping -----------------------------------------------------------------
def test_mapping_matches_exactly_and_by_prefix():
    mapping = {"08afc860": "abschluss"}
    assert sl.mapped_type("08afc860", mapping) == "abschluss"
    assert sl.mapped_type("08afc860-1234-abcd", mapping) == "abschluss"
    assert sl.mapped_type("ffffffff", mapping) is None


def test_load_mapping_skips_comment_keys(tmp_path):
    path = tmp_path / "session-types.json"
    path.write_text(json.dumps({"_zweck": "…", "abc123": "drain"}), encoding="utf-8")
    assert sl.load_mapping(path) == {"abc123": "drain"}


def test_load_mapping_tolerates_a_missing_file(tmp_path):
    assert sl.load_mapping(tmp_path / "fehlt.json") == {}


# --- session_type: Rangfolge der Signale -------------------------------------
def test_mapping_beats_skill_signal():
    art, herkunft = sl.session_type("abc", Counter({"implementing-scenario": 50}), {"abc": "tooling"})
    assert (art, herkunft) == ("tooling", "mapping")


def test_skill_signal_beats_heuristic():
    art, herkunft = sl.session_type(
        "abc", Counter({"draining-observations": 10}), {}, {"Client/src/App.tsx"}
    )
    assert (art, herkunft) == ("drain", "skill")


def test_dominant_skill_wins_among_several():
    skills = Counter({"implementing-scenario": 90, "review-code": 5})
    assert sl.session_type("abc", skills, {})[0] == "implementierung"


def test_scenario_design_is_not_implementation():
    """Ein `gherkin-workshop` entwirft Szenarien und liest Stories/Feature-Dateien statt
    Testcode – sein Leseprofil hat mit einem Implementierungslauf nichts gemein."""
    assert sl.session_type("abc", Counter({"gherkin-workshop": 4}), {})[0] == "workshop"


def test_companion_skills_do_not_determine_the_type():
    """`closing-session` läuft fast überall und darf die Art nicht prägen."""
    skills = Counter({"closing-session": 300, "kaizen": 20})
    assert sl.session_type("abc", skills, {})[0] == "retro"


def test_falls_back_to_heuristic_without_any_skill():
    art, herkunft = sl.session_type("abc", Counter(), {}, {".claude/scripts/foo.py"})
    assert (art, herkunft) == ("tooling", "heuristik")


def test_unknown_when_nothing_at_all_is_available():
    assert sl.session_type("abc", Counter(), {}, set()) == (sl.UNBEKANNT, "-")


# --- Log-Parsing -------------------------------------------------------------
def _rec(*blocks, skill: str | None = None) -> dict:
    rec: dict = {"message": {"content": list(blocks)}}
    if skill:
        rec["attributionSkill"] = skill
    return rec


def test_block_text_handles_plain_and_nested_results():
    assert sl.block_text({"type": "text", "text": "hallo"}) == "hallo"
    assert sl.block_text({"type": "tool_result", "content": "abc"}) == "abc"
    nested = {"type": "tool_result", "content": [{"type": "text", "text": "ab"}, {"type": "text", "text": "c"}]}
    assert sl.block_text(nested) == "abc"


def test_skills_are_counted_per_record():
    records = [_rec(skill="kaizen"), _rec(skill="kaizen"), _rec(skill="closing-session"), _rec()]
    assert sl.skills_in(records) == Counter({"kaizen": 2, "closing-session": 1})


def test_edited_paths_covers_edit_and_write():
    records = [
        _rec({"type": "tool_use", "name": "Edit", "input": {"file_path": "a.py"}}),
        _rec({"type": "tool_use", "name": "Write", "input": {"file_path": "b.py"}}),
        _rec({"type": "tool_use", "name": "Read", "input": {"file_path": "c.py"}}),
    ]
    assert sl.edited_paths(records) == {"a.py", "b.py"}


def test_read_events_pair_tool_use_with_its_result():
    records = [
        _rec({"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "a.md"}}),
        _rec({"type": "tool_result", "tool_use_id": "t1", "content": "12345"}),
    ]
    assert sl.read_events(records) == [("a.md", 5, False)]


def test_read_events_flag_targeted_reads():
    records = [
        _rec({"type": "tool_use", "id": "t1", "name": "Read",
              "input": {"file_path": "a.md", "offset": 100, "limit": 50}}),
        _rec({"type": "tool_result", "tool_use_id": "t1", "content": "12345"}),
    ]
    assert sl.read_events(records) == [("a.md", 5, True)]


# --- Ausgelagerte Tool-Ausgaben ----------------------------------------------
def test_effective_size_uses_the_persisted_file(tmp_path):
    """Claude Code lagert Ausgaben >~60 KB aus und lässt nur eine Vorschau im Log –
    wer die Vorschau misst, untercountet ausgerechnet die größten Reads."""
    target = tmp_path / "gross.txt"
    target.write_text("x" * 12345, encoding="utf-8")
    vorschau = f"<persisted-output>\nOutput too large (12.3KB). Full output saved to: {target}\n\nPreview"
    assert sl.effective_size(vorschau) == 12345


def test_effective_size_falls_back_to_the_preview_when_the_file_is_gone(tmp_path):
    vorschau = f"Full output saved to: {tmp_path / 'weg.txt'}\nPreview"
    assert sl.effective_size(vorschau) == len(vorschau)


def test_effective_size_of_a_normal_result_is_its_length():
    assert sl.effective_size("nur text") == 8


def test_results_of_other_tools_are_not_counted_as_reads():
    records = [
        _rec({"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}),
        _rec({"type": "tool_result", "tool_use_id": "t1", "content": "viel output"}),
    ]
    assert sl.read_events(records) == []


def test_project_log_dir_encodes_the_repo_path(tmp_path):
    from pathlib import Path
    assert sl.project_log_dir(Path("/home/kieritz/repos/mahl")).name == "-home-kieritz-repos-mahl"

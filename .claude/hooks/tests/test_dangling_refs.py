"""Tests für check-dangling-refs.py – Blockade beim Löschen noch referenzierter TD-/OQ-Einträge.

Gegenrichtung zu check-ref-direction.py: Jener erlaubt bewusste volatile Verweise über den
`ref-ok`-Marker, prüft sie danach aber nie wieder. Dieser Hook fängt den Moment ab, in dem
das Ziel verschwindet, und listet die verbliebenen Fundstellen auf.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
hook = import_module("check-dangling-refs")


# --- watched_pattern ---------------------------------------------------------
def test_recognizes_both_trackers():
    assert hook.watched_pattern("docs/tech-debt.md") is not None
    assert hook.watched_pattern("/abs/repo/docs/open-questions.md") is not None


def test_ignores_other_files():
    assert hook.watched_pattern("docs/history/adr.md") is None
    assert hook.watched_pattern("docs/kaizen/observations.md") is None


# --- removed_ids -------------------------------------------------------------
def test_detects_removed_entry():
    pattern = hook.WATCHED["docs/tech-debt.md"]
    pre = "## TD-S001-1 — A\ntext\n## TD-S002-1 — B\ntext\n"
    post = "## TD-S002-1 — B\ntext\n"
    assert hook.removed_ids(pre, post, pattern) == ["TD-S001-1"]


def test_no_removal_when_only_body_changes():
    pattern = hook.WATCHED["docs/tech-debt.md"]
    pre = "## TD-S001-1 — A\nalt\n"
    post = "## TD-S001-1 — A\nneu\n"
    assert hook.removed_ids(pre, post, pattern) == []


def test_renamed_heading_counts_as_removal():
    # Regression aus der Gegenprobe: ohne Lookahead las `TD-S001-1-ALT` als `TD-S001-1`,
    # die ID galt fälschlich als noch vorhanden und das Umbenennen blieb unbemerkt.
    pattern = hook.WATCHED["docs/tech-debt.md"]
    pre = "## TD-S001-1 — A\n"
    post = "## TD-S001-1-ALT — A\n"
    assert hook.removed_ids(pre, post, pattern) == ["TD-S001-1"]


def test_added_entry_is_not_a_removal():
    pattern = hook.WATCHED["docs/open-questions.md"]
    pre = "## OQ-S001-1 — A\n"
    post = "## OQ-S001-1 — A\n## OQ-S002-1 — B\n"
    assert hook.removed_ids(pre, post, pattern) == []


# --- find_references ---------------------------------------------------------
def test_empty_id_list_short_circuits(tmp_path):
    assert hook.find_references([], tmp_path / "x.md") == []


def test_finds_reference_in_repo(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    (tmp_path / "Server").mkdir()
    (tmp_path / "Server" / "Foo.cs").write_text(
        "// siehe TD-S001-1 für Details\n", encoding="utf-8")

    hits = hook.find_references(["TD-S001-1"], tmp_path / "docs" / "tech-debt.md")
    assert hits == [("Server/Foo.cs", 1, "TD-S001-1")]


def test_dangling_ok_line_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    (tmp_path / "notes.md").write_text(
        "War bis S119 als TD-S001-1 abgelegt. <!-- dangling-ok -->\n", encoding="utf-8")
    assert hook.find_references(["TD-S001-1"], tmp_path / "tech-debt.md") == []


def test_session_logs_and_archives_are_skipped(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    logs = tmp_path / "docs" / "history" / "sessions"
    logs.mkdir(parents=True)
    (logs / "session_100.md").write_text("TD-S001-1 erledigt\n", encoding="utf-8")
    archive = tmp_path / "docs" / "kaizen" / "archive"
    archive.mkdir(parents=True)
    (archive / "old.md").write_text("TD-S001-1 war mal\n", encoding="utf-8")

    assert hook.find_references(["TD-S001-1"], tmp_path / "x.md") == []


def test_tooling_test_fixtures_are_skipped(monkeypatch, tmp_path):
    """IDs in Tooling-Tests sind Fixtures, keine Verweise (OBS-S119-2)."""
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    for rel in ((".claude", "hooks", "tests"), (".claude", "scripts", "tests")):
        d = tmp_path.joinpath(*rel)
        d.mkdir(parents=True, exist_ok=True)
        (d / "test_x.py").write_text('fixture = "## TD-S001-1 — Beispiel"\n', encoding="utf-8")

    assert hook.find_references(["TD-S001-1"], tmp_path / "x.md") == []


def test_real_reference_outside_tests_still_blocks(monkeypatch, tmp_path):
    """GEGENPROBE: die Fixture-Ausnahme darf den Check nicht stilllegen."""
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    scripts = tmp_path / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "dotnet-test.py").write_text("# siehe TD-S001-1\n", encoding="utf-8")

    hits = hook.find_references(["TD-S001-1"], tmp_path / "x.md")
    assert len(hits) == 1
    assert hits[0][0].endswith("dotnet-test.py")


def test_tracker_itself_is_excluded(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    tracker = docs / "tech-debt.md"
    tracker.write_text("## TD-S001-1 — A\n", encoding="utf-8")

    assert hook.find_references(["TD-S001-1"], tracker) == []


def test_partial_id_is_not_a_match(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    (tmp_path / "notes.md").write_text("TD-S001-11 ist etwas anderes\n", encoding="utf-8")
    assert hook.find_references(["TD-S001-1"], tmp_path / "x.md") == []


def test_files_with_unscanned_suffix_are_skipped(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    (tmp_path / "image.png").write_bytes(b"\x89PNG TD-S001-1")
    assert hook.find_references(["TD-S001-1"], tmp_path / "x.md") == []


def test_undecodable_content_in_scanned_suffix_is_skipped(monkeypatch, tmp_path):
    # Erreicht den except-Zweig wirklich: `.md` passiert den Suffix-Filter und wird gelesen.
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    (tmp_path / "kaputt.md").write_bytes(b"\xff\xfe TD-S001-1 \x00")
    assert hook.find_references(["TD-S001-1"], tmp_path / "x.md") == []


def test_skip_dirs_apply_only_inside_the_repo(monkeypatch, tmp_path):
    # Regression: `path.parts` enthielt auch Verzeichnisse OBERHALB der Repo-Wurzel – lag der
    # Checkout unter einem Segment wie `dist`, lief der Scan stumm auf null Dateien.
    repo = tmp_path / "dist" / "mahl"
    repo.mkdir(parents=True)
    monkeypatch.setattr(hook, "_REPO_ROOT", repo)
    (repo / "notes.md").write_text("TD-S001-1\n", encoding="utf-8")

    assert hook.find_references(["TD-S001-1"], repo / "x.md") == [("notes.md", 1, "TD-S001-1")]


def test_nested_skip_dir_inside_repo_is_still_skipped(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    build = tmp_path / "Server" / "obj"
    build.mkdir(parents=True)
    (build / "generated.cs").write_text("// TD-S001-1\n", encoding="utf-8")

    assert hook.find_references(["TD-S001-1"], tmp_path / "x.md") == []


def test_multiple_hits_across_files_are_all_reported(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    (tmp_path / "a.md").write_text("TD-S001-1 und TD-S002-1\n", encoding="utf-8")
    (tmp_path / "b.cs").write_text("// TD-S001-1\n", encoding="utf-8")

    hits = hook.find_references(["TD-S001-1", "TD-S002-1"], tmp_path / "x.md")
    assert sorted(hits) == [
        ("a.md", 1, "TD-S001-1"), ("a.md", 1, "TD-S002-1"), ("b.cs", 1, "TD-S001-1"),
    ]


def test_hit_list_is_capped_and_announces_the_remainder(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    tracker = docs / "tech-debt.md"
    entry = "## TD-S001-1 — A\n**Fällig:** jetzt – x\n"
    tracker.write_text(entry, encoding="utf-8")
    for i in range(hook._MAX_HITS + 5):
        (tmp_path / f"ref{i}.md").write_text("TD-S001-1\n", encoding="utf-8")

    data = {"tool_name": "Edit",
            "tool_input": {"file_path": str(tracker), "old_string": entry, "new_string": ""}}
    reason = hook.check(data)

    assert reason is not None
    assert f"und {5} weitere" in reason
    assert reason.count("→ TD-S001-1") == hook._MAX_HITS


# --- check() – Dispatcher-Vertrag --------------------------------------------
def test_check_ignores_other_files(tmp_path):
    data = {"tool_name": "Edit",
            "tool_input": {"file_path": "docs/history/adr.md",
                           "old_string": "a", "new_string": "b"}}
    assert hook.check(data) is None


def test_check_blocks_removal_with_remaining_reference(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    tracker = docs / "tech-debt.md"
    entry = "## TD-S001-1 — A\n**Fällig:** jetzt – x\n"
    tracker.write_text(entry + "## TD-S002-1 — B\n", encoding="utf-8")
    (tmp_path / "Server").mkdir()
    (tmp_path / "Server" / "Foo.cs").write_text("// TD-S001-1\n", encoding="utf-8")

    data = {"tool_name": "Edit",
            "tool_input": {"file_path": str(tracker),
                           "old_string": entry, "new_string": ""}}
    reason = hook.check(data)

    assert reason is not None
    assert "TD-S001-1" in reason
    assert "Server/Foo.cs:1" in reason


def test_check_blocks_removal_via_write(monkeypatch, tmp_path):
    # Write ersetzt die ganze Datei – eigener Zweig in compute_post_content.
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    tracker = docs / "tech-debt.md"
    tracker.write_text("## TD-S001-1 — A\n## TD-S002-1 — B\n", encoding="utf-8")
    (tmp_path / "Server").mkdir()
    (tmp_path / "Server" / "Foo.cs").write_text("// TD-S001-1\n", encoding="utf-8")

    data = {"tool_name": "Write",
            "tool_input": {"file_path": str(tracker), "content": "## TD-S002-1 — B\n"}}
    reason = hook.check(data)

    assert reason is not None
    assert "Server/Foo.cs:1" in reason


def test_check_handles_replace_all(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    tracker = docs / "open-questions.md"
    tracker.write_text("## OQ-S001-1 — A\nweg\n## OQ-S002-1 — B\nweg\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("OQ-S001-1\n", encoding="utf-8")

    data = {"tool_name": "Edit",
            "tool_input": {"file_path": str(tracker), "old_string": "weg\n",
                           "new_string": "", "replace_all": True}}
    # Beide Einträge bleiben bestehen – nur ihre Rümpfe schrumpfen.
    assert hook.check(data) is None


def test_check_allows_removal_without_references(monkeypatch, tmp_path):
    monkeypatch.setattr(hook, "_REPO_ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    tracker = docs / "tech-debt.md"
    entry = "## TD-S001-1 — A\n**Fällig:** jetzt – x\n"
    tracker.write_text(entry + "## TD-S002-1 — B\n", encoding="utf-8")

    data = {"tool_name": "Edit",
            "tool_input": {"file_path": str(tracker),
                           "old_string": entry, "new_string": ""}}
    assert hook.check(data) is None

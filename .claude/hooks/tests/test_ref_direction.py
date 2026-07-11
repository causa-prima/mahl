"""Tests für check-ref-direction.py – PreToolUse-Poka-Yoke gegen volatil→stabil-Referenzen.

Regel: Eine stabile Datei (docs/**, .claude/skills/**, .claude/agents/**, CLAUDE.md) darf
kein volatiles ID-Schema (OBS-/OQ-/LL-/TD-S…) referenzieren. Ausnahmen: die kaizen-Bookkeeping-
Dateien, Archive/Session-Logs, volatile Tracker (tech-debt/open-questions/AGENT_MEMORY),
der kaizen-Skill – sowie einzelne Zeilen mit `ref-ok`-Marker.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
hook = import_module("check-ref-direction")


# --- is_protected ------------------------------------------------------------
def test_protects_docs_guidelines_and_reference():
    assert hook.is_protected("docs/guidelines/coding-guideline-typescript.md")
    assert hook.is_protected("docs/reference/architecture.md")
    assert hook.is_protected("docs/history/adr.md")


def test_protects_principles_despite_kaizen_folder():
    # principles.md ist eine stabile Leitplanke – trotz kaizen/ geschützt
    assert hook.is_protected("docs/kaizen/principles.md")


def test_protects_skills_agents_and_root_claudemd():
    assert hook.is_protected(".claude/skills/review-code/SKILL.md")
    assert hook.is_protected(".claude/agents/code-quality-auditor.md")
    assert hook.is_protected("CLAUDE.md")


def test_exempts_kaizen_bookkeeping_files():
    assert not hook.is_protected("docs/kaizen/observations.md")
    assert not hook.is_protected("docs/kaizen/countermeasures.md")
    assert not hook.is_protected("docs/kaizen/lessons_learned.md")
    assert not hook.is_protected("docs/kaizen/process.md")


def test_exempts_volatile_trackers():
    assert not hook.is_protected("docs/tech-debt.md")
    assert not hook.is_protected("docs/open-questions.md")
    assert not hook.is_protected("docs/AGENT_MEMORY.md")


def test_exempts_archive_sessions_and_kaizen_skill():
    assert not hook.is_protected("docs/kaizen/archive/observations_archive.md")
    assert not hook.is_protected("docs/history/sessions/session_101.md")
    assert not hook.is_protected(".claude/skills/kaizen/references/lessons_learned_template.md")


def test_does_not_protect_source_code():
    assert not hook.is_protected("Server/Domain/Ingredient.cs")
    assert not hook.is_protected("Client/src/pages/IngredientsPage.tsx")
    assert not hook.is_protected("README.md")


# --- find_volatile_refs ------------------------------------------------------
def test_finds_volatile_id_schemes():
    content = "Siehe TD-S089-1 und LL-S092-1.\nAuch OBS-S100-2 sowie OQ-S042-3."
    refs = hook.find_volatile_refs(content)
    found = {r[1] for r in refs}
    assert found == {"TD-S089-1", "LL-S092-1", "OBS-S100-2", "OQ-S042-3"}


def test_ignores_stable_adr_ids():
    # ADR ist stabil → kein Verstoß
    assert hook.find_volatile_refs("Begründung in ADR-S041-7 und ADR-S084-4.") == []


def test_ref_ok_marker_exempts_the_line():
    content = (
        "Status/Trigger: TD-S089-1 <!-- ref-ok -->\n"
        "Aber hier nicht: LL-S092-1\n"
    )
    refs = hook.find_volatile_refs(content)
    assert {r[1] for r in refs} == {"LL-S092-1"}


def test_reports_line_numbers():
    content = "sauber\nnoch sauber\nhier TD-S090-2 drin"
    refs = hook.find_volatile_refs(content)
    assert refs == [(3, "TD-S090-2")]


def test_clean_content_yields_no_refs():
    assert hook.find_volatile_refs("Nur normaler Text ohne IDs.\nZweite Zeile.") == []


# --- compute_post_content ----------------------------------------------------
def test_compute_post_content_write_returns_content():
    inp = {"file_path": "docs/x.md", "content": "TD-S001-1\n"}
    assert hook.compute_post_content("Write", "docs/x.md", inp) == "TD-S001-1\n"


def test_compute_post_content_edit_applies_replacement(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("alt: sauber\n", encoding="utf-8")
    inp = {"file_path": str(f), "old_string": "sauber", "new_string": "TD-S001-1"}
    assert hook.compute_post_content("Edit", str(f), inp) == "alt: TD-S001-1\n"

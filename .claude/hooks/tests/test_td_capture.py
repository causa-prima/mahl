"""Tests für check-td-capture.py – PreToolUse-Poka-Yoke gegen TD-Einträge ohne Fälligkeit.

Regel: Ein neuer oder geänderter Eintrag in `docs/tech-debt.md` trägt `**Fällig:**`,
`**Problem:**` und `**Behebung:**`. Die abgeschafften Felder `**Priorität:**` (kein Leser,
OBS-S112-2) und `**Behebung/Trigger:**` (vermischt „wie" und „wann", OBS-S112-1) blocken.
`**Fällig:** jetzt` verlangt die TD-ID in `docs/AGENT_MEMORY.md`, weil nur das bei jedem
Session-Start gelesen wird. Unberührte Bestands-Einträge blocken nie.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
hook = import_module("check-td-capture")


def _td(
    tid: str = "TD-S120-1",
    faellig: str | None = "mit US-602",
    problem: str | None = "Irgendwas ist Schuld.",
    behebung: str | None = "Irgendwie beheben.",
    extra: str = "",
) -> str:
    """Minimaler, formatgetreuer TD-Block."""
    lines = [f"## {tid} — Kurztitel"]
    if faellig is not None:
        lines.append(f"**Fällig:** {faellig}")
    if problem is not None:
        lines.append(f"**Problem:** {problem}")
    if behebung is not None:
        lines.append(f"**Behebung:** {behebung}")
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n\n---\n\n"


# --- is_td_file --------------------------------------------------------------
def test_matches_the_tech_debt_tracker():
    assert hook.is_td_file("docs/tech-debt.md")


def test_matches_absolute_path_to_the_tracker():
    assert hook.is_td_file("/home/kieritz/repos/mahl/docs/tech-debt.md")


def test_ignores_other_docs():
    assert not hook.is_td_file("docs/AGENT_MEMORY.md")
    assert not hook.is_td_file("docs/kaizen/observations.md")
    assert not hook.is_td_file("docs/open-questions.md")


# --- parse_td_entries --------------------------------------------------------
def test_splits_entries_by_td_heading():
    content = _td("TD-S120-1") + _td("TD-S120-2")
    assert sorted(hook.parse_td_entries(content)) == ["TD-S120-1", "TD-S120-2"]


def test_header_comment_is_not_an_entry():
    content = "# Technische Schuld\n\n<!--\n**Fällig:** jetzt\n-->\n\n" + _td()
    assert list(hook.parse_td_entries(content)) == ["TD-S120-1"]


# --- field_names / value_of --------------------------------------------------
def test_reads_field_names_and_values():
    body = hook.parse_td_entries(_td(faellig="ab MVP"))["TD-S120-1"]
    assert hook.field_names(body) == ["Fällig", "Problem", "Behebung"]
    assert hook.value_of(body, "Fällig") == "ab MVP"


def test_value_is_none_when_field_absent():
    body = hook.parse_td_entries(_td(faellig=None))["TD-S120-1"]
    assert hook.value_of(body, "Fällig") is None


def test_prose_paragraphs_are_read_as_names_but_do_not_disturb():
    """Fettgesetzte Prosa-Absätze sind in TD-Einträgen legitim – es gibt bewusst keine
    abschließende Feldliste (Unterschied zu check-obs-capture)."""
    body = hook.parse_td_entries(_td(extra="**Zusammenhang:** hängt an TD-S110-1."))["TD-S120-1"]
    assert "Zusammenhang" in hook.field_names(body)
    assert hook.check_entry("TD-S120-1", body, "") == []


# --- is_now ------------------------------------------------------------------
def test_recognizes_now_with_and_without_reason():
    assert hook.is_now("jetzt")
    assert hook.is_now("jetzt – die Anforderung gilt bereits")
    assert hook.is_now("Jetzt")


def test_does_not_mistake_other_values_for_now():
    assert not hook.is_now("ab MVP")
    assert not hook.is_now("mit US-602")
    assert not hook.is_now("jetztsowieso")  # kein Wortende → kein „jetzt"


# --- check_entry: Pflichtfelder ----------------------------------------------
def test_wellformed_entry_passes():
    body = hook.parse_td_entries(_td())["TD-S120-1"]
    assert hook.check_entry("TD-S120-1", body, "") == []


def test_missing_faellig_is_reported():
    body = hook.parse_td_entries(_td(faellig=None))["TD-S120-1"]
    assert any("`**Fällig:**` fehlt" in r for r in hook.check_entry("TD-S120-1", body, ""))


def test_missing_problem_and_behebung_are_reported():
    body = hook.parse_td_entries(_td(problem=None, behebung=None))["TD-S120-1"]
    reasons = hook.check_entry("TD-S120-1", body, "")
    assert any("`**Problem:**` fehlt" in r for r in reasons)
    assert any("`**Behebung:**` fehlt" in r for r in reasons)


def test_empty_faellig_is_reported():
    body = hook.parse_td_entries(_td(faellig=""))["TD-S120-1"]
    assert any("ist leer" in r for r in hook.check_entry("TD-S120-1", body, ""))


# --- check_entry: abgeschaffte Felder ----------------------------------------
def test_retired_prioritaet_field_blocks():
    body = hook.parse_td_entries(_td(extra="**Priorität:** Hoch"))["TD-S120-1"]
    assert any("`**Priorität:**`" in r for r in hook.check_entry("TD-S120-1", body, ""))


def test_retired_combined_field_blocks_and_counts_as_missing_behebung():
    """Die alte Vorlage: `**Behebung/Trigger:**` statt getrennter Felder."""
    old = f"## TD-S120-1 — Alt\n**Priorität:** Mittel\n**Problem:** X\n**Behebung/Trigger:** Y\n"
    body = hook.parse_td_entries(old)["TD-S120-1"]
    reasons = hook.check_entry("TD-S120-1", body, "")
    assert any("`**Behebung/Trigger:**`" in r for r in reasons)
    assert any("`**Fällig:**` fehlt" in r for r in reasons)
    assert any("`**Behebung:**` fehlt" in r for r in reasons)


# --- check_entry: „jetzt" verlangt AGENT_MEMORY ------------------------------
def test_now_without_memory_entry_blocks():
    body = hook.parse_td_entries(_td(faellig="jetzt"))["TD-S120-1"]
    reasons = hook.check_entry("TD-S120-1", body, "Nächste Prioritäten\n- irgendwas anderes")
    assert any("AGENT_MEMORY" in r for r in reasons)


def test_now_with_memory_entry_passes():
    body = hook.parse_td_entries(_td(faellig="jetzt"))["TD-S120-1"]
    memory = "## Nächste Prioritäten\n- Theme-Foundation ziehen (TD-S120-1).\n"
    assert hook.check_entry("TD-S120-1", body, memory) == []


def test_event_trigger_needs_no_memory_entry():
    body = hook.parse_td_entries(_td(faellig="ab MVP"))["TD-S120-1"]
    assert hook.check_entry("TD-S120-1", body, "") == []


# --- find_violations: nur Neues und Geändertes -------------------------------
def test_untouched_broken_entry_does_not_block():
    """Fremde Altlast darf den eigenen Edit nicht blocken."""
    broken = _td("TD-S119-1", faellig=None)
    pre = broken
    post = broken + _td("TD-S120-1")
    assert hook.find_violations(pre, post, "") == []


def test_new_broken_entry_blocks():
    pre = _td("TD-S119-1")
    post = pre + _td("TD-S120-1", faellig=None)
    assert [tid for tid, _ in hook.find_violations(pre, post, "")] == ["TD-S120-1"]


def test_changed_entry_is_rechecked():
    pre = _td("TD-S119-1")
    post = _td("TD-S119-1", faellig=None, problem="Jetzt umformuliert.")
    assert [tid for tid, _ in hook.find_violations(pre, post, "")] == ["TD-S119-1"]


# --- memory_text_for ---------------------------------------------------------
def test_finds_agent_memory_next_to_the_tracker(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "AGENT_MEMORY.md").write_text("TD-S120-1 ist dran", encoding="utf-8")
    assert "TD-S120-1" in hook.memory_text_for(str(tmp_path / "docs" / "tech-debt.md"))


def test_missing_agent_memory_yields_empty_string(tmp_path):
    assert hook.memory_text_for(str(tmp_path / "docs" / "tech-debt.md")) == ""


# --- check(): Dispatcher-Einstieg --------------------------------------------
def _payload(file_path: str, content: str, tool: str = "Write") -> dict:
    return {"tool_name": tool, "tool_input": {"file_path": file_path, "content": content}}


def test_check_ignores_other_tools_and_files(tmp_path):
    td = tmp_path / "docs" / "tech-debt.md"
    td.parent.mkdir()
    td.write_text("", encoding="utf-8")
    assert hook.check({"tool_name": "Bash", "tool_input": {"file_path": str(td)}}) is None
    assert hook.check(_payload(str(tmp_path / "docs" / "open-questions.md"), _td(faellig=None))) is None


def test_check_reports_the_offending_entry(tmp_path):
    td = tmp_path / "docs" / "tech-debt.md"
    td.parent.mkdir()
    td.write_text("", encoding="utf-8")
    reason = hook.check(_payload(str(td), _td(faellig=None)))
    assert reason is not None
    assert "TD-S120-1" in reason
    assert "**Fällig:**" in reason


def test_check_passes_wellformed_write(tmp_path):
    td = tmp_path / "docs" / "tech-debt.md"
    td.parent.mkdir()
    td.write_text("", encoding="utf-8")
    assert hook.check(_payload(str(td), _td())) is None


def test_check_simulates_an_edit(tmp_path):
    td = tmp_path / "docs" / "tech-debt.md"
    td.parent.mkdir()
    td.write_text(_td("TD-S119-1"), encoding="utf-8")
    payload = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(td),
            "old_string": "**Fällig:** mit US-602",
            "new_string": "**Fällig:**",
        },
    }
    reason = hook.check(payload)
    assert reason is not None and "ist leer" in reason

"""Tests für check-oq-capture.py – Schreibzeit-Prüfung der OQ-Fälligkeit.

Regel: `**Fällig:**` ist bei offenen Fragen **optional** (ohne das Feld greift die
Alters-Regel nach ~10 Sessions). Ist es gesetzt, unterdrückt es genau diese Alters-Regel –
dann muss es tragen: auswertbarer Kopf, mindestens ein terminierter Anker, Referenziertes
existiert. Geprüft werden nur neue und geänderte Einträge.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
hook = import_module("check-oq-capture")
import td_anchors  # noqa: E402


def oq(oid: str, faellig: str | None = None, title: str = "Frage?") -> str:
    block = f"## {oid} — {title}\n**Frage:** Was gilt?\n"
    if faellig is not None:
        block += f"**Fällig:** {faellig}\n"
    return block + "**Hintergrund:** Kontext.\n\n"


# --- is_oq_file --------------------------------------------------------------
def test_recognizes_oq_file_relative_and_absolute():
    assert hook.is_oq_file("docs/open-questions.md")
    assert hook.is_oq_file("/home/x/repo/docs/open-questions.md")


def test_ignores_other_trackers():
    assert not hook.is_oq_file("docs/tech-debt.md")
    assert not hook.is_oq_file("docs/history/adr.md")


# --- check_entry: Feld ist Pflicht -------------------------------------------
def test_missing_due_field_is_rejected():
    """Seit S121 Pflicht (OBS-S117-4): ohne Termin ist eine treibende Frage von einer
    frisch gestellten nicht unterscheidbar."""
    reasons = hook.check_entry("OQ-S001-1", "**Frage:** Was gilt?\n")
    assert reasons and "fehlt" in reasons[0]


def test_empty_due_field_is_rejected():
    reasons = hook.check_entry("OQ-S001-1", "**Fällig:**\n")
    assert reasons and "leer" in reasons[0]


# --- check_entry: gesetzte Anker müssen tragen -------------------------------
def test_valid_session_anchor_passes():
    assert hook.check_entry("OQ-S001-1", "**Fällig:** S140 – Backstop\n") == []


def test_valid_phase_anchor_passes():
    assert hook.check_entry("OQ-S001-1", "**Fällig:** Phase:V1 – mit der Phase\n") == []


def test_typo_in_anchor_is_rejected():
    # Der Fehlermodus, der ohne diesen Hook erst beim nächsten Session-Start auffiele –
    # und bis dahin die Frage stillschweigend nicht vorlegt.
    reasons = hook.check_entry("OQ-S001-1", "**Fällig:** Phase-V1 – Vertipper\n")
    assert reasons and "unbekannter Anker" in reasons[0]


def test_unterminated_story_anchor_alone_is_rejected():
    # Ein gesetzter Anker unterdrückt die Alters-Regel; ein nie eintretender ließe die
    # Frage dauerhaft verwaisen – schlechter als gar kein Feld.
    reasons = hook.check_entry("OQ-S001-1", "**Fällig:** US-602 – irgendwann\n")
    assert reasons and "kein terminierter Anker" in reasons[0]


def test_story_anchor_with_backstop_passes():
    assert hook.check_entry("OQ-S001-1", "**Fällig:** US-602, S128 – mit Backstop\n") == []


def test_prose_after_the_dash_is_not_parsed_as_anchor():
    body = "**Fällig:** S128 – der tragende Trigger ist Phase-irgendwas, nicht das Alter\n"
    assert hook.check_entry("OQ-S001-1", body) == []


# --- find_violations: nur neue und geänderte Einträge ------------------------
def test_untouched_bad_entry_does_not_block():
    pre = oq("OQ-S001-1", faellig="Phase-V1 – kaputt")
    post = pre + oq("OQ-S002-1", faellig="S140 – sauber")
    assert hook.find_violations(pre, post) == []


def test_new_bad_entry_blocks():
    pre = oq("OQ-S001-1", faellig="S140 – sauber")
    post = pre + oq("OQ-S002-1", faellig="Phase-V1 – kaputt")
    assert [oid for oid, _ in hook.find_violations(pre, post)] == ["OQ-S002-1"]


def test_changed_entry_is_rechecked():
    pre = oq("OQ-S001-1", faellig="S140 – sauber")
    post = oq("OQ-S001-1", faellig="Phase-V1 – jetzt kaputt")
    assert [oid for oid, _ in hook.find_violations(pre, post)] == ["OQ-S001-1"]


# --- check(): Dispatcher-Vertrag ---------------------------------------------
def _write_tracker(tmp_path, content: str):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    target = docs / "open-questions.md"
    target.write_text(content, encoding="utf-8")
    return target


def test_check_ignores_other_tools(tmp_path):
    assert hook.check({"tool_name": "Read",
                       "tool_input": {"file_path": "docs/open-questions.md"}}) is None


def test_check_ignores_other_files(tmp_path):
    data = {"tool_name": "Edit",
            "tool_input": {"file_path": "docs/tech-debt.md",
                           "old_string": "a", "new_string": "**Fällig:** Phase-V1 – kaputt"}}
    assert hook.check(data) is None


def test_check_blocks_typo_via_edit(tmp_path):
    old = oq("OQ-S001-1", faellig="S140 – sauber")
    target = _write_tracker(tmp_path, old)
    new = oq("OQ-S001-1", faellig="Phase-V1 – Vertipper")

    reason = hook.check({"tool_name": "Edit",
                         "tool_input": {"file_path": str(target),
                                        "old_string": old, "new_string": new}})
    assert reason is not None
    assert "OQ-S001-1" in reason
    assert "Anker-Vokabular" in reason


def test_check_blocks_typo_via_write(tmp_path):
    target = _write_tracker(tmp_path, oq("OQ-S001-1", faellig="S140 – sauber"))
    content = oq("OQ-S001-1", faellig="Phase-V1 – Vertipper")

    reason = hook.check({"tool_name": "Write",
                         "tool_input": {"file_path": str(target), "content": content}})
    assert reason is not None
    assert "OQ-S001-1" in reason


def test_check_passes_valid_entry(tmp_path):
    old = oq("OQ-S001-1", faellig="S140 – sauber")
    target = _write_tracker(tmp_path, old)
    new = oq("OQ-S001-1", faellig="S141 – auch sauber")

    assert hook.check({"tool_name": "Edit",
                       "tool_input": {"file_path": str(target),
                                      "old_string": old, "new_string": new}}) is None


def test_check_blocks_entry_without_due_field(tmp_path):
    """Das Feld zu entfernen ist seit S121 ein Verstoß, kein Rückfall auf die Alters-Regel."""
    old = oq("OQ-S001-1", faellig="S140 – sauber")
    target = _write_tracker(tmp_path, old)
    new = oq("OQ-S001-1")

    grund = hook.check({"tool_name": "Edit",
                        "tool_input": {"file_path": str(target),
                                       "old_string": old, "new_string": new}})
    assert grund and "fehlt" in grund

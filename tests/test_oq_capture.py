"""Tests für check-oq-capture.py – Schreibzeit-Prüfung der OQ-Fälligkeit.

Regel: `**Fällig:**` ist bei offenen Fragen **Pflicht** (seit S121). Weil ein gesetzter
Anker die Alters-Regel unterdrückt, muss er tragen: auswertbarer Kopf, mindestens ein
terminierter Anker, Referenziertes existiert. Geprüft werden nur neue und geänderte Einträge.
"""
from importlib import import_module

import pytest

hook = import_module("prozesscode.hooks.check-oq-capture")


def oq(oid: str, faellig: str | None = None, title: str = "Frage?",
       aufschub: str | None = "User – im Gespräch geparkt") -> str:
    block = f"## {oid} — {title}\n**Frage:** Was gilt?\n"
    if faellig is not None:
        block += f"**Fällig:** {faellig}\n"
    block += "**Hintergrund:** Kontext.\n"
    if aufschub is not None:
        block += f"**Aufschubgrund:** {aufschub}\n"
    return block + "\n"


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


# --- Aufschubgrund (S133): Pflicht nur für NEUE Einträge ----------------------
def test_new_entry_without_aufschubgrund_blocks():
    post = oq("OQ-S002-1", faellig="S140 – sauber", aufschub=None)
    verstoesse = hook.find_violations("", post)
    assert [oid for oid, _ in verstoesse] == ["OQ-S002-1"]
    assert "Aufschubgrund" in verstoesse[0][1]


def test_changed_old_entry_without_aufschubgrund_passes():
    pre = oq("OQ-S001-1", faellig="S140 – sauber", aufschub=None)
    post = oq("OQ-S001-1", faellig="S150 – verschoben", aufschub=None)
    assert hook.find_violations(pre, post) == []


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


@pytest.mark.aufrufpfad("check-oq-capture")
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


# --- check(): Anker-Kontext aus dem Repo neben der Datei --------------------------
# `check()` lädt den Kontext aus dem Repo der bearbeiteten Datei. Fällt er weg, gilt jeder
# `TD-`-Anker als unbekannt – und eine gültige Frage blockt.
def _mit_tech_debt(tmp_path, td_text: str):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "tech-debt.md").write_text(td_text, encoding="utf-8")


def test_check_prueft_nur_die_oq_datei(tmp_path):
    """Ein formwidriger OQ-Block in einer anderen Datei ist nicht Sache dieses Hooks."""
    andere = tmp_path / "docs" / "notizen.md"
    andere.parent.mkdir()
    assert hook.check({"tool_name": "Write",
                       "tool_input": {"file_path": str(andere), "content": oq("OQ-S001-1")}}) is None


def test_check_kennt_die_td_eintraege_des_repos(tmp_path):
    _mit_tech_debt(tmp_path, "## TD-S120-1 — Schuld\n**Fällig:** Phase:MVP\n\n---\n")
    target = _write_tracker(tmp_path, "")
    inhalt = oq("OQ-S001-1", faellig="TD-S120-1 – sobald die Schuld weg ist")
    assert hook.check({"tool_name": "Write",
                       "tool_input": {"file_path": str(target), "content": inhalt}}) is None


def test_check_meldet_unbekannten_td_anker(tmp_path):
    """Gegenstück: derselbe Anker, aber das Repo kennt den Eintrag nicht."""
    _mit_tech_debt(tmp_path, "")
    target = _write_tracker(tmp_path, "")
    inhalt = oq("OQ-S001-1", faellig="TD-S120-1 – sobald die Schuld weg ist")
    grund = hook.check({"tool_name": "Write",
                        "tool_input": {"file_path": str(target), "content": inhalt}})
    assert "existiert nicht" in grund


def test_check_nennt_jeden_verletzenden_eintrag_auf_eigener_zeile(tmp_path):
    target = _write_tracker(tmp_path, "")
    inhalt = oq("OQ-S001-1") + oq("OQ-S001-2")
    zeilen = hook.check({"tool_name": "Write",
                         "tool_input": {"file_path": str(target), "content": inhalt}}).splitlines()
    assert [z.split(":")[0] for z in zeilen[1:3]] == ["  - OQ-S001-1", "  - OQ-S001-2"]


def test_mehrere_gruende_eines_eintrags_stehen_getrennt():
    assert hook.find_violations("", oq("OQ-S001-1", aufschub=None)) == [
        ("OQ-S001-1", hook._FAELLIG_FEHLT + " · " + hook.aufschub_verstoss(None))]


def test_kontext_ist_optional():
    assert hook.check_entry("OQ-S001-1", "**Fällig:** S140 – Termin\n") == []
    assert hook.find_violations("", oq("OQ-S001-1", faellig="S140 – Termin")) == []


@pytest.mark.parametrize("pfad, wurzel", [
    ("docs/open-questions.md", "."),
    ("/home/u/repo/docs/open-questions.md", "/home/u/repo"),
])
def test_repo_wurzel_aus_dem_pfad(pfad, wurzel):
    assert hook.repo_root_for(pfad) == hook.Path(wurzel)

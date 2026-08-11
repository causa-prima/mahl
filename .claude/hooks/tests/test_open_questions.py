"""Tests für open_questions.py – fällige offene Fragen für die Session-Agenda.

Regel: Eine Frage wird vorgelegt, wenn ihr optionales `**Fällig:** S<NNN>` erreicht ist oder –
ohne Termin – wenn sie ~10 Sessions alt ist. Ein gesetzter Termin unterdrückt die Alters-Regel,
sonst wäre er wirkungslos. Höchstens drei, älteste zuerst.

Bis S116 hing diese Logik in `obs-drain.py`; sie ist jetzt ein eigenes Agenda-Modul, weil
offene Fragen ein anderer Tracker mit anderem Ausgang sind (mit dem User klären statt im Drain
entscheiden).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import open_questions as oqm  # noqa: E402


def oq(oid: str, title: str = "Frage?", faellig: int | None = None) -> str:
    block = f"## {oid} — {title}\n**Frage:** Was gilt?\n"
    if faellig:
        block += f"**Fällig:** S{faellig}\n"
    return block + "**Hintergrund:** Kontext.\n"


def parse_oq(*blocks: str) -> list[dict]:
    return oqm.parse("\n".join(blocks))


# --- parse -------------------------------------------------------------------
def test_parses_id_session_and_title():
    fragen = oqm.parse(oq("OQ-S083-1", title="Taxonomie klären"))
    assert len(fragen) == 1
    assert fragen[0]["id"] == "OQ-S083-1"
    assert fragen[0]["session"] == 83
    assert fragen[0]["title"] == "Taxonomie klären"
    assert fragen[0]["faellig"] is None


def test_parses_the_optional_due_session():
    assert oqm.parse(oq("OQ-S094-1", faellig=120))[0]["faellig"] == 120


def test_empty_file_yields_no_questions():
    assert oqm.parse("") == []


# --- due ---------------------------------------------------------------------
def test_due_question_by_reached_date():
    assert [f["id"] for f in oqm.due(oqm.parse(oq("OQ-S114-1", faellig=115)), 115)] == ["OQ-S114-1"]


def test_future_date_is_not_due_yet():
    """Ein gesetzter Termin unterdrückt die Alters-Regel – sonst wäre er wirkungslos."""
    assert oqm.due(oqm.parse(oq("OQ-S080-1", faellig=200)), 115) == []


def test_stale_question_without_date_is_presented():
    assert [f["id"] for f in oqm.due(oqm.parse(oq("OQ-S083-1")), 115)] == ["OQ-S083-1"]


def test_young_question_without_date_stays_quiet():
    assert oqm.due(oqm.parse(oq("OQ-S114-1")), 115) == []


def test_oldest_questions_come_first_and_are_capped():
    fragen = parse_oq(oq("OQ-S090-1"), oq("OQ-S080-1"), oq("OQ-S085-1"), oq("OQ-S070-1"))
    ids = [f["id"] for f in oqm.due(fragen, 115)]
    assert ids[0] == "OQ-S070-1"
    assert len(ids) <= oqm.MAX


def test_unknown_session_number_presents_nothing():
    """Ohne Session-Nummer ist kein Alter bestimmbar – dann lieber schweigen als raten."""
    assert oqm.due(oqm.parse(oq("OQ-S083-1")), None) == []

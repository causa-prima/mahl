"""Tests für open_questions.py – fällige offene Fragen für die Session-Agenda.

Regel: Eine Frage wird vorgelegt, wenn ihr optionales `**Fällig:**` eingetreten ist oder –
ohne Feld – wenn sie ~10 Sessions alt ist. Ein gesetzter Anker unterdrückt die Alters-Regel,
sonst wäre er wirkungslos. Höchstens drei, älteste zuerst.

Seit S119 (Beschluss E4) liest sich `**Fällig:**` nach der geteilten Anker-Grammatik aus
`td_anchors.py` statt nach einem eigenen `S<NNN>`-Regex. Zwei bewusste Abweichungen von der
TD-Auswertung sind hier festgehalten: `jetzt` erzeugt bei OQ einen Grund (kein zweiter Kanal
über AGENT_MEMORY), und ein fehlendes Feld fällt auf die Alters-Regel zurück (bei TD ist es
Pflicht). Ein *unlesbarer* Anker wird gemeldet statt verschluckt – genau der Fehlermodus,
den die Grammatik behebt.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import open_questions as oqm  # noqa: E402
import td_anchors  # noqa: E402


def oq(oid: str, title: str = "Frage?", faellig: str | None = None) -> str:
    block = f"## {oid} — {title}\n**Frage:** Was gilt?\n"
    if faellig:
        block += f"**Fällig:** {faellig}\n"
    return block + "**Hintergrund:** Kontext.\n"


def parse_oq(*blocks: str) -> list[dict]:
    return oqm.parse("\n".join(blocks))


def ktx(**kwargs) -> td_anchors.Kontext:
    """Auflöse-Kontext; ohne Angaben ist nichts eingetreten."""
    return td_anchors.Kontext(**kwargs)


# --- parse -------------------------------------------------------------------
def test_parses_id_session_and_title():
    fragen = oqm.parse(oq("OQ-S083-1", title="Taxonomie klären"))
    assert len(fragen) == 1
    assert fragen[0]["id"] == "OQ-S083-1"
    assert fragen[0]["session"] == 83
    assert fragen[0]["title"] == "Taxonomie klären"
    assert fragen[0]["faellig"] is None


def test_keeps_the_raw_due_value_including_prose():
    # Ausgewertet wird erst in due() – parse() darf den Kopf nicht wegschneiden.
    fragen = oqm.parse(oq("OQ-S094-1", faellig="Phase:V1 – Trigger ist das UX-Szenario"))
    assert fragen[0]["faellig"] == "Phase:V1 – Trigger ist das UX-Szenario"


def test_extracts_the_question_text_for_the_agenda():
    assert oqm.parse(oq("OQ-S083-1"))[0]["frage"] == "Was gilt?"


def test_empty_file_yields_no_questions():
    assert oqm.parse("") == []


# --- due: Anker-Grammatik ----------------------------------------------------
def test_due_by_reached_session_anchor():
    fragen = oqm.parse(oq("OQ-S114-1", faellig="S115 – Backstop"))
    assert [f["id"] for f in oqm.due(fragen, ktx(session=115), 115)] == ["OQ-S114-1"]


def test_future_session_anchor_is_not_due_yet():
    """Ein gesetzter Anker unterdrückt die Alters-Regel – sonst wäre er wirkungslos."""
    fragen = oqm.parse(oq("OQ-S080-1", faellig="S200 – weit geparkt"))
    assert oqm.due(fragen, ktx(session=115), 115) == []


def test_due_by_reached_phase_anchor():
    # Der Anker, den das alte S<NNN>-only-Regex still auf die Alters-Regel zurückfallen ließ.
    fragen = oqm.parse(oq("OQ-S094-1", faellig="Phase:V1 – Trigger ist das UX-Szenario"))
    assert [f["id"] for f in oqm.due(fragen, ktx(phase="V1", session=100), 100)] == ["OQ-S094-1"]


def test_unreached_phase_anchor_stays_quiet():
    fragen = oqm.parse(oq("OQ-S094-1", faellig="Phase:V1 – später"))
    assert oqm.due(fragen, ktx(phase="MVP", session=100), 100) == []


def test_jetzt_anchor_is_due_unlike_tech_debt():
    # Abweichung 1: OQ hat keinen zweiten Kanal über AGENT_MEMORY.
    fragen = oqm.parse(oq("OQ-S118-1", faellig="jetzt – blockiert den Umbau"))
    faellig = oqm.due(fragen, ktx(session=119), 119)
    assert [f["id"] for f in faellig] == ["OQ-S118-1"]
    assert "jetzt" in faellig[0]["gruende"][0]


def test_unparsable_anchor_is_reported_not_swallowed():
    # Vorher fiel ein Vertipper still auf die Alters-Regel zurück und blieb unbemerkt.
    fragen = oqm.parse(oq("OQ-S118-1", faellig="Phase-V1 – Tippfehler statt Phase:V1"))
    faellig = oqm.due(fragen, ktx(session=119), 119)
    assert [f["id"] for f in faellig] == ["OQ-S118-1"]
    assert "nicht auswertbar" in faellig[0]["gruende"][0]


def test_due_reports_its_reasons():
    fragen = oqm.parse(oq("OQ-S114-1", faellig="S115 – Backstop"))
    assert oqm.due(fragen, ktx(session=115), 115)[0]["gruende"] != []


# --- due: Alters-Regel ohne Feld ---------------------------------------------
def test_stale_question_without_due_field_is_presented():
    assert [f["id"] for f in oqm.due(oqm.parse(oq("OQ-S083-1")), ktx(), 115)] == ["OQ-S083-1"]


def test_young_question_without_due_field_stays_quiet():
    assert oqm.due(oqm.parse(oq("OQ-S114-1")), ktx(), 115) == []


def test_oldest_questions_come_first_and_are_capped():
    fragen = parse_oq(oq("OQ-S090-1"), oq("OQ-S080-1"), oq("OQ-S085-1"), oq("OQ-S070-1"))
    ids = [f["id"] for f in oqm.due(fragen, ktx(), 115)]
    assert ids[0] == "OQ-S070-1"
    assert len(ids) <= oqm.MAX


def test_unknown_session_number_presents_nothing():
    """Ohne Session-Nummer ist kein Alter bestimmbar – dann lieber schweigen als raten."""
    assert oqm.due(oqm.parse(oq("OQ-S083-1")), ktx(), None) == []

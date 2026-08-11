"""Tests für td_anchors.py – die Anker-Grammatik der Fälligkeiten.

Regel: `**Fällig:** <Anker>[, <Anker>…] – <Prosa>`. Der Kopf ist maschinenlesbar, mindestens
ein Anker muss **terminiert** sein (sagen WANN). Nicht terminiert: `US-NNN` und ein
`Szenario:` ohne Lauf-Zuordnung; eine `TD-`-Kette erbt und muss zyklenfrei sein.

Gegenprobe-Prinzip: Zu jedem „erkennt X"-Test gehört der Fall, in dem X NICHT vorliegt – ein
Prüfer, der immer anschlägt, prüft nichts.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import td_anchors as ta  # noqa: E402


def szenario(lauf=None, lauf_offen=False, implementiert=False) -> dict:
    return {"lauf": lauf, "lauf_offen": lauf_offen, "implementiert": implementiert}


# --- kopf_und_prosa ----------------------------------------------------------
def test_splits_head_from_prose_at_the_first_dash():
    kopf, prosa = ta.kopf_und_prosa("Phase:MVP – erst dort greift die Anforderung – wirklich")
    assert kopf == "Phase:MVP"
    assert prosa == "erst dort greift die Anforderung – wirklich"


def test_head_only_when_there_is_no_prose():
    assert ta.kopf_und_prosa("jetzt") == ("jetzt", "")


# --- parse: Vokabular --------------------------------------------------------
def test_parses_every_anchor_kind():
    anker, fehler = ta.parse('jetzt, Phase:MVP, S130, Szenario:„Titel", US-602, TD-S089-1')
    assert fehler == []
    assert {(a.art, a.wert) for a in anker} == {
        (ta.JETZT, ""), (ta.PHASE, "MVP"), (ta.SESSION, "S130"),
        (ta.SZENARIO, "Titel"), (ta.STORY, "US-602"), (ta.TD, "TD-S089-1"),
    }


def test_scenario_title_may_contain_commas():
    """Deshalb wird tokenisiert statt an Kommata gesplittet – ein Split zerschnitte den Titel."""
    anker, fehler = ta.parse('Szenario:„Zwei Dinge, ein Titel", Phase:MVP')
    assert fehler == []
    assert (ta.SZENARIO, "Zwei Dinge, ein Titel") in {(a.art, a.wert) for a in anker}


def test_td_id_is_not_mistaken_for_a_session_anchor():
    """`S089` steckt in `TD-S089-1` – die Alternativen-Reihenfolge muss das trennen."""
    anker, _ = ta.parse("TD-S089-1")
    assert [(a.art, a.wert) for a in anker] == [(ta.TD, "TD-S089-1")]


def test_prose_after_the_dash_is_not_parsed_as_anchors():
    anker, fehler = ta.parse("Phase:MVP – gemeinsam mit US-602 und TD-S044-1 behandeln")
    assert fehler == []
    assert [a.art for a in anker] == [ta.PHASE]


# --- parse: Gegenprobe -------------------------------------------------------
def test_old_prose_format_is_rejected():
    _, fehler = ta.parse("mit US-602 (URI-Felder)")
    assert any("unbekannter Anker" in f for f in fehler)


def test_typo_in_an_anchor_is_reported_instead_of_silently_ignored():
    _, fehler = ta.parse("Phase-MVP")
    assert any("unbekannter Anker" in f for f in fehler)
    assert any("kein Anker" in f for f in fehler)


def test_empty_value_is_reported():
    assert ta.parse("")[1] == ["`**Fällig:**` ist leer"]


# --- Terminierung ------------------------------------------------------------
def test_now_phase_and_session_terminate():
    ktx = ta.Kontext()
    for wert in ("jetzt", "Phase:MVP", "S130"):
        assert ta.ist_terminiert(ta.parse(wert)[0][0], ktx), wert


def test_story_anchor_never_terminates():
    assert not ta.ist_terminiert(ta.Anker(ta.STORY, "US-602"), ta.Kontext())


def test_scenario_terminates_only_inside_an_open_run():
    offen = ta.Kontext(szenarien={"T": szenario(lauf=7, lauf_offen=True)})
    ohne_lauf = ta.Kontext(szenarien={"T": szenario(lauf=None)})
    erledigt = ta.Kontext(szenarien={"T": szenario(lauf=7, lauf_offen=False)})
    assert ta.ist_terminiert(ta.Anker(ta.SZENARIO, "T"), offen)
    assert not ta.ist_terminiert(ta.Anker(ta.SZENARIO, "T"), ohne_lauf)
    assert not ta.ist_terminiert(ta.Anker(ta.SZENARIO, "T"), erledigt)


def test_td_chain_inherits_termination():
    ktx = ta.Kontext(td_faelligkeiten={"TD-S001-1": "TD-S002-1", "TD-S002-1": "Phase:MVP"})
    assert ta.ist_terminiert(ta.Anker(ta.TD, "TD-S001-1"), ktx)


def test_td_cycle_does_not_terminate():
    """TD-S090-2 und TD-S101-1 verwiesen real wechselseitig aufeinander."""
    ktx = ta.Kontext(td_faelligkeiten={"TD-S001-1": "TD-S002-1", "TD-S002-1": "TD-S001-1"})
    assert not ta.ist_terminiert(ta.Anker(ta.TD, "TD-S001-1"), ktx)


# --- validiere ---------------------------------------------------------------
def test_terminated_entry_passes():
    assert ta.validiere("TD-S001-1", "Phase:MVP – Begründung", ta.Kontext()) == []


def test_missing_backstop_is_reported():
    fehler = ta.validiere("TD-S001-1", "US-602", ta.Kontext())
    assert any("kein terminierter Anker" in f for f in fehler)


def test_story_anchor_with_a_backstop_passes():
    assert ta.validiere("TD-S001-1", "US-602, Phase:V1", ta.Kontext()) == []


def test_unknown_scenario_is_reported():
    fehler = ta.validiere("TD-S001-1", 'Szenario:„Gibt es nicht", Phase:MVP', ta.Kontext())
    assert any("matcht kein Szenario" in f for f in fehler)


def test_story_that_already_has_scenarios_must_be_rehung():
    ktx = ta.Kontext(storys_mit_szenarien=frozenset({"US-904"}))
    fehler = ta.validiere("TD-S001-1", "US-904, Phase:MVP", ktx)
    assert any("hat bereits Szenarien" in f for f in fehler)


def test_story_without_scenarios_is_still_allowed():
    ktx = ta.Kontext(storys_mit_szenarien=frozenset({"US-904"}))
    assert ta.validiere("TD-S001-1", "US-602, Phase:V1", ktx) == []


def test_dangling_td_reference_is_reported():
    fehler = ta.validiere("TD-S001-1", "TD-S999-9, Phase:MVP", ta.Kontext())
    assert any("existiert nicht" in f for f in fehler)


def test_self_reference_is_reported():
    ktx = ta.Kontext(td_faelligkeiten={"TD-S001-1": "TD-S001-1"})
    fehler = ta.validiere("TD-S001-1", "TD-S001-1, Phase:MVP", ktx)
    assert any("auf sich selbst" in f for f in fehler)


# --- faellig_gruende ---------------------------------------------------------
def test_phase_reached_is_due():
    ktx = ta.Kontext(phase="MVP")
    assert ta.faellig_gruende("TD-S001-1", "Phase:MVP", ktx) == ["Phase MVP ist erreicht"]


def test_phase_not_reached_is_quiet():
    assert ta.faellig_gruende("TD-S001-1", "Phase:MVP", ta.Kontext(phase="SKELETON")) == []


def test_session_deadline_reached_is_due():
    assert ta.faellig_gruende("TD-S001-1", "S120", ta.Kontext(session=120))


def test_session_deadline_ahead_is_quiet():
    assert ta.faellig_gruende("TD-S001-1", "S130", ta.Kontext(session=120)) == []


def test_current_story_is_due():
    gruende = ta.faellig_gruende("TD-S001-1", "US-602, Phase:V1", ta.Kontext(story="US-602"))
    assert any("aktuelle Story" in g for g in gruende)


def test_story_with_scenarios_asks_for_rehanging():
    ktx = ta.Kontext(storys_mit_szenarien=frozenset({"US-602"}))
    gruende = ta.faellig_gruende("TD-S001-1", "US-602, Phase:V1", ktx)
    assert any("umhängen" in g for g in gruende)


def test_resolved_predecessor_is_due():
    """Der Vorgänger ist aus tech-debt.md verschwunden = behoben."""
    gruende = ta.faellig_gruende("TD-S001-1", "TD-S002-1", ta.Kontext())
    assert any("ist behoben" in g for g in gruende)


def test_present_predecessor_is_quiet():
    ktx = ta.Kontext(td_faelligkeiten={"TD-S002-1": "Phase:MVP"})
    assert ta.faellig_gruende("TD-S001-1", "TD-S002-1", ktx) == []


def test_implemented_scenario_reports_the_missed_debt():
    ktx = ta.Kontext(szenarien={"T": szenario(lauf=7, implementiert=True)})
    gruende = ta.faellig_gruende("TD-S001-1", 'Szenario:„T", Phase:MVP', ktx)
    assert any("nicht mitgenommen" in g for g in gruende)


def test_vanished_scenario_is_reported():
    gruende = ta.faellig_gruende("TD-S001-1", 'Szenario:„Weg", Phase:MVP', ta.Kontext())
    assert any("existiert nicht" in g for g in gruende)


def test_scenario_without_a_run_is_not_a_recurring_due_reason():
    """Statischer Zustand mit vorhandenem Backstop – als Grund gemeldet stünde er in JEDER
    Session erneut da. Eine Lane, die Unverändertes wiederholt, wird überlesen."""
    ktx = ta.Kontext(szenarien={"T": szenario(lauf=None)})
    assert ta.faellig_gruende("TD-S001-1", 'Szenario:„T", Phase:MVP', ktx) == []


def test_now_alone_is_not_a_due_reason():
    """`jetzt`-Einträge stehen in AGENT_MEMORY und werden von dort vorgelegt – hier nochmals
    zu melden wäre genau die Doppelung, die gekürzt werden sollte."""
    assert ta.faellig_gruende("TD-S001-1", "jetzt – gilt heute", ta.Kontext()) == []


# --- Textextraktion ----------------------------------------------------------
def test_reads_faelligkeiten_per_entry():
    text = ("## TD-S001-1 — A\n**Fällig:** Phase:MVP – x\n**Problem:** p\n\n"
            "## TD-S002-1 — B\n**Fällig:** jetzt\n**Problem:** p\n")
    assert ta.td_faelligkeiten(text) == {"TD-S001-1": "Phase:MVP – x", "TD-S002-1": "jetzt"}


def test_entry_without_the_field_is_skipped():
    assert ta.td_faelligkeiten("## TD-S001-1 — A\n**Problem:** p\n") == {}


def test_reads_the_phase_from_memory():
    assert ta.phase_aus_memory("# M\n\n**Phase:** SKELETON 🔄\n") == "SKELETON"
    assert ta.phase_aus_memory("# M\n") is None


def test_scenario_index_marks_open_runs_and_stories():
    feature = (
        "@US-904\nFeature: F\n\n"
        "  # @run-7 · Liste · Full-Stack\n  Scenario: Fertig\n    Given x\n\n"
        "  # @run-8 · Neu · Full-Stack\n  Scenario: Offen\n    Given x\n\n"
        "  Scenario: Ohne Lauf\n    Given x\n"
    )
    index, storys = ta.szenario_index([feature], implementiert={"Fertig"})
    assert storys == frozenset({"US-904"})
    assert index["Fertig"] == {"lauf": 7, "lauf_offen": False, "implementiert": True}
    assert index["Offen"] == {"lauf": 8, "lauf_offen": True, "implementiert": False}
    assert index["Ohne Lauf"]["lauf"] is None

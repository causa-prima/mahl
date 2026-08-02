"""Tests für obs_entry.py – einzelne OBS-Einträge lesen, erfassen, ändern.

Der Kern ist die **Form-Garantie**: Über `add()` darf kein Eintrag entstehen, den
`check-obs-capture.py` blocken würde. Das Entscheidungsfeld ist deshalb nicht setzbar, und die
Aufzählungswerte werden geprüft statt übernommen.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

import obs_entry as oe

capture = import_module("check-obs-capture")

BESTAND = """# Observations

<!-- Header -->

## OBS-S110-1 – Erster
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: irgendwas
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S110-2 – Zweiter
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: noch was
- Entscheidung/Maßnahme: offen
- Bezug: OBS-S110-1
"""

FELDER = dict(
    titel="Ein Titel",
    quelle="User",
    impact="MITTEL",
    haeufigkeit="dauerhaft",
    kategorie="PROZESS",
    kontext="Doku",
    beobachtung="Etwas fiel auf.",
    bezug=None,
)


# --- Lesen -------------------------------------------------------------------
def test_get_returns_only_the_requested_entry():
    eintrag = oe.get(BESTAND, "OBS-S110-1")
    assert eintrag.startswith("## OBS-S110-1")
    assert "OBS-S110-2" not in eintrag
    assert "- Beobachtung: irgendwas" in eintrag


def test_get_returns_none_for_unknown_ids():
    assert oe.get(BESTAND, "OBS-S999-9") is None


def test_spans_cover_every_entry():
    assert sorted(oe.entry_spans(BESTAND)) == ["OBS-S110-1", "OBS-S110-2"]


# --- ID-Vergabe --------------------------------------------------------------
def test_next_id_continues_the_session_series():
    assert oe.next_id(BESTAND, 110) == "OBS-S110-3"


def test_next_id_starts_at_one_for_a_fresh_session():
    assert oe.next_id(BESTAND, 114) == "OBS-S114-1"


def test_next_id_pads_the_session_number():
    assert oe.next_id("", 99) == "OBS-S099-1"


# --- Erfassen ----------------------------------------------------------------
def test_add_appends_and_reports_the_new_id():
    neu, oid = oe.add(BESTAND, 114, **FELDER)
    assert oid == "OBS-S114-1"
    assert neu.startswith(BESTAND.rstrip("\n")[:40])
    assert oe.get(neu, oid) is not None


def test_add_keeps_existing_entries_untouched():
    neu, _ = oe.add(BESTAND, 114, **FELDER)
    assert oe.get(neu, "OBS-S110-1") == oe.get(BESTAND, "OBS-S110-1")


def test_bezug_is_omitted_when_not_given():
    eintrag = oe.format_entry("OBS-S114-1", **FELDER)
    assert "- Bezug:" not in eintrag


def test_bezug_is_included_when_given():
    eintrag = oe.format_entry("OBS-S114-1", **{**FELDER, "bezug": "LL-S114-1"})
    assert "- Bezug: LL-S114-1" in eintrag


# --- Form-Garantie: der Erfassungs-Hook darf nie greifen ---------------------
def test_generated_entry_passes_the_capture_hook():
    """Die eigentliche Zusage dieses Moduls: Was hier entsteht, ist nicht blockierbar."""
    neu, oid = oe.add(BESTAND, 114, **FELDER)
    assert capture.find_violations(BESTAND, neu) == []


def test_generated_entry_passes_even_with_a_solution_sounding_observation():
    """Der Hook blockt Lösungs-Ansagen im Text – dieselbe Prüfung gilt hier."""
    felder = {**FELDER, "beobachtung": "X ist langsam. Das Risiko: es könnte schlimmer werden."}
    neu, _ = oe.add(BESTAND, 114, **felder)
    assert capture.find_violations(BESTAND, neu) == []


def test_decision_field_is_not_settable():
    """Es gibt bewusst kein Argument dafür – der Drain entscheidet, nicht die Erfassung."""
    import inspect
    assert "entscheidung" not in inspect.signature(oe.format_entry).parameters


# --- Validierung -------------------------------------------------------------
def test_rejects_unknown_impact():
    try:
        oe.format_entry("OBS-S114-1", **{**FELDER, "impact": "SEHR HOCH"})
    except ValueError as fehler:
        assert "Impact" in str(fehler)
    else:
        raise AssertionError("ungültiger Impact wurde akzeptiert")


def test_rejects_unknown_frequency_and_category():
    for feld, wert in (("haeufigkeit", "immer"), ("kategorie", "SONSTIGES")):
        try:
            oe.format_entry("OBS-S114-1", **{**FELDER, feld: wert})
        except ValueError:
            continue
        raise AssertionError(f"ungültiger Wert für {feld} wurde akzeptiert")


def test_rejects_empty_title_or_observation():
    for feld in ("titel", "beobachtung"):
        try:
            oe.format_entry("OBS-S114-1", **{**FELDER, feld: "   "})
        except ValueError:
            continue
        raise AssertionError(f"leeres {feld} wurde akzeptiert")


# --- Ändern ------------------------------------------------------------------
def test_set_replaces_status_only():
    neu = oe.set_fields(BESTAND, "OBS-S110-1", status="UMGESETZT (S114)")
    assert "- Status: UMGESETZT (S114)" in oe.get(neu, "OBS-S110-1")
    assert oe.get(neu, "OBS-S110-2") == oe.get(BESTAND, "OBS-S110-2")


def test_set_replaces_decision_only():
    neu = oe.set_fields(BESTAND, "OBS-S110-2", entscheidung="Verworfen, weil …")
    eintrag = oe.get(neu, "OBS-S110-2")
    assert "- Entscheidung/Maßnahme: Verworfen, weil …" in eintrag
    assert "- Status: NEU" in eintrag


def test_set_keeps_the_bezug_line():
    neu = oe.set_fields(BESTAND, "OBS-S110-2", status="VERWORFEN (Grund)")
    assert "- Bezug: OBS-S110-1" in oe.get(neu, "OBS-S110-2")


def test_set_rejects_unknown_ids():
    try:
        oe.set_fields(BESTAND, "OBS-S999-9", status="X")
    except ValueError as fehler:
        assert "OBS-S999-9" in str(fehler)
    else:
        raise AssertionError("unbekannte ID wurde akzeptiert")


def test_set_changes_both_fields_at_once():
    neu = oe.set_fields(BESTAND, "OBS-S110-1", status="VERWORFEN (Gegenstand entfallen)",
                        entscheidung="Der betroffene Code existiert nicht mehr.")
    eintrag = oe.get(neu, "OBS-S110-1")
    assert "VERWORFEN (Gegenstand entfallen)" in eintrag
    assert "existiert nicht mehr" in eintrag

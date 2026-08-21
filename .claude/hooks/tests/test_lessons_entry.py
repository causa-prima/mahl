"""Tests für lessons_entry.py – einzelne Learnings lesen und erfassen.

Die Struktur ist parse-kritisch: `jenga_score.py` und `retro_report.py` lesen dieselben
Bullets. Deshalb prüfen die Tests die exakte Klammerform und dass bestehende Einträge beim
Anhängen unberührt bleiben.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

import lessons_entry as le

BESTAND = """# Lessons Learned

<!-- Header -->

## Session 113 – 2026-08-01

- **[HOCH] [PROZESS] [Doku] LL-S113-1 – Erster Titel**
  Quelle: User
  Was: Etwas passierte.
  Warum: Ursache.
  Regel: Mach es anders.

- **[MITTEL] [TOOLING] [Hook/Script] LL-S113-2 – Zweiter Titel**
  Quelle: Orchestrator
  Was: Noch etwas.
  Warum: Andere Ursache.
  Regel: Mach es so.

## Session 112 – 2026-07-31

- **[GERING] [AGENT] [Review] LL-S112-1 – Dritter Titel**
  Quelle: Subagent
  Was: Drittens.
  Warum: Weil.
  Regel: Denk dran.
"""

FELDER = dict(
    titel="Neuer Titel",
    impact="MITTEL",
    kategorie="PROZESS",
    kontext="Testing",
    quelle="Orchestrator",
    was="Es geschah dies.",
    warum="Weil jenes.",
    regel="Tu künftig das.",
)


# --- Lesen -------------------------------------------------------------------
def test_get_returns_only_the_requested_entry():
    eintrag = le.get(BESTAND, "LL-S113-1")
    assert "Erster Titel" in eintrag
    assert "Zweiter Titel" not in eintrag
    assert "Regel: Mach es anders." in eintrag


def test_get_stops_before_the_next_session_heading():
    eintrag = le.get(BESTAND, "LL-S113-2")
    assert "Session 112" not in eintrag
    assert "LL-S112-1" not in eintrag


def test_get_reads_the_last_entry_of_the_file():
    eintrag = le.get(BESTAND, "LL-S112-1")
    assert "Dritter Titel" in eintrag
    assert "Regel: Denk dran." in eintrag


def test_get_returns_none_for_unknown_ids():
    assert le.get(BESTAND, "LL-S999-9") is None


def test_spans_cover_every_entry():
    assert sorted(le.entry_spans(BESTAND)) == ["LL-S112-1", "LL-S113-1", "LL-S113-2"]


# --- ID-Vergabe --------------------------------------------------------------
def test_next_id_continues_the_session_series():
    assert le.next_id(BESTAND, 113) == "LL-S113-3"


def test_next_id_starts_at_one_for_a_fresh_session():
    assert le.next_id(BESTAND, 114) == "LL-S114-1"


# --- Format ------------------------------------------------------------------
def test_bullet_matches_the_canonical_shape():
    bullet = le.format_entry("LL-S114-1", **FELDER)
    erste = bullet.splitlines()[0]
    assert erste == "- **[MITTEL] [PROZESS] [Testing] LL-S114-1 – Neuer Titel**"


def test_bullet_carries_all_four_body_lines():
    zeilen = le.format_entry("LL-S114-1", **FELDER).splitlines()[1:]
    assert [z.split(":")[0].strip() for z in zeilen] == ["Quelle", "Was", "Warum", "Regel"]
    assert all(z.startswith("  ") for z in zeilen)


def test_generated_bullet_is_found_by_the_own_parser():
    """Rundlauf: Was `format_entry` schreibt, muss `entry_spans` wiederfinden."""
    neu, lid = le.add(BESTAND, 114, **FELDER)
    assert le.get(neu, lid) is not None


def test_rejects_unknown_impact_and_category():
    for feld, wert in (("impact", "SEHR HOCH"), ("kategorie", "SONSTIGES")):
        try:
            le.format_entry("LL-S114-1", **{**FELDER, feld: wert})
        except ValueError:
            continue
        raise AssertionError(f"ungültiger Wert für {feld} wurde akzeptiert")


def test_rejects_empty_required_texts():
    for feld in ("titel", "was", "warum", "regel"):
        try:
            le.format_entry("LL-S114-1", **{**FELDER, feld: "  "})
        except ValueError:
            continue
        raise AssertionError(f"leeres {feld} wurde akzeptiert")


# --- Anhängen ----------------------------------------------------------------
def test_add_appends_into_the_existing_session_section():
    neu, lid = le.add(BESTAND, 113, **FELDER)
    assert lid == "LL-S113-3"
    abschnitt_start, abschnitt_ende = le.session_heading_span(neu, 113)
    assert lid in neu[abschnitt_start:abschnitt_ende]


def test_add_does_not_disturb_the_following_session():
    neu, _ = le.add(BESTAND, 113, **FELDER)
    assert le.get(neu, "LL-S112-1") == le.get(BESTAND, "LL-S112-1")
    assert "## Session 112 – 2026-07-31" in neu


def test_add_keeps_existing_entries_of_the_same_session():
    neu, _ = le.add(BESTAND, 113, **FELDER)
    assert le.get(neu, "LL-S113-1") == le.get(BESTAND, "LL-S113-1")


def test_add_creates_the_section_when_the_session_is_new():
    neu, lid = le.add(BESTAND, 114, heute="2026-08-03", **FELDER)
    assert "## Session 114 – 2026-08-03" in neu
    assert lid == "LL-S114-1"
    assert le.get(neu, lid) is not None


def test_new_section_is_appended_at_the_end():
    neu, _ = le.add(BESTAND, 114, heute="2026-08-03", **FELDER)
    assert neu.index("## Session 114") > neu.index("## Session 112")


def test_blank_line_separates_appended_entries():
    neu, lid = le.add(BESTAND, 113, **FELDER)
    vorher = neu.split(f"{lid} –")[0]
    assert vorher.endswith("\n\n- **[MITTEL] [PROZESS] [Testing] ")


# --- Session-Abschnitt -------------------------------------------------------
def test_session_span_is_none_for_an_unknown_session():
    assert le.session_heading_span(BESTAND, 999) is None


def test_session_span_ends_before_the_next_heading():
    start, ende = le.session_heading_span(BESTAND, 113)
    abschnitt = BESTAND[start:ende]
    assert "LL-S113-2" in abschnitt
    assert "LL-S112-1" not in abschnitt


# --- CM-Bezug ----------------------------------------------------------------
# `process.md` verlangt für jedes KRITISCH-/HOCH-Finding einen Countermeasure-Eintrag; der
# Bezug entsteht bei der Erfassung, wo der Kontext noch frisch ist, statt in der Retro.
def _mit(**abweichung) -> dict:
    return {**FELDER, **abweichung}


def test_high_impact_requires_a_cm_reference():
    for impact in ("HOCH", "KRITISCH"):
        try:
            le.format_entry("LL-S114-1", **_mit(impact=impact))
        except ValueError:
            continue
        raise AssertionError(f"{impact} ohne CM-Bezug wurde akzeptiert")


def test_lower_impact_does_not_require_a_cm_reference():
    """Gegenprobe: Ein Fix, der den Bezug pauschal für alle fordert, fällt hier auf."""
    for impact in ("MITTEL", "GERING"):
        le.format_entry("LL-S114-1", **_mit(impact=impact))


def test_cm_reference_appears_as_its_own_body_line():
    zeilen = le.format_entry("LL-S114-1", **_mit(impact="HOCH", cm_bezug="CM-S116-1")).splitlines()
    assert "  CM-Bezug: CM-S116-1" in zeilen
    assert zeilen[-1].startswith("  CM-Bezug:"), "das Feld steht hinter Regel, sonst brechen Parser"


def test_cm_reference_accepts_neu_when_no_measure_exists_yet():
    """Ohne diesen Wert wäre ein Finding ohne passende Bestands-CM nicht erfassbar."""
    bullet = le.format_entry("LL-S114-1", **_mit(impact="HOCH", cm_bezug="neu"))
    assert "  CM-Bezug: neu" in bullet


def test_cm_reference_rejects_free_text():
    """Gegenprobe: Ohne Formprüfung wäre die Pflicht eine Formalie – jeder String erfüllte sie."""
    for wert in ("irgendwas", "siehe oben", "CM", "S116-1", ""):
        try:
            le.format_entry("LL-S114-1", **_mit(impact="HOCH", cm_bezug=wert))
        except ValueError:
            continue
        raise AssertionError(f"ungültiger CM-Bezug '{wert}' wurde akzeptiert")


def test_cm_reference_is_kept_when_given_for_lower_impact():
    bullet = le.format_entry("LL-S114-1", **_mit(impact="MITTEL", cm_bezug="CM-S047-1"))
    assert "  CM-Bezug: CM-S047-1" in bullet


def test_known_cm_ids_are_read_from_the_measures_file():
    """Ein Bezug auf eine nicht existierende CM wäre form-gültig und inhaltlich leer –
    eine tote Referenz. Deshalb kennt das Modul den Bestand."""
    bestand = (
        "# Countermeasures\n\n## Aktive Maßnahmen\n\n"
        "### CM-S116-1 – Titel\n**Impact:** HOCH\n\n"
        "### CM-S078-2 – Anderer Titel\n**Impact:** MITTEL\n"
    )
    assert le.cm_ids(bestand) == {"CM-S116-1", "CM-S078-2"}


def test_cm_ids_ignores_mentions_outside_headings():
    """Gegenprobe: Eine im Fließtext erwähnte ID ist kein Eintrag – sonst gälte jede
    Erwähnung als Existenznachweis und die Prüfung liefe faktisch leer."""
    bestand = "### CM-S116-1 – Titel\n**Maßnahme:** vgl. CM-S999-9 und CM-S888-8.\n"
    assert le.cm_ids(bestand) == {"CM-S116-1"}


def test_entry_with_cm_reference_is_found_by_the_own_parser():
    """Rundlauf: Das neue Feld darf `entry_spans` nicht aus dem Tritt bringen."""
    neu, lid = le.add(BESTAND, 114, **_mit(impact="HOCH", cm_bezug="neu"))
    assert le.get(neu, lid) is not None
    assert "CM-Bezug: neu" in le.get(neu, lid)

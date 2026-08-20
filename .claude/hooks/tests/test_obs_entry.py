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
    zusammen="keiner",
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


# --- Zusammen-erledigen: Pflichtangabe (S122) ------------------------------------------
# Cluster-Bildung im Drain braucht erfasste Verwandtschaft. Sie entsteht nur bei der Erfassung
# verlässlich – dort ist der Kontext frisch. Deshalb Pflichtfeld mit expliziter Negativ-Angabe
# ("keiner") statt optionalem Feld, das schweigend entfällt: Ein fehlendes Feld ist von
# "geprüft, es gibt keine" nicht unterscheidbar.
def test_zusammen_is_written():
    eintrag = oe.format_entry("OBS-S114-1", **{**FELDER, "zusammen": "OBS-S110-1"})
    assert "- Zusammen-erledigen: OBS-S110-1" in eintrag


def test_zusammen_keiner_is_written_explicitly():
    eintrag = oe.format_entry("OBS-S114-1", **{**FELDER, "zusammen": "keiner"})
    assert "- Zusammen-erledigen: keiner" in eintrag


def test_zusammen_is_required():
    import pytest
    with pytest.raises(ValueError, match="Zusammen-erledigen"):
        oe.format_entry("OBS-S114-1", **{**FELDER, "zusammen": ""})


def test_zusammen_rejects_unparseable_value():
    # Freitext wie "vielleicht sowas wie das andere" wäre für den Drain unlesbar und
    # fiele still auf "keine Kante" zurück – also blocken statt verschlucken.
    import pytest
    with pytest.raises(ValueError, match="Zusammen-erledigen"):
        oe.format_entry("OBS-S114-1", **{**FELDER, "zusammen": "das mit den Scripten"})


def test_set_writes_zusammen_into_an_existing_entry():
    # Der Drain muss die Kanten korrigieren können (Skill: „beider Seiten korrigieren") – und
    # Bestands-Einträge ohne das Feld brauchen es nachgetragen. Beides ginge sonst nur per Edit.
    neu = oe.set_fields(BESTAND, "OBS-S110-1", zusammen="OBS-S110-2")
    assert "- Zusammen-erledigen: OBS-S110-2" in oe.get(neu, "OBS-S110-1")


def test_set_inserts_the_field_when_missing():
    # Migrationsfall: Der Eintrag stammt aus der Zeit vor dem Pflichtfeld.
    assert "Zusammen-erledigen" not in BESTAND
    neu = oe.set_fields(BESTAND, "OBS-S110-1", zusammen="keiner")
    eintrag = oe.get(neu, "OBS-S110-1")
    zeilen = [z.split(":")[0] for z in eintrag.splitlines() if z.startswith("- ")]
    # Position wie bei neuen Einträgen: nach Beobachtung, vor der Entscheidung.
    assert zeilen.index("- Beobachtung") < zeilen.index("- Zusammen-erledigen") \
        < zeilen.index("- Entscheidung/Maßnahme")


def test_set_validates_zusammen_like_the_capture_does():
    import pytest
    with pytest.raises(ValueError, match="Zusammen-erledigen"):
        oe.set_fields(BESTAND, "OBS-S110-1", zusammen="irgendwas Unlesbares")


# --- Referenzielle Integrität der Kanten -------------------------------------
# Bewusst KEINE Spiegelung (A<->B): `cluster()` macht die Kante beim Lesen ohnehin ungerichtet,
# eine zweite Kopie könnte nur auseinanderlaufen. Was fehlt, ist die Prüfung, dass das Ziel
# überhaupt existiert – ein Vertipper fällt sonst lautlos aus, weil unbekannte Ziele im Cluster
# stillschweigend verworfen werden.
def test_add_rejects_an_unknown_target():
    import pytest
    with pytest.raises(ValueError, match="OBS-S999-9"):
        oe.add(BESTAND, 114, **{**FELDER, "zusammen": "OBS-S999-9"})


def test_add_accepts_an_existing_target():
    neu, oid = oe.add(BESTAND, 114, **{**FELDER, "zusammen": "OBS-S110-1"})
    assert "- Zusammen-erledigen: OBS-S110-1" in oe.get(neu, oid)


def test_set_rejects_an_unknown_target():
    import pytest
    with pytest.raises(ValueError, match="OBS-S999-9"):
        oe.set_fields(BESTAND, "OBS-S110-1", zusammen="OBS-S999-9")


def test_an_entry_cannot_point_at_itself():
    import pytest
    with pytest.raises(ValueError, match="sich selbst"):
        oe.set_fields(BESTAND, "OBS-S110-1", zusammen="OBS-S110-1")


def test_incoming_edges_are_shown_when_reading_an_entry():
    # Ersetzt die Spiegelung: Wer B liest, sieht die Kante von A – ohne sie zu duplizieren.
    # Auf den Marker prüfen, nicht auf die nackte ID: OBS-S110-2 trägt bereits `Bezug: OBS-S110-1`,
    # ein ID-Vergleich wäre also auch ohne jede Funktion grün.
    text = oe.set_fields(BESTAND, "OBS-S110-1", zusammen="OBS-S110-2")
    gelesen = oe.get(text, "OBS-S110-2")
    assert oe.EINGEHEND_MARKER in gelesen and "OBS-S110-1" in gelesen.split(oe.EINGEHEND_MARKER)[1]


def test_no_incoming_note_without_edges():
    assert oe.EINGEHEND_MARKER not in oe.get(BESTAND, "OBS-S110-1")


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


# --- Vorprägung (OBS-S112-8) -------------------------------------------------
# Die Erfassungsregel verlangt ein lösungsfreies `Entscheidung/Maßnahme`. Kommt eine
# Beobachtung aber vom User und nennt schon eine Maßnahme, blieben nur zwei Wege: tilgen
# (Informationsverlust) oder Ausnahme-Marker (wird zur Routine). Beides trat in S112 zweimal
# und in S115 erneut auf.
#
# Kern der Lösung: Die Information wird nicht getilgt, sondern beim Standardzugriff NICHT
# ausgegeben – denn eine Verifikationspflicht *nach* dem Lesen kommt zu spät. Wer den Volltext
# sieht, ist geprägt, egal was die Regel danach fordert.
VORPRAEGUNG_BESTAND = """## OBS-S115-9 – Etwas ist nicht ideal
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Das Ding klemmt in Fall X.
- Vorprägung: Der User halt Ansatz Z für den richtigen Weg.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
"""


def test_format_entry_writes_the_field_when_given():
    eintrag = oe.format_entry("OBS-S115-1", "T", "User", "MITTEL", "häufig", "TOOLING",
                              "Hook/Script", "Beobachtet.", None, "keiner", vorpraegung="Ansatz Z.")
    assert "- Vorprägung: Ansatz Z." in eintrag


def test_format_entry_omits_the_field_when_absent():
    eintrag = oe.format_entry("OBS-S115-1", "T", "User", "MITTEL", "häufig", "TOOLING",
                              "Hook/Script", "Beobachtet.", None, "keiner")
    assert "Vorprägung" not in eintrag


def test_field_sits_between_observation_and_decision():
    """Reihenfolge ist Teil des Formats – und macht beim Lesen der Datei die Trennung sichtbar."""
    eintrag = oe.format_entry("OBS-S115-1", "T", "User", "MITTEL", "häufig", "TOOLING",
                              "Hook/Script", "Beobachtet.", None, "keiner", vorpraegung="Ansatz Z.")
    zeilen = [z.split(":")[0] for z in eintrag.splitlines() if z.startswith("- ")]
    assert zeilen.index("- Beobachtung") < zeilen.index("- Vorprägung") < zeilen.index("- Entscheidung/Maßnahme")


def test_get_hides_the_field_by_default():
    ausgabe = oe.get(VORPRAEGUNG_BESTAND, "OBS-S115-9")
    assert "Ansatz Z" not in ausgabe
    assert "Beobachtung: Das Ding klemmt" in ausgabe


def test_get_points_to_the_retrieval_command():
    """Verbergen ohne Hinweis wäre stilles Tilgen – der Hinweis ist der Ersatz für das Feld."""
    ausgabe = oe.get(VORPRAEGUNG_BESTAND, "OBS-S115-9")
    assert "Vorprägung" in ausgabe
    assert "--vorprägung" in ausgabe
    assert "OBS-S115-9" in ausgabe


def test_get_reveals_the_field_on_request():
    ausgabe = oe.get(VORPRAEGUNG_BESTAND, "OBS-S115-9", mit_vorpraegung=True)
    assert "Ansatz Z" in ausgabe
    assert "--vorprägung" not in ausgabe


def test_get_stays_silent_for_entries_without_the_field():
    assert "Vorprägung" not in oe.get(BESTAND, "OBS-S110-1")


def test_append_extends_the_observation_in_place():
    """Konsolidierung: Der Drain-Skill verlangt, den tragenden Eintrag zu ERWEITERN.

    Ohne diesen Weg landet jede Konsolidierung im Hand-Edit der ganzen Datei – also im
    Pfad, den die Script-Pflicht gerade vermeiden soll (S115).
    """
    neu = oe.append_beobachtung(BESTAND, "OBS-S110-1", "Zweite Ausprägung (S115): auch bei X.")
    eintrag = oe.get(neu, "OBS-S110-1")
    assert "Zweite Ausprägung (S115): auch bei X." in eintrag
    # Der bestehende Text bleibt vollständig davor stehen.
    alt = oe.get(BESTAND, "OBS-S110-1")
    alte_beobachtung = [z for z in alt.splitlines() if z.startswith("- Beobachtung:")][0]
    assert alte_beobachtung[:-1] in eintrag


def test_append_keeps_the_other_fields_untouched():
    neu = oe.append_beobachtung(BESTAND, "OBS-S110-2", "Nachtrag.")
    eintrag = oe.get(neu, "OBS-S110-2")
    assert "- Status: NEU" in eintrag
    assert "- Bezug: OBS-S110-1" in eintrag


def test_append_stays_on_one_line():
    """Die Beobachtung ist EIN Feld – ein Zeilenumbruch würde das Format brechen."""
    neu = oe.append_beobachtung(BESTAND, "OBS-S110-1", "Nachtrag.")
    zeilen = [z for z in neu.splitlines() if z.startswith("- Beobachtung:")]
    assert len(zeilen) == 2  # unverändert: je Eintrag genau eine
    assert all("Nachtrag." not in z or z.startswith("- Beobachtung:") for z in neu.splitlines())


def test_append_takes_the_text_literally():
    text = r"Muster `//\s*ADR-` und Gruppe \1."
    neu = oe.append_beobachtung(BESTAND, "OBS-S110-1", text)
    assert text in oe.get(neu, "OBS-S110-1")


def test_append_rejects_unknown_ids():
    try:
        oe.append_beobachtung(BESTAND, "OBS-S999-9", "x")
    except ValueError as fehler:
        assert "OBS-S999-9" in str(fehler)
    else:
        raise AssertionError("unbekannte ID wurde akzeptiert")


def test_set_takes_the_value_literally_not_as_regex_template():
    """Der Wert ist Text, kein Ersetzungs-Template.

    In S115 blockierte das eine Drain-Eintragung: Ein Wert mit `\\s` (aus einem zitierten
    Regex) brach mit „bad escape“ ab. Der stillere Fall ist schlimmer – `\\1` wäre klanglos
    durch eine Regex-Gruppe ersetzt worden, also Datenkorruption statt Fehler.
    """
    wert = r"Muster war `//\s*ADR-` und Gruppe \1, Pfad C:\temp"
    neu = oe.set_fields(BESTAND, "OBS-S110-1", entscheidung=wert)
    assert f"- Entscheidung/Maßnahme: {wert}" in oe.get(neu, "OBS-S110-1")


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

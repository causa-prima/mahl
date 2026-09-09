"""Tests für tracker_entry.py – die gemeinsame Basis der Abschnitts-Tracker.

Warum es sie gibt (OBS-S120-2): Fünf Dokumente tragen strukturierte Einträge mit
Pflichtfeldern und IDs, und jedes löste Parsing, ID-Vergabe und Feld-Ersetzung neu. Zwei
davon – `open-questions.md` und `tech-debt.md` – sind bis auf Feldnamen und Prüfung
identisch aufgebaut: H2-Kopfzeile mit ID und Titel, `**Feld:**`-Zeilen, `---` als Trenner,
dieselbe Fälligkeits-Grammatik.

Bewusste Grenze: `observations.md` und `lessons_learned.md` haben ein anderes Eintragsformat
(`- Feld:` bzw. eine Bullet-Kopfzeile) und bleiben eigenständig. Sie hier mit einzupassen
hieße, die Basis um Sonderfälle aufzublähen, bis sie nichts mehr vereinfacht – das wäre eine
Vereinheitlichung auf dem Papier.
"""
from importlib import import_module

import pytest

te = import_module("prozesscode.tracker_entry")

SPEC = te.TrackerSpec(
    datei="docs/test.md",
    praefix="XX",
    felder=("Alpha", "Beta"),
)

BESTAND = """# Titel

<!-- Header -->

## XX-S100-1 — Erster
**Alpha:** eins
**Beta:** zwei

---

## XX-S100-2 — Zweiter
**Alpha:** drei
**Beta:** vier
"""


# --- Lesen -------------------------------------------------------------------
def test_get_liefert_den_eintrag():
    assert "eins" in te.get(SPEC, BESTAND, "XX-S100-1")


def test_get_liefert_nur_diesen_eintrag():
    """Gegenprobe – sonst wäre `get` ein verkappter Vollread."""
    assert "drei" not in te.get(SPEC, BESTAND, "XX-S100-1")


def test_get_unbekannte_id_ist_none():
    assert te.get(SPEC, BESTAND, "XX-S999-9") is None


def test_get_liefert_die_dokument_trennlinie_nicht_mit():
    """`---` trennt Einträge, es gehört keinem – im Volltext eines Eintrags stört es nur."""
    assert not te.get(SPEC, BESTAND, "XX-S100-1").rstrip().endswith("---")


# --- ID-Vergabe --------------------------------------------------------------
def test_next_id_zaehlt_innerhalb_der_session():
    assert te.next_id(SPEC, BESTAND, 100) == "XX-S100-3"


def test_next_id_beginnt_in_neuer_session_bei_eins():
    """Die Klasse aus OBS-S107-1: Wer die höchste bestehende Serie fortsetzt statt die
    laufende Session zu nehmen, nummeriert falsch."""
    assert te.next_id(SPEC, BESTAND, 124) == "XX-S124-1"


# --- Struktur ----------------------------------------------------------------
def test_verrutschtes_feld_faellt_auf():
    kaputt = BESTAND.replace("**Alpha:** eins\n**Beta:**", "**Alpha:** eins **Beta:**")
    with pytest.raises(ValueError):
        te.set_fields(SPEC, kaputt, "XX-S100-1", {"Alpha": "neu"})


def test_intakter_eintrag_bleibt_aenderbar():
    """Gegenprobe: Ein Check, der alles ablehnt, wäre ebenfalls grün."""
    neu = te.set_fields(SPEC, BESTAND, "XX-S100-1", {"Alpha": "neu"})
    assert "**Alpha:** neu" in neu


def test_feldzeile_im_wert_kapert_die_struktur_nicht():
    with pytest.raises(ValueError):
        te.set_fields(SPEC, BESTAND, "XX-S100-1", {"Alpha": "x\n**Beta:** gekapert"})


# --- Ändern ------------------------------------------------------------------
def test_set_laesst_nachbarn_unberuehrt():
    neu = te.set_fields(SPEC, BESTAND, "XX-S100-1", {"Alpha": "neu"})
    assert te.get(SPEC, neu, "XX-S100-2") == te.get(SPEC, BESTAND, "XX-S100-2")


def test_set_unbekanntes_feld_scheitert():
    with pytest.raises(ValueError):
        te.set_fields(SPEC, BESTAND, "XX-S100-1", {"Gamma": "x"})


def test_set_ersetzt_den_titel():
    """Der Titel ist der Kurztitel, unter dem der Eintrag im Gespräch läuft – taugt er nicht,
    wird er korrigiert statt ein zweiter Name danebengestellt."""
    neu = te.set_fields(SPEC, BESTAND, "XX-S100-1", {}, titel="Besserer Name")
    assert "## XX-S100-1 — Besserer Name" in neu
    assert "## XX-S100-1 — Erster" not in neu
    assert te.get(SPEC, neu, "XX-S100-2") == te.get(SPEC, BESTAND, "XX-S100-2")


def test_set_leerer_titel_scheitert():
    with pytest.raises(ValueError):
        te.set_fields(SPEC, BESTAND, "XX-S100-1", {}, titel="  ")


def test_set_wert_bleibt_literal():
    """Regex-Sonderzeichen im Wert dürfen nicht als Ersetzungs-Template wirken."""
    neu = te.set_fields(SPEC, BESTAND, "XX-S100-1", {"Alpha": r"\1 und \s"})
    assert r"\1 und \s" in te.get(SPEC, neu, "XX-S100-1")


# --- Anlegen -----------------------------------------------------------------
def test_add_haengt_unten_an():
    neu, oid = te.add(SPEC, BESTAND, 124, "Dritter", {"Alpha": "a", "Beta": "b"})
    assert oid == "XX-S124-1"
    assert neu.index("XX-S124-1") > neu.index("XX-S100-2")


def test_add_verlangt_alle_pflichtfelder():
    with pytest.raises(ValueError):
        te.add(SPEC, BESTAND, 124, "Dritter", {"Alpha": "a"})


# --- Löschen -----------------------------------------------------------------
def test_remove_entfernt_nur_den_eintrag():
    neu = te.remove(SPEC, BESTAND, "XX-S100-1")
    assert te.get(SPEC, neu, "XX-S100-1") is None
    assert te.get(SPEC, neu, "XX-S100-2") is not None


def test_remove_laesst_keine_trenner_ruine():
    neu = te.remove(SPEC, BESTAND, "XX-S100-1")
    assert "---\n\n---" not in neu
    assert not neu.rstrip().endswith("---")


def test_remove_haelt_den_header():
    neu = te.remove(SPEC, BESTAND, "XX-S100-1")
    assert neu.startswith("# Titel")
    assert "<!-- Header -->" in neu


def test_remove_unbekannte_id_scheitert():
    with pytest.raises(ValueError):
        te.remove(SPEC, BESTAND, "XX-S999-9")


# --- kuerzungen ---------------------------------------------------------------
# Ein `set` ersetzt den ganzen Feldwert. Kennt der Aufrufer nur eine gekürzte Übersicht des
# Felds (`list` zeigt bei einer offenen Frage nur den Anker, nicht die Begründung dahinter),
# überschreibt er unbemerkt Inhalt – in S131 real passiert und nur durch `git diff` gefangen.
# Die Erfolgsmeldung der Tracker-Werkzeuge nennt bis dahin nur, WELCHES Feld geändert wurde.
LANG = "**Alpha:** S150 – verschoben in S130, tragender Trigger bleibt der Wechsel auf .NET 11.\n"
KURZ = "**Alpha:** S150\n"


def test_kuerzung_wird_gemeldet():
    meldungen = te.kuerzungen(LANG, KURZ)
    assert len(meldungen) == 1
    assert "Alpha" in meldungen[0]


def test_meldung_nennt_beide_laengen():
    meldung = te.kuerzungen(LANG, KURZ)[0]
    # Gezählt wird der Feldwert, nicht die Zeile – der `**Feld:**`-Präfix ist kein Inhalt.
    assert "76" in meldung and "4" in meldung


def test_meldung_nennt_den_weg_zum_verlorenen_text():
    assert "git diff" in te.kuerzungen(LANG, KURZ)[0]


def test_meldung_nennt_eintrag_und_feld_lesbar():
    # Erste Fassung gab den Schlüssel als rohes Tupel aus: „('OQ-S119-3', 'Fällig')".
    meldung = te.kuerzungen("## XX-S1-1 — Erster\n" + LANG, "## XX-S1-1 — Erster\n" + KURZ)[0]
    assert "XX-S1-1 · Alpha" in meldung and "(" not in meldung


def test_kleine_kuerzung_ist_kein_befund():
    # Sonst meldet jede Tippfehler-Korrektur – eine Warnung bei jedem Aufruf bedeutet nichts.
    assert te.kuerzungen("**Alpha:** abcdefghij\n", "**Alpha:** abcdefg\n") == []


def test_verlaengerung_ist_kein_befund():
    assert te.kuerzungen(KURZ, LANG) == []


def test_unveraenderter_text_ist_kein_befund():
    assert te.kuerzungen(LANG, LANG) == []


def test_mehrere_felder_werden_einzeln_gemeldet():
    alt = LANG + "**Beta:** " + "y" * 90 + "\n"
    neu = KURZ + "**Beta:** y\n"
    assert len(te.kuerzungen(alt, neu)) == 2


def test_neues_feld_ohne_vorgaenger_ist_kein_befund():
    # Beim `add` gibt es keinen alten Wert – dort ist nichts verloren gegangen.
    assert te.kuerzungen("", LANG) == []


def test_felder_werden_je_eintrag_verglichen():
    """Der Fall, an dem die erste Fassung scheiterte – und mit ihr die ganze Wirkung.

    Eine Tracker-Datei enthält viele Einträge, und jeder trägt dieselben Feldnamen. Wurden die
    Werte dateiweit in ein dict gesammelt, überschrieb der letzte Eintrag alle vorigen: Die
    Kürzung im ERSTEN Eintrag verglich sich gegen den Wert des letzten und fiel durch. Genau
    so blieb die Warnung beim echten `oq set` aus – der Fehler, den sie verhindern sollte,
    trat ein zweites Mal ein.
    """
    alt = ("## XX-S1-1 — Erster\n" + LANG + "\n## XX-S1-2 — Zweiter\n**Alpha:** kurz\n")
    neu = ("## XX-S1-1 — Erster\n" + KURZ + "\n## XX-S1-2 — Zweiter\n**Alpha:** kurz\n")
    meldungen = te.kuerzungen(alt, neu)
    assert len(meldungen) == 1 and "Alpha" in meldungen[0]


def test_gleicher_feldname_in_anderem_eintrag_bleibt_unberuehrt():
    alt = ("## XX-S1-1 — Erster\n**Alpha:** kurz\n\n## XX-S1-2 — Zweiter\n" + LANG)
    neu = ("## XX-S1-1 — Erster\n**Alpha:** kurz\n\n## XX-S1-2 — Zweiter\n" + KURZ)
    assert len(te.kuerzungen(alt, neu)) == 1

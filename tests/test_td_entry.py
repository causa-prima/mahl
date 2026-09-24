"""Tests für td_entry.py – technische Schuld lesen, erfassen, ändern, löschen.

Zwei Dinge sind hier eigen, alles Übrige liegt in `tracker_entry.py`:

  1. Die `Fällig`-Anker-Grammatik (geteilt mit OQ, kanonisch in `td_anchors.py`).
  2. Die Kopplung an `AGENT_MEMORY.md` (OBS-S118-1): `**Fällig:** jetzt` verlangt, dass die
     TD-ID dort unter „Nächste Prioritäten" steht – `tech-debt.md` wird nur situativ gelesen,
     `AGENT_MEMORY.md` bei jedem Session-Start injiziert. Ein „jetzt" ohne diesen Eintrag
     bewegt nichts. Bisher wurde der Punkt von Hand dupliziert; `check-td-capture.py` blockt
     zwar das Fehlen, erzeugt ihn aber nicht.
"""
from importlib import import_module

import pytest

td = import_module("prozesscode.td_entry")

BESTAND = """# Technische Schuld

<!-- Header -->

## TD-S044-1 — STJ/Deserialisierung
**Fällig:** Phase:V1 – URI-Felder.
**Problem:** 400 vs. 500 bei ungültigem URI.
**Behebung:** STJ-Pfad verifizieren.

---

## TD-S089-1 — Coverage-Gate
**Fällig:** jetzt – seit S089 offen.
**Problem:** Branch-Coverage-Gate deaktiviert.
**Behebung:** collect_coverage reaktivieren.
"""

MEMORY = """# Agent Memory

## Nächste Prioritäten

- **Coverage-Gate reaktivieren (TD-S089-1)** — `Fällig: jetzt` · Quelle: `docs/tech-debt.md` → TD-S089-1 · Done: Gate ist grün.

- **Theme ziehen (TD-S083-2)** — `Fällig: Phase:MVP` · Quelle: `docs/tech-debt.md` → TD-S083-2 · Done: 44px.
"""


# --- Lesen und Ändern (Basis) ------------------------------------------------
def test_get_liefert_den_eintrag():
    assert "STJ-Pfad verifizieren" in td.get(BESTAND, "TD-S044-1")


def test_get_liefert_nur_diesen_eintrag():
    assert "Coverage" not in td.get(BESTAND, "TD-S044-1")


def test_set_ersetzt_ein_feld():
    neu = td.set_fields(BESTAND, "TD-S044-1", behebung="anders lösen")
    assert "**Behebung:** anders lösen" in td.get(neu, "TD-S044-1")


def test_remove_entfernt_nur_den_eintrag():
    neu = td.remove(BESTAND, "TD-S044-1")
    assert td.get(neu, "TD-S044-1") is None
    assert td.get(neu, "TD-S089-1") is not None


# --- Anker-Grammatik ---------------------------------------------------------
AUFSCHUB = "Umfang – eigener Umbau"


def test_add_weist_untragfaehigen_anker_ab():
    with pytest.raises(ValueError):
        td.add(BESTAND, 124, titel="X", faellig="irgendwann", problem="P", behebung="B",
               aufschubgrund=AUFSCHUB)


def test_add_akzeptiert_gueltigen_anker():
    """Gegenprobe zum Test darüber."""
    neu, tid = td.add(BESTAND, 124, titel="X", faellig="Phase:MVP – beim Wechsel",
                      problem="P", behebung="B", aufschubgrund=AUFSCHUB)
    assert tid == "TD-S124-1"
    assert td.get(neu, tid) is not None


# --- Aufschubgrund (S133) ----------------------------------------------------
def test_add_schreibt_den_aufschubgrund():
    neu, tid = td.add(BESTAND, 124, titel="X", faellig="Phase:MVP – beim Wechsel",
                      problem="P", behebung="B", aufschubgrund=AUFSCHUB)
    assert f"**Aufschubgrund:** {AUFSCHUB}" in td.get(neu, tid)


def test_add_ohne_tragenden_aufschubgrund_scheitert():
    with pytest.raises(ValueError):
        td.add(BESTAND, 124, titel="X", faellig="Phase:MVP – beim Wechsel",
               problem="P", behebung="B", aufschubgrund="später")


def test_bestandseintrag_ohne_aufschubgrund_bleibt_aenderbar():
    """Das Feld gilt ab S133 – ältere Einträge führen es legitim nicht."""
    neu = td.set_fields(BESTAND, "TD-S044-1", behebung="anders lösen")
    assert "Aufschubgrund" not in td.get(neu, "TD-S044-1")


# --- AGENT_MEMORY-Kopplung (OBS-S118-1) --------------------------------------
def test_jetzt_erkennt_fehlenden_memory_punkt():
    assert td.braucht_memory_punkt("jetzt – sofort")
    assert not td.braucht_memory_punkt("Phase:MVP – später")


def test_memory_punkt_wird_als_platzhalter_erzeugt():
    """Kein Titel, keine Fälligkeit – die leben in tech-debt.md und würden hier driften."""
    neu = td.memory_ergaenzen(MEMORY, "TD-S124-1", "Test ist grün.")
    assert "- TD-S124-1 · Done: Test ist grün." in neu
    assert "**Neuer Posten" not in neu


def test_memory_punkt_steht_bei_den_jetzt_punkten():
    """Die Reihenfolge in AGENT_MEMORY ist die Auswahl – ein `jetzt` hinter einem
    `Phase:MVP` würde die Gruppierung brechen, die den ersten jetzt-Punkt bestimmt."""
    neu = td.memory_ergaenzen(MEMORY, "TD-S124-1", "Grün.")
    assert neu.index("TD-S124-1") < neu.index("TD-S083-2")


def test_platzhalter_zaehlt_bei_der_einfuegeposition_mit():
    """Ein bestehender Platzhalter trägt sein `jetzt` in tech-debt.md – wer nur die
    ausgeschriebenen Punkte zählt, setzt den neuen davor und verschiebt die Rangfolge."""
    kurz = MEMORY.replace(
        "- **Coverage-Gate reaktivieren (TD-S089-1)** — `Fällig: jetzt` · Quelle: "
        "`docs/tech-debt.md` → TD-S089-1 · Done: Gate ist grün.",
        "- TD-S089-1 · Done: Gate ist grün.")
    neu = td.memory_ergaenzen(kurz, "TD-S124-1", "Grün.", BESTAND)
    assert neu.index("TD-S124-1") > neu.index("TD-S089-1")


def test_memory_punkt_wird_entfernt():
    neu = td.memory_entfernen(MEMORY, "TD-S089-1")
    assert "TD-S089-1" not in neu
    assert "TD-S083-2" in neu


def test_ein_selbst_geschriebener_punkt_ist_auch_wieder_entfernbar():
    """Die Kurzform ist die, die das Werkzeug SELBST schreibt – sie muss zurückgehen.

    In S129 tat sie es nicht: `memory_entfernen` suchte `- **…` mit Fettdruck, wie die
    ausgeschriebenen Punkte sie tragen. Der Platzhalter (`- TD-S129-1 · Done: …`) passte
    nicht, die Funktion gab still den unveränderten Text zurück – und `td.py remove` meldete
    trotzdem Erfolg, weil `memory_hat` mit einem anderen Muster arbeitet. Zurück blieb ein
    verwaister Prioritäten-Punkt, der bei jedem Session-Start vorgelegt worden wäre.

    Der Test erzeugt den Punkt bewusst über `memory_ergaenzen`, statt ihn in eine Fixture zu
    schreiben: Eine handgeschriebene Fixture kann von dem abweichen, was das Werkzeug
    erzeugt – und genau diese Abweichung war der Fehler.
    """
    mit = td.memory_ergaenzen(MEMORY, "TD-S129-9", "Fertig.", BESTAND)
    assert "TD-S129-9" in mit
    assert "TD-S129-9" not in td.memory_entfernen(mit, "TD-S129-9")


def test_memory_entfernen_ohne_treffer_aendert_nichts():
    """Gegenprobe: sonst könnte die Funktion beliebig löschen und wäre trotzdem grün."""
    assert td.memory_entfernen(MEMORY, "TD-S999-9") == MEMORY


def test_memory_hat_erkennt_vorhandensein():
    assert td.memory_hat(MEMORY, "TD-S089-1")
    assert not td.memory_hat(MEMORY, "TD-S999-9")


# --- Platzhalter statt Kopie (OBS-S118-1, Variante V3) -----------------------
# Die AGENT_MEMORY-Zeile eines TD-Punkts trägt nur ID und Done-Kriterium; Titel und
# Fälligkeit werden beim Rendern aus tech-debt.md aufgelöst. Damit existiert der Titel nur
# einmal und kann nicht driften, während die Rangfolge – die nirgendwo sonst lebt – in
# AGENT_MEMORY handgepflegt bleibt.
KURZ = """# Agent Memory

## Nächste Prioritäten

- TD-S089-1 · Done: Gate ist grün.
  Zusatzzeile bleibt erhalten.

- **Nicht-TD-Punkt** — `Fällig: jetzt` · Quelle: `docs/open-questions.md` · Done: geklärt.
"""


def test_platzhalter_wird_zur_vollen_zeile_aufgeloest():
    out = td.memory_aufloesen(KURZ, BESTAND)
    assert "**Coverage-Gate (TD-S089-1)**" in out
    assert "`Fällig: jetzt`" in out          # aus tech-debt.md, nicht aus der Zeile
    assert "Done: Gate ist grün." in out


def test_aufloesen_uebernimmt_die_faelligkeit_aus_tech_debt():
    """Der Beleg, dass wirklich aufgelöst und nicht nur umformatiert wird: TD-S044-1 trägt
    `Phase:V1`, was in der AGENT_MEMORY-Zeile nirgends steht."""
    kurz = KURZ.replace("TD-S089-1 · Done: Gate ist grün.", "TD-S044-1 · Done: 400 statt 500.")
    assert "`Fällig: Phase:V1`" in td.memory_aufloesen(kurz, BESTAND)


def test_zusatzzeilen_bleiben_erhalten():
    assert "Zusatzzeile bleibt erhalten." in td.memory_aufloesen(KURZ, BESTAND)


def test_nicht_td_punkte_bleiben_unveraendert():
    """Gegenprobe: Der Auflöser darf nur TD-Platzhalter anfassen."""
    out = td.memory_aufloesen(KURZ, BESTAND)
    assert "- **Nicht-TD-Punkt** — `Fällig: jetzt` · Quelle: `docs/open-questions.md`" in out


def test_unbekannte_id_wird_sichtbar_gemeldet():
    """Ein Platzhalter ohne TD-Eintrag darf nicht still verschwinden – dann stünde ein
    Prioritäten-Punkt ohne Inhalt da und niemand wüsste, dass er fehlt."""
    kurz = KURZ.replace("TD-S089-1", "TD-S999-9")
    out = td.memory_aufloesen(kurz, BESTAND)
    assert "TD-S999-9" in out
    assert "⚠" in out


def test_memory_zeile_ist_die_kurzform():
    zeile = td.memory_zeile("TD-S124-1", "Test ist grün.")
    assert zeile == "- TD-S124-1 · Done: Test ist grün."


def test_erzeugter_punkt_ist_wieder_aufloesbar():
    """Rundlauf: Was `memory_ergaenzen` schreibt, muss `memory_aufloesen` lesen können."""
    geschrieben = td.memory_ergaenzen(KURZ, "TD-S044-1", "STJ", "400 statt 500.")
    assert "**STJ/Deserialisierung (TD-S044-1)**" in td.memory_aufloesen(geschrieben, BESTAND)

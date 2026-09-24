"""Tests für eintrag_felder.py – Felder mit festem Wertebereich, die mehrere Tracker teilen."""
import pytest

from prozesscode import eintrag_felder as ef


# --- Aufschubgrund: warum ein Befund erfasst statt behoben wird (S133) -------------
@pytest.mark.parametrize("wert", [
    "User – im Gespräch auf später gelegt",
    "Umfang - braucht einen eigenen Umbau dreier Hooks",
    "Recherche – Ursache des SIGKILL ungeklärt, mehrere Läufe nötig",
])
def test_aufschubgrund_mit_zulaessigem_wert_und_grund_traegt(wert):
    assert ef.pruefe_aufschubgrund(wert) == wert.strip()


@pytest.mark.parametrize("wert", [
    "",
    "Umfang",                       # Grund fehlt – genau er ist der Zweck des Feldes
    "Umfang –   ",
    "später – keine Zeit",           # kein zulässiger Wert
    "Entscheidung – steht mir nicht zu",  # bewusst verworfen: dann wird gefragt, nicht erfasst
])
def test_aufschubgrund_ohne_wert_oder_grund_wird_abgewiesen(wert):
    with pytest.raises(ValueError):
        ef.pruefe_aufschubgrund(wert)


def test_abweisung_nennt_die_zulaessigen_werte():
    """Die Meldung sagt, was zu tun ist – sonst wird geraten."""
    with pytest.raises(ValueError) as fehler:
        ef.pruefe_aufschubgrund("irgendwann")
    for wert in ef.AUFSCHUB_WERTE:
        assert wert in str(fehler.value)


# --- fett_feldwert: `**Feld:**`-Zeilen von TD und OQ -----------------------------------
def test_feldwert_liefert_den_getrimmten_wert():
    block = "## TD-S1-1 — X\n**Fällig:**  Phase:MVP \n**Problem:** P\n"
    assert ef.fett_feldwert(block, "Fällig") == "Phase:MVP"


def test_feldwert_ist_none_wenn_das_feld_fehlt():
    assert ef.fett_feldwert("**Problem:** P\n", "Fällig") is None


def test_feldwert_zaehlt_nur_am_zeilenanfang():
    """Ein zitiertes `**Fällig:**` im Fließtext ist kein Feld."""
    assert ef.fett_feldwert("**Problem:** siehe **Fällig:** oben\n", "Fällig") is None


def test_feldwert_behandelt_sonderzeichen_im_feldnamen_literal():
    assert ef.fett_feldwert("**Behebung/Trigger:** x\n", "Behebung/Trigger") == "x"
    assert ef.fett_feldwert("**AXB:** x\n", "A.B") is None


# --- aufschub_verstoss: die Hook-Sicht ----------------------------------------------
def test_aufschub_verstoss_meldet_fehlendes_feld():
    assert "fehlt" in ef.aufschub_verstoss(None)


def test_aufschub_verstoss_schweigt_bei_tragendem_wert():
    assert ef.aufschub_verstoss("Umfang – eigener Umbau") is None


# --- Quelle ------------------------------------------------------------------------
@pytest.mark.parametrize("wert", ["User", "Orchestrator", "Subagent",
                                  "Subagent (security-auditor, Review run-8)"])
def test_quelle_einzeln_zulaessig(wert):
    assert ef.pruefe_quelle(wert, kombinierbar=False) == wert


@pytest.mark.parametrize("wert", ["Agent", "", "user", "Orchestrator + User"])
def test_quelle_einzeln_abgewiesen(wert):
    with pytest.raises(ValueError):
        ef.pruefe_quelle(wert, kombinierbar=False)


def test_quelle_kombiniert_nur_wo_erlaubt():
    """OBS kennen gemeinsame Herkunft ('User + Orchestrator'), LL nicht."""
    assert ef.pruefe_quelle("User + Orchestrator", kombinierbar=True) == "User + Orchestrator"


def test_quelle_kombiniert_prueft_jeden_teil():
    with pytest.raises(ValueError):
        ef.pruefe_quelle("User + Agent", kombinierbar=True)


# --- OBS-Status: die Schlüsselwörter, von denen Drain und Archiv abhängen -----------
@pytest.mark.parametrize("wert", [
    "NEU", "UMGESETZT (S114)", "VERWORFEN (kein Bedarf)",
    "IN BEOBACHTUNG bis S140 – nach drei Läufen neu bewerten",
])
def test_obs_status_zulaessig(wert):
    assert ef.pruefe_obs_status(wert) == wert


@pytest.mark.parametrize("wert", [
    "ERLEDIGT",
    "umgesetzt",                    # Drain und Archiv vergleichen nach upper() – aber einheitlich schreiben
    "IN BEOBACHTUNG",               # ohne Termin: obs_parse warnt nur, die Wiedervorlage fiele aus
    "IN BEOBACHTUNG bis irgendwann",
])
def test_obs_status_abgewiesen(wert):
    with pytest.raises(ValueError):
        ef.pruefe_obs_status(wert)

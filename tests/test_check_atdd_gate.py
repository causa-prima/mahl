"""Tests für check-atdd-gate.py – das Gate vor jeder Szenario-Implementierung.

Das Gate entscheidet, ob ein Lauf (`@US-904 run-2`) oder ein Szenario-Tag in `features/`
existiert, und gibt genau die Szenarien aus, die implementiert werden. Ein falscher Treffer
lässt fremde Szenarien in den Lauf, ein falscher Fehlschlag hält ihn auf.

Die Fixtures haben die Form der echten Feature-Dateien (Ausschnitt aus
`features/ingredients.feature`): Feature-Tag, Background, Run-Kommentar über dem Szenario,
mehrere Szenarien je Lauf und ein Szenario ohne Lauf. Die Läufe gegen das echte `features/`
stehen in `test_aufrufpfad_wrapper.py`.
"""
from importlib import import_module

import pytest
from conftest import cli_aufruf

gate = import_module("prozesscode.check-atdd-gate")

ZUTATEN = """\
@US-904
Feature: Zutaten verwalten

  Als Rezept-Sammler möchte ich Zutaten anlegen und löschen,
  damit ich sie in Rezepten nutzen kann.

  Background:
    Given die Anwendung ist gestartet
    And ich navigiere zur Zutaten-Seite

  @US-904-edge-case
  Scenario: Zutaten-Liste ist leer wenn keine Zutaten vorhanden sind
    Given es sind keine Zutaten vorhanden

  # @run-2 · Anlegen·Dialog-Verhalten · Frontend-only
  @US-904-happy-path
  Scenario: Felder sind beim Öffnen des Dialogs leer
    When ich auf "Zutat anlegen" klicke
    Then ist das Name-Feld leer

  # @run-2 · Anlegen·Dialog-Verhalten · Frontend-only
  @US-904-happy-path @US-904-edge-case
  Scenario: Pflichtfelder im Dialog sind als solche markiert
    When ich auf "Zutat anlegen" klicke
    Then ist das Name-Feld als Pflichtfeld markiert

  # @run-5 · Anlegen·Mehrfeld-Validierung · Full-Stack · Singleton
  @US-904-happy-path
  Scenario: Zutat ohne Namen wird abgelehnt
    When ich eine Zutat ohne Namen speichere
    Then sehe ich den Fehler "Name fehlt"
"""

# Eine zweite Story mit derselben Laufnummer – sie darf in keinem US-904-Lauf auftauchen.
REZEPTE = """\
@US-602
Feature: Rezepte verwalten

  # @run-2 · Rezept·Detailansicht · Full-Stack
  @US-602-happy-path
  Scenario: Rezept öffnen
    When ich das Rezept "Pfannkuchen" öffne
"""

# Ein Kopf in der Form von `features/shopping-lists.feature`: Überschriften mit Spiegelstrichen,
# Folgezeilen, ein Absatz ohne Spiegelstrich, Leerkommentare als Trenner, Pfeile in Prosa und
# Regeln mit und ohne Vermerk. Davor ein Kommentar vor dem Feature-Tag (gültiges Gherkin) und eine
# Beschreibungszeile ohne „#", die einen Pfeil und eine Laufnummer enthält – sie ist keine Kopf-Regel.
EINKAUF = """\
# language: de
@US-201
Feature: Einkaufsliste aus den Vormerkungen

  Als Feierabend-Planer möchte ich eine Liste aller benötigten Zutaten sehen.
  Vorbild ist Bring! → Kacheln mit Name und Menge, ab run-2 mit Gesamtmenge.

  # @phase: SKELETON
  #
  # Regeln:
  #   - Übernehmen ERSETZT die Einkaufsliste vollständig – ohne Rückfrage.
  #   - Findet der Server keine Vormerkung, wird die Einkaufsliste leer.
  #     → Integrationstest · run-2
  #   - Nach dem Übernehmen zeigt die Einkaufsliste nie die bisherige Liste.
  #     → Komponententest · run-3
  #   - Ladeverhalten wie auf den übrigen Seiten → Komponententest · run-1, run-2
  #   - Kachel: Name → Menge, wie die Detailansicht seit run-2.
  #     → Komponententest · run-3
  # Offen für den ADR-Check: Scheitert Übernehmen, bleibt die bisherige Liste
  # unverändert. → Integrationstest ·
  # run-2
  #
  # Bekannte Grenzen (SKELETON, im Workshop mit dem User
  # so entschieden):
  #   - Schlägt Übernehmen fehl, bleibt man ohne Meldung auf der Vorgemerkt-Seite.
  #     → Komponententest · run-2
  #   - Eine gelöschte Zutat hat kein spezifiziertes Verhalten, auch nicht in run-2.
  #     → keine (unbestimmt erlaubt)
  #
  # Hinweise für die Step-Implementierung: Reihenfolge Titel → Zutatenfeld → Schritte.

  Background:
    Given die Anwendung ist gestartet

  # @run-2 · Übernehmen · Full-Stack
  @US-201-happy-path
  Scenario: Zutaten übernehmen
    When ich die Zutaten übernehme

  # @run-3 · Übernehmen·Button · Frontend-only · Singleton
  @US-201-edge-case
  Scenario: Button gesperrt
    When ich übernehme
"""

_HINTERGRUND = ("─── ingredients.feature ───\n"
                "  Background:\n"
                "    Given die Anwendung ist gestartet\n"
                "    And ich navigiere zur Zutaten-Seite\n"
                "\n")


@pytest.fixture
def features(tmp_path, monkeypatch):
    (tmp_path / "ingredients.feature").write_text(ZUTATEN, encoding="utf-8")
    (tmp_path / "recipes.feature").write_text(REZEPTE, encoding="utf-8")
    monkeypatch.setattr(gate, "_FEATURES_DIR", tmp_path)
    return tmp_path


# --- Lauf-Modus ---------------------------------------------------------------
@pytest.mark.aufrufpfad("check-atdd-gate")
def test_lauf_gibt_alle_seine_szenarien_mit_background_aus(features, monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, gate, "@US-904", "run-2") == 0
    assert capsys.readouterr().out == (
        "✅  run-2 „Anlegen·Dialog-Verhalten\" (Frontend-only) – 2 Szenario(s) gefunden:\n"
        "\n"
        f"{_HINTERGRUND}"
        "@US-904-happy-path\n"
        "  Scenario: Felder sind beim Öffnen des Dialogs leer\n"
        "    When ich auf \"Zutat anlegen\" klicke\n"
        "    Then ist das Name-Feld leer\n"
        "\n"
        f"{_HINTERGRUND}"
        "@US-904-edge-case @US-904-happy-path\n"
        "  Scenario: Pflichtfelder im Dialog sind als solche markiert\n"
        "    When ich auf \"Zutat anlegen\" klicke\n"
        "    Then ist das Name-Feld als Pflichtfeld markiert\n"
        "\n")


def test_ein_singleton_lauf_traegt_die_markierung(features, monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, gate, "@US-904", "run-5") == 0
    assert capsys.readouterr().out.startswith(
        "✅  run-5 „Anlegen·Mehrfeld-Validierung\" (Full-Stack · Singleton) "
        "– 1 Szenario(s) gefunden:\n\n")


def test_ein_lauf_gehoert_nur_zu_seiner_story(features, monkeypatch, capsys):
    """Dieselbe Laufnummer in einer anderen Story bleibt draußen – ohne Background-Block,
    weil diese Datei keinen hat."""
    assert cli_aufruf(monkeypatch, gate, "@US-602", "run-2") == 0
    assert capsys.readouterr().out == (
        "✅  run-2 „Rezept·Detailansicht\" (Full-Stack) – 1 Szenario(s) gefunden:\n"
        "\n"
        "─── recipes.feature ───\n"
        "@US-602-happy-path\n"
        "  Scenario: Rezept öffnen\n"
        "    When ich das Rezept \"Pfannkuchen\" öffne\n"
        "\n")


def test_lauf_gibt_die_ihm_zugeordneten_kopf_regeln_mit_ueberschrift_aus(
        features, monkeypatch, capsys):
    """Ein Spiegelstrich samt Folgezeilen oder ein Absatz ist eine Regel; sie gehört zum Lauf,
    wenn hinter ihrem letzten Pfeil (dem Vermerk) dessen Nummer steht – auch über einen
    Zeilenumbruch hinweg und neben einer zweiten Nummer. Die Überschrift steht einmal je Gruppe.
    Draußen bleiben: Regeln anderer Läufe, ohne Vermerk, mit der Nummer nur vor dem Pfeil, mit
    Pfeil und Nummer in der Prosa vor dem Vermerk, und die Beschreibung ohne „#"."""
    (features / "shopping-lists.feature").write_text(EINKAUF, encoding="utf-8")
    assert cli_aufruf(monkeypatch, gate, "@US-201", "run-2") == 0
    assert capsys.readouterr().out == (
        "✅  run-2 „Übernehmen\" (Full-Stack) – 1 Szenario(s) gefunden, dazu 4 Kopf-Regel(n):\n"
        "\n"
        "─── shopping-lists.feature ───\n"
        "  Background:\n"
        "    Given die Anwendung ist gestartet\n"
        "\n"
        "@US-201-happy-path\n"
        "  Scenario: Zutaten übernehmen\n"
        "    When ich die Zutaten übernehme\n"
        "\n"
        "─── shopping-lists.feature · Kopf-Regeln ohne Szenario, per Test abzusichern ───\n"
        "  # Regeln:\n"
        "  #   - Findet der Server keine Vormerkung, wird die Einkaufsliste leer.\n"
        "  #     → Integrationstest · run-2\n"
        "  #   - Ladeverhalten wie auf den übrigen Seiten → Komponententest · run-1, run-2\n"
        "  # Offen für den ADR-Check: Scheitert Übernehmen, bleibt die bisherige Liste\n"
        "  # unverändert. → Integrationstest ·\n"
        "  # run-2\n"
        "  # Bekannte Grenzen (SKELETON, im Workshop mit dem User\n"
        "  # so entschieden):\n"
        "  #   - Schlägt Übernehmen fehl, bleibt man ohne Meldung auf der Vorgemerkt-Seite.\n"
        "  #     → Komponententest · run-2\n"
        "\n")


def test_ein_lauf_ohne_kopf_regeln_gibt_nur_seine_szenarien_aus(features, monkeypatch, capsys):
    (features / "shopping-lists.feature").write_text(EINKAUF, encoding="utf-8")
    assert cli_aufruf(monkeypatch, gate, "@US-904", "run-5") == 0
    assert "Kopf-Regel" not in capsys.readouterr().out


def test_ein_vermerk_auf_einen_lauf_ohne_szenario_haelt_das_gate_an(features, monkeypatch, capsys):
    """run-1 hat einen Vermerk, aber kein Szenario: Das Gate prüft weiter nur Szenarien; die
    Regel erscheint nicht (Grenze, CLU-kopf-regeln)."""
    (features / "shopping-lists.feature").write_text(EINKAUF, encoding="utf-8")
    assert cli_aufruf(monkeypatch, gate, "@US-201", "run-1") == 1
    assert "Kopf-Regel" not in capsys.readouterr().out


def test_kopf_regeln_einer_anderen_story_bleiben_draussen(features, monkeypatch, capsys):
    (features / "shopping-lists.feature").write_text(EINKAUF, encoding="utf-8")
    assert cli_aufruf(monkeypatch, gate, "@US-602", "run-2") == 0
    assert "Kopf-Regel" not in capsys.readouterr().out


def test_ein_unbekannter_lauf_haelt_das_gate_an(features, monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, gate, "@US-904", "run-9") == 1
    assert capsys.readouterr().out == (
        "❌  Kein Szenario mit run-9 unter Feature-Tag @US-904 in features/ gefunden.\n"
        "   Bitte zuerst /gherkin-workshop (Szenario-Clustering) für diese Story ausführen.\n")


# --- Tag-Modus ----------------------------------------------------------------
def test_tag_mit_titel_findet_genau_das_eine_szenario(features, monkeypatch, capsys):
    """Der Titelfilter vergleicht ohne Groß-/Kleinschreibung. Davor stehen ein Szenario ohne
    den Tag und eines mit Tag, aber anderem Titel – beide dürfen die Suche nicht beenden."""
    assert cli_aufruf(monkeypatch, gate, "@US-904-happy-path", "PFLICHTFELDER") == 0
    assert capsys.readouterr().out == (
        "✅  1 Szenario(s) mit Tag @US-904-happy-path gefunden:\n"
        "\n"
        f"{_HINTERGRUND}"
        "@US-904-edge-case @US-904-happy-path\n"
        "  Scenario: Pflichtfelder im Dialog sind als solche markiert\n"
        "    When ich auf \"Zutat anlegen\" klicke\n"
        "    Then ist das Name-Feld als Pflichtfeld markiert\n"
        "\n")


def test_tag_mit_unbekanntem_titel(features, monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, gate, "@US-904-happy-path", "Gibt es nicht") == 1
    assert capsys.readouterr().out == (
        "❌  Kein Szenario mit Tag @US-904-happy-path und Titel 'gibt es nicht' in features/ "
        "gefunden.\n"
        "   Bitte zuerst /gherkin-workshop für die betreffende User Story ausführen.\n")


def test_unbekannter_tag_ohne_titel(features, monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, gate, "@US-999") == 1
    assert capsys.readouterr().out == (
        "❌  Kein Szenario mit Tag @US-999 in features/ gefunden.\n"
        "   Bitte zuerst /gherkin-workshop für die betreffende User Story ausführen.\n")


# --- Aufruffehler -------------------------------------------------------------
def test_ohne_argument_nennt_es_die_verwendung(features, monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, gate) == 1
    ausgabe = capsys.readouterr()
    assert ausgabe.out == ""
    assert ausgabe.err == (
        "Verwendung: check-atdd-gate.py <@tag> [Szenario-Titel] | <@story-tag> run-N\n")


def test_ohne_features_verzeichnis_haelt_das_gate_an(tmp_path, monkeypatch, capsys):
    fehlt = tmp_path / "features"
    monkeypatch.setattr(gate, "_FEATURES_DIR", fehlt)
    assert cli_aufruf(monkeypatch, gate, "@US-904") == 1
    ausgabe = capsys.readouterr()
    assert ausgabe.out == ""
    assert ausgabe.err == f"❌  features/-Verzeichnis nicht gefunden: {fehlt}\n"

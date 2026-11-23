@CROSS-navigation
Feature: Navigation zwischen Seiten

  Jede Hauptseite (Zutaten, Rezepte, Vorgemerkt) ist über die Navigationsleiste erreichbar – nicht
  nur per Direktlink.

  # @phase: SKELETON
  #
  # Querschnittliche Datei nach ADR-S103-1: Wie man von einer Seite zur anderen kommt, gehört
  # keiner einzelnen Story. Kommt eine Seite hinzu, bekommt sie hier ihre Szenarien, ohne dass
  # die Feature-Dateien der Entitäten angepasst werden müssen.
  #
  # „Given das Rezept X existiert": Hinweis für die Step-Implementierung im Kopf von
  # features/recipes.feature.
  #
  # Lauf-Kommentare (anders als in den übrigen Querschnittsdateien): Die Szenarien setzen
  # Läufe von US-602 voraus, und Läufe von US-602 setzen die Navigationsleiste voraus – das
  # lässt sich nur mit Kanten zwischen Läufen ausdrücken, nicht mit einer Kante für die Datei.

  Background:
    Given die Anwendung ist gestartet

  # @run-1 · Navigationsleiste · Frontend-only · braucht:US-602/run-1
  @CROSS-navigation-ingredients-to-recipes
  Scenario: Von der Zutaten-Seite zur Rezepte-Seite navigieren
    Given ich navigiere zur Zutaten-Seite
    When ich in der Navigationsleiste auf "Rezepte" klicke
    Then sehe ich die Rezepte-Seite

  # @run-1 · Navigationsleiste · Frontend-only · braucht:US-602/run-1
  @CROSS-navigation-recipes-to-ingredients
  Scenario: Von der Rezepte-Seite zur Zutaten-Seite navigieren
    Given ich navigiere zur Rezepte-Seite
    When ich in der Navigationsleiste auf "Zutaten" klicke
    Then sehe ich die Zutaten-Seite

  # Nach einem Direktlink im neuen Fenster gibt es keinen Browserverlauf – die Navigationsleiste
  # ist dann der einzige Weg zurück.
  # @run-2 · Navigationsleiste·aus der Detailansicht · Full-Stack · Singleton · braucht:US-602/run-4
  @CROSS-navigation-recipe-to-recipes
  Scenario: Von der Detailansicht eines Rezepts zur Rezept-Liste navigieren
    Given das Rezept "Pfannkuchen" existiert
    And ich habe den Direktlink des Rezepts "Pfannkuchen" in einem neuen Browserfenster geöffnet
    When ich in der Navigationsleiste auf "Rezepte" klicke
    Then sehe ich die Rezept-Liste mit "Pfannkuchen"

  # @run-4 · Navigationsleiste·Vorgemerkt · Frontend-only · Singleton · braucht:US-803/run-1
  @CROSS-navigation-recipes-to-planned
  Scenario: Von der Rezepte-Seite zur Vorgemerkt-Seite navigieren
    Given ich navigiere zur Rezepte-Seite
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    Then sehe ich die Vorgemerkt-Seite

  # Übergangsregel: Ziel ist laut User die Startseite nach US-001 „Geräte-Kontext“ – das Rezept für
  # heute, sonst die Vorgemerkt-Seite (US-803). Bis zu US-001 bleibt es die Rezept-Liste, auch
  # wenn die Vorgemerkt-Seite schon existiert (User-Entscheid im Workshop von US-803).
  # @run-3 · Einstieg · Frontend-only
  @CROSS-navigation-start-page
  Scenario: Ohne Adresse öffnet die Anwendung die Rezepte-Seite
    When ich die Anwendung ohne Pfad öffne
    Then sehe ich die Rezepte-Seite

  # @run-3 · Einstieg · Frontend-only
  @CROSS-navigation-unknown-address
  Scenario: Eine unbekannte Adresse zeigt „Seite nicht gefunden.“ mit Navigationsleiste
    When ich die Adresse "/zutatn" öffne
    Then sehe ich die Meldung "Seite nicht gefunden."
    When ich in der Navigationsleiste auf "Rezepte" klicke
    Then sehe ich die Rezepte-Seite

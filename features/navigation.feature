@CROSS-navigation
Feature: Navigation zwischen Seiten

  Jede Hauptseite (Zutaten, Rezepte) ist über die Navigationsleiste erreichbar – nicht nur per
  Direktlink.

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

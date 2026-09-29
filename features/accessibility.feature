@NFR-accessibility
Feature: Bedienbarkeit per Finger

  Die Anwendung wird überwiegend am Handy bedient – in der Küche, im Laden, oft mit einer Hand.
  Jedes Bedienelement muss sich deshalb mit dem Finger sicher treffen lassen.

  # @phase: SKELETON
  # @braucht: US-904/run-7,US-904/run-2,US-904/run-8
  #
  # Gilt für alle Listen-Seiten – der Test läuft je Seite über deren Page Object (ADR-S112-5), die
  # Kanten decken die gemessenen Zustände der Zutaten-Seite ab: Liste (run-7), Anlege-Dialog (run-2),
  # Undo-Toast (run-8).
  # Anforderung: docs/process/nfr.md (Accessibility); Durchsetzung im Theme: UX-Guideline, Visuelle Baseline.

  @NFR-accessibility-touch
  Scenario: Jedes Bedienelement ist groß genug für die Bedienung per Finger
    Given eine Zutat steht in der Liste
    When ich den Anlege-Dialog öffne, ihn abbreche und die Zutat lösche
    Then misst jedes Bedienelement mindestens 44×44 Pixel – in der Liste, im Anlege-Dialog und neben dem Undo-Toast

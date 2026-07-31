@CROSS-interaction
Feature: Querschnittliches Interaktionsverhalten

  Aktionen, die Daten verändern, verhalten sich überall in der Anwendung gleich –
  unabhängig davon, in welcher Liste oder auf welcher Seite sie ausgelöst werden.

  # Gilt für alle Listen und Seiten – Szenarien nutzen die Zutaten-Seite als Vertreter.
  # Eigene Feature-Datei statt Ablage an einer Story, weil keines dieser Verhalten
  # zutatenspezifisch ist (Muster wie navigation.feature/resilience.feature, ADR-S103-1).
  # Implementierungs-Scope: nach MVP.
  #
  # ACHTUNG – Vollständigkeit NICHT per gherkin-workshop geprüft: Diese Szenarien stammen aus
  # Review-Findings und einem tech-debt-Durchgang, nicht aus einer systematischen Zustandsraum-
  # Analyse. Vor der Implementierung einen Workshop-Lauf über diese Datei führen (fehlende
  # Nachbarfälle, Fehlerpfade). Der Anlass für jedes Szenario steht in docs/tech-debt.md.
  #
  # Offen: Die Vertreter-Konvention belegt das Verhalten nur für die eine geprüfte Seite. Womit
  # sichergestellt wird, dass andere Seiten es ebenfalls zeigen – dieselbe Komponente statt
  # nachgebautem Verhalten –, ist noch nicht festgelegt.

  @CROSS-interaction-pending
  Scenario: Rückgängig ist während des Wiederherstellens deaktiviert
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    And ich im Toast auf "Rückgängig" klicke
    Then ist "Rückgängig" deaktiviert solange die Antwort aussteht

  @CROSS-interaction-pending
  Scenario: Zwei gleichzeitige Löschvorgänge sperren beide Zeilen
    Given die Zutaten "Mehl" und "Zucker" existieren
    When ich bei "Mehl" auf Löschen klicke
    And ich bei "Zucker" auf Löschen klicke solange die Antwort für "Mehl" aussteht
    Then ist der Löschen-Button von "Mehl" deaktiviert solange dessen Antwort aussteht
    And ist der Löschen-Button von "Zucker" deaktiviert solange dessen Antwort aussteht

  @CROSS-interaction-feedback
  Scenario: Der Undo-Toast lässt sich manuell schließen
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    And ich im Toast auf Schließen klicke
    Then sehe ich den Toast "Mehl gelöscht" nicht mehr
    And ist "Mehl" weiterhin gelöscht

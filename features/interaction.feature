@CROSS-interaction
Feature: Querschnittliches Interaktionsverhalten

  Aktionen, die Daten verändern, verhalten sich überall in der Anwendung gleich –
  unabhängig davon, in welcher Liste oder auf welcher Seite sie ausgelöst werden.

  # @phase: V1
  # @braucht: CROSS-interaction/run-1
  #
  # Gilt für alle Listen und Seiten – Szenarien nutzen die Zutaten-Seite als Vertreter.
  # Eigene Feature-Datei statt Ablage an einer Story, weil keines dieser Verhalten
  # zutatenspezifisch ist (Muster wie navigation.feature/resilience.feature, ADR-S103-1).
  #
  # Ein Vertreter belegt das Verhalten nur für die eine geprüfte Seite. Dass andere Seiten es
  # ebenfalls zeigen, sichert ADR-S112-5: geteilte Implementierung statt nachgebautem Verhalten,
  # nachgewiesen durch eine Suite, die je Seite über ein Page Object läuft
  # (Client/e2e/interaction.spec.ts). Szenarien dieser Datei gehören in diese Suite; auf einer
  # anderen Seite stehen deren Beschriftungen (z.B. „Entfernen" statt „Löschen").
  #
  # Die Läufe run-1 bis run-3 stammen aus US-904 (dort run-8, run-2 und run-9), sind per
  # gherkin-workshop geprüft und umgesetzt; sie tragen ihre Phase und ihre Vorgänger am Run-Tag.
  # run-4 kam aus dem Review von US-803 run-5 (ein Rennen zwischen Löschen und Rückgängig), vom User
  # freigegeben.
  #
  # ACHTUNG – Vollständigkeit der Szenarien OHNE Run-Tag NICHT per gherkin-workshop geprüft: Sie
  # stammen aus Review-Findings und einem tech-debt-Durchgang, nicht aus einer systematischen
  # Zustandsraum-Analyse. Vor ihrer Implementierung einen Workshop-Lauf über diese Datei führen
  # (fehlende Nachbarfälle, Fehlerpfade). Der Anlass für jedes steht in docs/tech-debt.md. Alle
  # drei setzen Löschen samt Undo-Toast voraus – das ist run-1.

  Background:
    Given die Anwendung ist gestartet
    And ich navigiere zur Zutaten-Seite

  # @run-1 · Löschen·Undo-Toast · Full-Stack · Phase:SKELETON · braucht:US-904/run-7
  @CROSS-interaction-undo
  Scenario: Zutat löschen
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    Then ist die Zutaten-Liste leer
    And sehe ich den Toast "Mehl gelöscht" mit "Rückgängig"-Aktion

  # @run-1 · Löschen·Undo-Toast · Full-Stack · Phase:SKELETON · braucht:US-904/run-7
  @CROSS-interaction-undo
  Scenario: Löschen rückgängig machen via Toast
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    And ich im Toast auf "Rückgängig" klicke
    Then sehe ich "Mehl" in der Zutaten-Liste mit Einheit "g"
    And ist der Toast "Mehl gelöscht" nicht mehr sichtbar

  # @run-1 · Löschen·Undo-Toast · Full-Stack · Phase:SKELETON · braucht:US-904/run-7
  @CROSS-interaction-undo
  Scenario: Undo-Toast bleibt bei einem Klick daneben erhalten
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    And ich neben den Toast klicke
    Then sehe ich weiterhin den Toast "Mehl gelöscht" mit "Rückgängig"-Aktion

  # @run-1 · Löschen·Undo-Toast · Full-Stack · Phase:SKELETON · braucht:US-904/run-7
  @CROSS-interaction-undo
  Scenario: Zweites Löschen gibt dem neuen Toast die volle Rückgängig-Zeit
    Given die Zutaten "Mehl" und "Zucker" existieren
    When ich bei "Mehl" auf Löschen klicke
    And ich kurz vor Ablauf der Toast-Anzeigezeit bei "Zucker" auf Löschen klicke
    Then sehe ich den Toast "Zucker gelöscht" mit "Rückgängig"-Aktion
    And ist "Rückgängig" für "Zucker" noch verfügbar, nachdem die Anzeigezeit des ersten Toasts abgelaufen wäre

  # @run-1 · Löschen·Undo-Toast · Full-Stack · Phase:SKELETON · braucht:US-904/run-7
  @CROSS-interaction-undo
  Scenario: Nur der zuletzt gelöschten Zutat lässt sich das Löschen rückgängig machen
    Given die Zutaten "Mehl" und "Zucker" existieren
    When ich bei "Mehl" auf Löschen klicke
    And ich bei "Zucker" auf Löschen klicke
    And ich im Toast auf "Rückgängig" klicke
    Then sehe ich "Zucker" in der Zutaten-Liste
    And ist die Zutat "Mehl" weiterhin gelöscht

  # @run-2 · Anlegen·Pending · Frontend-only · Phase:SKELETON · braucht:US-904/run-2
  @CROSS-interaction-pending
  Scenario: Speichern-Button ist während des Speicherns deaktiviert
    When ich auf "Zutat anlegen" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then ist der "Speichern"-Button deaktiviert solange die Antwort aussteht

  # @run-2 · Anlegen·Pending · Frontend-only · Phase:SKELETON · braucht:US-904/run-2
  @CROSS-interaction-pending
  Scenario: Abbrechen ist während des Speicherns deaktiviert
    When ich auf "Zutat anlegen" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then ist der "Abbrechen"-Button deaktiviert solange die Antwort aussteht

  # @run-2 · Anlegen·Pending · Frontend-only · Phase:SKELETON · braucht:US-904/run-2
  @CROSS-interaction-pending
  Scenario: Der Dialog lässt sich während des Speicherns nicht per Escape schließen
    When ich auf "Zutat anlegen" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And ich auf "Speichern" klicke
    And ich Escape drücke
    Then ist der "Zutat anlegen"-Dialog weiterhin geöffnet solange die Antwort aussteht

  # @run-2 · Anlegen·Pending · Frontend-only · Phase:SKELETON · braucht:US-904/run-2
  @CROSS-interaction-pending
  Scenario: Der Dialog lässt sich während des Speicherns nicht per Backdrop-Klick schließen
    When ich auf "Zutat anlegen" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And ich auf "Speichern" klicke
    And ich neben den Dialog klicke
    Then ist der "Zutat anlegen"-Dialog weiterhin geöffnet solange die Antwort aussteht

  # @run-3 · Löschen·Pending · Frontend-only · Singleton · Phase:SKELETON · braucht:run-1
  @CROSS-interaction-pending
  Scenario: Löschen-Button ist während des Löschens deaktiviert
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    Then ist der Löschen-Button für "Mehl" deaktiviert solange die Antwort aussteht

  # @run-4 · Löschen·Rückgängig während des Löschens · Full-Stack · Singleton · Phase:SKELETON · braucht:run-1
  @CROSS-interaction-undo
  Scenario: Rückgängig während das Löschen noch läuft stellt die Zutat dauerhaft wieder her
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    And ich im Toast auf "Rückgängig" klicke, solange die Antwort für das Löschen aussteht
    And ich die Seite neu lade
    Then sehe ich "Mehl" in der Zutaten-Liste mit Einheit "g"

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

@US-904
Feature: Zutaten verwalten

  Als Rezept-Sammler möchte ich Zutaten anlegen und löschen,
  damit ich sie in Rezepten nutzen kann.

  # Scope SKELETON: Create, Read (Liste), Delete.
  # Update (Bearbeiten) und Tags: V1-Scope.

  # kein Auth-Gate in SKELETON-Scope
  Background:
    Given die Anwendung ist gestartet
    And ich navigiere zur Zutaten-Seite

  @US-904-happy-path
  Scenario: Zutaten-Liste ist leer wenn keine Zutaten vorhanden sind
    Given es sind keine Zutaten vorhanden
    Then sehe ich den Hinweis "Noch keine Zutaten angelegt."
    And sehe ich den Button "Zutat anlegen"

  @US-904-happy-path
  Scenario: Zutat anlegen
    When ich auf "Zutat anlegen" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich "Tomaten" in der Zutaten-Liste mit Einheit "Stück"

  @US-904-happy-path
  Scenario: Mehrere Zutaten erscheinen alphabetisch sortiert
    Given die Zutat "Zwiebel" mit Einheit "Stück" existiert
    And die Zutat "Apfel" mit Einheit "Stück" existiert
    When ich auf "Zutat anlegen" klicke
    And ich "Mehl" als Name eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then zeigt die Zutaten-Liste in dieser Reihenfolge: "Apfel", "Mehl", "Zwiebel"

  @US-904-happy-path
  Scenario: Zutat löschen
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    Then ist die Zutaten-Liste leer
    And sehe ich den Toast "Mehl gelöscht" mit "Rückgängig"-Aktion

  @US-904-happy-path
  Scenario: Löschen rückgängig machen via Toast
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    And ich im Toast auf "Rückgängig" klicke
    Then sehe ich "Mehl" in der Zutaten-Liste mit Einheit "g"

  @US-904-happy-path
  Scenario: Speichern-Button ist während des Speicherns deaktiviert
    When ich auf "Zutat anlegen" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then ist der "Speichern"-Button deaktiviert solange die Antwort aussteht

  @US-904-happy-path
  Scenario: Löschen-Button ist während des Löschens deaktiviert
    Given nur die Zutat "Mehl" mit Einheit "g" existiert
    When ich bei "Mehl" auf Löschen klicke
    Then ist der Löschen-Button für "Mehl" deaktiviert solange die Antwort aussteht

  @US-904-error
  Scenario: Zutat mit leerem Namen anlegen schlägt fehl
    When ich auf "Zutat anlegen" klicke
    And ich keinen Namen eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Name darf nicht leer sein."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Zutat mit Namen aus nur Leerzeichen anlegen schlägt fehl
    When ich auf "Zutat anlegen" klicke
    And ich "   " als Name eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Name darf nicht leer sein."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Zutat mit leerer Einheit anlegen schlägt fehl
    When ich auf "Zutat anlegen" klicke
    And ich "Salz" als Name eingebe
    And ich keine Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Einheit darf nicht leer sein."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Zutat mit Einheit aus nur Leerzeichen anlegen schlägt fehl
    When ich auf "Zutat anlegen" klicke
    And ich "Salz" als Name eingebe
    And ich "   " als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Einheit darf nicht leer sein."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Beide Pflichtfelder leer – beide Fehlermeldungen erscheinen gleichzeitig
    When ich auf "Zutat anlegen" klicke
    And ich keinen Namen eingebe
    And ich keine Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Name darf nicht leer sein."
    And sehe ich die Fehlermeldung "Einheit darf nicht leer sein."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Zutat mit zu langem Namen anlegen schlägt fehl
    When ich auf "Zutat anlegen" klicke
    And ich einen Namen mit 31 Zeichen eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Name darf maximal 30 Zeichen lang sein."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Zutat mit zu langer Einheit anlegen schlägt fehl
    When ich auf "Zutat anlegen" klicke
    And ich "Salz" als Name eingebe
    And ich eine Einheit mit 21 Zeichen eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Einheit darf maximal 20 Zeichen lang sein."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Zutat mit bereits vorhandenem Namen anlegen schlägt fehl
    Given die Zutat "Zucker" mit Einheit "g" existiert
    When ich auf "Zutat anlegen" klicke
    And ich "Zucker" als Name eingebe
    And ich "kg" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Eine Zutat mit dem Namen 'Zucker' existiert bereits."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Zutat mit vorhandenem Namen in abweichender Schreibweise anlegen schlägt fehl
    Given die Zutat "Tomaten" mit Einheit "Stück" existiert
    When ich auf "Zutat anlegen" klicke
    And ich "tomaten" als Name eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Eine Zutat mit dem Namen 'tomaten' existiert bereits."
    And die Zutaten-Liste bleibt unverändert

  @US-904-error
  Scenario: Fehlermeldung bei Duplikat zeigt getrimmten Namen
    Given die Zutat "Tomaten" mit Einheit "Stück" existiert
    When ich auf "Zutat anlegen" klicke
    And ich "tomaten " als Name eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Eine Zutat mit dem Namen 'tomaten' existiert bereits."
    And die Zutaten-Liste bleibt unverändert

  # Race-Condition-Szenario: kein UI-Pfad erreichbar; Step mappt auf direkten DELETE /api/ingredients/{id}-Call.
  @US-904-edge-case
  Scenario: Bereits gelöschte Zutat erneut löschen schlägt fehl
    Given die Zutat "Pfeffer" mit Einheit "g" existiert und gelöscht wurde
    When ich den Lösch-Befehl für "Pfeffer" erneut absende
    Then sehe ich die Fehlermeldung "Zutat wurde nicht gefunden."

  @US-904-edge-case
  Scenario: Soft-deleted Zutat erscheint nicht in der Zutaten-Liste
    Given die Zutat "Basilikum" mit Einheit "Bund" existiert und gelöscht wurde
    When ich die Zutaten-Liste betrachte
    Then ist "Basilikum" nicht in der Zutaten-Liste sichtbar

  @US-904-edge-case
  Scenario: Führende und nachfolgende Leerzeichen werden beim Speichern entfernt
    When ich auf "Zutat anlegen" klicke
    And ich "  Oregano  " als Name eingebe
    And ich "  g  " als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich "Oregano" in der Zutaten-Liste mit Einheit "g"

  @US-904-edge-case
  Scenario: Name mit exakt 30 Zeichen wird akzeptiert
    When ich auf "Zutat anlegen" klicke
    And ich einen Namen mit genau 30 Zeichen eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die neue Zutat in der Zutaten-Liste

  @US-904-edge-case
  Scenario: Einheit mit exakt 20 Zeichen wird akzeptiert
    When ich auf "Zutat anlegen" klicke
    And ich "Salz" als Name eingebe
    And ich eine Einheit mit genau 20 Zeichen eingebe
    And ich auf "Speichern" klicke
    Then sehe ich "Salz" in der Zutaten-Liste

  @US-904-edge-case
  Scenario: Gelöschte Zutat mit gleichem Namen anlegen reaktiviert diese
    Given die Zutat "Butter" mit Einheit "g" existiert und gelöscht wurde
    When ich auf "Zutat anlegen" klicke
    And ich "Butter" als Name eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich "Butter" in der Zutaten-Liste mit Einheit "g"

  @US-904-edge-case
  Scenario: Reaktivierung übernimmt neue Einheit
    Given die Zutat "Butter" mit Einheit "Würfel" existiert und gelöscht wurde
    When ich auf "Zutat anlegen" klicke
    And ich "Butter" als Name eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich "Butter" in der Zutaten-Liste mit Einheit "g"

  @US-904-edge-case
  Scenario: Reaktivierung übernimmt neuen Namen bei abweichender Schreibweise
    Given die Zutat "mehl" mit Einheit "g" existiert und gelöscht wurde
    When ich auf "Zutat anlegen" klicke
    And ich "Mehl" als Name eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich "Mehl" in der Zutaten-Liste mit Einheit "g"

  # Einheit im Then bewusst nicht spezifiziert: im Parallelfall ist die Einheit der bereits
  # aktiven Zutat nicht durch diesen Request kontrollierbar (hängt vom parallelen Restore ab).
  # Given "parallel bereits wiederhergestellt": Step mappt auf direkten POST /api/ingredients um Parallelzustand zu simulieren.
  @US-904-edge-case
  Scenario: Reaktivierung gelingt auch wenn Zutat parallel bereits wiederhergestellt wurde
    Given die Zutat "Koriander" mit Einheit "Bund" existiert und gelöscht wurde
    And "Koriander" wurde parallel bereits durch jemand anderen wiederhergestellt
    When ich auf "Zutat anlegen" klicke
    And ich "Koriander" als Name eingebe
    And ich "Bund" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich "Koriander" in der Zutaten-Liste

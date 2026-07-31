@NFR-resilience
Feature: Querschnittliche Fehlerbehandlung

  Das System muss bei technischen Problemen eine verständliche Rückmeldung liefern,
  damit der Nutzer weiß was zu tun ist.
  Daten die aufwändig einzugeben sind, dürfen bei einem Fehler nicht verloren gehen.

  # Gilt für alle Endpoints und Seiten – Szenarien nutzen die Zutaten-Seite als Vertreter.
  # 504-Fehler fallen in die Netzwerkfehler-Kategorie (Server hat Anfrage nie verarbeitet).
  # Implementierungs-Scope: MVP
  #
  # BEWUSST NICHT hier als Szenario geführt – „die UI zeigt keine technischen Fehlerdetails an,
  # falls der Server doch welche sendet". Diese Vorbedingung ist in Produktion realistisch
  # (Fehlkonfiguration), lässt sich in der E2E-Umgebung aber nicht echt herstellen: dort sendet
  # der Server per Konstruktion keine Details, ein E2E-Test müsste die Antwort fälschen. Sie ist
  # ein Querschnitts-/Infra-Test nach der Ausnahme in docs/process/e2e-testing.md (ADR-S106-3)
  # und wird auf Komponentenebene nachgewiesen. Die zugehörigen Anforderungen stehen in
  # docs/process/nfr.md: Anzeige-Seite unter Reliability, Wire-Seite unter Security.

  @NFR-resilience-network
  Scenario: Backend nicht erreichbar beim Laden einer Seite
    Given die Anwendung ist gestartet
    And das Backend ist nicht erreichbar
    When ich zur Zutaten-Seite navigiere
    Then sehe ich den Toast "Server nicht erreichbar. Bitte Verbindung prüfen."
    And die Seite zeigt einen Fehler-Hinweis anstelle der Zutaten-Liste

  @NFR-resilience-server
  Scenario: Backend liefert Serverfehler beim Laden einer Seite
    Given die Anwendung ist gestartet
    And das Backend antwortet mit einem Serverfehler
    When ich zur Zutaten-Seite navigiere
    Then sehe ich den Toast "Ein unerwarteter Fehler ist aufgetreten."
    And die Seite zeigt einen Fehler-Hinweis anstelle der Zutaten-Liste

  @NFR-resilience-network
  Scenario: Backend nicht erreichbar beim Speichern – Formular bleibt offen
    Given die Anwendung ist gestartet
    And ich navigiere zur Zutaten-Seite
    And ich auf "Neue Zutat" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And das Backend ist nicht erreichbar
    When ich auf "Speichern" klicke
    Then sehe ich den Toast "Server nicht erreichbar. Bitte Verbindung prüfen."
    And das Formular bleibt geöffnet mit den eingegebenen Daten

  @NFR-resilience-server
  Scenario: Backend liefert Serverfehler beim Speichern – Formular bleibt offen
    Given die Anwendung ist gestartet
    And ich navigiere zur Zutaten-Seite
    And ich auf "Neue Zutat" klicke
    And ich "Tomaten" als Name eingebe
    And ich "Stück" als Einheit eingebe
    And das Backend antwortet mit einem Serverfehler
    When ich auf "Speichern" klicke
    Then sehe ich den Toast "Ein unerwarteter Fehler ist aufgetreten."
    And das Formular bleibt geöffnet mit den eingegebenen Daten

  # Auth-Scope: kein SKELETON-Scope. Szenario gilt ab MVP (wenn Auth-Gate aktiv ist).
  @NFR-resilience-auth
  Scenario: Sitzung abgelaufen – Weiterleitung zur Anmeldung mit Rückkehr-URL
    Given die Anwendung ist gestartet
    And meine Sitzung ist abgelaufen
    When ich zur Zutaten-Seite navigiere
    Then werde ich zur Anmeldung weitergeleitet
    And nach erfolgreicher Anmeldung kehre ich zur Zutaten-Seite zurück
    And es erscheint kein Fehler-Toast

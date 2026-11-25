@US-803
Feature: Rezepte vormerken

  Als Feierabend-Planer möchte ich Rezepte vormerken,
  damit ich daraus meine Einkaufsliste erstellen kann.

  Nutzungskontext: Geplant wird abends mit wenig Energie, meist am Handy, manchmal am Laptop.
  Man blättert durch die Rezept-Liste und merkt direkt dort vor (spart Klicks), oder nach einem
  Blick in die Detailansicht. Vorgemerkt heißt eingeplant, nicht verbindlich – meist für eine
  Woche, gelegentlich länger, also auch mehr als sieben Rezepte. Danach folgt die Einkaufsliste.
  Korrigiert wird durch Entfernen auf der Vorgemerkt-Seite oder durch erneutes Umschalten.

  # @phase: SKELETON
  # @stufen: SKELETON
  #
  # Begriff: Eine Vormerkung ist ein Rezept, das für die kommenden Tage eingeplant ist (Glossar
  # „Vormerkung“). Sie ersetzt Wochen-Pool, Wochenplan und Plan-Eintrag: ein Konzept, eine
  # Ansicht; der Tag ist ab MVP eine zusätzliche, optionale Eigenschaft.
  #
  # Scope SKELETON: Umschalter in jeder Zeile der Rezept-Liste und in der Detailansicht,
  # Vorgemerkt-Seite (Titel als Link zur Detailansicht, „Entfernen“ mit Rückgängig-Toast,
  # Leerzustand), Eintrag „Vorgemerkt“ in der Navigationsleiste (features/navigation.feature).
  # Ein Rezept ist höchstens einmal vorgemerkt; Vormerken und Entfernen sind idempotent – ein
  # schon vorgemerktes Rezept erneut vormerken gilt als Erfolg (ADR-S153-1).
  #
  # Umschalter: Ein Button mit Symbol und Text, in Rezept-Liste und Detailansicht gleich – nicht
  # vorgemerkt „Vormerken“ mit einer Liste mit Plus, vorgemerkt „Vorgemerkt“ mit einer Liste mit
  # Häkchen in Primärfarbe (Text und Form tragen den Zustand, die Farbe nur zusätzlich). Sein Name
  # für Screenreader nennt das Rezept: „Pfannkuchen vormerken“ bzw. „Pfannkuchen vorgemerkt“. Er
  # zeigt den neuen Zustand erst mit der Antwort des Servers, nicht vorab.
  # Umschalten zeigt keinen Toast. In der Rezept-Liste öffnet der Umschalter nicht die
  # Detailansicht. Solange die Vormerkungen noch laden, zeigen Rezept-Liste und Detailansicht
  # keinen Umschalter.
  #
  # Übergangsregel (gherkin-workshop, „Tiefe je Regel“): Die alphabetische Reihenfolge der
  # Vorgemerkt-Seite löst die MVP-Stufe dieser Story ab (Sortierung nach Tag). Spezifiziert ist
  # nur der Gutfall, keine Grenzfälle (Umlaute, Groß-/Kleinschreibung).
  #
  # Querschnitts-Verträge (ADR-S112-5 – geteilte Implementierung und parametrisierte Suite,
  # keine wiederholten Szenarien hier). Die Vorgemerkt-Seite ist nach der Zutaten-Seite die
  # zweite Seite mit Rückgängig-Toast. Beide teilen die Umsetzung (useDeleteWithUndo, UndoToast);
  # die Szenarien, die Client/e2e/interaction.spec.ts je Seite ausführt – Löschen, Rückgängig,
  # Toast-Lebensdauer, mehrere Toasts, Sperre beim Löschen –, stehen in features/interaction.feature.
  # Die Vorgemerkt-Seite ist in Client/e2e/pages/interactionPages.ts angemeldet und deklariert:
  #   - Rückgängig-Toast und Sperre von „Entfernen“, solange die Anfrage läuft – ja; das Verb
  #     des Toasts („entfernt“ statt „gelöscht“) ist eine Eigenschaft der Seite. Anlege-Dialog:
  #     nicht anwendbar.
  #   - Bedienbarkeit per Finger (@NFR-accessibility-touch): Vorgemerkt-Seite sowie Umschalter in
  #     Rezept-Liste und Detailansicht – gemessen über deren Page Objects (sie warten, bis die
  #     Umschalter erscheinen).
  # Die Szenarien unten prüfen, was nur diese Seite betrifft: das Verb, die Wirkung auf die
  # Rezept-Liste und die alphabetische Wiedereinordnung. Der optimistische Toast (TD-S108-1)
  # bleibt bis zur MVP-Stufe. Wie die Rezeptseiten (dort per Komponententest, nicht in der
  # Suite): Während des Ladens erscheint nicht der Leerzustand; ein technischer Ladefehler zeigt
  # einen Fehlerhinweis, nie den Leerzustand.
  #
  # Bekannte Grenzen (SKELETON, vom User so entschieden):
  #   - Kein Live-Abgleich: Was auf einem anderen Gerät vorgemerkt oder entfernt wird, erscheint
  #     erst nach Neuladen oder Navigieren.
  #   - Schlägt Umschalten fehl (Netz, Server), bleibt der alte Zustand ohne Meldung stehen.
  #     Schlägt Entfernen fehl, erscheint der Toast trotzdem (TD-S108-1), die Zeile bleibt.
  #     Schlägt das Laden der Vormerkungen in Rezept-Liste oder Detailansicht fehl, fehlen die
  #     Umschalter ohne Meldung. Den MVP-Workshop von features/resilience.feature erinnert
  #     dessen Kopf daran.
  #   - Verlassen der Vorgemerkt-Seite schließt einen offenen Toast samt „Rückgängig“ (wie auf
  #     der Zutaten-Seite); der Rückweg ist der Umschalter.
  #   - Der Umschalter hat keine Sperre und keinen Ladezustand, solange die Antwort aussteht
  #     (Abweichung von der UX-Guideline „Sichtbares Feedback“; kommt mit den Pending-Szenarien,
  #     V1). Ein Doppeltipp kann zurückschalten – sichtbar, ein weiterer Tipp korrigiert.
  #   - ADR-S007-1 (Vormerken eines Rezepts, das es nicht gibt, wird abgelehnt) ist über die
  #     Oberfläche nicht erreichbar und hat kein Szenario; Szenario und Prüfung kommen mit US-616
  #     (V1).
  #
  # Für den Workshop der MVP-Stufe dieser Story:
  #   - Tage in derselben Ansicht (Kalender-/Wochendarstellung, Zuordnen per Drag & Drop) und
  #     Planungs-Portion je Vormerkung – ändert Darstellung, Sortierung und Leerzustand der
  #     Vorgemerkt-Seite. Wertebereich des Tags (ADR-S154-1, vom User genannt): höchstens vier
  #     Wochen im Voraus, nicht in der Vergangenheit.
  #   - Ausschalten per Umschalter braucht einen Rückweg, sobald dabei Informationen verloren
  #     gehen (Tag, Portion); „Rückgängig“ muss sie wiederherstellen.
  #   - Vormerken auf einem zweiten Gerät mit abweichendem Tag: Idempotenz ist dann kein stiller
  #     Erfolg mehr.
  #   - Darf dasselbe Rezept an mehreren Tagen vorgemerkt sein? („höchstens einmal“ gilt bisher
  #     nur ohne Tage.)
  #   - Anzahl vorgemerkter Rezepte bzw. „reicht bis Tag x“; zuletzt vorgemerkt; Beliebtheit.
  # Für V1 (US-616 Rezepte löschen): was mit der Vormerkung eines gelöschten Rezepts geschieht.
  #
  # Hinweise für die Step-Implementierung (kein Verhalten): „Given das Rezept X existiert“ wie im
  # Kopf von features/recipes.feature; „Given das Rezept X ist vorgemerkt“ legt es bei Bedarf an.
  # „ich navigiere zur Vorgemerkt-Seite“ ruft die Adresse auf, nicht die Navigationsleiste.
  # „zeigt die Vorgemerkt-Seite genau …“ schließt den Leerzustand-Hinweis „Noch keine Rezepte
  # vorgemerkt.“ aus.

  Background:
    Given die Anwendung ist gestartet

  # @run-1 · Liste·Leerzustand · Full-Stack · Singleton
  @US-803-happy-path
  Scenario: Ohne Vormerkungen zeigt die Vorgemerkt-Seite einen Hinweis
    Given das Rezept "Pfannkuchen" existiert
    And kein Rezept ist vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    Then sehe ich den Hinweis "Noch keine Rezepte vorgemerkt." und den Link "Zur Rezept-Liste"
    When ich auf "Zur Rezept-Liste" klicke
    Then sehe ich die Rezept-Liste mit "Pfannkuchen"

  # @run-3 · Liste · Full-Stack
  @US-803-happy-path
  Scenario: Die Vorgemerkt-Seite zeigt nur die vorgemerkten Rezepte, alphabetisch
    Given die Rezepte "Pfannkuchen", "Spaghetti Bolognese", "Linsensalat" und "Kartoffelsuppe" existieren, in dieser Reihenfolge angelegt
    And die Rezepte "Spaghetti Bolognese", "Kartoffelsuppe" und "Pfannkuchen" sind in dieser Reihenfolge vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    Then zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen", "Spaghetti Bolognese" in dieser Reihenfolge

  # @run-2 · Vormerken · Full-Stack · braucht:CROSS-navigation/run-4
  @US-803-happy-path
  Scenario Outline: Ein Rezept vormerken
    Given die Rezepte "Kartoffelsuppe" und "Pfannkuchen" existieren
    And kein Rezept ist vorgemerkt
    When ich <Ort> öffne
    And ich bei "Pfannkuchen" auf "Vormerken" klicke
    Then <Anzeige>
    And sehe ich weiterhin <Ort>
    And sehe ich keinen Toast
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    Then zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen"
    When ich in der Navigationsleiste auf "Rezepte" klicke
    Then zeigt die Rezept-Liste bei "Pfannkuchen" "Vorgemerkt" und bei "Kartoffelsuppe" "Vormerken"
    When ich die Seite neu lade
    Then zeigt die Rezept-Liste bei "Pfannkuchen" "Vorgemerkt" und bei "Kartoffelsuppe" "Vormerken"

    Examples:
      | Ort                                         | Anzeige                                                                                    |
      | die Rezept-Liste                            | zeigt die Rezept-Liste bei "Pfannkuchen" "Vorgemerkt" und bei "Kartoffelsuppe" "Vormerken" |
      | die Detailansicht des Rezepts "Pfannkuchen" | zeigt der Umschalter "Vorgemerkt"                                                          |

  # @run-4 · Umschalter·Aufheben · Full-Stack
  @US-803-happy-path
  Scenario Outline: Eine Vormerkung per Umschalter aufheben
    Given die Rezepte "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt
    When ich <Ort> öffne
    And ich bei "Pfannkuchen" auf "Vorgemerkt" klicke
    Then <Anzeige>
    And sehe ich weiterhin <Ort>
    And sehe ich keinen Toast
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    Then zeigt die Vorgemerkt-Seite genau das Rezept "Kartoffelsuppe"
    When ich in der Navigationsleiste auf "Rezepte" klicke
    Then zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt"
    When ich die Seite neu lade
    Then zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt"

    Examples:
      | Ort                                         | Anzeige                                                                                    |
      | die Rezept-Liste                            | zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt" |
      | die Detailansicht des Rezepts "Pfannkuchen" | zeigt der Umschalter "Vormerken"                                                           |

  # @run-3 · Liste · Full-Stack
  @US-803-happy-path
  Scenario: Ein vorgemerktes Rezept von der Vorgemerkt-Seite aus öffnen
    Given das Rezept "Pfannkuchen" mit der Zutat "250 g Mehl" ist vorgemerkt
    And das Rezept "Kartoffelsuppe" ist vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich auf "Pfannkuchen" klicke
    Then sehe ich die Detailansicht des Rezepts "Pfannkuchen" mit der Zutat "250 g Mehl"
    And zeigt der Umschalter "Vorgemerkt"

  # @run-5 · Entfernen·Rückgängig · Full-Stack
  @US-803-happy-path
  Scenario: Eine Vormerkung auf der Vorgemerkt-Seite entfernen
    Given die Rezepte "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich bei "Pfannkuchen" auf "Entfernen" klicke
    Then zeigt die Vorgemerkt-Seite genau das Rezept "Kartoffelsuppe"
    And sehe ich den Toast "Pfannkuchen entfernt" mit "Rückgängig"-Aktion
    When ich in der Navigationsleiste auf "Rezepte" klicke
    Then zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken" und bei "Kartoffelsuppe" "Vorgemerkt"
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    And ich die Seite neu lade
    Then zeigt die Vorgemerkt-Seite genau das Rezept "Kartoffelsuppe"

  # @run-5 · Entfernen·Rückgängig · Full-Stack
  @US-803-happy-path
  Scenario: Das Entfernen einer Vormerkung rückgängig machen
    Given die Rezepte "Kartoffelsuppe" und "Pfannkuchen" sind vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich bei "Kartoffelsuppe" auf "Entfernen" klicke
    And ich im Toast auf "Rückgängig" klicke
    Then zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen" in dieser Reihenfolge
    And sehe ich den Toast "Kartoffelsuppe entfernt" nicht mehr
    When ich die Seite neu lade
    Then zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen" in dieser Reihenfolge

  # @run-2 · Vormerken · Full-Stack · braucht:CROSS-navigation/run-4
  # Die Anzeige ist veraltet: Zwischen Laden und Klick hat ein anderes Gerät vorgemerkt. Für den
  # Nutzer ist das Ziel erreicht. (Eine Fehlermeldung für Umschalten gibt es im SKELETON nicht –
  # geprüft wird, dass der Umschalter trotzdem umspringt.)
  @US-803-edge-case
  Scenario: Ein inzwischen anderswo vorgemerktes Rezept vormerken
    Given das Rezept "Pfannkuchen" existiert
    And kein Rezept ist vorgemerkt
    And ich habe die Rezept-Liste geöffnet
    And das Rezept "Pfannkuchen" wird danach auf einem anderen Gerät vorgemerkt
    When ich bei "Pfannkuchen" auf "Vormerken" klicke
    Then zeigt die Rezept-Liste bei "Pfannkuchen" "Vorgemerkt"
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    And ich die Seite neu lade
    Then zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen"

  # @run-4 · Umschalter·Aufheben · Full-Stack
  # Die Anzeige ist veraltet: Zwischen Laden und Klick hat ein anderes Gerät die Vormerkung
  # aufgehoben. Für den Nutzer ist das Ziel erreicht. (Eine Fehlermeldung für Umschalten gibt es im
  # SKELETON nicht – geprüft wird, dass der Umschalter trotzdem umspringt.)
  @US-803-edge-case
  Scenario: Eine inzwischen anderswo aufgehobene Vormerkung aufheben
    Given das Rezept "Pfannkuchen" ist vorgemerkt
    And sonst ist kein Rezept vorgemerkt
    And ich habe die Rezept-Liste geöffnet
    And die Vormerkung von "Pfannkuchen" wird danach auf einem anderen Gerät aufgehoben
    When ich bei "Pfannkuchen" auf "Vorgemerkt" klicke
    Then zeigt die Rezept-Liste bei "Pfannkuchen" "Vormerken"
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    And ich die Seite neu lade
    Then sehe ich den Hinweis "Noch keine Rezepte vorgemerkt."

  # @run-5 · Entfernen·Rückgängig · Full-Stack
  @US-803-edge-case
  Scenario: Die letzte Vormerkung entfernen und zurückholen
    Given das Rezept "Pfannkuchen" ist vorgemerkt
    And sonst ist kein Rezept vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich bei "Pfannkuchen" auf "Entfernen" klicke
    Then sehe ich den Hinweis "Noch keine Rezepte vorgemerkt." und den Link "Zur Rezept-Liste"
    And sehe ich den Toast "Pfannkuchen entfernt" mit "Rückgängig"-Aktion
    When ich im Toast auf "Rückgängig" klicke
    Then zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen"
    And sehe ich den Hinweis "Noch keine Rezepte vorgemerkt." nicht mehr

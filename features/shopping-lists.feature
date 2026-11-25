@US-201
Feature: Einkaufsliste aus den Vormerkungen

  Als Feierabend-Planer möchte ich vor dem Einkauf eine Liste aller benötigten Zutaten sehen,
  damit ich nichts Doppeltes kaufe.

  Nutzungskontext: Der Plan steht, die Rezepte sind vorgemerkt. Freitagmorgen oder am Vorabend
  geht man zu Hause mit dem Handy in einer Hand Vorratsschrank und Kühlschrank durch, zwei bis
  fünf Minuten. Gedacht wird „Was brauche ich diese Woche?" – eine Zutatenliste mit
  Gesamtmengen, nicht nach Rezepten gegliedert. Vorbild ist Bring! (Kacheln mit Name und Menge,
  ADR-S067-1). Die Einkaufsliste ist später auch für andere Artikel da (Frühstück, Drogerie);
  deshalb übernimmt man die Rezept-Zutaten auf der Vorgemerkt-Seite, nicht auf der Einkaufsliste.

  # @phase: SKELETON
  # @stufen: SKELETON
  # @braucht: US-803/run-3
  #
  # Scope SKELETON: Button „Auf die Einkaufsliste" auf der Vorgemerkt-Seite (Name für
  # Screenreader: „Zutaten aller vorgemerkten Rezepte auf die Einkaufsliste"), Seite
  # „Einkaufsliste" mit Eintrag in der Navigationsleiste (features/navigation.feature).
  # Abhaken, Bereich „Zuletzt gekauft" und die Unterscheidbarkeit gekaufter Artikel sind US-303
  # (eigene Feature-Datei); diese Datei spezifiziert nur das Erstellen und Anzeigen.
  #
  # Regeln:
  #   - Übernehmen liest die Vormerkungen auf dem Server zum Zeitpunkt des Klicks und ERSETZT die
  #     Einkaufsliste vollständig – ohne Rückfrage. Danach öffnet sich die Einkaufsliste.
  #   - Nach dem Übernehmen zeigt die Einkaufsliste nie, auch nicht kurz, die bisherige Liste.
  #     → Komponententest · run-2
  #   - Die Einkaufsliste ist eine Momentaufnahme: Spätere Änderungen an den Vormerkungen wirken
  #     erst beim nächsten Übernehmen. Übernehmen selbst ändert die Vormerkungen nicht.
  #   - Findet der Server beim Übernehmen keine Vormerkung (auf einem anderen Gerät alle
  #     entfernt), wird die Einkaufsliste leer und zeigt ihren Leerzustand.
  #     → Integrationstest · run-2
  #   - Eine Zeile je Zutat; die Mengen aller vorgemerkten Rezepte werden addiert. Eine
  #     Rezept-Zutat steht immer in der Einheit ihrer Zutat (ADR-S135-2), es wird nicht
  #     umgerechnet. „Ohne Menge" zählt als 0; steht eine Zutat in allen Rezepten ohne Menge,
  #     steht sie ohne Menge auf der Liste (ADR-S020-1). Die Gesamtmenge darf das Maximum einer
  #     Rezept-Zutat (9999,999) überschreiten – 6000 g und 5000 g Mehl ergeben 11000 g –, hat aber
  #     die Plausibilitätsgrenze 99999,999; darüber scheitert Übernehmen (ADR-S154-2, Grenzfall-
  #     Szenarien: TD-S154-5).
  #   - Anzeige: Name und Menge mit Einheit, Dezimalkomma, ohne Nullen am Ende und ohne
  #     Tausenderpunkt – wie die Mengen der Detailansicht eines Rezepts.
  #   - Zahl und Einheit einer Menge brechen nicht auseinander (geschütztes Leerzeichen) – auf
  #     der Einkaufsliste wie in der Detailansicht eines Rezepts.
  #     → Komponententest · run-2
  #   - Übernehmen lässt die anderen Seiten unberührt: Zurück auf der Vorgemerkt-Seite stehen die
  #     Vormerkungen sofort da, ohne Ladezustand.
  #     → Komponententest · run-2
  #   - Ohne Vormerkungen gibt es keinen Button; die Vorgemerkt-Seite zeigt nur ihren Leerzustand.
  #   - Ladeverhalten wie auf den übrigen Seiten (per Komponententest, nicht in der Suite):
  #     Während des Ladens erscheint nicht der Leerzustand; ein Ladefehler zeigt einen
  #     Fehlerhinweis, nie den Leerzustand.
  #     → Komponententest · run-1
  #   - „Alphabetisch" heißt deutsche Sortierung wie bei allen Listen (ADR-S142-1): Umlaute beim
  #     Grundbuchstaben, Klein- und Großschreibung ohne Vorrang.
  #     → Integrationstest · run-2
  # Invarianten, auch bei zwei gleichzeitigen Übernehmen (zwei Geräte; Umsetzung: ADR-S154-3):
  #   - Scheitert Übernehmen, bleibt die bisherige Einkaufsliste unverändert.
  #     → Integrationstest · run-2
  #   - Jede Zutat steht höchstens einmal auf der Liste – Szenario „Dieselbe Zutat aus mehreren
  #     Rezepten steht einmal mit der Gesamtmenge da"; gleichzeitig sichert es der Primärschlüssel.
  #
  # Übergangsregeln (gherkin-workshop, „Tiefe je Regel"; spezifiziert ist nur der Gutfall):
  #   - Ersetzen beim Übernehmen – löst US-301/US-307 (MVP) ab: Eigene Artikel auf der Liste
  #     dürfen dann nicht verloren gehen.
  #   - Alphabetische Reihenfolge – löst US-302 (V1, Laufweg) ab.
  #   - Leerzustand „Die Einkaufsliste ist leer." mit Link „Zu den vorgemerkten Rezepten" – im
  #     MVP lassen sich Artikel auf der Seite selbst hinzufügen.
  #
  # Querschnitts-Verträge: Die Navigation zur Einkaufsliste steht in features/navigation.feature
  # (ADR-S103-1). Bedienbarkeit per Finger (@NFR-accessibility-touch, ADR-S112-5): Die
  # Einkaufsliste meldet sich in Client/e2e/pages/touchTargetPages.ts an, mit den Zuständen
  # Leerzustand (Link) und Liste; der Button „Auf die Einkaufsliste" wird im Zustand „Liste" der
  # Vorgemerkt-Seite mitgemessen. Die Registries in Client/e2e/pages/interactionPages.ts sind
  # nicht anwendbar (kein Anlege-Dialog, kein Löschen); die Sperre des Buttons steht unten als
  # Szenario dieser Story, weil es ihn nur auf einer Seite gibt.
  #
  # Bekannte Grenzen (SKELETON, vom User so entschieden):
  #   - Erneutes Übernehmen verwirft auch abgehakte Artikel (US-303) ohne Rückfrage.
  #   - Schlägt Übernehmen fehl (Netz, Server), bleibt man ohne Meldung auf der Vorgemerkt-Seite,
  #     der Button wird wieder frei. Den MVP-Workshop von features/resilience.feature erinnert
  #     dessen Kopf daran.
  #     → Komponententest · run-2, run-3
  #   - Eine gelöschte Zutat hat kein spezifiziertes Verhalten – weder in einem vorgemerkten
  #     Rezept beim Übernehmen noch als Eintrag, der schon auf der Einkaufsliste steht (wie in
  #     features/recipes.feature; selten, Wegwerfdaten, erneutes Übernehmen korrigiert).
  #     → keine (unbestimmt erlaubt)
  # Bekannte Grenzen (SKELETON, im Workshop abgeleitet):
  #   - Eine gefüllte Einkaufsliste lässt sich auf diesem Gerät nicht leeren: Ohne Vormerkung gibt
  #     es keinen Button.
  #   - Große Gesamtmengen stehen in der Einheit der Zutat da („11000 g"); Umrechnen in größere
  #     Einheiten kommt mit der Einheiten-Umrechnung.
  #   - Abweichung von der UX-Guideline „Sichtbares Feedback" (Sperren während Pending): Während
  #     das Übernehmen läuft, bleiben „Entfernen" und die Navigation bedienbar. Wer in diesem
  #     Moment entfernt, findet das Rezept je nach Reihenfolge noch auf der Liste; wer die Seite
  #     verlässt, landet trotzdem auf der Einkaufsliste (TD-S154-4).
  #     → keine (unbestimmt erlaubt)
  # Bekannte Grenzen (SKELETON, in der Umsetzung entstanden, vom User bestätigt):
  #   - Momentaufnahme ist nur die Menge: Name und Einheit eines Eintrags kommen beim Anzeigen
  #     von der Zutat. Wird sie danach umbenannt, zeigt die Einkaufsliste schon den neuen Namen.
  #     → keine (unbestimmt erlaubt)
  #
  # Für den Workshop der MVP-Stufe (Einkaufsliste mit eigenen Artikeln, US-301/US-307):
  #   - Übernehmen ergänzt statt zu ersetzen; Zutaten, die schon auf der Liste stehen?
  #   - Je Eintrag festhalten, aus welcher Vormerkung er stammt; dann ließe sich ohne Button
  #     automatisch übernehmen, was noch nicht übernommen ist.
  #   - Einzelne Zutaten bewusst nicht übernehmen (noch vorrätig).
  #   - Name des Buttons überprüfen.
  #   - Kachel-Raster responsive: auf größeren Bildschirmen mehr Kacheln je Zeile als drei, aber
  #     begrenzt, damit die Liste bedienbar bleibt (Wunsch des Users; im MVP oder V1).
  #   - Akzeptanzkriterium „außer Zutaten mit Flag ‚Immer vorrätig'" (US-906): Das
  #     Ausschluss-Szenario hier oder in US-906 entscheiden.
  # Für den Workshop von US-303: Erneutes Übernehmen löscht auch Einträge in „Zuletzt gekauft" –
  # ausdrücklich entscheiden, ob das so bleibt.
  #
  # Hinweise für die Step-Implementierung (kein Verhalten): „Given das Rezept X mit den Zutaten
  # … ist vorgemerkt" legt Zutaten und Rezept bei Bedarf an; keine dieser Zutaten ist „Immer
  # vorrätig". „zeigt die Einkaufsliste genau …" navigiert nicht selbst, liest je Eintrag Name
  # und Menge getrennt (Kachel-Layout) und schließt den Leerzustand aus; „–" als Menge (in der
  # Tabelle wie im Parameter) heißt: keine Menge angezeigt. Klick auf „Auf die Einkaufsliste" und
  # die Prüfung, dass der Button fehlt, nutzen denselben Locator – sonst bestünde die Prüfung auf
  # Abwesenheit auch, wenn der Button da ist (Name für Screenreader siehe oben).

  Background:
    Given die Anwendung ist gestartet

  # @run-1 · Liste·Leerzustand · Full-Stack · Singleton
  @US-201-happy-path
  Scenario: Eine noch nie gefüllte Einkaufsliste zeigt einen Hinweis
    Given das Rezept "Pfannkuchen" ist vorgemerkt
    And die Einkaufsliste ist leer
    When ich zur Einkaufsliste navigiere
    Then sehe ich den Hinweis "Die Einkaufsliste ist leer." und den Link "Zu den vorgemerkten Rezepten"
    When ich auf "Zu den vorgemerkten Rezepten" klicke
    Then zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen"

  # @run-2 · Übernehmen · Full-Stack
  @US-201-happy-path
  Scenario: Die Zutaten der vorgemerkten Rezepte alphabetisch auf die Einkaufsliste übernehmen
    Given das Rezept "Pfannkuchen" mit den Zutaten "250 g Mehl", "0,5 l Milch" und "3 Stück Eier" ist vorgemerkt
    And das Rezept "Kartoffelsuppe" mit den Zutaten "1000 g Kartoffeln" und "Salz" ist vorgemerkt
    And das Rezept "Linsensalat" mit der Zutat "200 g Linsen" existiert und ist nicht vorgemerkt
    And die Einkaufsliste ist leer
    When ich zur Vorgemerkt-Seite navigiere
    And ich auf "Auf die Einkaufsliste" klicke
    Then sehe ich die Einkaufsliste
    And zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge:
      | Zutat      | Menge   |
      | Eier       | 3 Stück |
      | Kartoffeln | 1000 g  |
      | Mehl       | 250 g   |
      | Milch      | 0,5 l   |
      | Salz       | –       |
    When ich die Seite neu lade
    Then zeigt die Einkaufsliste genau dieselben Einträge in derselben Reihenfolge
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    Then zeigt die Vorgemerkt-Seite genau die Rezepte "Kartoffelsuppe", "Pfannkuchen" in dieser Reihenfolge

  # @run-2 · Übernehmen · Full-Stack
  @US-201-happy-path
  Scenario: Dieselbe Zutat aus mehreren Rezepten steht einmal mit der Gesamtmenge da
    Given das Rezept "Pfannkuchen" mit den Zutaten "250 g Mehl" und "0,5 l Milch" ist vorgemerkt
    And das Rezept "Waffeln" mit den Zutaten "300 g Mehl" und "100 g Butter" ist vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich auf "Auf die Einkaufsliste" klicke
    Then zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge:
      | Zutat  | Menge |
      | Butter | 100 g |
      | Mehl   | 550 g |
      | Milch  | 0,5 l |

  # @run-2 · Übernehmen · Full-Stack
  @US-201-happy-path
  Scenario: Die Einkaufsliste bleibt bis zum erneuten Übernehmen unverändert, das sie dann ersetzt
    Given das Rezept "Pfannkuchen" mit den Zutaten "250 g Mehl" und "0,5 l Milch" ist vorgemerkt
    And das Rezept "Kartoffelsuppe" mit den Zutaten "1000 g Kartoffeln" und "Salz" ist vorgemerkt
    And das Rezept "Linsensalat" mit der Zutat "200 g Linsen" existiert
    And die Zutaten der vorgemerkten Rezepte sind auf die Einkaufsliste übernommen
    And danach ist "Kartoffelsuppe" nicht mehr vorgemerkt und "Linsensalat" vorgemerkt
    When ich zur Einkaufsliste navigiere
    Then zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge:
      | Zutat      | Menge  |
      | Kartoffeln | 1000 g |
      | Mehl       | 250 g  |
      | Milch      | 0,5 l  |
      | Salz       | –      |
    When ich in der Navigationsleiste auf "Vorgemerkt" klicke
    And ich auf "Auf die Einkaufsliste" klicke
    Then zeigt die Einkaufsliste genau diese Einträge in dieser Reihenfolge:
      | Zutat  | Menge |
      | Linsen | 200 g |
      | Mehl   | 250 g |
      | Milch  | 0,5 l |
    When ich die Seite neu lade
    Then zeigt die Einkaufsliste genau dieselben Einträge in derselben Reihenfolge

  # @run-3 · Übernehmen·Button · Frontend-only
  # Den Button gibt es nur auf dieser Seite – kein Vertreter-Szenario für features/
  # interaction.feature; die Regel selbst steht in der UX-Guideline „Sichtbares Feedback".
  @US-201-happy-path
  Scenario: „Auf die Einkaufsliste" ist gesperrt, solange das Übernehmen läuft
    Given das Rezept "Pfannkuchen" mit der Zutat "250 g Mehl" ist vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich auf "Auf die Einkaufsliste" klicke
    Then ist "Auf die Einkaufsliste" deaktiviert, solange die Antwort aussteht
    And sehe ich danach die Einkaufsliste
    And zeigt die Einkaufsliste genau den Eintrag "Mehl" mit der Menge "250 g"

  # @run-2 · Übernehmen · Full-Stack
  # „Zucker" in beiden Reihenfolgen: Ein Fehler, der vom ersten Rezept abhängt, fiele sonst nur
  # in einer auf.
  @US-201-edge-case
  Scenario Outline: Zutaten ohne Menge auf der Einkaufsliste
    Given das Rezept "Pfannkuchen" mit der Zutat "<Zeile Pfannkuchen>" ist vorgemerkt
    And das Rezept "Waffeln" mit der Zutat "<Zeile Waffeln>" ist vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich auf "Auf die Einkaufsliste" klicke
    Then zeigt die Einkaufsliste genau den Eintrag "<Zutat>" mit der Menge "<Menge>"

    Examples:
      | Zeile Pfannkuchen | Zeile Waffeln | Zutat  | Menge |
      | 50 g Zucker       | Zucker        | Zucker | 50 g  |
      | Zucker            | 50 g Zucker   | Zucker | 50 g  |
      | Salz              | Salz          | Salz   | –     |

  # @run-2 · Übernehmen · Full-Stack
  @US-201-edge-case
  Scenario Outline: Gesamtmengen stehen in deutscher Schreibweise da
    Given das Rezept "Pfannkuchen" mit der Zutat "<Zeile Pfannkuchen>" ist vorgemerkt
    And das Rezept "Waffeln" mit der Zutat "<Zeile Waffeln>" ist vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    And ich auf "Auf die Einkaufsliste" klicke
    Then zeigt die Einkaufsliste genau den Eintrag "<Zutat>" mit der Menge "<Menge>"

    Examples:
      | Zeile Pfannkuchen | Zeile Waffeln | Zutat | Menge   | Fall                                         |
      | 0,1 l Milch       | 0,2 l Milch   | Milch | 0,3 l   | exakt dezimal addiert                        |
      | 0,125 l Milch     | 0,375 l Milch | Milch | 0,5 l   | keine Nullen am Ende                         |
      | 0,5 l Milch       | 0,5 l Milch   | Milch | 1 l     | ganze Zahl ohne Komma                        |
      | 0,125 l Milch     | 0,25 l Milch  | Milch | 0,375 l | drei Nachkommastellen bleiben                |
      | 6000 g Mehl       | 5000 g Mehl   | Mehl  | 11000 g | über dem Rezept-Maximum, ohne Tausenderpunkt |

  # @run-3 · Übernehmen·Button · Frontend-only
  @US-201-edge-case
  Scenario: Ohne Vormerkungen bietet die Vorgemerkt-Seite kein Übernehmen an
    Given das Rezept "Pfannkuchen" existiert
    And kein Rezept ist vorgemerkt
    When ich zur Vorgemerkt-Seite navigiere
    Then sehe ich den Hinweis "Noch keine Rezepte vorgemerkt." und den Link "Zur Rezept-Liste"
    And sehe ich keinen Button "Auf die Einkaufsliste"

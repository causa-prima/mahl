@US-602
Feature: Rezepte erfassen

  Als Rezept-Sammler möchte ich Rezepte manuell anlegen,
  damit ich auch analoge Rezepte digitalisieren kann.

  Nutzungskontext: Erfasst wird beim Übertragen einer Vorlage (Webseite, Buch) – heute meist am
  Laptop, weil es am Handy umständlich ist; Ziel ist, dass es auch dort leicht geht. Zutaten
  stehen in der Vorlage schon als „Menge Einheit Zutat" und werden zeilenweise abgetippt oder
  eingefügt. Beim Übertragen muss man wiederfinden, wo man in der Vorlage war. Angesehen und
  gekocht wird aus der Detailansicht, am Tablet oder Handy: vor dem Kochen ein Überblick, beim
  Kochen die Stelle wiederfinden, nachdem man weggeschaut hat.

  # @phase: SKELETON
  # @stufen: SKELETON
  #
  # Scope SKELETON: Rezept anlegen (Titel, Zutaten als Freitext, Schritte), Rezept-Liste,
  # Detailansicht, Direktlink. MVP-Stufe dieser Story (Abschnitt unten): Verlassen mit
  # Eingaben, Browserverlauf, Löschsperre für verwendete Zutaten, lange Texte bei Handybreite;
  # Foto und Basis-Portion ohne Szenarien hier. Bearbeiten: US-614 (MVP). Löschen: US-616 (V1).
  # Schritte umsortieren: US-606 (geparkt).
  #
  # Übergangsregel (gherkin-workshop, „Tiefe je Regel"): Das Zutatenfeld samt Zerlegen der
  # Zeilen löst US-607 (MVP) ab – Zutaten je Schritt, Zerlegen beim Bestätigen jeder Zeile,
  # Brüche, Stückzahl ohne Einheit, Modifizierer, fehlende Zutat direkt anlegen, dieselbe Zutat
  # mehrfach. Spezifiziert sind deshalb nur der Gutfall und die typischsten Fehler (gemessen an
  # der Rezeptsammlung des Users: Namen aus mehreren Wörtern, „Pck.", Menge ohne Einheit);
  # anderes Verhalten des Zerlegers ist unbestimmt, das Rezept wird dann nicht gespeichert. Die Mengenwerte (ADR-S020-1) sind stabil und voll spezifiziert.
  #
  # Zutaten: ein mehrzeiliges Feld, eine Zutat je Zeile; leere Zeilen und Zeilen aus Leerraum
  # werden übergangen, die Reihenfolge der Zeilen ist die Reihenfolge im Rezept. Zerlegt wird
  # beim Speichern auf dem Server:
  #   - Beginnt die Zeile mit einer Ziffer, ist das erste Wort die Menge. Gültig ist eine Menge
  #     nur aus Ziffern, optional mit einem Komma und weiteren Ziffern; größer als 0, höchstens
  #     3 Nachkommastellen (Nullen am Ende zählen nicht), höchstens 9999,999.
  #   - Mit Menge: Ist der Rest der Name einer aktiven Zutat, fehlt die Einheit. Sonst ist bei
  #     mehreren Wörtern das erste die Einheit und der Rest die Zutat, ein einzelnes Wort ist die
  #     Zutat; die Einheit muss die Basiseinheit der Zutat sein.
  #   - Ohne Menge: Die ganze Zeile ist die Zutat, ohne Einheit („Salz").
  #   - Namen und Einheiten ohne Unterschied der Groß-/Kleinschreibung; gelöschte Zutaten gelten
  #     als nicht gefunden. Jede Zutat höchstens einmal je Rezept – eine Zeilenprüfung im
  #     Speicher, gemeldet mit den übrigen Zeilenmeldungen (innerhalb des Aggregats; ein
  #     DB-Index wäre höchstens Absicherung, anders als ADR-S105-2 für Namen über Aggregate).
  # Jede fehlerhafte Zeile bekommt genau eine Meldung, die mit der zitierten (normalisierten)
  # Zeile beginnt – ein Textfeld zeigt keine Zeilennummern; alle Meldungen erscheinen gemeinsam
  # in Zeilenreihenfolge. Genannte Namen und Einheiten sind die eingegebenen, die mögliche
  # Einheit ist die gespeicherte. Eine fehlerhafte Zeile zählt nicht als Zutat; „mindestens eine
  # Zutat" meldet nur ein Feld ohne nicht leere Zeile. Das Zitat ist im SKELETON unbegrenzt lang
  # (Querschnitt „Ausgaben begrenzen" folgt im MVP, UX-Guideline „Fehlermeldungen als Hilfe").
  # Bekannte Grenzen (SKELETON):
  #   - Eine Basiseinheit aus mehreren Wörtern („kleine Dose") wird nicht erkannt.
  #   - Wer dem Hinweis „Neue Zutaten werden auf der Zutaten-Seite angelegt." über die
  #     Navigationsleiste folgt oder im Browser zurückgeht, verliert die Eingaben ohne Nachfrage
  #     – die Nachfrage kommt im MVP. Vom User so hingenommen.
  #   - Eine verwendete Zutat lässt sich löschen; die Sperre kommt im MVP. Ein Rezept mit einer
  #     gelöschten Zutat hat kein spezifiziertes Verhalten (selten, Wegwerfdaten – vom User so
  #     entschieden).
  #   - Mehrere Absätze, in ein Schrittfeld eingefügt, ergeben einen Schritt.
  #
  # Schritte: ein mehrzeiliges Feld je Schritt (Enter fügt einen Zeilenumbruch ein, der beim
  # Speichern zu einem Leerzeichen wird – kein versehentliches Absenden), jedes Feld zeigt
  # seine Nummer (beim Übertragen wiederfinden, wo man in der Vorlage war); nach „Schritt
  # hinzufügen" liegt der Fokus im neuen Feld. Alle fehlerhaften Schritte werden gemeldet. Leere
  # Schrittfelder werden nicht mitgeschickt; ein Feld zu leeren ist im SKELETON der Weg, einen
  # Schritt zu entfernen. Die Detailansicht zeigt jeden Schritt als eigenen Eintrag mit seiner
  # Nummer, lückenlos gezählt; Abstand und Form legt der UI-Entwurf fest.
  # Die Rezept-Liste ist alphabetisch sortiert (deutsches Locale, ohne Unterschied der
  # Groß-/Kleinschreibung).
  #
  # Leerraum und unsichtbare Zeichen: Titel, Anweisung und jede Zutatenzeile werden nach der
  # querschnittlichen Regel normalisiert (features/text-input.feature). Als Eingabe für die
  # Nachfrage „Eingaben verwerfen?" zählt ein Feld, das nach dieser Normalisierung nicht leer ist.
  #
  # Meldungen: Alle Meldungen kommen vom Server und erscheinen gemeinsam; sie bleiben bis zum
  # nächsten Speichern stehen. Die Titel-Eindeutigkeit prüft der Server erst, wenn alle übrigen
  # Prüfungen bestanden sind (ADR-S105-2: nur der Unique-Index prüft); ein Hinweis schon beim
  # Verlassen des Titelfelds kommt mit der MVP-Stufe dieser Story (Akzeptanzkriterium dort,
  # Szenarien im Workshop dieser Stufe). Fokus nach einem Fehler: auf das erste fehlerhafte
  # Feld in der Reihenfolge Titel → Zutatenfeld → Schritte.
  # Nachfrage „Eingaben verwerfen?": Beim Öffnen liegt der Fokus auf „Weiter bearbeiten" – ein
  # versehentliches Enter verwirft nichts.
  #
  # Querschnitts-Verträge dieser Seiten (ADR-S112-5 – geteilte Implementierung und
  # parametrisierte Suite, keine wiederholten Szenarien hier). Die Rezeptseiten deklarieren:
  #   - Rezept-Liste und Detailansicht: Während des Ladens erscheint weder der Leerzustand noch
  #     „Rezept nicht gefunden."; ein technischer Ladefehler zeigt einen Fehlerhinweis – nie den
  #     Leerzustand und nie „Rezept nicht gefunden."
  #   - Formular speichern: technischer Fehler lässt das Formular mit allen Eingaben stehen;
  #     während des Speicherns sind „Speichern", „Abbrechen", die Felder, „Schritt hinzufügen"
  #     und das Absenden per Enter gesperrt (ab MVP auch Navigationsleiste und Browser-Zurück –
  #     Szenario im MVP-Abschnitt). Escape und Backdrop: nicht anwendbar, das Formular ist eine
  #     Seite. Ein Speicherergebnis, das erst nach dem Verlassen des Formulars eintrifft (im
  #     SKELETON über Navigationsleiste oder Zurück möglich), löst keine Weiterleitung mehr aus.
  #   - Bedienbarkeit per Finger (@NFR-accessibility-touch): Rezept-Liste, Formular samt
  #     Nachfrage und Detailansicht – gemessen über deren Page Objects.
  # Die bestehende Suite kennt nur Anlege-Dialoge, in denen das Verlassen während des
  # Speicherns gesperrt ist; die Migrationsschritte (4) bis (6) aus ADR-S112-5 werden mit dieser
  # zweiten Seite fällig und nehmen den Fall „Speicherergebnis nach Verlassen" neu in die Suite
  # auf.
  # Navigation zwischen den Seiten über die Navigationsleiste: features/navigation.feature;
  # Wege über Links und Buttons im Seiteninhalt (Liste → Detail, „Rezept anlegen", Abbrechen,
  # „Zur Rezept-Liste") stehen hier. Wie diese Wege den Browserverlauf verändern, legt die
  # MVP-Stufe fest (Abschnitt unten).
  #
  # Paralleles Anlegen eines gleichnamigen Rezepts hat kein eigenes Szenario: Die Eindeutigkeit
  # prüft nur der Server beim Speichern – ob das andere Rezept vor oder während der Erfassung
  # entstand, durchläuft denselben Pfad wie „Titel existiert bereits".
  #
  # Then-Schritte der Edge-Cases – und der Fehler-Szenarien, deren Gegenstand die Form, Zahl
  # oder Reihenfolge der Meldungen oder der Fokus ist – prüfen die jeweils untersuchte
  # Eigenschaft; den übrigen Endzustand prüft der Step-Code (e2e-testing.md, Assertion-Tiefe):
  # nach einem Fehler weiterhin im Formular mit allen Eingaben und Rezept-Liste unverändert,
  # nach einem Erfolg Detailansicht mit allen Eingaben und das Rezept genau einmal in der
  # Rezept-Liste. „genau die Fehlermeldung" heißt: keine weitere Meldung bei den Zutaten.
  #
  # Hinweis für die Step-Implementierung (kein Verhalten), gilt auch für navigation.feature:
  # Ein Rezept braucht mindestens eine Zutat und einen Schritt. „Given das Rezept X existiert"
  # ohne weitere Angaben erfindet beides – mit einer eigenen Zutat, deren Name und Einheit
  # sonst in keinem Schritt und keiner Zeile des Szenarios vorkommen, damit sie weder Szenarien
  # zum Löschen von Zutaten noch das Zerlegen der Zeilen berührt.
  # „… mit der Zutat "250 g Mehl" …" legt eine fehlende Zutat mit der genannten Einheit als
  # Basiseinheit an; „… mit der Zutat "Salz" …" eine ohne Menge mit beliebiger Einheit. Fehlt
  # bei Teilangaben der Schritt („… mit der Zutat "250 g Mehl" an anderer Stelle angelegt"),
  # wird er wie oben erfunden.
  #
  # Der MVP-Abschnitt unten ist eine eigene Sortiereinheit (happy-path → error → edge-case
  # beginnt dort neu).

  Background:
    Given die Anwendung ist gestartet

  # ---------------------------------------------------------------- happy-path

  # @run-1 · Liste·Leerzustand · Full-Stack · Singleton
  @US-602-happy-path
  Scenario: Rezept-Liste ist leer wenn keine Rezepte vorhanden sind
    Given es sind keine Rezepte vorhanden
    When ich zur Rezepte-Seite navigiere
    Then sehe ich den Hinweis "Noch keine Rezepte angelegt."
    And sehe ich den Button "Rezept anlegen"

  # @run-5 · Formular·Öffnen · Frontend-only
  @US-602-happy-path
  Scenario: Felder sind beim Öffnen des Formulars leer
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    Then ist das Titel-Feld leer
    And ist das Zutatenfeld leer
    And gibt es genau ein Schrittfeld, es ist leer und trägt die Nummer 1

  # @run-5 · Formular·Öffnen · Frontend-only
  @US-602-happy-path
  Scenario: Pflichtfelder im Formular sind als solche markiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    Then ist das Titel-Feld als Pflichtfeld markiert
    And ist das Zutatenfeld als Pflichtfeld markiert
    And ist der Abschnitt "Schritte" als Pflichtangabe markiert

  # Die Eingabeform einer Zutatenzeile ist nicht offensichtlich; der Hinweis steht schon vor der
  # ersten Eingabe da und bleibt beim Tippen sichtbar (kein Platzhalter, der verschwindet).
  # @run-5 · Formular·Öffnen · Frontend-only
  @US-602-happy-path
  Scenario: Das Zutatenfeld erklärt seine Eingabeform
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    Then sehe ich am Zutatenfeld den Hinweis "Eine Zutat je Zeile: Menge, Einheit, Zutat – z. B. „250 g Mehl“ oder „Salz“."
    When ich "250 g Mehl" als Zutaten eingebe
    Then sehe ich am Zutatenfeld weiterhin den Hinweis "Eine Zutat je Zeile: Menge, Einheit, Zutat – z. B. „250 g Mehl“ oder „Salz“."

  # @run-5 · Formular·Öffnen · Frontend-only
  @US-602-happy-path
  Scenario: Beim Öffnen des Formulars liegt der Fokus auf dem Titel
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    Then liegt der Fokus auf dem Titel-Feld

  # @run-5 · Formular·Öffnen · Frontend-only
  @US-602-happy-path
  Scenario: Jedes Schrittfeld zeigt seine Nummer
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich auf "Schritt hinzufügen" klicke
    And ich auf "Schritt hinzufügen" klicke
    Then tragen die Schrittfelder in dieser Reihenfolge die Nummern 1, 2, 3

  # @run-5 · Formular·Öffnen · Frontend-only
  @US-602-happy-path
  Scenario: Nach „Schritt hinzufügen" liegt der Fokus im neuen Schrittfeld
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    Then liegt der Fokus auf dem zweiten Schrittfeld

  # @run-2 · Anlegen·Success · Full-Stack · Singleton
  @US-602-happy-path
  Scenario: Rezept anlegen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    And die Zutat "Milch" mit Einheit "ml" existiert
    And die Zutat "Salz" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich als Zutaten eingebe:
      | Salz         |
      | 250 g Mehl   |
      | 500 ml Milch |
    And ich "Mehl und Milch verrühren." als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich "In der Pfanne ausbacken." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Detailansicht des Rezepts "Pfannkuchen"
    And zeigt sie die Zutaten in dieser Reihenfolge: "Salz", "250 g Mehl", "500 ml Milch"
    And zeigt sie die Schritte als einzelne Einträge: 1 "Mehl und Milch verrühren.", 2 "In der Pfanne ausbacken."
    And steht "Pfannkuchen" genau einmal in der Rezept-Liste

  # @run-3 · Liste·Sortierung · Full-Stack · Singleton
  @US-602-happy-path
  Scenario: Mehrere Rezepte erscheinen alphabetisch sortiert
    Given das Rezept "Zwiebelkuchen" existiert
    And das Rezept "Ölkuchen" existiert
    And das Rezept "apfelstrudel" existiert
    And das Rezept "Brot" existiert
    When ich zur Rezepte-Seite navigiere
    Then zeigt die Rezept-Liste in dieser Reihenfolge: "apfelstrudel", "Brot", "Ölkuchen", "Zwiebelkuchen"

  # Zwei Rezepte, damit ein falsch geladenes Rezept auffällt: „Brot" steht in der Liste vor
  # „Pfannkuchen" (wer das erste lädt statt des angeklickten, zeigt Brot), und „500 g Weizenmehl"
  # erscheint, wenn die Zutaten nicht nach Rezept gefiltert werden. Mit nur einem Rezept
  # bestünden beide Fehler. Gilt ebenso für den Direktlink.
  # @run-4 · Detail·Öffnen · Full-Stack
  @US-602-happy-path
  Scenario: Rezept aus der Rezept-Liste öffnen
    Given das Rezept "Pfannkuchen" mit der Zutat "250 g Mehl" und dem Schritt "Teig rühren." existiert
    And das Rezept "Brot" mit der Zutat "500 g Weizenmehl" und dem Schritt "Teig kneten." existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Pfannkuchen" klicke
    Then sehe ich die Detailansicht des Rezepts "Pfannkuchen"
    And zeigt sie die Zutat "250 g Mehl"
    And zeigt sie den Schritt 1 "Teig rühren."
    And zeigt sie nicht die Zutat "500 g Weizenmehl"

  # @run-4 · Detail·Öffnen · Full-Stack
  @US-602-happy-path
  Scenario: Rezept per Direktlink aufrufen
    Given das Rezept "Pfannkuchen" mit der Zutat "250 g Mehl" und dem Schritt "Teig rühren." existiert
    And das Rezept "Brot" mit der Zutat "500 g Weizenmehl" und dem Schritt "Teig kneten." existiert
    When ich den Direktlink des Rezepts "Pfannkuchen" in einem neuen Browserfenster öffne
    Then sehe ich die Detailansicht des Rezepts "Pfannkuchen"
    And zeigt sie die Zutat "250 g Mehl"
    And zeigt sie nicht die Zutat "500 g Weizenmehl"

  # @run-6 · Formular·Abbrechen · Frontend-only
  @US-602-happy-path
  Scenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich auf "Abbrechen" klicke
    Then sehe ich die Rezept-Liste
    And wurde ich nicht gefragt, ob ich Eingaben verwerfen möchte

  # @run-6 · Formular·Abbrechen · Frontend-only
  @US-602-happy-path
  Scenario Outline: Abbrechen mit Eingaben fragt nach – Verwerfen führt zur Rezept-Liste
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich <Eingabe>
    And ich auf "Abbrechen" klicke
    Then sehe ich die Nachfrage "Eingaben verwerfen?"
    When ich auf "Verwerfen" klicke
    Then sehe ich die Rezept-Liste

    Examples:
      | Eingabe                            |
      | "Pfannkuchen" als Titel eingebe    |
      | "Salz" als Zutaten eingebe         |
      | "Teig rühren." als Schritt eingebe |

  # @run-6 · Formular·Abbrechen · Frontend-only
  @US-602-happy-path
  Scenario: Abbrechen mit Eingaben fragt nach – Weiter bearbeiten behält die Eingaben
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich auf "Abbrechen" klicke
    And ich auf "Weiter bearbeiten" klicke
    Then sehe ich das Formular mit dem Titel "Pfannkuchen" und den Zutaten "250 g Mehl"
    And sehe ich keine Nachfrage mehr

  # Ein versehentliches Enter verwirft nichts.
  # @run-6 · Formular·Abbrechen · Frontend-only
  @US-602-happy-path
  Scenario: Beim Öffnen der Nachfrage liegt der Fokus auf „Weiter bearbeiten"
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich auf "Abbrechen" klicke
    Then liegt in der Nachfrage der Fokus auf "Weiter bearbeiten"

  # ---------------------------------------------------------------- error

  # @run-8 · Anlegen·Validierung Pflichtangaben · Full-Stack
  @US-602-error
  Scenario: Leeres Formular speichern zeigt alle Pflichtmeldungen gleichzeitig
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich auf "Speichern" klicke
    Then sehe ich am Titel die Fehlermeldung "Titel darf nicht leer sein."
    And sehe ich bei den Zutaten die Fehlermeldung "Rezept muss mindestens eine Zutat haben."
    And sehe ich bei den Schritten die Fehlermeldung "Rezept muss mindestens einen Schritt haben."
    And liegt der Fokus auf dem Titel-Feld
    And bin ich weiterhin im Formular
    And ist die Rezept-Liste unverändert

  # @run-9 · Anlegen·Validierung Titel und Anweisung · Full-Stack
  @US-602-error
  Scenario Outline: Ungültiger Titel
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich <Titel> als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich am Titel die Fehlermeldung "<Meldung>"
    And liegt der Fokus auf dem Titel-Feld
    And bin ich weiterhin im Formular mit allen Eingaben
    And ist die Rezept-Liste unverändert

    Examples:
      | Titel                      | Meldung                                   |
      | "   "                      | Titel darf nicht leer sein.               |
      | einen Text aus 101 Zeichen | Titel darf maximal 100 Zeichen lang sein. |

  # Umlaut „Käsekuchen"/„KÄSEKUCHEN": prüft Case-Insensitivität auch jenseits von ASCII.
  # Zerlegtes „ä" und „apfel   strudel": Die Eindeutigkeit gilt für den normalisierten Titel.
  # @run-12 · Anlegen·Validierung Titel eindeutig · Full-Stack
  @US-602-error
  Scenario Outline: Titel existiert bereits – unabhängig von Schreibweise und Leerraum
    Given das Rezept "<Vorhanden>" existiert
    And die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich <Eingabe> als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich am Titel die Fehlermeldung "Ein Rezept mit dem Titel '<Normalisiert>' existiert bereits."
    And liegt der Fokus auf dem Titel-Feld
    And bin ich weiterhin im Formular mit allen Eingaben
    And steht "<Vorhanden>" genau einmal in der Rezept-Liste

    # Eingabe in Anführungszeichen: Gherkin trimmt Tabellenzellen, die Leerzeichen gingen sonst verloren.
    Examples:
      | Vorhanden     | Eingabe                                                     | Normalisiert  |
      | Pfannkuchen   | "Pfannkuchen"                                               | Pfannkuchen   |
      | Pfannkuchen   | "PFANNKUCHEN"                                               | PFANNKUCHEN   |
      | Pfannkuchen   | "  pfannkuchen  "                                           | pfannkuchen   |
      | Käsekuchen    | "KÄSEKUCHEN"                                                | KÄSEKUCHEN    |
      | Käsekuchen    | "Käsekuchen" mit einem „ä“ aus „a“ und kombinierendem Trema | Käsekuchen    |
      | Apfel Strudel | "apfel   strudel"                                           | apfel strudel |

  # @run-8 · Anlegen·Validierung Pflichtangaben · Full-Stack
  @US-602-error
  Scenario Outline: Rezept ohne Zutat oder ohne Schritt
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich <Eingabe>
    And ich auf "Speichern" klicke
    Then sehe ich <Ort> die Fehlermeldung "<Meldung>"
    And liegt der Fokus auf <Fokus>
    And bin ich weiterhin im Formular mit allen Eingaben
    And ist die Rezept-Liste unverändert

    Examples:
      | Eingabe                                                                             | Ort               | Meldung                                     | Fokus                  |
      | "Teig rühren." als Schritt eingebe                                                  | bei den Zutaten   | Rezept muss mindestens eine Zutat haben.    | dem Zutatenfeld        |
      | als Zutaten nur leere Zeilen und Leerzeichen und "Teig rühren." als Schritt eingebe | bei den Zutaten   | Rezept muss mindestens eine Zutat haben.    | dem Zutatenfeld        |
      | "250 g Mehl" als Zutaten eingebe                                                    | bei den Schritten | Rezept muss mindestens einen Schritt haben. | dem ersten Schrittfeld |
      | "250 g Mehl" als Zutaten und "   " als Schritt eingebe                              | bei den Schritten | Rezept muss mindestens einen Schritt haben. | dem ersten Schrittfeld |

  # Mengenwerte nach ADR-S020-1 (stabil, volle Tiefe): Wertgrenzen und Zahlform mit Komma. Die
  # sehr langen Zahlen belegen, dass exakt dezimal gerechnet wird – ohne Rundung und Überlauf.
  # @run-10 · Anlegen·Validierung Menge · Full-Stack
  @US-602-error
  Scenario Outline: Ungültige Menge in einer Zutatenzeile
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "<Zeile>" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich bei den Zutaten genau die Fehlermeldung "„<Zeile>“: <Meldung>"
    And liegt der Fokus auf dem Zutatenfeld
    And bin ich weiterhin im Formular mit allen Eingaben
    And ist die Rezept-Liste unverändert

    Examples:
      | Zeile                                    | Meldung                                      |
      | 0 g Mehl                                 | Menge muss größer als 0 sein.                |
      | 0,0005 g Mehl                            | Menge darf maximal 3 Nachkommastellen haben. |
      | 1,0000000000000000000000000000001 g Mehl | Menge darf maximal 3 Nachkommastellen haben. |
      | 0,0000000000000000000000000000001 g Mehl | Menge darf maximal 3 Nachkommastellen haben. |
      | 10000 g Mehl                             | Menge darf maximal 9999,999 sein.            |
      | 10000,000 g Mehl                         | Menge darf maximal 9999,999 sein.            |
      | 100000000000000000000000000000 g Mehl    | Menge darf maximal 9999,999 sein.            |
      | 1.5 g Mehl                               | Menge muss eine Zahl sein (z. B. 1,5).       |
      | 1.000 g Mehl                             | Menge muss eine Zahl sein (z. B. 1,5).       |
      | 5, g Mehl                                | Menge muss eine Zahl sein (z. B. 1,5).       |
      | 1,5,5 g Mehl                             | Menge muss eine Zahl sein (z. B. 1,5).       |

  # Die typischsten Fehler beim Übertragen (Übergangsregel): vertippter Name, falsche Einheit.
  # „1 Zwiebel" (Stückzahl, erst ab US-607) sieht wohlgeformt aus – ohne Festlegung könnte die
  # Zeile still mit Menge und ohne Einheit gespeichert werden (gegen ADR-S020-1).
  # „250 g Butter": Die Suche nach dem Namen filtert gelöschte Zutaten von Hand – fehlt der
  # Filter, verwiese ein Rezept auf eine gelöschte Zutat; der Speicherpfad überlebt US-607.
  # @run-11 · Anlegen·Validierung Zutatenzeile · Full-Stack
  @US-602-error
  Scenario Outline: Zutat nicht gefunden oder Einheit falsch
    Given die Zutat "Mehl" mit Einheit "g" existiert
    And die Zutat "Zwiebel" mit Einheit "Stück" existiert
    And die Zutat "Butter" mit Einheit "g" existiert und gelöscht wurde
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "<Zeile>" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich bei den Zutaten genau die Fehlermeldung "„<Zeile>“: <Meldung>"
    And liegt der Fokus auf dem Zutatenfeld
    And bin ich weiterhin im Formular mit allen Eingaben
    And ist die Rezept-Liste unverändert

    Examples:
      | Zeile        | Meldung                                                                            |
      | 250 g Mehk   | Zutat 'Mehk' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt.   |
      | 250 g Butter | Zutat 'Butter' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt. |
      | 2 EL Mehl    | Einheit 'EL' passt nicht zu 'Mehl' (möglich: 'g').                                 |
      | 1 Zwiebel    | Einheit fehlt (für 'Zwiebel': 'Stück').                                            |

  # @run-11 · Anlegen·Validierung Zutatenzeile · Full-Stack
  @US-602-error
  Scenario: Alle fehlerhaften Zutatenzeilen werden gemeinsam und in Zeilenreihenfolge gemeldet
    Given die Zutat "Mehl" mit Einheit "g" existiert
    And die Zutat "Milch" mit Einheit "ml" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich als Zutaten eingebe:
      | 250 g Mehl |
      | 2 Eier     |
      | 500 Milch  |
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich bei den Zutaten genau die Fehlermeldungen in dieser Reihenfolge:
      | „2 Eier“: Zutat 'Eier' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt. |
      | „500 Milch“: Einheit fehlt (für 'Milch': 'ml').                                            |
    And liegt der Fokus auf dem Zutatenfeld

  # @run-11 · Anlegen·Validierung Zutatenzeile · Full-Stack
  @US-602-error
  Scenario: Eine Zutat, die schon in einer früheren Zeile steht, wird gemeldet
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich als Zutaten eingebe:
      | 250 g Mehl |
      | 100 g Mehl |
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich bei den Zutaten genau die Fehlermeldung "„100 g Mehl“: Zutat 'Mehl' steht bereits in einer früheren Zeile."
    And liegt der Fokus auf dem Zutatenfeld
    And bin ich weiterhin im Formular mit allen Eingaben
    And ist die Rezept-Liste unverändert

  # @run-9 · Anlegen·Validierung Titel und Anweisung · Full-Stack
  @US-602-error
  Scenario: Schritt-Anweisung mit mehr als 1000 Zeichen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich eine Anweisung aus 1001 Zeichen als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich am zweiten Schritt die Fehlermeldung "Schritt-Anweisung darf maximal 1000 Zeichen lang sein."
    And liegt der Fokus auf dem zweiten Schrittfeld
    And bin ich weiterhin im Formular mit allen Eingaben
    And ist die Rezept-Liste unverändert

  # Leere Schrittfelder werden nicht mitgeschickt – die Meldung muss trotzdem am Formularfeld
  # erscheinen, nicht an der Position in der gesendeten Liste (dort wäre es das zweite Feld).
  # @run-9 · Anlegen·Validierung Titel und Anweisung · Full-Stack
  @US-602-error
  Scenario: Meldungen erscheinen am richtigen Schritt, auch hinter leeren Schrittfeldern
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich "   " als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich eine Anweisung aus 1001 Zeichen als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich am dritten Schritt die Fehlermeldung "Schritt-Anweisung darf maximal 1000 Zeichen lang sein."
    And sind der erste und der zweite Schritt nicht als fehlerhaft markiert
    And liegt der Fokus auf dem dritten Schrittfeld

  # @run-9 · Anlegen·Validierung Titel und Anweisung · Full-Stack
  @US-602-error
  Scenario: Alle fehlerhaften Schritte werden gemeldet, der Fokus liegt auf dem ersten
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich eine Anweisung aus 1001 Zeichen als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich eine Anweisung aus 1001 Zeichen als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich am zweiten und am dritten Schritt je die Fehlermeldung "Schritt-Anweisung darf maximal 1000 Zeichen lang sein."
    And ist der erste Schritt nicht als fehlerhaft markiert
    And liegt der Fokus auf dem zweiten Schrittfeld

  # @run-13 · Formular·nach dem Speichern · Full-Stack · braucht:CROSS-navigation/run-1
  @US-602-error
  Scenario: Fokus springt auf das erste fehlerhafte Feld
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehk" als Zutaten eingebe
    And ich eine Anweisung aus 1001 Zeichen als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich bei den Zutaten genau die Fehlermeldung "„250 g Mehk“: Zutat 'Mehk' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt."
    And sehe ich am ersten Schritt die Fehlermeldung "Schritt-Anweisung darf maximal 1000 Zeichen lang sein."
    And sehe ich bei den Schritten keine Meldung "Rezept muss mindestens einen Schritt haben."
    And liegt der Fokus auf dem Zutatenfeld

  # Ein alter Fehlerzustand darf das erneute Absenden nicht blockieren.
  # @run-13 · Formular·nach dem Speichern · Full-Stack · braucht:CROSS-navigation/run-1
  @US-602-error
  Scenario: Nach Korrektur der gemeldeten Zeile wird das Rezept gespeichert
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehk" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    And die Fehlermeldung "„250 g Mehk“: Zutat 'Mehk' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt." erscheint
    And ich die Zutaten durch "250 g Mehl" ersetze
    And ich auf "Speichern" klicke
    Then sehe ich die Detailansicht des Rezepts "Pfannkuchen"
    And zeigt sie die Zutat "250 g Mehl"
    And steht "Pfannkuchen" genau einmal in der Rezept-Liste

  # @run-12 · Anlegen·Validierung Titel eindeutig · Full-Stack
  @US-602-error
  Scenario: Titel-Eindeutigkeit wird erst geprüft, wenn alle übrigen Prüfungen bestanden sind
    Given das Rezept "Pfannkuchen" existiert
    And die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehk" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich bei den Zutaten genau die Fehlermeldung "„250 g Mehk“: Zutat 'Mehk' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt."
    And sehe ich keine Fehlermeldung am Titel
    When ich die Zutaten durch "250 g Mehl" ersetze
    And ich auf "Speichern" klicke
    Then sehe ich am Titel die Fehlermeldung "Ein Rezept mit dem Titel 'Pfannkuchen' existiert bereits."
    And sehe ich bei den Zutaten keine Fehlermeldung mehr

  # Kein UI-Pfad erreichbar: Das Formular schickt leere Schrittfelder nicht mit.
  # Step mappt auf einen direkten Speicher-Befehl.
  # @run-8 · Anlegen·Validierung Pflichtangaben · Full-Stack
  @US-602-error
  Scenario: Ein Rezept mit einer leeren Schritt-Anweisung wird abgelehnt
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich den Speicher-Befehl für das Rezept "Pfannkuchen" mit der Zutatenzeile "250 g Mehl" und den Schritten "Teig rühren." und "   " absende
    Then erhalte ich am zweiten Schritt die Fehlermeldung "Schritt-Anweisung darf nicht leer sein."
    And ist die Rezept-Liste unverändert

  # @run-4 · Detail·Öffnen · Full-Stack
  @US-602-error
  Scenario Outline: Direktlink auf ein Rezept, das es nicht gibt
    When ich einen Rezept-Link mit <Kennung> öffne
    Then sehe ich den Hinweis "Rezept nicht gefunden."
    When ich auf "Zur Rezept-Liste" klicke
    Then sehe ich die Rezept-Liste

    Examples:
      | Kennung                                       |
      | einer gültig aufgebauten, unbekannten Kennung |
      | einer ungültigen Kennung                      |

  # ---------------------------------------------------------------- edge-case

  # @run-7 · Anlegen·Eingaben bereinigen und erkennen · Full-Stack · braucht:CROSS-text/run-1
  @US-602-edge-case
  Scenario: Titel und Anweisung werden mit zusammengefasstem Leerraum und in eingegebener Schreibweise gespeichert
    Given die Zutat "Linsen" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "  linsensuppe   vom  blech  " als Titel eingebe
    And ich "125 g Linsen" als Zutaten eingebe
    And ich als Schritt eine Anweisung mit Zeilenumbrüchen, Tabulatoren und mehrfachen Leerzeichen zwischen "Linsen" und "kochen." einfüge
    And ich auf "Speichern" klicke
    Then sehe ich die Detailansicht des Rezepts "linsensuppe vom blech"
    And zeigt sie den Schritt 1 "Linsen kochen." ohne Zeilenumbruch
    And steht "linsensuppe vom blech" in der Rezept-Liste

  # @run-9 · Anlegen·Validierung Titel und Anweisung · Full-Stack
  @US-602-edge-case
  Scenario: Titel und Anweisung mit genau der zulässigen Länge werden gespeichert
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich einen Titel aus 100 Zeichen mit je zwei Leerzeichen davor und dahinter und einem doppelten statt einem einfachen Leerzeichen im Inneren eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich eine Anweisung aus 1000 Zeichen mit je zwei Leerzeichen davor und dahinter und einem doppelten statt einem einfachen Leerzeichen im Inneren als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Detailansicht des neuen Rezepts
    And ist sein Titel genau der Text aus 100 Zeichen, mit einfachem Leerzeichen im Inneren
    And ist sein einziger Schritt genau die Anweisung aus 1000 Zeichen, mit einfachem Leerzeichen im Inneren

  # @run-10 · Anlegen·Validierung Menge · Full-Stack
  @US-602-edge-case
  Scenario Outline: Mengen an den Grenzen werden gespeichert und angezeigt
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "<Zeile>" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then zeigt die Detailansicht die Zutat "<Anzeige>"

    # Nullen am Ende zählen nicht als Nachkommastellen.
    Examples:
      | Zeile            | Anzeige         |
      | 0,001 g Mehl     | 0,001 g Mehl    |
      | 9999,999 g Mehl  | 9999,999 g Mehl |
      | 0,0010 g Mehl    | 0,001 g Mehl    |
      | 9999,9990 g Mehl | 9999,999 g Mehl |

  # Gutfall der Übergangsregel in den Schreibweisen, die in der Rezeptsammlung häufig sind:
  # Namen aus mehreren Wörtern, Einheit mit Punkt, Kleinschreibung, Name ohne Menge.
  # @run-7 · Anlegen·Eingaben bereinigen und erkennen · Full-Stack · braucht:CROSS-text/run-1
  @US-602-edge-case
  Scenario Outline: Zutatenzeilen in typischer Schreibweise werden erkannt und wie gespeichert angezeigt
    Given die Zutat "<Name>" mit Einheit "<Einheit>" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Testrezept" als Titel eingebe
    And ich "<Zeile>" als Zutaten eingebe
    And ich "Alles mischen." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then zeigt die Detailansicht die Zutat "<Anzeige>"

    Examples:
      | Name              | Einheit | Zeile                | Anzeige              |
      | rote Linsen       | g       | 125 g rote Linsen    | 125 g rote Linsen    |
      | Vanillezucker     | Pck.    | 1 Pck. Vanillezucker | 1 Pck. Vanillezucker |
      | Mehl              | g       | 250 G mehl           | 250 g Mehl           |
      | schwarzer Pfeffer | Prise   | schwarzer pfeffer    | schwarzer Pfeffer    |

  # @run-7 · Anlegen·Eingaben bereinigen und erkennen · Full-Stack · braucht:CROSS-text/run-1
  @US-602-edge-case
  Scenario: Leere Zeilen und Zeilen aus Leerzeichen im Zutatenfeld werden übergangen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    And die Zutat "Milch" mit Einheit "ml" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich als Zutaten "250 g Mehl", eine leere Zeile, eine Zeile aus Leerzeichen und "500 ml Milch" eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then zeigt die Detailansicht die Zutaten in dieser Reihenfolge: "250 g Mehl", "500 ml Milch"

  # Die Nummern der Detailansicht sind lückenlos – das leere Feld dazwischen zählt nicht.
  # @run-7 · Anlegen·Eingaben bereinigen und erkennen · Full-Stack · braucht:CROSS-text/run-1
  @US-602-edge-case
  Scenario: Leere Schrittfelder werden beim Speichern übergangen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Eier trennen." als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich "   " als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich "Eiweiß steif schlagen." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then zeigt die Detailansicht die Schritte als einzelne Einträge: 1 "Eier trennen.", 2 "Eiweiß steif schlagen."

  # Client und Server müssen gleich entscheiden, was leer ist – sonst schickte der Client das
  # Feld mit, und der Server meldete „Schritt-Anweisung darf nicht leer sein.".
  # @run-7 · Anlegen·Eingaben bereinigen und erkennen · Full-Stack · braucht:CROSS-text/run-1
  @US-602-edge-case
  Scenario: Ein Schrittfeld nur aus Leerzeichen ohne Breite wird übergangen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich als Schritt nur Leerzeichen ohne Breite eingebe
    And ich auf "Speichern" klicke
    Then zeigt die Detailansicht den Schritt 1 "Teig rühren." als einzigen Schritt

  # @run-6 · Formular·Abbrechen · Frontend-only
  @US-602-edge-case
  Scenario: Abbrechen fragt nicht nach, wenn nur Leerraum eingegeben wurde
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich als Titel Leerzeichen und Leerzeichen ohne Breite eingebe
    And ich als Zutaten nur leere Zeilen, Leerzeichen und Leerzeichen ohne Breite eingebe
    And ich "   " als Schritt eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich als Schritt nur Leerzeichen ohne Breite eingebe
    And ich auf "Abbrechen" klicke
    Then sehe ich die Rezept-Liste
    And wurde ich nicht gefragt, ob ich Eingaben verwerfen möchte

  # Was das Schließen der Nachfrage auslöst, legt die Anwendung fest – an „Verwerfen" gebunden,
  # gingen die Eingaben verloren.
  # @run-6 · Formular·Abbrechen · Frontend-only
  @US-602-edge-case
  Scenario Outline: Escape oder Klick neben die Nachfrage behält die Eingaben
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich auf "Abbrechen" klicke
    And ich <Schließen>
    Then sehe ich das Formular mit dem Titel "Pfannkuchen"
    And sehe ich keine Nachfrage mehr

    Examples:
      | Schließen                  |
      | Escape drücke              |
      | neben die Nachfrage klicke |

  # @run-6 · Formular·Abbrechen · Frontend-only
  @US-602-edge-case
  Scenario: Nach Verwerfen ist das Formular beim erneuten Öffnen leer
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich auf "Schritt hinzufügen" klicke
    And ich auf "Abbrechen" klicke
    And ich auf "Verwerfen" klicke
    And ich auf "Rezept anlegen" klicke
    Then ist das Titel-Feld leer
    And ist das Zutatenfeld leer
    And gibt es genau ein Schrittfeld, es ist leer und trägt die Nummer 1

  # @run-13 · Formular·nach dem Speichern · Full-Stack · braucht:CROSS-navigation/run-1
  @US-602-edge-case
  Scenario: Nach fehlgeschlagenem Speichern und Verwerfen ist das Formular beim erneuten Öffnen fehlerfrei
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    And die Fehlermeldung "Titel darf nicht leer sein." erscheint
    And ich auf "Abbrechen" klicke
    And ich auf "Verwerfen" klicke
    And ich auf "Rezept anlegen" klicke
    Then ist keine Fehlermeldung sichtbar
    And ist kein Feld als ungültig markiert

  # Meldungen sind keine Eingaben: ohne Eingaben keine Nachfrage, und sie bleiben nicht stehen.
  # @run-13 · Formular·nach dem Speichern · Full-Stack · braucht:CROSS-navigation/run-1
  @US-602-edge-case
  Scenario: Nach fehlgeschlagenem Speichern ohne Eingaben bricht man ohne Nachfrage ab und öffnet das Formular fehlerfrei
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich auf "Speichern" klicke
    And die Fehlermeldung "Titel darf nicht leer sein." erscheint
    And ich auf "Abbrechen" klicke
    Then sehe ich die Rezept-Liste
    And wurde ich nicht gefragt, ob ich Eingaben verwerfen möchte
    When ich auf "Rezept anlegen" klicke
    Then ist keine Fehlermeldung sichtbar
    And ist kein Feld als ungültig markiert

  # @run-13 · Formular·nach dem Speichern · Full-Stack · braucht:CROSS-navigation/run-1
  @US-602-edge-case
  Scenario: Nach erfolgreichem Speichern ist das Formular beim erneuten Öffnen leer
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    And die Detailansicht des Rezepts "Pfannkuchen" erscheint
    And ich in der Navigationsleiste auf "Rezepte" klicke
    Then steht "Pfannkuchen" genau einmal in der Rezept-Liste
    When ich auf "Rezept anlegen" klicke
    Then ist das Titel-Feld leer
    And ist das Zutatenfeld leer
    And gibt es genau ein Schrittfeld, es ist leer und trägt die Nummer 1

  # Meldungen bleiben bis zum nächsten Speichern: Das Zutatenfeld hat Meldungen zu mehreren
  # Zeilen – verschwänden sie beim Tippen, gingen die zu noch nicht korrigierten Zeilen verloren.
  # @run-13 · Formular·nach dem Speichern · Full-Stack · braucht:CROSS-navigation/run-1
  @US-602-edge-case
  Scenario: Meldungen bleiben beim Bearbeiten bis zum nächsten Speichern stehen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehk" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    And ich die Zutaten durch "250 g Mehl" ersetze
    Then sehe ich bei den Zutaten weiterhin die Fehlermeldung "„250 g Mehk“: Zutat 'Mehk' nicht gefunden. Neue Zutaten werden auf der Zutaten-Seite angelegt."

  # @run-5 · Formular·Öffnen · Frontend-only
  @US-602-edge-case
  Scenario: Das Formular lässt sich über seine Adresse direkt öffnen und ist leer
    When ich die Adresse des Formulars "Rezept anlegen" in einem neuen Browserfenster öffne
    Then ist das Titel-Feld leer
    And ist das Zutatenfeld leer
    And gibt es genau ein Schrittfeld, es ist leer und trägt die Nummer 1

  # ---------------------------------------------------------------- MVP: Verlassen mit Eingaben, Browserverlauf, Löschsperre, Handybreite
  # Verlassen und Verlauf stehen hier und nicht in navigation.feature: Sie schützen die Eingaben
  # dieses Formulars, nicht den Weg zwischen Seiten (ADR-S103-1 betrifft Erreichbarkeit).
  #
  # Verlauf: Speichern ersetzt das Formular im Verlauf durch die Detailansicht. Abbrechen ohne
  # Eingaben und Verwerfen nach Abbrechen kehren zur Rezept-Liste zurück, ohne einen neuen
  # Verlaufseintrag anzulegen; wurde das Formular direkt geöffnet, ersetzt die Rezept-Liste das
  # Formular. Browser-Zurück wird im Formular abgefangen – in einem direkt geöffneten Fenster
  # ohne Verlauf ist das nicht möglich.
  #
  # Löschsperre: Eine Zutat, die in einem Rezept verwendet wird, lässt sich nicht löschen. Die
  # Meldung erscheint an der Zeile dieser Zutat in der Zutaten-Liste (nah am auslösenden Element;
  # ein Toast würde den Rückgängig-Toast überdecken – ADR-S108-3 schließt Stapeln aus). Sie
  # bleibt stehen, bis auf der Seite erneut gelöscht oder die Seite verlassen wird. Bis zu drei
  # Rezepte werden alphabetisch (deutsches Locale, ohne Unterschied der Groß-/Kleinschreibung)
  # genannt, weitere nur als Anzahl. Der Toast „X gelöscht" erscheint erst mit der Antwort des
  # Servers. Diese Szenarien machen TD-S108-1 (Toast vor der Antwort, kein Status-Check) und
  # TD-S110-1 (Sperre nur im Erfolgspfad) fällig.
  # Offen für den ADR-Check der Umsetzung: „Zutat löschen" und „Rezept speichern" prüfen je vor
  # dem Schreiben (Verwendung bzw. Zutat vorhanden); die Invariante „kein Rezept verweist auf
  # eine gelöschte Zutat" muss auch bei echter Gleichzeitigkeit halten (Soft-Delete – ein
  # Fremdschlüssel allein genügt nicht).
  #
  # Offen für den Workshop der MVP-Stufe (bewusst dorthin vertagt):
  #   - „Direkt geöffnet" als „nicht über ‚Rezept anlegen' erreicht" definieren statt „ohne
  #     Verlauf" – im selben Tab per Lesezeichen geöffnet, führte „zurück" sonst aus der App.
  #   - Browser-Zurück (Zurück-Geste am Handy) bei offener Nachfrage: schließt sie und bleibt
  #     im Formular?
  #   - Verlauf nach abgefangenem Zurück und anschließendem Speichern: Zurück aus der
  #     Detailansicht darf nicht ins Formular führen.
  #   - Handybreite auch für Zutatenname (30) und Einheit (20) ohne Leerzeichen.
  #   - „Titel-Eindeutigkeit wird erst geprüft, wenn alle übrigen Prüfungen bestanden sind"
  #     prüft, dass nach dem ersten Speichern am Titel keine Meldung steht. Mit dem Hinweis beim
  #     Verlassen des Titelfelds stünde dort eine – das Szenario ist anzupassen.

  # @run-14 · Verlassen·Nachfrage · Frontend-only · Phase:MVP · braucht:CROSS-navigation/run-1
  @US-602-happy-path
  Scenario Outline: Verlassen mit Eingaben fragt nach – Verwerfen führt zum gewählten Ziel
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich <Weg>
    Then sehe ich die Nachfrage "Eingaben verwerfen?"
    When ich auf "Verwerfen" klicke
    Then sehe ich <Seite>

    Examples:
      | Weg                                           | Seite             |
      | in der Navigationsleiste auf "Zutaten" klicke | die Zutaten-Seite |
      | in der Navigationsleiste auf "Rezepte" klicke | die Rezept-Liste  |
      | im Browser zurückgehe                         | die Rezept-Liste  |

  # Ein zweiter Versuch muss wieder nachfragen – beim Abfangen von Browser-Zurück ist das die
  # typische Bruchstelle (Nachfrage bleibt aus oder der Verlauf ist verschoben).
  # @run-14 · Verlassen·Nachfrage · Frontend-only · Phase:MVP · braucht:CROSS-navigation/run-1
  @US-602-happy-path
  Scenario Outline: Verlassen mit Eingaben fragt nach – Weiter bearbeiten bleibt im Formular, auch beim zweiten Versuch
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich <Weg>
    And ich auf "Weiter bearbeiten" klicke
    Then sehe ich das Formular mit dem Titel "Pfannkuchen"
    And ist das Formular weiterhin unter seiner eigenen Adresse geöffnet
    When ich <Weg>
    Then sehe ich die Nachfrage "Eingaben verwerfen?"
    When ich auf "Verwerfen" klicke
    Then sehe ich <Seite>

    Examples:
      | Weg                                           | Seite             |
      | in der Navigationsleiste auf "Zutaten" klicke | die Zutaten-Seite |
      | im Browser zurückgehe                         | die Rezept-Liste  |

  # @run-17 · Löschen·Sperre · Full-Stack · Phase:MVP
  @US-602-error
  Scenario Outline: Eine Zutat, die in Rezepten verwendet wird, lässt sich nicht löschen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    And die Zutat "Mehl" wird verwendet in: <Rezepte>
    When ich zur Zutaten-Seite navigiere
    And ich bei "Mehl" auf Löschen klicke
    Then sehe ich an der Zeile "Mehl" die Fehlermeldung "<Meldung>"
    And steht "Mehl" weiterhin in der Zutaten-Liste
    And sehe ich keinen Toast "Mehl gelöscht"
    And lässt sich bei "Mehl" wieder auf Löschen klicken

    Examples:
      | Rezepte                                                | Meldung                                                                                                                        |
      | "Pfannkuchen"                                          | Zutat 'Mehl' wird im Rezept 'Pfannkuchen' verwendet und kann nicht gelöscht werden.                                            |
      | "Pfannkuchen", "Brot"                                  | Zutat 'Mehl' wird in den Rezepten 'Brot' und 'Pfannkuchen' verwendet und kann nicht gelöscht werden.                           |
      | "Pfannkuchen", "Brot", "Kuchen"                        | Zutat 'Mehl' wird in den Rezepten 'Brot', 'Kuchen' und 'Pfannkuchen' verwendet und kann nicht gelöscht werden.                 |
      | "Pfannkuchen", "Brot", "Kuchen", "Zopf"                | Zutat 'Mehl' wird in den Rezepten 'Brot', 'Kuchen', 'Pfannkuchen' und einem weiteren verwendet und kann nicht gelöscht werden. |
      | "Pfannkuchen", "Brot", "Ölbrot", "apfelkuchen", "Zopf" | Zutat 'Mehl' wird in den Rezepten 'apfelkuchen', 'Brot', 'Ölbrot' und 2 weiteren verwendet und kann nicht gelöscht werden.     |

  # Eine Rezept-Zutat ohne Menge ist ebenso eine Verwendung wie eine mit Menge.
  # @run-17 · Löschen·Sperre · Full-Stack · Phase:MVP
  @US-602-error
  Scenario: Eine Zutat, die nur ohne Menge verwendet wird, lässt sich nicht löschen
    Given die Zutat "Salz" mit Einheit "g" existiert
    And das Rezept "Pfannkuchen" mit der Zutat "Salz" und dem Schritt "Teig rühren." existiert
    When ich zur Zutaten-Seite navigiere
    And ich bei "Salz" auf Löschen klicke
    Then sehe ich an der Zeile "Salz" die Fehlermeldung "Zutat 'Salz' wird im Rezept 'Pfannkuchen' verwendet und kann nicht gelöscht werden."
    And steht "Salz" weiterhin in der Zutaten-Liste

  # @run-14 · Verlassen·Nachfrage · Frontend-only · Phase:MVP · braucht:CROSS-navigation/run-1
  @US-602-edge-case
  Scenario Outline: Ohne Eingaben verlässt man das Formular ohne Nachfrage
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich <Weg>
    Then sehe ich <Seite>
    And wurde ich nicht gefragt, ob ich Eingaben verwerfen möchte

    Examples:
      | Weg                                           | Seite             |
      | in der Navigationsleiste auf "Zutaten" klicke | die Zutaten-Seite |
      | im Browser zurückgehe                         | die Rezept-Liste  |

  # Die Weiterleitung nach dem Speichern verlässt das Formular selbst – sie darf die Nachfrage
  # nicht auslösen.
  # @run-15 · Verlassen·während des Speicherns · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario: Speichern führt ohne Nachfrage zur Detailansicht
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Detailansicht des Rezepts "Pfannkuchen"
    And wurde ich nicht gefragt, ob ich Eingaben verwerfen möchte

  # Browser-Zurück lässt sich nicht deaktivieren, nur abfangen. Während des Speicherns sind
  # beide Wege gesperrt: Eine Nachfrage mit „Verwerfen" wäre hier irreführend, das Rezept
  # entsteht trotzdem.
  # @run-15 · Verlassen·während des Speicherns · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario Outline: Während des Speicherns lässt sich das Formular nicht verlassen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    And das Speichern eines Rezepts dauert spürbar
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich "250 g Mehl" als Zutaten eingebe
    And ich "Teig rühren." als Schritt eingebe
    And ich auf "Speichern" klicke
    And ich, während das Speichern noch läuft, <Weg>
    Then sehe ich weiterhin das Formular, ohne Nachfrage
    And ist das Formular weiterhin unter seiner eigenen Adresse geöffnet
    When das Speichern abgeschlossen ist
    Then sehe ich die Detailansicht des Rezepts "Pfannkuchen"

    Examples:
      | Weg                                           |
      | im Browser zurückgehe                         |
      | in der Navigationsleiste auf "Zutaten" klicke |

  # Nach abgefangenem Browser-Zurück muss das Schließen der Nachfrage auch Adresse und Verlauf
  # wiederherstellen – eigene Logik neben „Weiter bearbeiten".
  # @run-14 · Verlassen·Nachfrage · Frontend-only · Phase:MVP · braucht:CROSS-navigation/run-1
  @US-602-edge-case
  Scenario Outline: Escape oder Klick neben die Nachfrage nach Browser-Zurück bleibt im Formular
    When ich zur Rezepte-Seite navigiere
    And ich auf "Rezept anlegen" klicke
    And ich "Pfannkuchen" als Titel eingebe
    And ich im Browser zurückgehe
    And ich <Schließen>
    Then sehe ich das Formular mit dem Titel "Pfannkuchen"
    And ist das Formular weiterhin unter seiner eigenen Adresse geöffnet
    And sehe ich keine Nachfrage mehr

    Examples:
      | Schließen                  |
      | Escape drücke              |
      | neben die Nachfrage klicke |

  # Ausgangsverlauf: Zutaten-Seite → Rezept-Liste → Formular. Speichern ersetzt das Formular
  # durch die Detailansicht; Abbrechen kehrt ohne neuen Verlaufseintrag zur Liste zurück.
  # @run-16 · Verlauf · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario Outline: Zurück nach Speichern oder Abbrechen führt nicht ins Formular
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Zutaten-Seite navigiere
    And ich in der Navigationsleiste auf "Rezepte" klicke
    And ich auf "Rezept anlegen" klicke
    And <Abschluss>
    And ich im Browser zurückgehe
    Then sehe ich <Seite>
    And sehe ich kein Formular

    Examples:
      | Abschluss                                                                                                               | Seite                              |
      | ich "Pfannkuchen" als Titel, "250 g Mehl" als Zutaten und "Teig rühren." als Schritt eingebe und auf "Speichern" klicke | die Rezept-Liste mit "Pfannkuchen" |
      | ich "Pfannkuchen" als Titel eingebe, auf "Abbrechen" und dann auf "Verwerfen" klicke                                    | die Zutaten-Seite                  |
      | ich ohne Eingaben auf "Abbrechen" klicke                                                                                | die Zutaten-Seite                  |

  # Ohne Verlauf darf Verlassen nicht „zurück" bedeuten – das verließe die Anwendung.
  # @run-16 · Verlauf · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario Outline: Abbrechen in einem direkt geöffneten Formular führt zur Rezept-Liste
    When ich die Adresse des Formulars "Rezept anlegen" in einem neuen Browserfenster öffne
    And <Verlassen>
    Then sehe ich die Rezept-Liste

    Examples:
      | Verlassen                                                                            |
      | ich "Pfannkuchen" als Titel eingebe, auf "Abbrechen" und dann auf "Verwerfen" klicke |
      | ich ohne Eingaben auf "Abbrechen" klicke                                             |

  # Schließt eine Prüfung nur im Client anhand der beim Laden bekannten Verwendung aus.
  # @run-17 · Löschen·Sperre · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario: Eine Zutat, die erst nach dem Laden der Zutaten-Seite verwendet wurde, lässt sich nicht löschen
    Given die Zutat "Mehl" mit Einheit "g" existiert
    When ich zur Zutaten-Seite navigiere
    And das Rezept "Pfannkuchen" mit der Zutat "250 g Mehl" an anderer Stelle angelegt wird
    And ich bei "Mehl" auf Löschen klicke
    Then sehe ich an der Zeile "Mehl" die Fehlermeldung "Zutat 'Mehl' wird im Rezept 'Pfannkuchen' verwendet und kann nicht gelöscht werden."
    And steht "Mehl" weiterhin in der Zutaten-Liste
    And sehe ich keinen Toast "Mehl gelöscht"

  # Gegenprobe zur Löschsperre: Sie darf nur verwendete Zutaten treffen.
  # @run-17 · Löschen·Sperre · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario: Eine unbenutzte Zutat lässt sich löschen, auch wenn Rezepte existieren
    Given die Zutat "Zucker" mit Einheit "g" existiert
    And als einziges Rezept existiert "Pfannkuchen" mit der Zutat "250 g Mehl" und dem Schritt "Teig rühren."
    When ich zur Zutaten-Seite navigiere
    And ich bei "Zucker" auf Löschen klicke
    Then ist "Zucker" nicht in der Zutaten-Liste
    And steht "Mehl" weiterhin in der Zutaten-Liste
    And sehe ich den Toast "Zucker gelöscht" mit "Rückgängig"-Aktion

  # Ob eine Löschung gesperrt ist, steht erst mit der Antwort fest – ein Toast davor würde
  # „Mehl gelöscht" samt Rückgängig für eine Löschung zeigen, die nie stattfindet.
  # @run-18 · Löschen·Sperrmeldung und Toast · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario: Während eine Löschung läuft, erscheint noch kein Toast
    Given die Zutat "Mehl" mit Einheit "g" existiert
    And das Rezept "Pfannkuchen" mit der Zutat "250 g Mehl" und dem Schritt "Teig rühren." existiert
    And das Löschen einer Zutat dauert spürbar
    When ich zur Zutaten-Seite navigiere
    And ich bei "Mehl" auf Löschen klicke
    Then sehe ich, während das Löschen noch läuft, keinen Toast "Mehl gelöscht"
    When das Löschen abgeschlossen ist
    Then sehe ich an der Zeile "Mehl" die Fehlermeldung "Zutat 'Mehl' wird im Rezept 'Pfannkuchen' verwendet und kann nicht gelöscht werden."
    And sehe ich keinen Toast "Mehl gelöscht"

  # Die Sperrmeldung bleibt nur bis zum nächsten Löschversuch oder bis die Seite verlassen wird.
  # @run-18 · Löschen·Sperrmeldung und Toast · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario Outline: Die Sperrmeldung verschwindet beim nächsten Löschen oder Verlassen der Seite
    Given die Zutat "Zucker" mit Einheit "g" existiert
    And als einziges Rezept existiert "Pfannkuchen" mit der Zutat "250 g Mehl" und dem Schritt "Teig rühren."
    When ich zur Zutaten-Seite navigiere
    And ich bei "Mehl" auf Löschen klicke
    And die Fehlermeldung an der Zeile "Mehl" erscheint
    And ich <Aktion>
    Then sehe ich an der Zeile "Mehl" keine Fehlermeldung mehr

    Examples:
      | Aktion                                                               |
      | bei "Zucker" auf Löschen klicke                                      |
      | in der Navigationsleiste auf "Rezepte" und dann auf "Zutaten" klicke |

  # Eine gesperrte Löschung ist keine Löschung – sie darf das Rückgängig einer vorherigen nicht
  # verdrängen.
  # @run-18 · Löschen·Sperrmeldung und Toast · Full-Stack · Phase:MVP
  @US-602-edge-case
  Scenario: Die Sperrmeldung lässt das Rückgängig einer zuvor gelöschten Zutat bestehen
    Given die Zutat "Zucker" mit Einheit "g" existiert
    And als einziges Rezept existiert "Pfannkuchen" mit der Zutat "250 g Mehl" und dem Schritt "Teig rühren."
    When ich zur Zutaten-Seite navigiere
    And ich bei "Zucker" auf Löschen klicke
    And ich bei "Mehl" auf Löschen klicke
    Then sehe ich an der Zeile "Mehl" die Fehlermeldung "Zutat 'Mehl' wird im Rezept 'Pfannkuchen' verwendet und kann nicht gelöscht werden."
    When ich, während die Meldung an der Zeile "Mehl" sichtbar ist, im Toast "Zucker gelöscht" auf "Rückgängig" klicke
    Then steht "Zucker" wieder in der Zutaten-Liste

  # Gelesen wird am Handy (Detailansicht zum Kochen). Ein Wort ohne Leerzeichen bricht sonst
  # nicht um; Meldungen mit solchen Wörtern entstehen nur bei Missbrauch.
  # Querschnittlich, sobald eine zweite Seite so lange Texte hat (Umzug nach ADR-S112-5).
  # @run-19 · Handybreite · Full-Stack · Singleton · Phase:MVP
  @US-602-edge-case
  Scenario: Lange Texte ohne Leerzeichen passen bei Handybreite ohne horizontales Scrollen
    Given das Rezept mit einem Titel aus 100 Zeichen ohne Leerzeichen und einer Anweisung aus 1000 Zeichen ohne Leerzeichen existiert
    And das Browserfenster hat Handybreite
    When ich zur Rezepte-Seite navigiere
    Then lässt sich die Rezept-Liste nicht horizontal scrollen
    When ich das Rezept öffne
    Then lässt sich die Detailansicht nicht horizontal scrollen

@CROSS-text
Feature: Texteingaben werden einheitlich normalisiert

  Jedes Textfeld der Anwendung behandelt Leerraum, unsichtbare Zeichen und zusammengesetzte
  Zeichen gleich – damit eingefügter Text aus Webseiten oder anderen Geräten nicht zu
  scheinbar gleichen, aber verschiedenen Werten führt.

  # @phase: SKELETON
  #
  # Querschnittliche Datei (Ablage-Regel im gherkin-workshop): Die Regel gilt für jedes
  # Textfeld – Zutat (Name, Basiseinheit), Rezept (Titel, Anweisung, Zutatenzeile) und jedes
  # künftige. Sie wird über einen geteilten Texttyp garantiert (ADR-S112-5); die Szenarien
  # hier nutzen die Zutaten-Seite als Vertreter, recipes.feature prüft die Rezeptfelder.
  #
  # Regel: Jede Folge von Leerraum (jedes Unicode-Leerzeichen einschließlich geschützter
  # Leerzeichen, Tabulator, Zeilenumbruch) wird zu einem Leerzeichen; unsichtbare Zeichen
  # (Leerzeichen ohne Breite U+200B, weiches Trennzeichen U+00AD, Wortverbinder U+2060,
  # Byte-Order-Mark U+FEFF) werden entfernt; der Text wird in die Unicode-Normalform NFC
  # gebracht und getrimmt – vor Prüfung und Speicherung (ADR-S135-1). Längen und Eindeutigkeit
  # beziehen sich auf den normalisierten Wert; ein „Zeichen" ist eine UTF-16-Codeeinheit, wie in
  # der bestehenden Längenprüfung und bei `maxlength` im Browser (ein Emoji zählt meist 2).
  # Client und Server normalisieren gleich, wo der Client selbst entscheidet (z. B. ob ein Feld
  # leer ist).
  # Bestehende Daten: im SKELETON per Drop+Recreate; eine Migration bestehender Werte ist
  # nicht vorgesehen.
  #
  # Ein Lauf für die ganze Datei (Lauf-Kommentar statt Einzel-Läufe): US-602/run-7 setzt den
  # geteilten Texttyp voraus und braucht dafür ein Ziel für seine Kante.

  Background:
    Given die Anwendung ist gestartet
    And ich navigiere zur Zutaten-Seite

  # @run-1 · Normalisierung · Full-Stack
  @CROSS-text-collapse
  Scenario: Mehrfacher Leerraum im Inneren wird zu einem Leerzeichen
    When ich auf "Zutat anlegen" klicke
    And ich als Name "rote" und "Linsen" mit mehrfachen Leerzeichen und einem Tabulator dazwischen einfüge
    And ich "kleine" und "Dose" mit mehrfachen Leerzeichen dazwischen als Einheit eingebe
    And ich auf "Speichern" klicke
    Then steht "rote Linsen" mit der Einheit "kleine Dose" in der Zutaten-Liste

  # Sieht gleich aus, muss gleich sein – typisch für Text, der von Webseiten kopiert wird.
  # @run-1 · Normalisierung · Full-Stack
  @CROSS-text-duplicate
  Scenario Outline: Ein nach der Normalisierung gleicher Name gilt als Duplikat
    Given die Zutat "<Vorhanden>" mit Einheit "g" existiert
    When ich auf "Zutat anlegen" klicke
    And ich als Name <Eingabe> eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Eine Zutat mit dem Namen '<Normalisiert>' existiert bereits."
    And steht "<Vorhanden>" genau einmal in der Zutaten-Liste

    Examples:
      | Vorhanden   | Eingabe                                                                   | Normalisiert |
      | rote Linsen | "rote" und "Linsen" mit zwei Leerzeichen dazwischen                       | rote Linsen  |
      | rote Linsen | "rote" und "Linsen" mit einem geschützten Leerzeichen dazwischen          | rote Linsen  |
      | rote Linsen | "rote" und "Linsen" mit einem schmalen geschützten Leerzeichen dazwischen | rote Linsen  |
      | Käse        | "Käse" mit einem „ä“ aus „a“ und kombinierendem Trema                     | Käse         |
      | Käse        | "Käse" mit einem Leerzeichen ohne Breite nach dem „K“                     | Käse         |
      | Käse        | "Käse" mit einem weichen Trennzeichen nach dem „K“                        | Käse         |
      | Käse        | "Käse" mit einem Wortverbinder nach dem „K“                               | Käse         |
      | Käse        | "Käse" mit einer Byte-Order-Mark nach dem „K“          | Käse         |

  # @run-1 · Normalisierung · Full-Stack
  @CROSS-text-length
  Scenario: Die Längengrenze gilt für den normalisierten Wert
    When ich auf "Zutat anlegen" klicke
    And ich einen Namen aus 30 Zeichen mit einem doppelten statt einem einfachen Leerzeichen im Inneren eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die neue Zutat mit einfachem Leerzeichen im Inneren in der Zutaten-Liste

  # @run-1 · Normalisierung · Full-Stack
  @CROSS-text-invisible-only
  Scenario: Ein Wert nur aus unsichtbaren Zeichen gilt als leer
    When ich auf "Zutat anlegen" klicke
    And ich als Name nur Leerzeichen ohne Breite eingebe
    And ich "g" als Einheit eingebe
    And ich auf "Speichern" klicke
    Then sehe ich die Fehlermeldung "Name darf nicht leer sein."

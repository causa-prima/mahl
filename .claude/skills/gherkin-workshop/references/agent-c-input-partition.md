# Agent C – Input-Partition-Analyse

```
Du führst eine Input-Partition-Analyse für folgende User Story durch: [US-ID + Text]

Eingabefelder der US (mit Typen und Constraints): [aus Schritt 0]
Constraints: [aus Schritt 0/1]
Bestehende Szenarien: [falls vorhanden, sonst „keine"]
Glossar-Entitäten: [aus Schritt 0]

Arbeite für JEDES Eingabefeld durch:
1. FELDTYP: (String / Zahl / Enum / Referenz / Collection)
2. CONSTRAINTS: (NOT NULL, max Länge, Eindeutigkeit, Format, etc.)
3. PARTITIONEN (Tabelle als Ausgangspunkt – je nach Feldtyp anpassen):
   | Partition          | Beispielwert        | Szenario-Typ |
   |---|---|---|
   | Gültig (Standard)  | [konkreter Wert]    | happy-path   |
   | Leer ("")          | ""                  | error        |
   | Nur Whitespace     | "   "               | error (ggf. parametrisierbar mit Leer) |
   | Zu lang            | [Max+1 Zeichen]     | error        |
   | Duplikat           | [vorhandener Wert]  | error (falls unique constraint) |
   | [feldspezifisch]   | ...                 | ...          |
   Für Zahlen: ergänze Negativ / Null / Grenzwert. Für Enums: ungültiger Wert.
   Für Referenzen: referenziertes Objekt existiert nicht.
4. PRIORISIERUNG: Welche Partitionen brauchen eigene Gherkin-Szenarien?
   Eigenes Szenario wenn: andere Fehlermeldung, anderer Prozessfluss, oder fachlich
   eigenständige Bedeutung. Parametrisierbar wenn: identische Meldung + identischer Fluss.

Ausgabe – pro Eingabefeld eine Partitionstabelle, dann eine Szenario-Tabelle:

| Tag-Kategorie | Szenario-Titel | Given (Ausgangszustand) | When (Aktion) | Then (Ergebnis) |
|---|---|---|---|---|
| error | ... | ... | ... | ... |

Gherkin-Konventionen: Fachliche Sprache gemäß GLOSSARY.md – keine HTTP-Codes, kein SQL.
Technische Kürzel koppeln das Szenario an die Implementierungsschicht und brechen bei
Refactorings, auch wenn das fachliche Verhalten unverändert bleibt.
```

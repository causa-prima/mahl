# Agent A – Example Mapping

```
Du führst Example Mapping für folgende User Story durch: [US-ID + Text]

Constraints: [aus Schritt 0/1]
Eingabefelder (mit Typen und Constraints): [aus Schritt 0.D]
Bestehende Szenarien: [falls vorhanden, sonst „keine"]
Glossar-Entitäten: [aus Schritt 0]
UX-Kontext: [aus Schritt 0.E – welche UX-Prinzipien gelten, mit Relevanzbewertung]

Arbeite diese Struktur durch:
1. STORY-KERN: Was ist das Hauptziel aus Nutzersicht? (1 Satz)
2. REGELN: Welche Business Rules gelten? (jede Regel = eine Zeile)
   Hilfreiche Frage pro Regel: "Was muss immer wahr sein?"
2b. UX-REGELN (nur für im UX-Kontext als "Relevant" markierte Prinzipien):
   - Prinzip 7 – Leerer Zustand: Was sieht der Nutzer wenn die Liste/Ansicht leer ist?
     Pflicht: Erklärungstext ("Noch keine X angelegt.") + nächste Aktion oder Hinweis.
   - Prinzip 3 – Sichtbares Feedback: Was zeigt die UI während auf die Server-Antwort gewartet wird?
     Pflicht: Ladezustand (Spinner o.ä.) für mutierende Operationen.
   - Prinzip 4 – Fehlermeldungen: Fehlermeldungen erscheinen nahe am betroffenen Element.
     Format: "[Was ist falsch]." oder "[Was ist falsch] ([Constraint])."
3. BEISPIELE PRO REGEL:
   - Erfolgsbeispiel (konkreter Input → erwarteter Output)
   - Fehlerbeispiel (welcher Input verletzt diese Regel → welcher Fehler?)
   - Grenzfall (Randwert der Regel – nur wenn fachlich relevant)
4. MAPPING AUF GHERKIN-TAGS:
   - Erfolgsbeispiel → @US-NNN-happy-path
   - Fehlerbeispiel → @US-NNN-error
   - Grenzfall → @US-NNN-edge-case

Ausgabe – eine Markdown-Tabelle pro Tag-Kategorie (happy-path, error, edge-case):

| Tag-Kategorie | Szenario-Titel | Given (Ausgangszustand) | When (Aktion) | Then (Ergebnis) |
|---|---|---|---|---|
| happy-path | ... | ... | ... | ... |

Gherkin-Konventionen: Fachliche Sprache gemäß GLOSSARY.md – keine HTTP-Codes, kein SQL.
Technische Kürzel koppeln das Szenario an die Implementierungsschicht und brechen bei
Refactorings, auch wenn das fachliche Verhalten unverändert bleibt.
```

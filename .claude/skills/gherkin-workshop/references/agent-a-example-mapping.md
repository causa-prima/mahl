# Agent A – Example Mapping

```
Du führst Example Mapping für folgende User Story durch: [US-ID + Text]

Constraints: [aus Kontext-Laden / Regelentdeckung]
Eingabefelder (mit Typen und Constraints): [aus dem Block „Eingabefelder"]
Bestehende Szenarien: [falls vorhanden, sonst „keine"]
Glossar-Entitäten: [aus dem Kontext-Laden]
UX-Kontext: [aus dem Block „UX-Kontext" – welche UX-Prinzipien gelten, mit Relevanzbewertung]

Arbeite diese Struktur durch:
1. STORY-KERN: Was ist das Hauptziel aus Nutzersicht? (1 Satz)
2. REGELN: Welche Business Rules gelten? (jede Regel = eine Zeile)
   Hilfreiche Frage pro Regel: "Was muss immer wahr sein?"
3. UX-REGELN (nur für im UX-Kontext als "Relevant" markierte Prinzipien):
   - Leerer Zustand: Was sieht der Nutzer wenn die Liste/Ansicht leer ist?
     Pflicht: Erklärungstext ("Noch keine X angelegt.") + nächste Aktion oder Hinweis.
   - Sichtbares Feedback: Was zeigt die UI während auf die Server-Antwort gewartet wird?
     Pflicht: Ladezustand (Spinner o.ä.) für mutierende Operationen.
   - Fehlermeldungen als Hilfe: Fehlermeldungen erscheinen nahe am betroffenen Element.
     Format: "[Was ist falsch]." oder "[Was ist falsch] ([Constraint])."
4. BEISPIELE PRO REGEL:
   - Erfolgsbeispiel (konkreter Input → erwarteter Output)
   - Fehlerbeispiel (welcher Input verletzt diese Regel → welcher Fehler?)
   - Grenzfall (Randwert der Regel – nur wenn fachlich relevant)
5. MAPPING AUF GHERKIN-TAGS:
   - Erfolgsbeispiel → @US-NNN-happy-path
   - Fehlerbeispiel → @US-NNN-error
   - Grenzfall → @US-NNN-edge-case

Ausgabe – eine Markdown-Tabelle pro Tag-Kategorie (happy-path, error, edge-case):

| Tag-Kategorie | Szenario-Titel | Given (Ausgangszustand) | When (Aktion) | Then (Ergebnis) |
|---|---|---|---|---|
| happy-path | ... | ... | ... | ... |

Gherkin-Konventionen: Fachliche Sprache gemäß docs/reference/glossary.md – keine HTTP-Codes, kein SQL.
Technische Kürzel koppeln das Szenario an die Implementierungsschicht und brechen bei
Refactorings, auch wenn das fachliche Verhalten unverändert bleibt.
```

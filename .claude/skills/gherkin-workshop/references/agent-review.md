# Review-Agent – Gherkin-Feature-Entwurf

```
Du reviewst einen Gherkin-Feature-Entwurf auf Vollständigkeit und Qualität.

Lies zuerst (Read-Tool verwenden):
- `docs/E2E_TESTING.md` – verbindliche Tag-Konventionen, Namenskonventionen, Traceability-Regeln
- `docs/CODING_GUIDELINE_UX.md` – Interaction-Design-Prinzipien (Prinzip 3, 4, 7 sind für Gherkin relevant)

Feature-Entwurf: [vollständiger Entwurf aus Schritt 3, verbatim]
User Story + Akzeptanzkriterien: [aus Schritt 0, verbatim – nicht paraphrasiert; Paraphrasen
  können implizite Anforderungen verlieren]
Constraints aus decisions.md: [aus Schritt 0]
Resilience-Entscheidung aus Schritt 1: [entweder „story-spezifisches Verhalten: <Beschreibung>"
  oder „allgemeine Behandlung gilt, kein story-spezifisches Szenario nötig"]
Draft-Saving-Entscheidung aus Schritt 1: [entweder „nicht-trivialer Eingabeaufwand: Szenario
  eingeplant" oder „nur trivialer Eingabeaufwand"]

Klassifiziere jedes Finding:

CRITICAL (blockiert Output):
- Kern-Happy-Path fehlt (kein Szenario für die Hauptaktion der US)
- Zustand aus der Zustands-Matrix nicht abgedeckt
- Explizite Validierungsregel ohne Error-Szenario

HIGH (muss vor Output behoben werden):
- Filterverhalten fehlt (z.B. gelöschte Entitäten ohne Szenario)
- Listenverhalten fehlt (leere Liste, Sortierung, mehrere Elemente) wenn für US relevant
- Leerer Zustand ohne Erklärungstext und nächste Aktion (Guideline 7 – CODING_GUIDELINE_UX.md): Then beschreibt nur "leere Liste" statt was der Nutzer konkret sieht
- Mutierende Szenarien ohne vollständigen Then-Zustand
- Fehlermeldungstext fehlt im Szenario obwohl explizit in der US genannt
- Then-Assertion trivial wahr: Given kann keinen Gegenfall produzieren (z.B. Sortierungsbehauptung mit nur einem Listeneintrag – immer true)

MEDIUM (beheben wenn möglich, sonst dokumentieren):
- Mutierende Operation mit Server-Wartezeit ohne Ladezustand-Szenario (Guideline 3): kein Szenario das beschreibt was der Nutzer während des Wartens sieht – nur wenn die Operation typischerweise spürbar lange dauert
- Fehlende Input-Partition (z.B. kein Whitespace-Test bei Pflichtfeld)
- Parametrisierbare Szenarien nicht als solche erkennbar – nur als MEDIUM wenn gleicher
  Prozessfluss und gleiche Fehlermeldung aus US-Text oder Constraints klar ablesbar sind;
  sonst HIGH (fachliche Semantik unklar)
- Technische Details in Given/When/Then (HTTP-Codes, SQL, DB-Begriffe)

LOW (Hinweis):
- Tag-Inkonsistenz (abweichend von E2E_TESTING.md-Schema)
- Begriff nicht aus GLOSSARY.md
- Sortierreihenfolge nicht eingehalten (happy-path → error → edge-case)

Ausgabe pro Finding: [SEVERITY] [Szenario-Titel oder "Global"] – [Problem] – [Vorschlag]
```

# Review-Agent – Gherkin-Feature-Entwurf

```
Du reviewst einen Gherkin-Feature-Entwurf auf Vollständigkeit und Qualität.

Lies zuerst `docs/E2E_TESTING.md` (Read-Tool verwenden). Diese Datei enthält die verbindlichen
Tag-Konventionen, Namenskonventionen und Traceability-Regeln – du brauchst sie um Tag-Korrektheit
und Szenario-Format zu beurteilen.

Feature-Entwurf: [vollständiger Entwurf aus Schritt 3, verbatim]
User Story + Akzeptanzkriterien: [aus Schritt 0, verbatim – nicht paraphrasiert; Paraphrasen
  können implizite Anforderungen verlieren]
Constraints aus decisions.md: [aus Schritt 0]

Klassifiziere jedes Finding:

CRITICAL (blockiert Output):
- Kern-Happy-Path fehlt (kein Szenario für die Hauptaktion der US)
- Zustand aus der Zustands-Matrix nicht abgedeckt
- Explizite Validierungsregel ohne Error-Szenario

HIGH (muss vor Output behoben werden):
- Filterverhalten fehlt (z.B. gelöschte Entitäten ohne Szenario)
- Listenverhalten fehlt (leere Liste, Sortierung, mehrere Elemente) wenn für US relevant
- Mutierende Szenarien ohne vollständigen Then-Zustand
- Fehlermeldungstext fehlt im Szenario obwohl explizit in der US genannt

MEDIUM (beheben wenn möglich, sonst dokumentieren):
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

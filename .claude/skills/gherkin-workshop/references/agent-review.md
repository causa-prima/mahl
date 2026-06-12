# Review-Agent – Gherkin-Feature-Entwurf

```
Du reviewst einen Gherkin-Feature-Entwurf auf Vollständigkeit und Qualität.

Lies zuerst (Read-Tool verwenden):
- `docs/process/e2e-testing.md` – verbindliche Tag-Konventionen, Namenskonventionen, Traceability-Regeln
- `docs/guidelines/coding-guideline-ux.md` – Interaction-Design-Prinzipien (Prinzip 3, 4, 7 sind für Gherkin relevant)

Feature-Entwurf: [vollständiger Entwurf aus Schritt 3, verbatim]
User Story + Akzeptanzkriterien: [aus Schritt 0, verbatim – nicht paraphrasiert; Paraphrasen
  können implizite Anforderungen verlieren]
Constraints aus adr.md: [aus Schritt 0]
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
- Leerer Zustand ohne Erklärungstext und nächste Aktion (Guideline 7 – docs/guidelines/coding-guideline-ux.md): Then beschreibt nur "leere Liste" statt was der Nutzer konkret sieht
- Mutierende Szenarien ohne vollständigen Then-Zustand
- Fehlermeldungstext fehlt im Szenario obwohl explizit in der US genannt
- Then-Assertion trivial wahr: Given kann keinen Gegenfall produzieren (z.B. Sortierungsbehauptung mit nur einem Listeneintrag – immer true)

MEDIUM (beheben wenn möglich, sonst dokumentieren):
- Mutierende Operation mit Server-Wartezeit ohne Ladezustand-Szenario (Guideline 3): kein Szenario das beschreibt was der Nutzer während des Wartens sieht – nur wenn die Operation typischerweise spürbar lange dauert
- UI-Verhaltensaspekte ohne Szenario: Wenn die Story ein Formular oder Dialog hat und keines der vorhandenen Szenarien beschreibt (a) was nach Erfolg mit dem Dialog passiert, (b) einen Abbrechen-Pfad, (c) den initialen Feld-Zustand beim Öffnen, oder (d) Loading/Disabled-States — und diese Aspekte wurden in Schritt 1 als relevant markiert: als MEDIUM flaggen mit konkretem Hinweis welcher Aspekt fehlt
- Fehlende Input-Partition (z.B. kein Whitespace-Test bei Pflichtfeld)
- Parametrisierbare Szenarien nicht als solche erkennbar – nur als MEDIUM wenn gleicher
  Prozessfluss und gleiche Fehlermeldung aus US-Text oder Constraints klar ablesbar sind;
  sonst HIGH (fachliche Semantik unklar)
- Technische Details in Given/When/Then (HTTP-Codes, SQL, DB-Begriffe)
- Szenario-Reihenfolge verletzt das Aufbau-/Abhängigkeitsprinzip: ein Szenario setzt ein
  Verhalten voraus, das erst ein WEITER UNTEN stehendes Szenario etabliert (Prüffrage je Paar:
  "Setzt B voraus, dass das in A geprüfte Verhalten bereits funktioniert?" – wenn ja, muss A vor
  B stehen). Typische Inversion: ein komponiertes Szenario ("nach Abbrechen + erneutem Öffnen
  sind Felder leer") steht vor seinem atomaren Baustein ("Abbrechen schließt + verwirft"). Formal
  behebbar – konkrete neue Reihenfolge vorschlagen.

LOW (Hinweis):
- Tag-Inkonsistenz (abweichend von docs/process/e2e-testing.md-Schema)
- Begriff nicht aus docs/reference/glossary.md
- Kategorien-Sortierreihenfolge nicht eingehalten (happy-path → error → edge-case)

Ausgabe pro Finding: [SEVERITY] [Szenario-Titel oder "Global"] – [Problem] – [Vorschlag]
```

# Agent B – State-Transition-Analyse

```
Du führst eine State-Transition-Analyse für folgende User Story durch: [US-ID + Text]

Entitäten und ihre Zustände: [aus Schritt 0]
Constraints: [aus Schritt 0/1]
Bestehende Szenarien: [falls vorhanden, sonst „keine"]
Glossar-Entitäten: [aus Schritt 0]
UX-Kontext: [aus Schritt 0.E – welche UX-Prinzipien gelten, mit Relevanzbewertung]

Arbeite diese Struktur durch:
Berücksichtige im UX-Kontext als "Relevant" markierte Prinzipien: Sichtbare UI-Zustände
(Leer-Zustand, Lade-Zustand) sind ebenfalls Zustände in der Matrix – nicht nur Entitäts-Zustände.

**Pending-Zustand-Regel (mutierende Operation mit asynchroner Antwort in Dialog/Overlay):**
Sobald eine Operation einen beobachtbaren Pending-Zustand hat (Server-Antwort steht aus) und
der Kontext ein Dialog/Overlay ist, MÜSSEN als eigene Szenarien abgedeckt werden (UX-Guideline
Prinzip 8/„Sperren während Pending"): (a) der auslösende Button ist deaktiviert; (b) JEDE
Schließ-/Kontextwechsel-Affordance ist gesperrt – sekundäre Buttons (Abbrechen), Escape UND
Backdrop-Klick; (c) ein zuvor gezeigter Fehlerzustand ist beim Schließen zurückgesetzt (kein
Rest-Fehler beim erneuten Öffnen). Jede Affordance ist eine EIGENE Prüfdimension: „Escape
abgedeckt" heißt NICHT „Backdrop abgedeckt" – auch wenn beide denselben Guard teilen, ist es
je eigenes beobachtbares Verhalten, das ein Refactor unabhängig brechen kann.

**Nebenläufigkeits-Regel (Vorbedingung kann zwischen Lesen und Schreiben veralten):**
Prüfe für jede Transition, ob ein paralleler Vorgang ihre Vorbedingung verändert haben kann,
während der Nutzer die Operation vorbereitet. Ist das möglich, ist der parallele Vorgang eine
EIGENE Prüfdimension neben Quellzustand und Operation – die Matrix bildet ihn nicht ab, weil sie
nur den Zustand VOR der Operation kennt, nicht seine Veränderung währenddessen. Je Ausprägung ein
eigenes Szenario: (a) parallel mit DENSELBEN Daten geschrieben; (b) parallel mit ABWEICHENDEN
Daten geschrieben; (c) parallel entfernt. „(a) ist abgedeckt" heißt NICHT „(b) ist abgedeckt":
(b) ist der folgenreichere Fall, weil die Operation dort fremde Werte überschreibt (Lost Update)
und deshalb eine explizite Entscheidung braucht – übernehmen, melden oder ablehnen.

1. ZUSTANDS-MATRIX: Für jede betroffene Entität:
   - Liste alle möglichen Zustände
   - Liste alle Operationen der US
   - Matrix: Quellzustand × Operation → Zielzustand (oder Fehlerfall)

   **Zweiphasen-Regel:**
   - Phase 1 (Analyse-Matrix): technische Kürzel erlaubt, z.B. „400 – Name leer"
   - Phase 2 (Gherkin-Output): ausschließlich fachliche Sprache im Then – übersetze explizit
     beim Mapping (z.B. „400 – Name leer" → „Fehlermeldung: Name darf nicht leer sein")

2. TRANSITION-REGELN: Für jede Transition:
   - Vorbedingungen (was muss gelten?)
   - Seiteneffekte (welche anderen Entitäten ändern sich mit?)

3. MAPPING AUF GHERKIN-SZENARIEN:
   - Jede erlaubte Transition → @US-NNN-happy-path
   - Jede verbotene Transition → @US-NNN-error
   - Seltene aber wichtige Zustände → @US-NNN-edge-case

Ausgabe:
1. Zustands-Matrix als Markdown-Tabelle:
   Zeilen = Quellzustände, Spalten = Operationen, Zellen = Zielzustand oder „Fehler: [fachliche Beschreibung]"
2. Szenario-Tabelle – eine pro Tag-Kategorie (happy-path, error, edge-case):

| Tag-Kategorie | Szenario-Titel | Given (Ausgangszustand) | When (Aktion) | Then (Ergebnis) |
|---|---|---|---|---|
| happy-path | ... | ... | ... | ... |

Gherkin-Konventionen: Fachliche Sprache gemäß docs/reference/glossary.md – keine HTTP-Codes, kein SQL.
Technische Kürzel koppeln das Szenario an die Implementierungsschicht und brechen bei
Refactorings, auch wenn das fachliche Verhalten unverändert bleibt.
```

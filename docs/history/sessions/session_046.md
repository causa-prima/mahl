# Session 046 – 2026-04-02 – Prozess-Arbeit (Skill-Reviews + implementing-scenario)

## Was wurde gemacht

### gherkin-workshop Skill – weitere Review-Zyklen (Priorität 1 aus Session 045)

Drei Iterationen eines Subagenten-Review-Loops durchgeführt:

**Iteration 1 – Findings (CRITICAL/HIGH eingearbeitet):**
- Schritt 0.B: Expliziter NEIN-Fall wenn keine Feature-Datei existiert
- Schritt 0: neue Sektion D (Eingabefelder für Agent B+C)
- Schritt 2: Einheitliches Tabellen-Ausgabeformat für alle drei Subagenten-Prompts
- Schritt 2: Explizite Eingabe-Checkliste für alle drei Agents (Referenz auf 0.A/0.C/0.D)
- Schritt 3: Widerspruch-Erkennungsleitfaden (inhaltlich, nicht strukturell)
- Schritt 4: Klarere MEDIUM-Behandlung (selbst fixen vs. User fragen vs. dokumentieren)
- Schritt 5: Dateinamenskonvention (`features/<entity-plural-english>.feature`)
- Schritt 5: Konflikt-Auflösung bei User-Feedback vs. dokumentierte Regel

**Iteration 2 – Findings (HIGH/MEDIUM eingearbeitet):**
- HTTP-Codes in Agent B: Trennung Analyse-Matrix vs. Gherkin-Output explizit
- Dialog-Abschluss: konkrete Kriterien statt „ausreichend Klarheit"
- Schritt 3: Parametrisierbare Szenarien kennzeichnen (`# Kandidat für Scenario Outline`)
- Review-Loop Schritt 4: Iterationszähler explizit mit „Iteration N von 3"
- Agent C Partitions: als Template markiert, feldtyp-spezifische Ergänzungen

**Iteration 3:** Keine CRITICAL/HIGH mehr. Reviewer: „produktionsreif". Drei MEDIUMs eingearbeitet.
**Einschränkung:** Alle drei Review-Iterationen haben allgemeine Qualitätskriterien geprüft, aber NICHT explizit die skill-creator-Qualitätsprinzipien (Progressive Disclosure, Lean-Prompt, Theory of Mind, Warum statt MUST). Der Skill gilt daher noch nicht als vollständig reviewt.
- Orchestrierender Agent ersetzt Platzhalter vor Prompt-Übergabe (klargestellt)
- Widerspruchs-Prüfung im Dialog explizit formuliert
- Dialog-Abschluss-Kriterien mit Konsistenzprüfung

**Zwischenfehler behoben:** User-Korrekturen während der Arbeit:
- Verweis „wie Agent A" aus Agent-B-Prompt entfernt (Agent B kennt Agent A nicht)
- Konflikt-Formulierung: Szenario ODER Regel kann angepasst werden (nicht nur die Regel)

### implementing-feature → implementing-scenario (Priorität 2 aus Session 045)

Skill umgebaut und umbenannt:
- Verzeichnis `implementing-feature/` → `implementing-scenario/`
- Name, Description, Aufruf-Konvention aktualisiert
- Schritt 0 Punkt 1 (ATDD-Gate): prüft jetzt das spezifische Szenario aus `$ARGUMENTS`, nicht irgendein Szenario der Story; expliziter Stopp mit Verweis auf `gherkin-workshop` wenn nicht vorhanden
- Schritt 1–3 komplett ersetzt durch Double-Loop:
  - Äußerer Loop: Playwright-Test zuerst, ROT bestätigen, stehen lassen
  - Innerer Loop: outside-in je Schicht (Backend-Integration → Domain → Service/Repository), jede Schicht braucht eigenen roten Test
  - Expliziter Satz: „Der E2E-Test deckt das mit ab" ist kein Argument für das Weglassen innerer Tests
  - E2E-Loop schließen: erst wenn alle inneren grün sind
- AGENT_MEMORY-Update in Schritt 3 und 6: Szenario-Status statt Story-Status; nächstes Szenario explizit benennen
- `CLAUDE.md` Navigations-Tabelle aktualisiert

### Fehler und Korrektur: Edit-Tool-Fallback

Beim ersten Edit-Versuch versagte das Edit-Tool (mehrzeiliger old_string über Leerzeilen). Statt weitere Ursachenanalyse wurde zu schnell auf Python-Fallback gewechselt. User hat das korrekt angesprochen – ab dann ausschließlich Edit-Tool verwendet (funktionierte mit präziseren Match-Strings).

## Nicht umgesetzt (verschoben)

- `implementing-scenario` Review-Loop (analog zu gherkin-workshop): steht als Priorität an
- `TDD_PROCESS.md` ergänzen (innerer Loop / Unit-Test-Pflicht für Domain-Typen)
- `gherkin-workshop` für US-904 anwenden (Feature-File vervollständigen)
- `SKELETON_SPEC.md` Audit

## Offene Punkte für nächste Session

1. **`implementing-scenario` Review-Loop** – Skill durch Subagenten-Review-Zyklus laufen lassen bis keine HIGH-Findings mehr.

   **Wie der Review-Loop funktioniert:**
   Der eval-Loop aus dem skill-creator (evals.json, Benchmark-Runs, Viewer) wird NICHT verwendet.
   Stattdessen werden die **Qualitätsprinzipien aus dem skill-creator** als Bewertungsmaßstab genutzt:
   Progressive Disclosure, Writing Style (Warum erklären statt MUST-Verbote, Theory of Mind),
   klare Output-Kontrakte, Lean-Prompt (nichts ohne Wirkung), imperative Form, Selbstständigkeit
   des Skill-Aufrufers ohne Zusatzwissen. Der Reviewer-Subagent bekommt:
   - Den zu reviewenden Skill
   - Die relevanten Projekt-Guidelines zum Fachinhalt (`TDD_PROCESS.md`, `E2E_TESTING.md`, `CODING_GUIDELINE_*.md`), damit er beurteilen kann ob die Anweisungen fachlich korrekt sind
   - Die Skill-Creator-Qualitätsprinzipien (s.o.) als Bewertungsmaßstab für die Instruktions-Qualität
   - Findings klassifizieren (CRITICAL / HIGH / MEDIUM / LOW), einarbeiten, wiederholen bis keine HIGH mehr

   **WICHTIG:** Dem Reviewer-Agenten NICHT mitteilen, wie viele Reviews bereits stattgefunden haben oder was vorher geändert wurde. Jeder Reviewer soll unvoreingenommen und maximal kritisch schauen – Vorwissen über frühere Iterationen würde die Kritikbereitschaft dämpfen.
2. **`gherkin-workshop` auf US-904 anwenden** – Feature-File vervollständigen und freigeben lassen
3. **`TDD_PROCESS.md` ergänzen** – innerer Loop / Unit-Test-Pflicht für Domain-Typen explizit
4. **`SKELETON_SPEC.md` Audit** – Entscheidungen vs. Implementation-Details trennen
5. **US-904 Implementierung** – erst nach gherkin-workshop und Feature-File-Freigabe

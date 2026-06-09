# CLAUDE.md – Navigationszentrale

## KRITISCH: dotnet in WSL

.NET ist **nur auf dem Windows-Host** installiert. Details: `docs/process/dev-workflow.md` (Sektion "KRITISCH: dotnet in WSL").

---

## Navigation: Was lese ich für welche Aufgabe?

| Aufgabe | Lies |
|---------|------|
| Session starten / Status prüfen | `docs/AGENT_MEMORY.md` |
| Szenario implementieren | Skill `implementing-scenario` verwenden (ein Szenario pro Durchlauf, Double-Loop TDD) |
| Backend-Endpoint schreiben | `docs/reference/architecture.md` (inkl. Sektion 0c Hexagonal Architecture) → `docs/reference/skeleton-spec.md` (API-Sektion) |
| E2E Testing / BDD/Gherkin / Outside-In ATDD | `docs/process/e2e-testing.md` |
| C#-Code schreiben (Backend, Tests) | `docs/guidelines/coding-guideline-general.md` → `docs/guidelines/coding-guideline-csharp.md` (enthält Verweise auf ROP/SumTypes/Stryker-Ergänzungen) |
| TypeScript/React-Code schreiben | `docs/guidelines/coding-guideline-general.md` → `docs/guidelines/coding-guideline-typescript.md` |
| Frontend-UX / Interaction Design | `docs/guidelines/coding-guideline-ux.md` |
| Allgemeine Coding-Prinzipien (KISS, Naming, Komplexität) | `docs/guidelines/coding-guideline-general.md` |
| Datenbank-Schema ändern | `docs/process/dev-workflow.md` → `docs/reference/skeleton-spec.md` (DB-Sektion) |
| Domain-Logik / Fachbegriff | `docs/reference/glossary.md` → `docs/reference/architecture.md` |
| Code schreiben / TDD / Mutation Testing | `docs/process/tdd-process.md` (Red→Green→Refactor gilt immer) + `docs/process/dev-workflow.md` |
| Build / Run / Migration | `docs/process/dev-workflow.md` |
| Definition of Done / NFRs | `docs/process/nfr.md` |
| Autor-Self-Review | `docs/process/review-checklist.md` |
| Review-Agent beauftragen | Skill `review-code` (Scope-Matrix + Spawning via `subagent_type`) |
| Workflow-/Prozess-Audit durchführen | Skill `review-workflow` verwenden |
| Projektdokumentation prüfen | Skill `review-docs` verwenden |
| Learnings dokumentieren | `docs/kaizen/lessons_learned.md` (Format: `docs/kaizen/process.md`) |
| Verhaltensprinzipien (immer gültig) | `docs/kaizen/principles.md` |
| Maßnahmen-Tracking | `docs/kaizen/countermeasures.md` |
| Retro durchführen | Skill `kaizen` verwenden |
| Technische Schuld tracken | `docs/AGENT_MEMORY.md` (Sektion "Technische Schuld") |
| Langsame Befehle dokumentieren | `docs/process/slow-commands.md` |
| Befehl ausführen (Timeout / Auswahl) | `docs/process/dev-workflow.md` (Sektion "Befehlsauswahl & Timeouts") |
| Task-Liste anlegen / verwalten | `docs/process/task-system.md` |
| Warum wurde X so entschieden? | `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`) |
| Was passierte in Session X? | `docs/history/sessions/index.md` → ggf. spezifische Session-Datei |
| Neuen Agenten beauftragen | `.claude/agents/` (bestehende Definitionen als Vorlage) + Skill `review-code` |
| Interface/API designen (Design It Twice) | Skill `design-an-interface` verwenden |
| Session abschließen | Skill `closing-session` verwenden |

---

## Task-System (Fortschritt & Planung)

Aufgaben mit ≥ 3 Schritten erfordern eine Task-Liste → Regeln: `docs/process/task-system.md`

---

## Globale Skills: Vorrang lokaler Regeln

Globale Skills (z.B. `tdd`) gelten als Baseline. Lokale Skills und Docs ergänzen sie und gewinnen bei Konflikten – insbesondere:
- TDD-Prozess: Skill `write-code` **ergänzt** den globalen `tdd`-Skill um Guideline-Pflichten, PFLICHT-OUTPUT und Selbst-Review; TDD läuft als Schritt 2 von `write-code`. Bei Konflikten gelten `write-code` und `docs/process/tdd-process.md`.

---

## Entscheidungsfreiheit

**Technische Details** (Validierungsregeln, Error Codes, Schema-Details, UI-Details) → **selbst entscheiden & in `docs/history/adr.md` dokumentieren**

**Business-Logic, Architektur-Änderungen, unklare Requirements** → **nachfragen**

Faustregel: Hat die Entscheidung Business-Impact? Nein → entscheide selbst. Ja → frage nach.
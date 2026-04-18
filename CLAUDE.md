# CLAUDE.md – Navigationszentrale

## KRITISCH: dotnet in WSL

.NET ist **nur auf dem Windows-Host** installiert. Details: `docs/DEV_WORKFLOW.md` (Sektion "KRITISCH: dotnet in WSL").

---

## Navigation: Was lese ich für welche Aufgabe?

| Aufgabe | Lies |
|---------|------|
| Session starten / Status prüfen | `docs/AGENT_MEMORY.md` |
| Szenario implementieren | Skill `implementing-scenario` verwenden (ein Szenario pro Durchlauf, Double-Loop TDD) |
| Backend-Endpoint schreiben | `docs/ARCHITECTURE.md` (inkl. Sektion 0c Hexagonal Architecture) → `docs/SKELETON_SPEC.md` (API-Sektion) |
| E2E Testing / BDD/Gherkin / Outside-In ATDD | `docs/E2E_TESTING.md` |
| C#-Code schreiben (Backend, Tests) | `docs/CODING_GUIDELINE_GENERAL.md` → `docs/CODING_GUIDELINE_CSHARP.md` (enthält Verweise auf ROP/SumTypes/Stryker-Ergänzungen) |
| TypeScript/React-Code schreiben | `docs/CODING_GUIDELINE_GENERAL.md` → `docs/CODING_GUIDELINE_TYPESCRIPT.md` |
| Frontend-UX / Interaction Design | `docs/CODING_GUIDELINE_UX.md` |
| Allgemeine Coding-Prinzipien (KISS, Naming, Komplexität) | `docs/CODING_GUIDELINE_GENERAL.md` |
| Datenbank-Schema ändern | `docs/DEV_WORKFLOW.md` → `docs/SKELETON_SPEC.md` (DB-Sektion) |
| Domain-Logik / Fachbegriff | `docs/GLOSSARY.md` → `docs/ARCHITECTURE.md` |
| Code schreiben / TDD / Mutation Testing | `docs/TDD_PROCESS.md` (Red→Green→Refactor gilt immer) + `docs/DEV_WORKFLOW.md` |
| Build / Run / Migration | `docs/DEV_WORKFLOW.md` |
| Definition of Done / NFRs | `docs/NFR.md` |
| Autor-Self-Review | `docs/REVIEW_CHECKLIST.md` |
| Review-Agent beauftragen | `docs/LLM_PROMPT_TEMPLATE.md` (Sektion "Agents") |
| Learnings dokumentieren | `docs/kaizen/lessons_learned.md` (Format: `docs/kaizen/PROCESS.md`) |
| Verhaltensprinzipien (immer gültig) | `docs/kaizen/principles.md` |
| Maßnahmen-Tracking | `docs/kaizen/countermeasures.md` |
| Retro durchführen | Skill `kaizen` verwenden |
| Technische Schuld tracken | `docs/AGENT_MEMORY.md` (Sektion "Technische Schuld") |
| Langsame Befehle dokumentieren | `docs/slow-commands.md` |
| Befehl ausführen (Timeout / Auswahl) | `docs/DEV_WORKFLOW.md` (Sektion "Befehlsauswahl & Timeouts") |
| Task-Liste anlegen / verwalten | `docs/TASK_SYSTEM.md` |
| Warum wurde X so entschieden? | `docs/history/decisions.md` |
| Was passierte in Session X? | `docs/history/sessions/INDEX.md` → ggf. spezifische Session-Datei |
| Neuen Agenten beauftragen | `docs/LLM_PROMPT_TEMPLATE.md` |
| Interface/API designen (Design It Twice) | Skill `design-an-interface` verwenden |
| Session abschließen | Skill `closing-session` verwenden |

---

## Task-System (Fortschritt & Planung)

Aufgaben mit ≥ 3 Schritten erfordern eine Task-Liste → Regeln: `docs/TASK_SYSTEM.md`

---

## Globale Skills: Vorrang lokaler Regeln

Globale Skills (z.B. `tdd`) gelten als Baseline. Bei Widersprüchen zu projektspezifischen Docs oder Skills **gewinnen immer die lokalen Regeln** – insbesondere:
- TDD-Prozess: `docs/TDD_PROCESS.md` und Skill `write-code` haben Vorrang vor dem globalen `tdd`-Skill

---

## Entscheidungsfreiheit

**Technische Details** (Validierungsregeln, Error Codes, Schema-Details, UI-Details) → **selbst entscheiden & in `docs/history/decisions.md` dokumentieren**

**Business-Logic, Architektur-Änderungen, unklare Requirements** → **nachfragen**

Faustregel: Hat die Entscheidung Business-Impact? Nein → entscheide selbst. Ja → frage nach.
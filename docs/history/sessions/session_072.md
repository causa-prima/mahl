# Session 072 – Subagenten-Extraktion für implementing-scenario

**Datum:** 2026-06-05
**Phase:** SKELETON 🔄

---

## Kontext

Analyse und Refactoring des `/implementing-scenario`-Skills: Identifikation von Teilen die als formale Subagenten oder deterministisches Script extrahiert werden sollten.

---

## Ergebnisse

### Analyse (kein Code)
- Drei Fragen zur Skill-Architektur beantwortet: Subagenten-Ausgliederung, formale Subagenten vs. allgemeiner Subagent, Workflow-Eignung
- Bidirektionale Kommunikation (SendMessage) empirisch verifiziert: funktioniert, aber erfordert `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (aktiviert) und resumed agents laufen immer im Hintergrund – `permissionMode: acceptEdits` in den Subagenten-Definitionen kompensiert das für Datei-Writes

### Neue Subagenten
- `.claude/agents/backend-layer-implementer.md` – C#-Backend-Schicht, `permissionMode: acceptEdits`
- `.claude/agents/frontend-layer-implementer.md` – TypeScript/React-Schicht, `permissionMode: acceptEdits`
- Beide: Docs-Lade-Logik, Test-Einschränkungen, TDD-Vorgehen und Ausgabeformat im System-Prompt; dynamischer Teil (Akzeptanzkriterien, YAGNI-Liste, E2E-Pfad) per Message

### QA-Script
- `.claude/scripts/qa-check.py` – ersetzt den LLM-basierten QA-Agenten (Idee verworfen)
- Führt Stryker selbst aus (`--layer backend|frontend`) → Report ist immer frisch, kein `touch`-Betrug möglich
- Hash über: Report-Inhalt (SHA-256), staged-Tree-Fingerprint (`git ls-files --stage`), git-basierte Checks
- Orchestrator-Verifikationsmodus: `--skip-stryker` liest bestehenden Report, gleicher Hash wenn gleicher Zustand
- Frische-Check: Datei-mtime aller geänderten Code-Dateien vs. Report-mtime (robuster als `.git/index`-Ansatz)
- Layer-scoped: Backend prüft `Server/`, Frontend prüft `Client/src/` → keine Kreuz-Kontamination bei sequentiellen Schichten

### Skill-Update (`implementing-scenario/SKILL.md`)
- Subagent-Prompt-Template (60+ Zeilen) durch kompakte Subagenten-Referenz ersetzt
- Schritt 4 (Orchestrator-Check) auf `qa-check.py` umgestellt: Script liefert mechanische Findings, Orchestrator bewertet nur noch Suppression-Validität und Unit-Test-Autorisierung
- Spawn-Regeln aktualisiert: `name`-Pflicht für SendMessage, `permissionMode`-Erklärung

### stryker.config.json
- `"json"` zu `reporters` hinzugefügt → Frontend-Stryker erzeugt jetzt `Client/reports/mutation-testing-report.json`

---

## Offene Punkte / Technische Schuld

- `qa-check.py` wurde noch nicht gegen einen echten Szenario-Lauf getestet (nur Smoke-Test mit `--skip-stryker`)
- Custom-Subagenten (`backend-layer-implementer`, `frontend-layer-implementer`) erfordern Session-Neustart nach Erstellung bevor sie via `subagent_type` adressierbar sind – beim nächsten Szenario prüfen
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` ist Voraussetzung für SendMessage – ist global aktiv, aber nicht explizit dokumentiert als Dependency des Skill-Flows

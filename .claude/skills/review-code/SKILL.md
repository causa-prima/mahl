---
name: review-code
description: >
  Code-Review nach einer Implementierung: Autor-Selbstcheck via REVIEW_CHECKLIST.md,
  dann Review-Agenten nach Scope (KLEIN/MITTEL/GROSS) spawnen und Findings iterativ fixen.
  Verwende diesen Skill nach abgeschlossener Implementierung oder wenn der User explizit
  eine Code-Review anfordert.
user-invocable: false
---

# Skill: review-code

## Wann dieser Skill aktiv wird

Wenn du nach einer Implementierung eine Code-Review durchführst, oder wenn der User explizit nach einer Review fragt.

---

## Review-Ablauf

Lege zu Beginn folgende Task-Liste an:
```
TaskCreate: "1. Autor-Selbstcheck"
TaskCreate: "2. Stryker Mutation Testing"
TaskCreate: "3. Review-Agenten spawnen"
TaskCreate: "4. Findings auswerten"
```

### 1. Autor-Selbstcheck (REVIEW_CHECKLIST.md)
→ TaskUpdate "1. Autor-Selbstcheck": in_progress

Gehe `docs/REVIEW_CHECKLIST.md` systematisch Punkt für Punkt durch:
- Architecture Layer (internal-Typen, kein InternalsVisibleTo, Ports-only-Tests)
- Allgemeine Prinzipien (KISS, Naming)
- Domain Modeling
- Komplexität & Refactoring
- Tests
- Test-Audit (US-Tag im Testnamen, Traceability, kein Gold-Plating)

**Wichtig: Alle ❌ Must-Fix-Findings sofort selbst beheben – BEVOR Agenten gespawnt werden.**
Dazu `write-code`-Skill verwenden (TDD Red→Green→Refactor nach `docs/TDD_PROCESS.md` einhalten!).
⚠️-Findings kommentieren, aber erst nach den Agenten entscheiden.

### 2. Stryker Mutation Testing (Pflicht)
→ TaskUpdate "1. Autor-Selbstcheck": completed | TaskUpdate "2. Stryker Mutation Testing": in_progress

Befehle je nach Scope (Details: `docs/DEV_WORKFLOW.md` – Sektion "Mutation Testing"):

| Scope | Befehl |
|-------|--------|
| Backend (C#) | `python3 .claude/scripts/dotnet-stryker.py` (Details: `docs/DEV_WORKFLOW.md`) |
| Frontend (TS) | `cd Client && npx stryker run` |
| Beides | beide Befehle sequenziell |

**Erwartung: 100 % Mutation Score** (alle Mutanten killed).

Überlebende Mutanten haben genau zwei erlaubte Ursachen:
1. **Fehlender Test** → mit `write-code`-Skill nachholen (TDD nach `docs/TDD_PROCESS.md`), dann erneut Stryker
2. **Äquivalenter Mutant oder ausgenommener Pfad** (z.B. `> 0` ↔ `>= 1`, Logging, Infrastructure/Boilerplate) → in `stryker-config.json` exkludieren + Begründung in `docs/history/decisions.md`

Kein Mutant darf stillschweigend ignoriert werden.

### 3. Review-Agenten spawnen
→ TaskUpdate "2. Stryker Mutation Testing": completed | TaskUpdate "3. Review-Agenten spawnen": in_progress

Scope bestimmt, welche Agenten nötig sind (siehe `docs/LLM_PROMPT_TEMPLATE.md`):

| Was wurde geändert? | Agenten |
|--------------------|---------|
| Änderung ohne Verhaltensänderung (z. B. Rename, Refactoring ohne Logik-Änderung) | `code-quality` |
| Neue Funktionalität oder Verhaltensänderung (Domain/Application-Layer) | `code-quality` + `functional` + `test-quality` |
| + API-Grenze, User-Input oder Auth berührt | + `security` |
| + Frontend-Komponenten geändert | + `ux-ui` |

**Hinweis an Agenten:** Die Projekt-Guidelines (`docs/CODING_GUIDELINE_*.md`) haben Vorrang vor
agenten-eigenen Checklisten. Abweichungen müssen explizit begründet werden.

### 4. Findings auswerten
→ TaskUpdate "3. Review-Agenten spawnen": completed | TaskUpdate "4. Findings auswerten": in_progress

**Vor dem Fixen:** Prüfen ob das Finding semantisch korrekt ist — "Es ist implementierbar" ≠ "Es ist das richtige Verhalten." Insbesondere bei Performance-Tradeoff-Argumenten oder stillen Fallbacks kritisch hinterfragen.

- ❌ Must Fix → mit `write-code`-Skill beheben, dann Review-Agent nochmals für den geänderten Teil
- ⚠️ Improvement → abwägen, bei Business-Impact nachfragen
- ✅ OK → weiter

---

## Guideline-Referenzen

- `docs/CODING_GUIDELINE_GENERAL.md` (KISS, Naming, Komplexität)
- `docs/CODING_GUIDELINE_CSHARP.md` / `docs/CODING_GUIDELINE_TYPESCRIPT.md`
- `docs/REVIEW_CHECKLIST.md`
- `docs/LLM_PROMPT_TEMPLATE.md` (Agent-Prompts)

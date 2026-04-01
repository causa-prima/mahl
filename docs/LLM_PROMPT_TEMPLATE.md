# LLM Prompt Templates – Index

<!--
wann-lesen: Wenn ein Review-Agent oder Workflow-Command gestartet werden soll
kritische-regeln:
  - Welche Agenten bei welchem Scope laufen: review-code SKILL (Scope-Matrix KLEIN/MITTEL/GROSS)
  - ux-ui nur bei Frontend, security nur bei Auth/externen Daten
-->

Alle Workflows sind als Skills oder Agents hinterlegt.

> **Coding-Richtlinien:** Jeder Agent, der Code schreibt oder reviewt, liest **zuerst** die passende Richtlinie:
> - C# (Backend, Tests): `docs/CODING_GUIDELINE_CSHARP.md`
> - TypeScript/React (Frontend): `docs/CODING_GUIDELINE_TYPESCRIPT.md`
> - Übersicht der Kernprinzipien: `docs/ARCHITECTURE.md` (Sektion 0)

## Skills (automatisch getriggert oder via `/skill-name`)

| Skill | Pfad | Wann |
|---|---|---|
| `implementing-feature` | `.claude/skills/implementing-feature/SKILL.md` | Feature implementieren (TDD → Review → Docs) |
| `design-an-interface` | `.claude/skills/design-an-interface/SKILL.md` | API oder Interface designen, mehrere Optionen vergleichen ("design it twice") |
| `closing-session` | `.claude/skills/closing-session/SKILL.md` | Session abschließen |
| `review-code` | `.claude/skills/review-code/SKILL.md` | Code-Review nach Implementierung |
| `write-code` | `.claude/skills/write-code/SKILL.md` | Vor dem Schreiben von Produktionscode |
| `skill-creator` | `~/.claude/skills/skill-creator/SKILL.md` | Neuen Skill erstellen oder bestehenden anpassen |

## Agents (Review-Agenten, via Task-Tool)

| Agent | Pfad | Wann |
|---|---|---|
| `code-quality` | `.claude/agents/code-quality.md` | Wartbarkeit, Architektur, Refactoring |
| `functional` | `.claude/agents/functional.md` | Edge Cases, Fehlerszenarien, Datenintegrität |
| `test-quality` | `.claude/agents/test-quality.md` | Test-Design, Lesbarkeit, Isolation |
| `ux-ui` | `.claude/agents/ux-ui.md` | Nur bei Frontend-Änderungen |
| `security` | `.claude/agents/security.md` | Nur bei Auth / externen Daten / sicherheitsrelevanten Änderungen |

Scope-Entscheidung (welche Agenten bei welcher Änderungsgröße): → `review-code` SKILL.

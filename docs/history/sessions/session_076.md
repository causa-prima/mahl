# Session 076 – 2026-06-10: Doc- und Prozess-Tuning (TDD Batch-RED, Review-Auditoren, docs/-Reorg)

Reine Prozess-/Doku-Session, kein Produktionscode. Mehrere zusammenhängende Umbauten.

## Implementiert

### 1. TDD: one-test-at-a-time → Batch-RED mit Backstop
- Kernregel umgestellt: Statt „immer nur ein Test pro RED→GREEN→REFACTOR" wird der **gesamte Test-Batch einer Schicht** geschrieben, kollektiv rot bestätigt, dann implementiert.
- Begründung (synchron, gegen Lehrbuch-TDD formuliert): one-test-at-a-time diente (1) Working-Memory-Entlastung – für Agenten irrelevant; (2) Schutz gegen vakuöse Tests/Gold-Plating – das übernimmt **Stryker (100% Mutation) + 100% Branch/Statement-Coverage** als mechanischer, stärkerer Backstop.
- Erhalten: **Test-zuerst** und **Spec-Mapping** (jede Assertion + jedes signifikante Given/When mappt auf ein Gherkin-Kriterium – das prüft Stryker NICHT).
- Betroffen: globaler `tdd`-Skill (Batch als Default, konditioniert auf Backstop), `docs/process/tdd-process.md`, `implementing-scenario`, beide layer-implementer-Agenten.
- **Hook `tdd_one_test.py` entfernt** (erzwang die alte Granularität mechanisch) – Registrierung in `check-code-quality-blocking.py` + Test gelöscht. Hook-Suite 60/60 grün.

### 2. Review-Agenten neu strukturiert
- Die 6 Reviewer hatten keine YAML-Frontmatter → nicht via `subagent_type` spawnbar. Frontmatter ergänzt (read-only Tools: `Read, Grep, Glob`).
- Umbenannt zu `<dimension>-auditor`: `code-quality-auditor`, `functional-correctness-auditor`, `test-quality-auditor`, `security-auditor`, `ux-ui-auditor`, `workflow-auditor`. Damit klare Dichotomie: Skills = `review-*`, Agenten = `*-auditor` / `*-implementer`.
- Neuer Skill **`review-workflow`** (self-contained): Prozess-/Workflow-Audit im Verbesserungs-Loop, spawnt pro Runde einen frischen `workflow-auditor` (Frische-Augen-Prinzip aus principles.md).
- `LLM_PROMPT_TEMPLATE.md` gelöscht (redundanter, verrottender Index); Verweise auf `review-code` / `.claude/agents` umgebogen.

### 3. docs/ restrukturiert
- Themen-Ordner `guidelines/ process/ reference/` + `stories/`; durchgängig **kebab-case**. Sentinels (`CLAUDE.md`, `AGENT_MEMORY.md`) und Pflicht-Konvention `SKILL.md` bleiben uppercase; snake_case-Records (`session_*`, `szenario_*`) bewusst belassen.
- ~200 Referenzen aktualisiert (scriptgestützt: `docs/X.md`-Pfade, bare `.md`-Cross-Links, `.py`-Hints), History/Archive als Records ausgenommen.
- `INDEX.md → index.md`, `PROCESS.md → process.md`.

## Probleme / Fundstücke

- **Funktionaler Bug durch Reorg:** `check-dependency-allowlist.py` schützte die Dependency-Datei per Regex `DEPENDENCIES\.md$`. Nach Rename auf `dependencies.md` matchte die Regex nicht mehr → Schutz ausgehebelt. Gefixt; der (von Pass 1 schon aktualisierte) Test war zwischenzeitlich rot.
- **YAML-Colon:** Ein `: ` (Doppelpunkt+Leerzeichen) in der Agent-`description:` ließ `workflow-auditor` stumm nicht registrieren (Agent-Parser strikter als Skill-Parser). Doppelpunkt entfernt.
- **Case-only-Rename:** `INDEX.md→index.md` etc. wurde von git (NTFS/WSL, `core.ignorecase=true`) nicht erkannt. Fix über Zwei-Schritt-Rename mit Temp-Namen. → ins Projekt-Gedächtnis aufgenommen.
- **Bare-Referenzen:** Das Projekt nutzt massiv Referenzen ohne `docs/`-Präfix – eine einzelne Grep-Klasse fängt nur die Hälfte.

## Ergebnisse

- Alles in **einem** Commit (`Doc- und Prozess-Tuning…`, Co-Authored Sonnet 4.6 + Opus 4.8).
- Verifikation: Hook-Tests 60/60; zwei unabhängige Methoden (eigene Greps + zwei Haiku-Ref-Audit-Agenten) bestätigen: keine veralteten Referenzen in lebenden Dateien.

## Offene Punkte

- `~/.claude/skills/tdd` (globaler Batch-Default) liegt außerhalb des Repos – wirkt global, hier nicht versioniert.
- US-904 Szenario 2 weiterhin offen (unverändert seit 075).

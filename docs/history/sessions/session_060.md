# Session 060 – 2026-04-16

**Phase:** SKELETON  
**Schwerpunkt:** Infrastruktur / Doku-Qualität

## Erledigtes

### Positiv-Formulierungen abgeschlossen
Letzte 5 ausstehende Dateien umgestellt:
- `~/.claude/CLAUDE.md`: "Don't sugarcoat" → "Be brutally honest"
- `~/.claude/skills/tdd/mocking.md`: "Don't mock:" → positiver Umformulierung
- `~/.claude/skills/skill-creator/agents/analyzer.md`: **DO NOT:** → **Scope – stay within:**
- `~/.claude/skills/skill-creator/agents/comparator.md`: "DO NOT try to infer..." → positiv
- `docs/CODING_GUIDELINE_CSHARP.md`: Abschlusszeile umformuliert

### Frontend UX/Interaction Design Guideline
- `docs/CODING_GUIDELINE_UX.md` neu erstellt: 7 Prinzipien (Least Surprise, Don't Make Me Think, Sichtbares Feedback, Fehlermeldungen als Hilfe, Destructive Actions, Konsistente Terminologie, Leerer Zustand)
- Jedes Prinzip: Entscheidungsregel (maschinell ausführbar) + ✅/❌-Beispiele, positive Sprache
- Verlinkung in: `CLAUDE.md`, `CODING_GUIDELINE_TYPESCRIPT.md`, `REVIEW_CHECKLIST.md`, `write-code`, `implementing-scenario`
- Progressive Disclosure: UX-Guideline nur bei `src/components/` und `src/pages/`, nicht bei Services/Domain

### Frontend-Wrapper-Scripts
Neue Scripts analog zu `dotnet-test.py` / `dotnet-stryker.py`:
- `.claude/scripts/vitest-run.py` – `--filter`, `--verbose`, kein Watch-Mode
- `.claude/scripts/playwright-test.py` – `--filter` (via `--grep`), `--verbose`
- `.claude/scripts/stryker-frontend.py` – `--mutate src/pages/Foo.tsx`, `--detail`
- `_util.py` erweitert: `run_npm()` analog zu `run_dotnet()`
- `DEV_WORKFLOW.md` aktualisiert: Scripts, Timeout-Tabelle, KRITISCH-Block

### Hook check-bash-permission.py
- 5 neue WRONG_APPROACH-Einträge: `npm run test:e2e`, `npm run test`, `npx vitest`, `npx playwright`, `npx stryker` → zeigen direkt auf Python-Script
- 3 ALLOW-Einträge entfernt (npx via cmd.exe)
- 3 `_SMART_DENY_HINTS` entfernt (jetzt in WRONG_APPROACH)
- `kritische-regeln` in DEV_WORKFLOW.md auf Meta-Regel reduziert: "Hook erzwingt + zeigt richtigen Befehl"
- `test-bash-permission.py` für neue Patterns aktualisiert

## Offen / Nächste Session
- Review + Refactoring `check-bash-permission.py` (User-Wunsch)
- Stryker abschließen + Commit für US-904 Szenario 1

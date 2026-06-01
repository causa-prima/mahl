# Session 068 – 2026-05-29

**Phase:** SKELETON 🔄
**Ziel:** US-904 Szenario 2 „Zutat anlegen" implementieren

## Was versucht wurde

- Architektur-Check (Schritt 0) vollständig durchgeführt: Scope, API-Kontrakt, ETag-Entscheidung, YAGNI-Liste
- `POST /api/ingredients` 201-Response-Entscheidung in `decisions.md` dokumentiert
- ETag für `GET /api/ingredients/{id}` aus Szenario-2-Scope gestrichen (gehört zum Endpoint-Szenario)
- Zwei Frontend-Subagenten gespawnt – beide durch User-Interaktion (Tool-Call-Ablehnung) vorzeitig beendet, unvollständige Arbeit hinterlassen
- Dritter Subagent hat Frontend-Layer weitgehend implementiert (useResultQuery, useResultMutation, match.ts, ingredientsApi.ts, IngredientsPage.tsx, CreateIngredientDialog.tsx) – aber Stryker-Score bei 46% und offene Fragen zu YAGNI der Hooks
- Alle Working-Tree-Änderungen in `Client/src/` wurden revertiert (außer `eslint.config.js`)

## Was abgeschlossen ist

- `decisions.md`: POST /api/ingredients 201-Response dokumentiert, ETag-Scope korrigiert, weitere Korrekturen (weekly-pool-Pfad, "Migration ausstehend"-Hinweis entfernt)
- `Client/eslint.config.js`: `.flat`-Fix für react-hooks Flat-Config-API (war schon committed-Stand falsch)
- `.claude/scripts/eslint-run.py` + `jscpd-run.py`: neue WSL-Wrapper-Scripts (analog zu vitest-run.py)
- `.claude/hooks/check-bash-permission.py`: Hints für die neuen Scripts ergänzt
- `docs/kaizen/lessons_learned.md`: Session 068 mit 5 Einträgen dokumentiert

## Was noch aussteht

- **REVERT:** Working Tree in `Client/src/` enthält unvollständige Änderungen → bei nächstem Start rückgängig machen (Details in AGENT_MEMORY.md)
- **Offene Frage klären:** `MutationState` mit 4 Zuständen (Guideline-Pattern) vs. YAGNI (nur pending+success für dieses Szenario) – vor nächstem Subagenten-Aufruf entscheiden
- **US-904 Szenario 2 vollständig implementieren** – Frontend + Backend (inkl. ETag für GET /api/ingredients)

## Lessons Learned (Kurzfassung)

- Orchestrator darf keine Coding-Guidelines lesen (HOW-Dokumente gehören dem Subagenten)
- User-Interaktion während Subagenten-Ausführung bricht den Agenten ab → vorher kommunizieren: "alle Tool-Calls freigeben"
- Viele Stryker-Suppressionen = Signal für mögliches Gold-Plating → erst YAGNI prüfen
- `# --allow-once` nur für destruktive Einzelfall-Ausnahmen, nicht für Lesebefehle
- Orchestrator schreibt keinen Produktionscode (auch nicht "kleine" Fixes)

# Session 075 – 2026-06-09

**Phase:** SKELETON (Tooling/Prozess)
**Thema:** review-docs – implementing-scenario SKILL + Subagenten iterativ verbessert (5 Review-Runden)

---

## Was wurde gemacht

Iterativer Review-Loop für drei Dateien:
- `.claude/skills/implementing-scenario/SKILL.md`
- `.claude/agents/backend-layer-implementer.md`
- `.claude/agents/frontend-layer-implementer.md`

5 Review-Runden mit jeweils einem frischen Subagenten. Nach jeder Runde: Findings bewertet, mit User diskutiert, Änderungen umgesetzt.

### Inhaltliche Änderungen (kumuliert)

**Architektur-Entscheidung:** Frontend-Subagent implementiert beide Schichten (Komponente + Service-Client) in einem einzigen Aufruf sequenziell (outside-in). Begründung: Service-Clients sind für dieses Projekt typischerweise dünn (~20–40 Zeilen), kein eigener Review-Point nötig.

**Korrekturen:**
- Frontend-agent description: war „eine Schicht pro Aufruf" → jetzt „beide Frontend-Schichten, einmal aufgerufen"
- Spawn-Regel in SKILL.md: Frontend-Ausnahme von „EINE Schicht pro Subagent" explizit ergänzt
- Stryker-Survivor nicht-beobachtbar: Widerspruch zwischen SKILL.md (Unit Test) und Agenten (Suppression) behoben → beide sagen jetzt: Suppression (technisch erzwungene Zweige; der Subagent hätte das vor dem Return beheben müssen)
- `run_in_background: false`-Begründung korrigiert: Grund ist nicht „Haupt-Thread braucht Output", sondern „Berechtigungsanfragen werden sonst automatisch abgelehnt"
- ADR-Suche: `--full`-Flag erklärt; zwei-phasige Recherche (Orchestrator: cross-cutting + story; Subagent: resource-Tags) dokumentiert
- PLANUNG-Phase: Rückfragen gesammelt in einer Antwort; max. 2 Runden, dann Nutzer Situation erklären
- Staging-Protokoll: Subagent beschreibt Setup-Änderungen nach Freigabe; Orchestrator stagt diese nach
- Stryker-Survivor-Routing: schicht-spezifisch (Backend: via HTTP; Frontend: via Komponenten-API)
- Findings-Übergabe: Subagent führt qa-check nach Korrekturen erneut aus und liefert aktualisierten Hash
- Review-Code-Eingaben: „gemeinsam ermittelte ADRs" statt nur Orchestrator-ADRs
- Commit: git add explizit; Co-Authored-By vereinfacht
- `--skip-stryker`-Erklärung inline ergänzt
- Ausgabe: `git diff --name-only` statt Diff
- PLANUNG-Formulierung: „Details nicht explizit geklärt in übergebenen AK/Scope-Grenzen"
- „Vorgehen (strikt)" → „Vorgehen" in beiden Agenten
- GRUNDSATZ: Negativbeispiele vereinfacht, dann gestrichen (positiver Maßstab reicht)
- Fake-it-till-you-make-it: kurze Klammererklärung ergänzt
- SumTypes-Bedingung in Backend-Agent geschärft: „Ergibt die PLANUNG Sum-Types als nötig: vor RED lesen"
- Commit-Mapping: Beschreibung klarer; Beispiel beibehalten
- decisions.py-Kurzreferenz: refs-Flag ergänzt

**Auch geändert (zu Beginn der Session, vor Review-Loop):**
- `docs/CODING_GUIDELINE_CSHARP.md` + `docs/CODING_GUIDELINE_TYPESCRIPT.md`: Persona-Präfixe entfernt
- `CLAUDE.md`: TDD-Skill-Beziehung präzisiert

---

## Probleme / Auffälligkeiten

- **Frontend-Description-Inkonsistenz selbst eingebaut:** Nach der Entscheidung „ein Frontend-Subagent für beide Schichten" wurde SKILL.md aktualisiert, aber die agent-description nicht synchron gehalten. Das wurde erst im nächsten Review-Lauf gefunden. Lessons: Bei strukturellen Änderungen immer alle zugehörigen Dateien (SKILL.md + agent-descriptions + spawn-Regeln) gleichzeitig prüfen.
- **Reviewer-Kontext-Verwechslung:** In Round 4 glaubte der Reviewer, Kontext-Infos aus meinem Review-Prompt seien dauerhaft im Systemkontext verfügbar. Dadurch wurden OVERLOAD-Findings für Inhalte gemeldet die nur in SKILL.md selbst stehen – nicht in einem System-Prompt. Findings #15/#16 waren deshalb INVALID.
- **Suppression vs. Unit Test:** Echte inhaltliche Inkonsistenz zwischen SKILL.md und Agenten-Definitionen (beide sagten different Dinge für „nicht beobachtbarer Survivor"). Behoben durch Diskussion: Die einzigen wirklich nicht-beobachtbaren Fälle sind technisch erzwungene Zweige (exhaustiver default-case) – dafür ist Suppression korrekt.

---

## Offene Punkte

- US-904 Szenario 2 neu implementieren (steht weiterhin aus)
- `review-docs` für andere Docs noch nicht erledigt (war nur SKILL + Subagenten im Scope)
- Commit dieser Session noch ausstehend (user-gewünscht: nur stagen, kein Commit)

# Session 056 – 2026-04-14

## Überblick

Kaizen-Retro (Sessions 048–055) + Bash-Permission-System-Umbau + CM #1-Umsetzung + TypeScript-Fehlerbehandlungs-Architekturentscheidung.

---

## Durchgeführt

### Kaizen-Retro (Sessions 048–055)

- `lessons_learned.md` archiviert → `docs/kaizen/archive/session_048_to_055.md`
- Neue `lessons_learned.md` aus Template angelegt
- `countermeasures.md`: CM#3 (YAGNI) verschärft, neue OFFEN-CM für Bash-Permission-System (A1)
- `docs/kaizen/PROCESS.md`: Neue Sektion "Umsetzung offener Maßnahmen" – Regel 1 (AGENT_MEMORY) + Regel 2 (Eskalation nach 2 Retros ohne Umsetzung)
- `retro_report.py`: Abschnitt 9 "ESKALIERT" implementiert (automatisch, ersetzt manuellen Check im Skill)
- `kaizen/SKILL.md`: Schritt F für eskalierten CMs + AGENT_MEMORY-Pflicht für neue OFFEN-Einträge
- `write-code/SKILL.md`: YAGNI-Bullet um Per-Member-Frage erweitert
- `gherkin-workshop/references/agent-review.md`: HIGH-Finding "trivial-wahre Then-Assertion" ergänzt

### Bash-Permission-System (CM A1 → AKTIV)

- `check-bash-permission.py` vollständig umgebaut:
  - Auto-deny für alle unbekannten Befehle (statt "ask")
  - `# --allow-once`-Marker für einmalige Ausnahmen mit User-Bestätigung
  - Log in `.claude/tmp/denied-commands.log` mit `[AUTO-DENY]`/`[ONE-TIME]`-Markern
  - Smart-Deny-Hints: zielgerichtete Fehlermeldungen
  - Neue Allow-Patterns: `npx vitest/playwright/stryker` via cmd.exe, `dotnet run`
- `test-bash-permission.py` entsprechend aktualisiert – alle 160 Tests grün
- `DEV_WORKFLOW.md`: `settings.local.json`-Referenz entfernt, Befehlsauswahl auf neues System aktualisiert

### CM #1: Iterations-Vorwissen (OFFEN → AKTIV)

- `review-code/SKILL.md` Schritt 3: Pflicht-Hinweis ergänzt – keine früheren Findings, keine false-positive-Labels an Agenten übergeben
- `countermeasures.md`: Status AKTIV

### TypeScript-Fehlerbehandlungs-Architektur

Lange Diskussion über plain Promise vs. ResultAsync, ausgeweitet zur vollständigen Architekturentscheidung:

**Entschiedenes Muster:**
```
Service-Funktion   →  ResultAsync<T, DomainError>    (domain errors als Werte, kein throw)
useResultMutation  →  MutationState<T, DomainError>  (React Query vollständig gekapselt)
Komponente         →  matchState() / matchKind()      (Compile-Fehler bei fehlendem Fall)
QueryCache.onError →  Toast                          (Netzwerk/500 zentral)
```

- `decisions.md`: Neue Sektion "Service-Layer + Custom Hooks + match()-Pflicht"
- `CODING_GUIDELINE_TYPESCRIPT.md`: Abschnitt 4b vollständig dokumentiert (useResultMutation, useResultQuery, match-Helpers, Vollbeispiel), Verbotene-Muster-Tabelle erweitert

**Verworfen:** F# + Fable + Elmish (Agenten-Codegenerierung zu unzuverlässig – Versions-Drift, Interop-Halluzinationen)

**Code-Migration:** Ausstehend – wird bei US-904 Szenario 2 mitgemacht

### Nebendiskussionen (kein Code)

- TypeScript structural vs. nominal typing, Discriminated Unions, illegale Zustände verhindern
- React Query: Zweck, `useMutation`/`useQuery`, QueryCache
- Background-Agents: Terminierung, Sub-Agenten-Kommunikation, Koordinationsansatz für implementing-scenario
- Deep-Link-Anforderung: als offenes TODO identifiziert (vor US-602 besprechen)

---

## Offen / Zurückgestellt

- Code-Migration `ingredientsApi.ts` von plain Promise → ResultAsync + useResultMutation: bei Szenario 2
- `useResultMutation`/`useResultQuery`/`matchState`/`matchKind` implementieren: bei Szenario 2
- ESLint-Regel (kein direkter `state.status`-Zugriff): nach Implementierung der Wrapper
- Frontend-Wrapper-Scripts (vitest, playwright, stryker): separater Task
- Deep-Link-Anforderung: offenes TODO, vor US-602 besprechen
- Backend Stryker erneut ausführen (VS wurde aktualisiert): noch ausstehend
- npm audit (1 High-Severity): noch ausstehend

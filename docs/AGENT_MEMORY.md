# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss: Mit User klären was wohin ausgelagert werden soll – sollte aber nie vorkommen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/decisions.md`
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, PROCESS)

**Letzte Aktualisierung:** 2026-06-01 (Session 069 – US-904 Szenario 2 abgebrochen, Prozessverbesserung priorisiert)
**Phase:** SKELETON 🔄 – US-904 Szenario 1 vollständig abgeschlossen; Szenario 2 Working-Tree-Stand vorhanden aber REVERT ausstehend

---

## Was ist implementiert

Anwendungscode (US-904 Szenario 1 vollständig, committed):
- `Infrastructure/DatabaseTypes/IngredientDbType.cs` (nur `Id Guid`)
- `Infrastructure/MahlDbContext.cs`
- `Server/Endpoints/IngredientsEndpoints.cs` (GET /api/ingredients → hardcoded `[]`)
- `Server/Program.cs` + `Server/appsettings.json`
- `Server.Tests/Helpers/TestWebApplicationFactory.cs` + `EndpointsTestsBase.cs`
- `Server.Tests/IngredientsEndpointsTests.cs` (1 Test grün)
- `Client/src/pages/IngredientsPage.tsx` (Empty State: Hinweis + "Zutat anlegen"-Button)
- `Client/src/pages/IngredientsPage.test.tsx` (1 Test grün, via MSW)
- `Client/src/services/ingredientsApi.ts` (plain Promise, GET /api/ingredients)
- `Client/src/mocks/server.ts` + `Client/src/test/setup.ts` (MSW-Infrastruktur)
- `Client/src/App.tsx` (BrowserRouter + Route /ingredients)
- `Client/src/main.tsx` (QueryClientProvider)
- `Client/vite.config.ts` (test: happy-dom, setupFiles, include)
- `Client/stryker.config.json` (main.tsx, src/test/**, src/mocks/** ausgeschlossen)
- `Client/e2e/ingredients.spec.ts` (Szenario 1 grün, Szenario 2 skip – korrekt)
- `features/ingredients.feature` (UX-Update: "Zutat anlegen", Empty-State-Text, Undo-Toast, Loading-State-Szenarien)

Working Tree (NICHT committed, REVERT ausstehend):
- `Infrastructure/DatabaseTypes/IngredientDbType.cs` (Name, DefaultUnit, DeletedAt hinzugefügt)
- `Infrastructure/Migrations/` (neu – InitialCreate, aber Gold-Plating-Code im Server)
- `Server/Endpoints/IngredientsEndpoints.cs` (GET+POST mit Gold-Plating-Validierung)
- `Server/Dtos/`, `Server/Types/NonEmptyTrimmedString.cs` (Gold-Plating)
- `Server.Tests/` (angepasst)
- `Client/src/pages/IngredientsPage.tsx`, `CreateIngredientDialog.tsx` (neu)
- `Client/src/hooks/useResultQuery.ts`, `Client/src/types/mutationState.ts` (neu)
- `.editorconfig` (Infrastructure/Migrations Sektion – BEHALTEN, korrekt)
- `.claude/scripts/stryker-parse-survivors.py` (neu, nützlich – BEHALTEN)

Infrastruktur (unverändert):
- `mahl.sln` + 3 `.csproj`-Projekte, `Client/` mit allen Paketen inkl. Stryker + MSW
- `features/resilience.feature` (5 Szenarien, @NFR-resilience, Scope MVP)

---

## Nächste Prioritäten (Reihenfolge bindend; keine Nummerierung verwenden, sondern nur Anstriche)

- **Kaizen-Retro** (Jenga-Score -57, RETRO FÄLLIG) – zu Beginn der nächsten Session.

- **Prozessverbesserungen** (alle vor Szenario-2-Neuimplementierung umsetzen):
   - **SKILL `implementing-scenario`**: Orchestrator-Check auf Produktionscode ausweiten (Diff gegen Given/When/Then); Stryker-Suppressionen mit Vorwärts-Referenz automatisch als ❌ behandeln
   - **Subagenten-Prompt-Template**: Stryker-Übergabe = vollständiger Lauf ohne `--mutate` + Pfad zur HTML-Report-Datei; am Ende einen Prozessverbesserungs-Abschnitt fordern ("Was hat nicht funktioniert, was braucht besseres Tooling?")
   - **Bash-Permission-Hook**: Hint für `sed`-Aufrufe ergänzen (→ Read-Tool mit offset/limit-Parametern)
   - **allow-once-Mechanismus**: Lösung für das Problem, dass nach einem Deny unklar ist welche Befehle freigegeben sind (z.B. Hook der bei Session-Start oder erstem Bash-Deny eine Liste erlaubter Befehle ausgibt)
   - **DLL-Lock / Backend-Start**: Tooling verbessern damit vor Stryker/Build automatisch geprüft wird ob ein dotnet-run-Prozess läuft

- **`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`** in globale `settings.json` eintragen (vor nächster Session).

- **REVERT Working Tree** (nach Prozessverbesserung, vor Neuimplementierung):
   - `git restore` für alle modifizierten Server/Infrastructure/Client-Dateien außer `.editorconfig` und `.claude/scripts/stryker-parse-survivors.py`
   - `git clean -f Server/Dtos/ Server/Types/ Server/Domain/ Infrastructure/Migrations/ Client/src/hooks/ Client/src/pages/CreateIngredientDialog.tsx Client/src/types/mutationState.ts`

- **US-904 Szenario 2 neu implementieren** (mit verbessertem Prozess) – nur was das Szenario fordert: POST /api/ingredients (happy path, kein Validierungsfehler-Code), GET mit ETag (Content-Hash SHA-256). ETag für `GET /api/ingredients/{id}` (xmin): wird beim entsprechenden Endpoint-Szenario umgesetzt, NICHT hier.

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität die über MVP hinausgeht: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/CODING_GUIDELINE_UX.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch – erst ab US-602 relevant |
| Frontend Service | `fetchIngredients` als plain Promise – Migration auf ResultAsync ausstehend | Mittel |
| Frontend Stryker | `ConditionalExpression` (`if (true)`) + `ArrowFunction` NoCoverage in `IngredientsPage.tsx` – bewusst belassen, Szenario 2 killt sie | Mittel |
| Frontend Stryker | `ingredientsApi.ts` URL-Survivor: real gap (React Query schluckt Fetch-Fehler, Fallback `= []`); nicht supprimiert | Mittel |
| Frontend Stryker | `= []` Default in `IngredientsPage.tsx` supprimiert – Suppression entfällt wenn Loading-State-Szenario implementiert ist | Niedrig |
| E2E-Test | `EmptyDb`-Test ohne DB-Reset – latent flaky wenn DB vorher befüllt | Niedrig |

---

## Offene Fragen

- **Soll YAGNI für useResultQuery/MutationState gelten?** → Nur `pending|success` implementieren oder vollständige Union? TypeScript-Exhaustiveness-Check erzwingt alle Zweige. Klären vor Szenario-2-Implementierung.

# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss: Mit User klären was wohin ausgelagert werden soll – sollte aber nie vorkommen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/decisions.md`
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, PROCESS)

**Letzte Aktualisierung:** 2026-04-18 (Session 065 – Szenario 1 abgeschlossen)
**Phase:** SKELETON 🔄 – US-904 Szenario 1 vollständig abgeschlossen inkl. UX-Update (Guideline 6+7+5)

---

## Was ist implementiert

Anwendungscode (US-904 Szenario 1 vollständig):
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
- `features/ingredients.feature` (UX-Update: Guideline 6+7+5 angewendet – "Zutat anlegen", Empty-State-Text, Undo-Toast, Loading-State-Szenarien)

Infrastruktur (unverändert):
- `mahl.sln` + 3 `.csproj`-Projekte, `Client/` mit allen Paketen inkl. Stryker + MSW
- `features/resilience.feature` (5 Szenarien, @NFR-resilience, Scope MVP)

---

## Nächste Prioritäten (Reihenfolge bindend)

- **US-904 Szenario 2:** `/implementing-scenario @US-904-happy-path "Zutat anlegen"` – inkl. Code-Migration `ingredientsApi.ts` → ResultAsync + useResultQuery + useResultMutation + **ETag-Support für `GET /api/ingredients` (Content-Hash) und `GET /api/ingredients/{id}` (xmin)**.
- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (d.h. Funktionalität die über MVP hinausgeht: Update einer Zutat + Tags für Zutaten).
- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.
- **Visuelle Konsistenz-Guideline:** `docs/CODING_GUIDELINE_UX.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch – erst ab US-602 relevant |
| Frontend Service | `fetchIngredients` als plain Promise – Migration auf ResultAsync + useResultQuery ausstehend (bei Szenario 2) | Mittel |
| Frontend Stryker | `ConditionalExpression` (`if (true)`) + `ArrowFunction` NoCoverage in `IngredientsPage.tsx` – bewusst belassen, Szenario 2 killt sie | Mittel |
| Frontend Stryker | `ingredientsApi.ts` URL-Survivor: real gap (React Query schluckt Fetch-Fehler, Fallback `= []`); nicht supprimiert | Mittel |
| Frontend Stryker | `= []` Default in `IngredientsPage.tsx` supprimiert – Suppression entfällt wenn Loading-State-Szenario implementiert ist | Niedrig |
| E2E-Test | `EmptyDb`-Test ohne DB-Reset – latent flaky wenn DB vorher befüllt | Niedrig |

---

## Offene Fragen

_Keine offenen Fragen_

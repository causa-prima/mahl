# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss: Mit User klären was wohin ausgelagert werden soll – sollte aber nie vorkommen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/decisions.md`
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, PROCESS)

**Letzte Aktualisierung:** 2026-06-04 (Session 070 – Kaizen-Retro + Revert Gold-Plating Working Tree abgeschlossen)
**Phase:** SKELETON 🔄 – US-904 Szenario 1 vollständig abgeschlossen; Szenario 2 bereit zur Neuimplementierung

---

## Nächste Prioritäten (Reihenfolge bindend; keine Nummerierung verwenden, sondern nur Anstriche)

- **decisions.md verbessern**: eindeutige IDs (DEC-XXX), Discoverability und Durchsuchbarkeit für Subagenten-Referenzierung prüfen – Voraussetzung für A1c (`#pragma DEC-XXX`-Enforcement in `implementing-scenario` Skill + Subagenten-Prompts)

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

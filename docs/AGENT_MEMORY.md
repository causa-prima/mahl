# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss: Mit User klären was wohin ausgelagert werden soll – sollte aber nie vorkommen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process)

**Letzte Aktualisierung:** 2026-06-10 (Session 076 – Doc-/Prozess-Tuning: TDD Batch-RED, Review-Auditoren, docs/-Reorg; committed + gepusht)
**Phase:** SKELETON 🔄 – US-904 Szenario 1 abgeschlossen; Szenario 2 bereit zur Neuimplementierung (jetzt mit Batch-RED-Prozess + `*-auditor`-Agenten)

---

## Nächste Prioritäten (Reihenfolge bindend; keine Nummerierung verwenden, sondern nur Anstriche)

- **US-904 weiter implementieren** (Batch-RED-Prozess) – erstes `@US-904-happy-path` („Zutaten-Liste ist leer") abgeschlossen; nächste Szenarien in Reihenfolge aus `features/ingredients.feature`, via `implementing-scenario`.

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität die über MVP hinausgeht: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

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

- **Soll YAGNI für useResultQuery/MutationState gelten?** → Nur `pending|success` implementieren oder vollständige Union? TypeScript-Exhaustiveness-Check erzwingt alle Zweige. Klären vor dem ersten Szenario mit async HTTP-State (Mutation/Loading) – die nächsten reinen Dialog-Szenarien brauchen es nicht.

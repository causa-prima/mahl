# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss: Mit User klären was wohin ausgelagert werden soll – sollte aber nie vorkommen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process)

**Letzte Aktualisierung:** 2026-06-10 (Session 079 – Bash-Permission-Friktion ausgewertet+behoben (Hook+Guidance+SessionStart, 2 Subagent-Evals); Details: session_079)
**Phase:** SKELETON 🔄 – US-904: „Liste leer" + „Felder leer beim Öffnen" abgeschlossen; nächstes Szenario aus `features/ingredients.feature` via `implementing-scenario`

---

## Nächste Prioritäten (Reihenfolge bindend; keine Nummerierung verwenden, sondern nur Anstriche)

- **US-904 weiter implementieren** (Batch-RED-Prozess) – „Zutaten-Liste leer" + „Felder leer beim Öffnen Dialog" abgeschlossen; nächste Szenarien in Reihenfolge aus `features/ingredients.feature`, via `implementing-scenario`. **Hinweis:** das nächste Szenario, das eine *befüllte* Liste rendert („Zutat anlegen" / „Mehrere Zutaten alphabetisch"), killt die 3 zeitlich begrenzten Stryker-Suppressions (s. tech debt) echt – dann entfernen.

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität die über MVP hinausgeht: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Eine offene Maßnahme** (Details + Status in `docs/kaizen/countermeasures.md`, OFFEN): HOCH→CM-Härtung prüfen (closing-session-Prüfung ist weich).

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch – erst ab US-602 relevant |
| Frontend Service | `fetchIngredients` als plain Promise – Migration auf ResultAsync ausstehend | Mittel |
| Frontend Stryker | 3 **zeitlich begrenzte** Suppressions auf dem Non-Empty-Listen-Pfad: `IngredientsPage.tsx` `if`-ConditionalExpression + `map`-ArrowFunction, `ingredientsApi.ts` URL-StringLiteral. Wurzel: kein Szenario rendert eine befüllte Liste. Beim Szenario „Zutat anlegen" / „Mehrere Zutaten" alle 3 entfernen (werden dann echt gekillt). | Mittel |
| Frontend Stryker | `= []` Default in `IngredientsPage.tsx` supprimiert – Suppression entfällt wenn Loading-State-Szenario implementiert ist | Niedrig |
| Frontend Test-Infra | `@testing-library/jest-dom` + `user-event` nicht installiert → `.value`-Cast statt `toHaveValue`, schwächere Fehlermeldungen. Installieren + ggf. Guideline-Abschnitt „verfügbares Test-Toolkit" ergänzen. | Mittel |
| Frontend Komponente | Dialog liegt nur im Empty-State-Branch von `IngredientsPage.tsx` – wird beim „Zutat anlegen"-Szenario zur Falle (Anlegen-Funktion verschwindet sobald die erste Zutat existiert); dann herausziehen. | Mittel |
| Frontend Komponente | `isDialogOpen` als `boolean` – bei Speichern/Validierung auf Discriminated Union (`status`) umstellen statt weitere Flags anzuhängen. | Niedrig |
| E2E-Test | `EmptyDb`-Test ohne DB-Reset – latent flaky wenn DB vorher befüllt | Niedrig |

---

## Offene Fragen

- **Soll YAGNI für useResultQuery/MutationState gelten?** → Nur `pending|success` implementieren oder vollständige Union? TypeScript-Exhaustiveness-Check erzwingt alle Zweige. Klären vor dem ersten Szenario mit async HTTP-State (Mutation/Loading) – die nächsten reinen Dialog-Szenarien brauchen es nicht.

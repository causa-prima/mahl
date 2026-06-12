# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss: Mit User klären was wohin ausgelagert werden soll – sollte aber nie vorkommen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process)

**Letzte Aktualisierung:** 2026-06-12 (Session 082 – US-904 „Abbrechen schließt Dialog…" (Guard-Test); `gherkin-workshop` Sortier-Härtung (Reihenfolge-Inversion); `vitest-run.py --filter`→Testname; Details: session_082)
**Phase:** SKELETON 🔄 – US-904 Szenarien-Fortschritt s. „Nächste Prioritäten"

---

## Nächste Prioritäten (Reihenfolge bindend; keine Nummerierung verwenden, sondern nur Anstriche)

- **US-904 weiter** – „Liste leer" + „Felder leer beim Öffnen" + „Felder nach Abbrechen wieder leer" + „Abbrechen schließt Dialog und verwirft Eingaben" fertig; **nächstes „Zutat anlegen"**, danach „Mehrere Zutaten sortiert"/„Löschen"/… in Reihenfolge aus `features/ingredients.feature` via `implementing-scenario`. **Hinweis:** „Zutat anlegen" rendert eine befüllte Liste → killt die 3 Stryker-Suppressions + Dialog aus Empty-State-Branch ziehen, UX nachziehen (`DialogTitle`/`DialogContent`/Touch ≥44px). Mit `DialogTitle` dann Test-Schließen-Nachweis auf `getByRole('dialog', { name })` spezifizieren (aktuell ohne Name). Eingaben `user.type`, Klicks `fireEvent.click` (TS-Guideline).

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
| Frontend Stryker | 3 **zeitlich begrenzte** Suppressions auf dem Non-Empty-Listen-Pfad (`IngredientsPage.tsx` if + map, `ingredientsApi.ts` URL-Literal). Wurzel: kein Szenario rendert eine befüllte Liste. Bei „Zutat anlegen" alle 3 entfernen. | Mittel |
| Frontend Stryker | `= []` Default in `IngredientsPage.tsx` supprimiert – Suppression entfällt wenn Loading-State-Szenario implementiert ist | Niedrig |
| Frontend Deps | `qs`-DoS (moderate) via `@stryker-mutator/core`→`typed-rest-client`→`qs` – dev-only, kein untrusted-Input-Pfad, akzeptiert; entfällt bei Stryker-Major-Bump. | Niedrig |
| Frontend Komponente | Dialog liegt nur im Empty-State-Branch von `IngredientsPage.tsx` – wird beim „Zutat anlegen"-Szenario zur Falle (Anlegen-Funktion verschwindet sobald die erste Zutat existiert); dann herausziehen. | Mittel |
| Frontend Komponente | `isDialogOpen` boolean + `closeDialog` synct 3 `useState`-Slices manuell – bei Speichern/Validierung auf Discriminated Union umstellen. Auch: Dialog ohne `onClose`. | Mittel |
| E2E-Test | `EmptyDb`-Test ohne DB-Reset – latent flaky wenn DB vorher befüllt | Niedrig |

---

## Offene Fragen

- **Soll YAGNI für useResultQuery/MutationState gelten?** → Nur `pending|success` implementieren oder vollständige Union? TypeScript-Exhaustiveness-Check erzwingt alle Zweige. **Jetzt fällig:** „Zutat anlegen" (nächstes Szenario) ist das erste mit async HTTP-State (POST/Mutation) – vor dessen Implementierung klären.

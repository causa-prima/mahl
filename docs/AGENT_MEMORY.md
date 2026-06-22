# Agent Memory – Mahl

> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process, observations)
> Technische Schuld: `docs/tech-debt.md` | Offene Fragen: `docs/open-questions.md`

**Letzte Aktualisierung:** 2026-06-22 (US-904 `@US-904-error` „leere Einheit" full-stack; erster Sum-Type im Repo `IngredientValidationError`/`SumType.cs`, ADR-S040-1/S018)
**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 weiter:**
  - **`@US-904-error`-Block:** „leerer Name" ✅ (S090), „leere Einheit" ✅ (S091, feld-tragender Fehlertyp via erstem Sum-Type). Verbleibend: „Namen/Einheit aus nur Leerzeichen" (Trim-Varianten — falten sich billig um denselben Code), **„Beide Pflichtfelder leer" (= collect-all-Merge, TD-S090-1)**, dann Duplikat-/Reaktivierungs-Szenarien. Offene Liste: `python3 .claude/scripts/next_scenario.py --open`.
  - **Erst-Formular-UX-Baseline** (mit der Implementierung, nicht vorab): Pflichtfeld-Affordance (Markierung) + Fokus-auf-Fehler als eigenes Szenario; UX-Guideline-Regel landet **mit** dem Code; `gherkin-workshop` um „Formular-UX-Baseline"-Checkliste ergänzen. Zeichenlimits nur gegen Abuse (keine Max-Length-Hints).
  - **Danach Feature-Reihenfolge** – nächstes laut Feature-Datei: {{NEXT_SCENARIO}}. Offene/erledigte Szenarien: `python3 .claude/scripts/next_scenario.py --open|--done`.
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): „sortiert" führt `OrderBy(name)` ein → aktiviert den S084-ETag real (TD-S084-2; Stryker-killbar weil Insertion-Order ≠ alphabetisch); „Speichern-Button deaktiviert" = pending-State (behebt Cold-Start-Race TD-S083-3). `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Offene Maßnahmen** (`docs/kaizen/countermeasures.md`, OFFEN): CM-S078-2 (HOCH→CM-Härtung, closing-session-Prüfung weich).

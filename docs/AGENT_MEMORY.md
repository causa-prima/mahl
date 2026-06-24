# Agent Memory – Mahl

> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process, observations)
> Technische Schuld: `docs/tech-debt.md` | Offene Fragen: `docs/open-questions.md`

**Letzte Aktualisierung:** 2026-06-24 (Kaizen-Retro S085–094)
**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **Aus Retro S095:**
  - **OBS-Backlog-Prozess (OBS-S095-1): eigene Session** – Design-Thema (Auflösung aus der Retro herauslösen, leichte Triage beim Erfassen); Diagnose im OBS festgehalten.
  - **Wrapper-Output-Fixes vor dem nächsten Szenario** (Retro-Entscheid, nicht beobachten): `dotnet-test.py` zeigt bei RED die fehlgeschlagene Assertion (Expected/Actual) → OBS-S091-1; `vitest-run.py --filter` weist gematchte/übersprungene Testzahl aus → OBS-S091-3.

- **US-904 weiter:**
  - **Zutaten-Dialog: Formular-UX-Baseline (Prinzip 8) vervollständigen** → **TD-S094-1** (Fokus-aufs-Fehlerfeld, Enter-Submit) + **TD-S077-1** (Escape); mit den nächsten Baseline-Szenarien am selben Dialog miterledigen.
  - **Nächstes Szenario laut Feature-Datei:** {{NEXT_SCENARIO}}. Offene/erledigte: `python3 .claude/scripts/next_scenario.py --open|--done`.
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): „sortiert" führt `OrderBy(name)` ein → aktiviert den S084-ETag real (TD-S084-2; Stryker-killbar weil Insertion-Order ≠ alphabetisch); „Speichern-Button deaktiviert" = pending-State (behebt Cold-Start-Race TD-S083-3). `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.


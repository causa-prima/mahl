# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 weiter:**
  - **Zutaten-Dialog: Formular-UX-Baseline (Prinzip 8) vervollständigen** → **TD-S094-1** (Fokus-aufs-Fehlerfeld: passend bei run-4 „Einheit-Validierung"; Enter-Submit: passend bei run-1/run-2) + **TD-S077-1** (Escape: passend bei run-2 „Dialog-Verhalten"); jeweils mit dem betreffenden Lauf miterledigen.
  - **Nächster Lauf laut Feature-Datei:** {{NEXT_RUN}}. Offene/erledigte: `python3 .claude/scripts/next_run.py --open|--done --story US-904`.
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): „sortiert" (run-7 „Liste") führt `OrderBy(name)` ein → aktiviert den S084-ETag real (TD-S084-2; Stryker-killbar weil Insertion-Order ≠ alphabetisch); „Speichern-Button deaktiviert" (run-2 „Dialog-Verhalten") = pending-State (behebt Cold-Start-Race TD-S083-3). `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.


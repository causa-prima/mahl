# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 nächster Lauf:** {{NEXT_RUN}}. Offene/erledigte: `python3 .claude/scripts/next_run.py --open|--done --story US-904`.

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen. US-602 ist zugleich die erste Story mit einer zweiten Seite – damit greift erstmals der Checklisten-Punkt „Erreichbarkeit (Navigation)" im `gherkin-workshop` (Schritt 1): Navigations-Szenario gehört nach ADR-S103-1 in `features/navigation.feature` (`@CROSS-navigation`), nicht ins Rezepte-Feature; strukturelle Nav-Vorgabe siehe UX-Guideline Prinzip 9.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.


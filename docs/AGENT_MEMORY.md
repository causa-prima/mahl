# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 nächster Lauf:** {{NEXT_RUN}}. Offene/erledigte: `python3 .claude/scripts/next_run.py --open|--done --story US-904`.
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): **run-10 „Löschen·Konflikt" wurde vorgezogen** (vor run-7): DELETE-Endpoint (soft-delete, `DeletedAt`) + erste Single-Resource-xmin-ETag-Grundlage (POST liefert ETag; If-Match 428/400/412; ADR-S106-1/-2) existieren. Konsequenzen: run-8 (Löschen-UI) baut auf dem DELETE-Endpoint auf; run-8 Sz.1 „Liste leer nach Löschen" **setzt run-7's GET-Filter voraus** (OBS-S106-1); run-11 muss den Unique-Index partiell machen (`WHERE DeletedAt IS NULL`) für Reaktivierung. „sortiert" (run-7 „Liste") führt `OrderBy(name)` ein → aktiviert den TD-S084-2-ETag real (Stryker-killbar weil Insertion-Order ≠ alphabetisch). Cold-Start-Race **TD-S083-3 bleibt offen** – `disabled={isPending}` sperrt nur *während des POST*, nicht bis zum Settle des initialen GET. Tests: `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen. US-602 ist zugleich die erste Story mit einer zweiten Seite – damit greift erstmals der Checklisten-Punkt „Erreichbarkeit (Navigation)" im `gherkin-workshop` (Schritt 1): Navigations-Szenario gehört nach ADR-S103-1 in `features/navigation.feature` (`@CROSS-navigation`), nicht ins Rezepte-Feature; strukturelle Nav-Vorgabe siehe UX-Guideline Prinzip 9.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.


# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 nächster Lauf:** {{NEXT_RUN}}. Offene/erledigte: `python3 .claude/scripts/next_run.py --open|--done --story US-904`.

- **Vor dem nächsten `gherkin-workshop`: alle Workshop-Beobachtungen drainen (Gate, nicht nur Priorität).** Vier offene OBS betreffen den Workshop selbst und würden sich sonst in die nächste Story fortpflanzen: übersehene Konflikt-Variante eines Nebenläufigkeits-Szenarios (OBS-S111-1), Cross-Run-Zustandsabhängigkeiten im Clustering (OBS-S106-1), fehlendes Vorab-Flag für Querschnitts-Policy-Rollout (OBS-S106-2), Checkliste ohne transiente Feedback-Elemente wie Toast/Snackbar (OBS-S108-2). Der Workshop läuft als nächstes für die Folge-Story von US-904 – deshalb `draining-observations` auf diese vier **vor** dem Workshop ausführen und die beschlossenen Korrekturen am Skill umsetzen.

- **Vor dem nächsten `gherkin-workshop`: `docs/tech-debt.md` vollständig durchgehen und je Eintrag trennen — feature-spezifisch (US-904/Zutaten) oder allgemein?** Für die feature-spezifischen jetzt entscheiden: weitertragen, direkt umsetzen oder löschen. — Grund: Mit dem letzten US-904-Lauf ist der Kontext, aus dem diese Einträge stammen, noch präsent; später ist er es nicht mehr, und erledigte oder gegenstandslose Posten werden inertial weitergeschleppt. Einzelne Einträge verlangen zudem ausdrücklich ein Gherkin-Szenario, bevor sie umgesetzt werden dürfen (u. a. TD-S108-4, TD-S110-1(d)) – die gehören als Input in den Workshop, sonst greift ihr Trigger nie (LL-S111-2). — Done: Jeder Eintrag ist entweder als allgemein eingestuft oder feature-spezifisch entschieden; die weiterzutragenden liegen als Workshop-Input vor.

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen. US-602 ist zugleich die erste Story mit einer zweiten Seite – damit greift erstmals der Checklisten-Punkt „Erreichbarkeit (Navigation)" im `gherkin-workshop` (Schritt 1): Navigations-Szenario gehört nach ADR-S103-1 in `features/navigation.feature` (`@CROSS-navigation`), nicht ins Rezepte-Feature; strukturelle Nav-Vorgabe siehe UX-Guideline Prinzip 9.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.


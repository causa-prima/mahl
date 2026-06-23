# Agent Memory – Mahl

> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process, observations)
> Technische Schuld: `docs/tech-debt.md` | Offene Fragen: `docs/open-questions.md`

**Letzte Aktualisierung:** 2026-06-23 (US-904 `@US-904-error` „beide Pflichtfelder leer" = collect-all-Merge umgesetzt, TD-S090-1 erledigt; Backend-`ToDomain` kurzschließend→collect-all, Frontend unverändert; F1-Refactor Describe-Tupel; LL-S093-1, OBS-S093-1/-2)
**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 weiter:**
  - **Vorgezogen (jetzt fällig) — Erst-Formular-UX-Baseline:** EIN gebündeltes, eigenes Szenario: Pflichtfeld-Affordance (Markierung) + Fokus-auf-**erstes**-Fehlerfeld (cross-cutting Formular-Mechanismen, je ein Code-Pfad, ein Test treibt+bewacht — **nicht** in jedes Error-Szenario retrofitten). **Grund der Vorziehung:** „Fokus aufs *erste* Fehlerfeld" ist erst bei **mehreren** gleichzeitigen Fehlern beobachtbar; diese Voraussetzung („beide Pflichtfelder leer") ist mit S093 erfüllt. Baseline jetzt am ersten Formular etablieren, bevor weitere Formulare das Muster vervielfachen (Retrofit-Vermeidung). UX-Guideline-Regel + `gherkin-workshop`-„Formular-UX-Baseline"-Checkliste landen **mit** dem Code. Zeichenlimits nur gegen Abuse (keine Max-Length-Hints). **Done, wenn** Affordance- + Fokus-Szenario implementiert + Guideline/Checkliste ergänzt.
  - **Danach Feature-Reihenfolge** – nächstes laut Feature-Datei: {{NEXT_SCENARIO}}. Offene/erledigte Szenarien: `python3 .claude/scripts/next_scenario.py --open|--done`.
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): „sortiert" führt `OrderBy(name)` ein → aktiviert den S084-ETag real (TD-S084-2; Stryker-killbar weil Insertion-Order ≠ alphabetisch); „Speichern-Button deaktiviert" = pending-State (behebt Cold-Start-Race TD-S083-3). `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Offene Maßnahmen** (`docs/kaizen/countermeasures.md`, OFFEN): CM-S078-2 (HOCH→CM-Härtung, closing-session-Prüfung weich).

# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 nächster Lauf:** {{NEXT_RUN}}. Offene/erledigte: `python3 .claude/scripts/next_run.py --open|--done --story US-904`.
  - **TD-S094-1 (Fokus aufs erste Fehlerfeld, Prinzip 8):** mit run-4 „Einheit-Validierung" miterledigen.
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): „sortiert" (run-7 „Liste") führt `OrderBy(name)` ein → aktiviert den TD-S084-2-ETag real (Stryker-killbar weil Insertion-Order ≠ alphabetisch). Cold-Start-Race **TD-S083-3 bleibt offen** – `disabled={isPending}` sperrt nur *während des POST*, nicht bis zum Settle des initialen GET. Tests: `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Nächste Kaizen-Retro – Auftakt-Sonde (OBS-S092-3):** Zu Beginn der Retro mehrere Subagenten ein LL-Sample **blind** re-raten lassen (v.a. Impact) — Grund: LL-Metadaten-Fehler verzerren Jenga/Prioritäts-Matrix; Nutzen eines festen Workshop-Schritts erst so verifizieren. Done: Abweichungen ausgewertet + Entscheidung über festen Schritt getroffen (OBS-S092-3 dann schließen).


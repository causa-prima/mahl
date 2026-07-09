# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **US-904 run-2-Rest (nächster Produktions-Lauf):** 3 spec-first-Szenarien implementieren – **S1** „Abbrechen während Speichern deaktiviert", **S2** „Dialog nicht per Escape schließbar während Speichern", **S3** „kein Rest-Fehler nach Fehlschlag+Abbrechen+Reopen". — Grund: Review fand die realen Bugs R1 (`saveError` wird beim Schließen nicht resettet) + R2 (Datenverlust-Race: Schließen während Pending) szenariolos (S100); S1+S2 sperren alle Schließ-Pfade während Pending (subsumieren R2), S3 resettet den Fehlerzustand (deckt R1). — Done: alle 3 grün + Stryker 100 %.
  - **Nächster Lauf laut Feature-Datei:** {{NEXT_RUN}}. Offene/erledigte: `python3 .claude/scripts/next_run.py --open|--done --story US-904`.
  - **TD-S094-1 (Fokus aufs erste Fehlerfeld, Prinzip 8):** mit run-4 „Einheit-Validierung" miterledigen. — Done: Fokus springt bei Validierungsfehler aufs betroffene Feld. (Enter-Submit + Escape sind mit run-2 bereits erledigt.)
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): „sortiert" (run-7 „Liste") führt `OrderBy(name)` ein → aktiviert den TD-S084-2-ETag real (Stryker-killbar weil Insertion-Order ≠ alphabetisch). Cold-Start-Race **TD-S083-3 bleibt offen** – run-2's `disabled={isPending}` sperrt nur *während des POST*, nicht bis zum Settle des initialen GET. Tests: `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Nächste Kaizen-Retro – Auftakt-Sonde (OBS-S092-3):** Zu Beginn der Retro mehrere Subagenten ein LL-Sample **blind** re-raten lassen (v.a. Impact) — Grund: LL-Metadaten-Fehler verzerren Jenga/Prioritäts-Matrix; Nutzen eines festen Workshop-Schritts erst so verifizieren. Done: Abweichungen ausgewertet + Entscheidung über festen Schritt getroffen (OBS-S092-3 dann schließen).


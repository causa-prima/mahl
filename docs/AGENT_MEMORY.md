# Agent Memory – Mahl

> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process, observations)
> Technische Schuld: `docs/tech-debt.md` | Offene Fragen: `docs/open-questions.md`

**Letzte Aktualisierung:** 2026-06-20 (WSL-native Toolchain-Migration abgeschlossen – .NET + Node nativ in WSL, Repo auf ext4 `~/repos/mahl`)
**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)

---

## Nächste Prioritäten

- **TS-LSP-Pilot (OBS-S085-4) – ZUERST:** Migration hat den Blocker entfernt (Node WSL-nativ + `typescript-language-server` installiert). Jetzt `typescript-lsp`-Plugin + `ENABLE_LSP_TOOL` eine Session testweise evaluieren (Nutzen: Auto-Typfehler nach Edits, find-refs, Symbole). C# bleibt zurückgestellt (Client-Showstopper #1359).

- **US-904 weiter:**
  - **Zuerst der `@US-904-error`-Block** (vor dem happy-path-Rest, also vor „sortiert"): erzwingt `NonEmptyTrimmedString`-Validierung, ADR-S000-4-Suppression entfällt.
  - **Danach Feature-Reihenfolge** – nächstes laut Feature-Datei: {{NEXT_SCENARIO}}. Offene/erledigte Szenarien: `python3 .claude/scripts/next_scenario.py --open|--done`.
  - **Roadmap-Kontext** (nicht an „nächstes" gebunden): „sortiert" führt `OrderBy(name)` ein → aktiviert den S084-ETag real (TD-S084-2; Stryker-killbar weil Insertion-Order ≠ alphabetisch); „Speichern-Button deaktiviert" = pending-State (behebt Cold-Start-Race TD-S083-3). `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität über MVP hinaus: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Offene Maßnahmen** (`docs/kaizen/countermeasures.md`, OFFEN): CM-S078-2 (HOCH→CM-Härtung, closing-session-Prüfung weich).

# Session 088 – 2026-06-18

**Phase:** SKELETON
**Fokus:** Szenario-Tracking in AGENT_MEMORY automatisieren + bidirektionaler Poka-Yoke (löst den Prioritäten-Widerspruch aus der S087-Restruktur)

## Auslöser

Beim Start (geplant: nächstes US-904-Szenario implementieren) fiel ein **Widerspruch** in `AGENT_MEMORY.md` auf: Das Header-Feld „Nächstes Szenario" zeigte auf ein US-904-Szenario, der erste Prioritäten-Anstrich war aber OBS-4. Zwei konkurrierende „nächstes"-Pointer → der prominentere (Header) gewann fälschlich. Ursache: „Nächstes Szenario" war strukturell ein Top-Level-Feld, semantisch aber ein Kind des US-904-Prioritäten-Items.

## Implementiert

### Resolver + geteilter Parser
- `_feature.py` – geteilter Gherkin-Parser (SSOT); `check-atdd-gate.py` auf ihn umgestellt (vorher lokale Kopie).
- `next_scenario.py` – Modi `--render` (löst `{{NEXT_SCENARIO}}` in AGENT_MEMORY zum nächsten unimplementierten Szenario laut Feature-Datei auf: Story → Feature via `@US-NNN`-Tag → erstes offenes in Datei-Reihenfolge), `--open`/`--done` (Szenario-Status je Feature ohne Datei-Öffnen), `--check` (repo-weiter Mapping-Verifier). Fail-open-Fallback bei Render.

### AGENT_MEMORY-Umbau
- Header-Feld „Nächstes Szenario" + Feature-Pfad aus Story-Zeile entfernt. `{{NEXT_SCENARIO}}`-Platzhalter im US-904-Anstrich (entkoppelt, kein stale-anfälliger Folgetext). `@US-904-error`-Block als expliziter Override über dem Platzhalter (Feature-File-Reihenfolge bleibt unangetastet). `session-start.sh` rendert via `--render` (statt `cat`), `|| cat` als harter Fallback.

### `// Szenario:`-Kommentar-Konvention + Enforcement
- Konvention: jeder Playwright-Testfall trägt `// Szenario: <exakter Gherkin-Titel>` (maschineller Spec↔Test-Link; löst die S087-Blockade „kein Mapping CamelCase↔Titel"). 5 bestehende E2E-Tests retroaktiv markiert.
- **Poka-Yoke-Hook `check-e2e-scenario-ref.py`** (PreToolUse `Edit|Write`, blockierend, exit 2), bidirektional:
  - Spec-Edit: Präsenz (jeder Testfall hat Kommentar) + Gültigkeit (Titel matcht Feature-Szenario) + Eindeutigkeit (kein Cross-File-Duplikat). Simuliert Post-Edit-Inhalt (liest Datei + wendet Edit an).
  - Feature-Edit: blockt, wenn eine Umbenennung/Entfernung einen bestehenden `// Szenario:`-Kommentar verwaisen lässt. Rename-Deadlock bewusst akzeptiert (seltener Fall → per Hand-Edit außerhalb des Agenten-Tools lösen).
- 32 neue Tests; **live am echten Edit-Tool nach Reload verifiziert** (Spec- und Feature-Seite, je Block + Durchlass, sauber revertiert).

### Doku
- ADR-S041-7 um Link-Mechanismus-Addendum (S088) erweitert. `closing-session` Schritt 8 auf Platzhalter-Pflege gestrafft. `e2e-testing.md` um Per-Szenario-Link ergänzt. OBS-S085-16 Status auf „Teil A S087 / Teil B S088" aktualisiert (Generator doch umgesetzt).

## Probleme / Findings
- **LL-S088-1 (MITTEL):** Mapping-Guard zuerst in `qa-check.py` (Subagenten-Übergabebeweis) platziert – falscher Verantwortungsträger (Orchestrator besitzt E2E-Tests). Vollständig revertiert nach User-Hinweis.
- **LL-S088-2 (MITTEL):** Hook zuerst nur mit Kommentar-Gültigkeit gebaut; Präsenz (jeder Test braucht Kommentar) fehlte, obwohl der User-Wortlaut „alle Tests einen gültigen Verweis" beides implizierte.

## Entscheidungen
- **Schlüssel K3** (Titel-Kommentar) statt K1 (verbatim Titel als Testname, bricht CamelCase) oder K2 (paralleler Slug-Namespace) – Titel existiert schon, dient zugleich ADR-S041-7-Traceability.
- **Feature-Seite blockierend** (statt nicht-blockierender Warnung) – User akzeptiert den Rename-Deadlock; Hand-Edit als Escape.
- **Mapping-Guard = Orchestrator-Verantwortung**, nicht Teil von `qa-check.py`.

## Offene Punkte
- **OBS-S088-1** (NEU): Hook-Registrierung – ein Dispatcher je Matcher/Event statt Einzeleinträge in `settings.json` (reload-freie Check-Erweiterung). Als eigener fokussierter Refactor.
- **OBS-4** (TS-LSP-Pilot) weiterhin offen/extern blockiert (claude-code#1359) – nächste-Session-Pilot.

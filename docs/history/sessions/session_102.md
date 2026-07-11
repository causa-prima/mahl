# Session 102 – 2026-07-10/11

**Phase:** SKELETON
**Story:** US-904 (Zutaten) – run-3 „Anlegen·Name-Validierung" abgeschlossen

## Implementiert

### OBS-Drain (Blöcke 1–4, über zwei Kalendertage; committet `c9c4a1b`)
Proaktiver Backlog-Drain, 7 OBS aufgelöst + archiviert:
- OBS-S100-1/-2 → Prinzip „Zustandsdokumente tragen nur offenen Zustand" (`principles.md`, CM-S102-1) + Vertrauens-/Ermüdungs-Linse (`process.md`).
- OBS-S095-3 → Poka-Yoke-Hook `check-ref-direction.py` (blockt volatil→stabil-Referenzen, CM-S102-2), `adr.md`-Bestand bereinigt.
- OBS-S095-2 / S086-5 → `review-docs` Low-Value-Kriterium + `closing-session` Session-Datei-Scope (diese Datei folgt bereits der neuen Regel).
- OBS-S101-2 → Leitplanke „Arbeitende Subagenten nicht pollen" in `implementing-scenario` (CM-S102-3).
- OBS-S095-4 → verworfen (unzuverlässiger Selbst-Eskalations-Trigger); OBS-S088-1 → aufgeschoben.

### US-904 run-3 „Anlegen·Name-Validierung" (Backend)
Server-seitige Max-Length-Validierung (`name` > 30 Zeichen, nach Trimming, ADR-S051-3):
- Neuer payloadloser Sum-Type-Case `NameTooLong` (ADR-S018-1/S040-1); Boundary-Validatoren `ValidateName`/`ValidateUnit` in `IngredientMappings`; `const MaxNameLength = 30`; feld-keyed 422 „Name darf maximal 30 Zeichen lang sein." (ADR-S051-2).
- 2 neue E2E-Tests (31→Fehler, 30→ok) + 2 Backend-Integration-Tests. Frontend unverändert – die feld-agnostische Fehleranzeige deckt „zu lang" ab (unabhängig per Verifikations-Subagent bestätigt, kein FE-Code).
- Ergebnis: Playwright 20/20 (US904), Backend 17/17, Stryker 100 %, Review 0 ❌ (2 ⚠️ umgesetzt: Test-Datenkonstante extrahiert, `MaxNameLength`-Konstante).

## Entscheidungen
- run-3 war real **Backend-only** trotz Full-Stack-Cluster: 2 der 4 Szenarien (leerer/Leerzeichen-Name) + die FE-Anzeige stammen bereits aus run-1/run-5.
- CM-S102-3 nach run-3 verfeinert: „finished"/Completion ≠ idle-Zwischensignal – Root-Cause via Log-Nachschau: ein Review-Auditor gab seinen Report als plain text statt per `SendMessage` aus (für den Orchestrator unsichtbar).
- Doku-Fix: `tdd-process.md` Test-Setup auf xunit.v3 + AwesomeAssertions korrigiert (Doku nannte fälschlich NUnit/FluentAssertions).

## Erkenntnisse (Verweise)
- LL-S102-1 – Lösungskandidaten bei OBS-Erfassung biasen den Drain (→ `lessons_learned.md`).
- OBS-S102-1/-2/-3 – `dotnet-stryker.py --mutate` nur Einzelpfad; qa-check-Test-Freigabe-Audit sieht geänderte Testdatei nicht; Team-Subagenten berichten inkonsistent (plain text statt `SendMessage`) (→ `observations.md`).
- TD-S102-1 – kein app-weites Request-Body-Size-Limit; `defaultUnit` ohne Längenlimit (→ `tech-debt.md`).

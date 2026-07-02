# Session 098 – 2026-07-02

**Phase:** SKELETON
**Fokus:** US-904 `run-1` „Anlegen·Success" (Trim-Szenario) + TD-S083-5 (E2E-DB per-Test-Isolation).

## Ausgangslage
`run-1` war überwiegend Vorarbeit aus S083: Happy-Path „Zutat anlegen" bereits voll implementiert/getestet
(E2E, Frontend-Unit, Backend, Domain). Offen nur das zweite Szenario des Laufs – „Führende und nachfolgende
Leerzeichen werden beim Speichern entfernt" (edge-case). Dessen Trim-Verhalten existierte produktionsseitig
bereits (`NonEmptyTrimmedString.Create`, `input?.Trim()`, ADR-S051-1) – kein Test pinnte aber „  Oregano  " →
„Oregano" gespeichert/angezeigt.

## Umgesetzt

### run-1 Trim-Szenario (Charakterisierung mit echtem RED→GREEN)
- Backend-Integrationstest (`US904_EdgeCase_...TrimsAndPersistsTrimmedValue`): Response-Body **und** DB-State
  = getrimmt (Full-State-Assertion). E2E-Test (`ingredients.spec.ts`) prüft die Anzeige.
- **E2E-Assertion-Technik:** Whitespace ist auf E2E-Ebene nur über eine **Regex** gegen den rohen DOM-Text
  beobachtbar – Playwrights String-Matcher (`getByText`, `toHaveText('x')`) normalisieren Whitespace immer
  (auch `exact:true`). Lösung: `exact:true` zum Lokalisieren, `toHaveText(/^Oregano$/)` prüft den Rohtext.
- Da das Verhalten schon existierte, war kein RED möglich – der User kommentierte das `?.Trim()` temporär aus
  → beide Tests RED aus korrektem Grund → wiederhergestellt → GREEN. Kein Produktionscode-Änderung am Trim.

### TD-S083-5 behoben: E2E-DB per-Test-Isolation (ADR-S084-4 Addendum)
Die E2E-Postgres hatte keinen Reset zwischen Läufen (Residual-Akkumulation, S090/S091-Rezidive). Neu:
- Eigene DB `mahl_e2e` (`appsettings.E2E.json`), aktiviert via `ASPNETCORE_ENVIRONMENT=E2E`.
- `Program.cs`-Guard aktiviert nur in E2E `E2ETestSupport.UseE2ETestSupportAsync`: `MigrateAsync()` beim Start
  + `POST /api/test/reset` (generisches `TRUNCATE` aller Tabellen aus dem EF-Modell). Reset läuft über einen
  HTTP-Port (ADR-S041-1), nicht per DB-Direktzugriff. Playwright-`beforeEach` ruft den Reset mit loud
  `expect(status).toBe(204)`. `workers: 1` erzwingt die Single-Worker-Prämisse.
- `E2ETestSupport` aus Backend-Stryker ausgeschlossen (E2E-only-Scaffolding, analog `Program.cs`).
- Doku: `coding-guideline-csharp.md` (Ausnahme für Test-Scaffolding-Endpoints), `tech-debt.md` (TD entfernt),
  `observations.md` (OBS-S090-5-Referenz aktualisiert).

### Review
3 Auditoren (test-quality, code-quality, functional-correctness), 0 ❌. Umgesetzt: F1 (ADR-Dateiname),
F3 (Kommentar-Duplikation → ADR-Referenz), FC1 (`workers: 1`), FC2 (Prämissen-Kommentar). F2/F4/F6/FC7 +
DOM-Locator/`Given` bewusst aufgeschoben (Bestandsmuster/optionale Politur).

## Probleme / Korrekturen
- **`launchSettings.json` überschrieb still `ASPNETCORE_ENVIRONMENT=E2E`** → Reset-Endpoint 404 → verwirrende
  Akkumulations-Debuggerei. Fix: `--no-launch-profile`. → LL-S098-1.
- **`MigrateAsync()` direkt in `Program.<Main>$`** riss das EF-Relational-Assembly in Mains JIT → **alle** 15
  Backend-Integrationstests (InMemory-Host) `FileNotFoundException`, obwohl der E2E-Branch nie lief. Fix:
  Auslagern in eigene Methode (Body JITtet erst bei E2E-Aufruf). → LL-S098-2.
- **TD-S083-5 nicht proaktiv in Schritt 0 gefunden**, sondern reaktiv als der E2E-Test an Residuen scheiterte –
  genau der von OBS-S090-5 vorhergesagte Fall (Infra-TD ohne Szenario-Bezug). → LL-S098-3 (Materialisierung
  von OBS-S090-5).

## Ergebnisse
- Backend 15/15 grün, E2E 11/11 grün (per-Test-Isolation verifiziert: `EmptyDb` grün trotz vorheriger
  Create-Tests), Backend-Mutation 100 % (0 Survivors), ESLint 0 Errors.

## Offene Punkte
- **Enter-Submit** (UX-Baseline Prinzip 8, framework-geliefert → Review, kein Szenario): auf run-2 aufgeschoben.
- **Per-Worker-E2E-DB** (Parallelität): als Grenze in ADR-S084-4 Addendum + `playwright.config.ts` dokumentiert;
  erst bei spürbarer Laufzeit umsetzen (Weg 3a: per-Worker-Full-Stack).
- Optionale ⚠️ (F2/F4/F6/FC7): nicht umgesetzt, keine Blocker.

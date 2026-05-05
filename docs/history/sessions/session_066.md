# Session 066 – 2026-05-05

**Phase:** SKELETON  
**Dauer:** ca. 1,5h  
**Scope:** TDD-Prozess-Review + Tooling-Erweiterung (Single-Tier, jscpd, ESLint, SonarAnalyzer)

---

## Was wurde gemacht

### Prozess-Änderungen

**Single-Tier-Regel eingeführt (`docs/TDD_PROCESS.md`):**
- Coding-Subagenten schreiben keine Unit Tests auf isolierte Domänenlogik.
- Standard: nur HTTP-Integrationstests (C#) und MSW-Komponenten-Tests (TypeScript).
- Ausnahme: Stryker-getriggert + strukturell nicht via HTTP beobachtbar + Quelltrennung (Haupt-Thread schreibt den Test).
- Langsame Stryker-Läufe durch wachsende Integration-Test-Suite sind akzeptierter Trade-off.

**REFACTOR-Gate mit PFLICHT-OUTPUT ergänzt (`docs/TDD_PROCESS.md`):**
- `ESLint: [0 Errors / N Errors] | dotnet build: [clean / N Fehler] | jscpd: [Keine Duplikate / N Duplikate: ...]`
- Orchestrator-Verification: fehlendes PFLICHT-OUTPUT = Gate nicht ausgeführt.

**Subagenten-Prompt gehärtet (`.claude/skills/implementing-scenario/SKILL.md`):**
- Explizites Unit-Test-Verbot inkl. MSW-Ausnahme.
- Stryker-Survivor-Check vor Schritt 4.
- Orchestrator-Checks 4 (Linter-Gate) + 5 (Unit-Test-Check) ergänzt.

**REVIEW_CHECKLIST.md:** Unit-Test-Check-Punkt hinzugefügt (Stryker-Survivor-Nachweis als Pflicht).

### Tooling

**ESLint vollständig eingerichtet (`Client/eslint.config.js`):**
- Alle Packages fehlten in `package.json` – wurden ergänzt und installiert.
- Code-Qualitäts-Metriken: `complexity ≤ 10`, `max-lines-per-function ≤ 20`, `max-lines: warn 200`.
- `eslint-plugin-react-hooks` v5.2.0: API-Korrektur `configs['recommended-latest']` (war: `configs.flat.recommended`).
- `src/test/setup.ts`: Project-Service-Fix via `allowDefaultProject: ['src/test/*.ts']`.

**SonarAnalyzer-Metriken konfiguriert (`.editorconfig`):**
- S3776 cognitive complexity > 15, S138 Methode > 80 Zeilen, S104 Datei > 1000 Zeilen → Warning → TreatWarningsAsErrors.

**jscpd eingerichtet (`jscpd.config.json`, `Client/package.json`):**
- Cross-language (TypeScript + C#), minTokens 70, Test-Dateien + Migrations ausgeschlossen.
- `npm run lint:duplicates` als Script.

**Hook-Auto-Freigabe ergänzt:**
- `npm run lint:duplicates` in `test-bash-permission.py`.

**DEV_WORKFLOW.md:** `npm run lint` und `npm run lint:duplicates` in Befehls-Tabelle ergänzt.

### ESLint-Fixes (4 Fehler behoben)

- `IngredientsPage.test.tsx`: `expect` aus Import entfernt; `ui: Readonly<React.ReactElement>` (immutable parameter).
- `IngredientsPage.tsx`: `eslint-disable-next-line` für `useQuery` (Tech-Debt bis Szenario 2).
- `src/test/setup.ts`: void arrow shorthand → Block-Body (`{ server.listen(...) }`).

---

## Ergebnisse

- ESLint: 0 Errors (verifiziert)
- TDD_PROCESS.md, SKILL.md, REVIEW_CHECKLIST.md: Single-Tier + PFLICHT-OUTPUT konsistent dokumentiert
- jscpd: konfiguriert und freigegeben (noch kein Lauf durchgeführt – neue Infrastruktur)

---

## Offene Punkte

- `npm audit`: 1 moderate severity vulnerability (aus vorherigem Install) – noch nicht behoben.
- Major npm-Package-Updates: User hat explizit gebeten, in nächster Session zu prüfen.

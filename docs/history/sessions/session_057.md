# Session 057 – 2026-04-15

## Überblick

MSW-Einführung + Frontend-Teststrategie-Klärung + Bash-Permission-System-Umbau (WRONG_APPROACH vs. DESTRUCTIVE) + npm-Vulnerability-Fix + Doku-Updates.

---

## Durchgeführt

### MSW eingeführt (HTTP-Level-Mocking)

- `msw` installiert (nach DEPENDENCIES.md-Prozess + User-Freigabe)
- `Client/src/mocks/server.ts` + `Client/src/test/setup.ts` angelegt
- `Client/vite.config.ts`: `setupFiles` ergänzt
- `Client/src/services/ingredientsApi.test.ts` angelegt (HTTP-Kontrakt-Test via MSW) – dann wieder gelöscht (s.u.)
- `docs/history/decisions.md`: Entscheidung "MSW statt vi.mock" dokumentiert
- `docs/DEPENDENCIES.md`: `msw` zur Allowlist ergänzt (durch User)

### Frontend-Teststrategie: teste durch öffentliche Oberfläche

Längere Diskussion über den richtigen Test-Schnitt im Frontend, analog zum Backend (nur über HTTP-Endpoints testen):

- `IngredientsPage.test.tsx`: `vi.mock` entfernt, MSW-Handler eingebaut → Komponente exercist `fetchIngredients` als Implementierungsdetail
- `ingredientsApi.test.ts`: gelöscht – Service-Funktionen sind keine testbare Oberfläche
- `CODING_GUIDELINE_TYPESCRIPT.md`: neue Sektion 6 "Test-Architektur" mit Teststrategie und MSW-Pflicht
- `REVIEW_CHECKLIST.md`: Frontend-Test-Punkt unter "## Tests" ergänzt

### Bash-Permission-System: WRONG_APPROACH vs. DESTRUCTIVE

Strukturelle Umgestaltung des Hooks nach User-Feedback ("falsche und destruktive Befehle werden vermischt"):

- `DENY_PATTERNS` → `WRONG_APPROACH_PATTERNS` (falscher Ansatz, kein Override)
- Neues `DESTRUCTIVE_PATTERNS` (destruktiv aber legitim, per `# --allow-once` freigabefähig)
- `rm -rf`, `git reset --hard`, `git push --force`, `find -delete` etc. aus WRONG_APPROACH herausgelöst
- `rm` (einzelne Datei, ohne `-r`) → Allow-Liste
- `find`-Allow-Pattern: Negative Lookaheads für `-delete` und `-exec rm`
- Logging-Fix: `\n\n` → `\n`
- `npm audit` → Allow-Liste
- Alle Tests angepasst (160+ → grün)
- `DEV_WORKFLOW.md` aktualisiert

### Review check-bash-permission.py

Review-Agent fand u.a.:
- **KRITISCH**: `DESTRUCTIVE_PATTERNS` war dead code (wurde gefixt)
- **KRITISCH**: `find -exec sh -c 'rm ...'` umgeht Lookahead (technische Schuld)
- **HOCH**: `check_command` / `check_simple_command` mit divergierender Logik

### npm audit fix

- Vite 8.0.0–8.0.4: 3 High-Severity-CVEs (Dev-Server-only), gefixt auf 8.0.5+

---

## Offen / Zurückgestellt

- `find -exec sh -c 'rm ...'` Bypass: technische Schuld, noch nicht gefixt
- Frontend Wrapper Scripts (vitest-run.py, playwright-test.py, stryker-frontend.py): kein Kontext mehr
- Stryker Szenario 1 Survivors (`minHeight`, `queryKey`) noch nicht supprimiert
- Backend Stryker: noch nicht erneut ausgeführt
- Commit für Szenario 1: ausstehend
- `review-code/SKILL.md`: Refactoring-Scope in Review-Prompt – Diskussion zurückgestellt
- `DESTRUCTIVE_PATTERNS`-Refactoring (Deduplizierung mit `_SMART_DENY_HINTS`): zurückgestellt

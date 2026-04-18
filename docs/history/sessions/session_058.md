# Session 058 – 2026-04-15

**Phase:** SKELETON (Infrastruktur / Architektur)

## Ergebnisse

### Analyzer-Regeln evaluiert und verschärft (grill-me)
- `Directory.Build.props`: `TreatWarningsAsErrors=true` ergänzt – alle Analyzer-Warnings sind jetzt buildbreakend
- `eslint.config.js`: `no-restricted-imports` für direktes `useQuery`/`useMutation` (Wrapper-Pflicht), `fetch()`-Verbot auf `src/**` ausgeweitet (außer `src/services/`), `no-restricted-syntax` für `.isOk()`/`.isErr()`/`._unsafeUnwrap()` in Produktionscode, `functional/no-throw-statements` deaktiviert (exhaustive switch handler)
- Hooks: `rop.py` TS-Teil → ESLint. `throw_check.py` TS-Teil entfernt. `primitives.py` in `check_blocking` (Properties) + `check_nonblocking` (Parameter) aufgeteilt. `immutability.py` blockierend. `domain_visibility.py` gelöscht (CA1515 + TreatWarningsAsErrors). Dispatcher aktualisiert. 67 Hook-Tests grün.

### ETags – Architekturentscheidung getroffen
- **Global:** alle Endpoints (nicht nur "mutierbare Ressourcen" – Terminologie-Fehler korrigiert)
- **Beide Zwecke:** HTTP-Caching (If-None-Match → 304) + Optimistic Concurrency (If-Match → 412/428)
- **ETag-Quelle:** Single Resource → PostgreSQL `xmin` via `UseXminAsConcurrencyToken()`. Collection → SHA-256-Content-Hash.
- SUM(xmin) für Collections diskutiert und recherchiert – nicht etabliertes Muster, Content-Hash bevorzugt.
- Dokumentiert in `decisions.md`, `CODING_GUIDELINE_CSHARP.md` (Abschnitt 6), `REVIEW_CHECKLIST.md`.

## Offen geblieben
- Frontend-Design-Guidelines
- Positive Formulierungen in Guidelines/Skills
- Session-Abschluss Trigger-Fix
- Task-Liste aufräumen
- Frontend-Wrapper-Scripts, retro.py Agenten-Modus, Stryker, Commit Szenario 1

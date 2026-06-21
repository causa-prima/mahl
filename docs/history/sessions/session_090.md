# Session 090 – 2026-06-21

**Phase:** SKELETON
**Fokus:** US-904-Szenario `@US-904-error` „Zutat mit leerem Namen anlegen schlägt fehl" (Full-Stack) + Validierungs-Architektur festgelegt

## Implementiert

### Szenario (via implementing-scenario, Full-Stack)
- **Backend:** `NonEmptyTrimmedString.Create` → `OneOf<NonEmptyTrimmedString, Error>` (payloadloser `Error`, leerer/whitespace-Name abgelehnt) – damit entfällt die ADR-S000-4-Suppression. `OneOfExtensions.Map/Bind` auf `<TIn,TOut,TError>` generalisiert. Endpoint mappt den Fehler via `NameRequiredProblem()` → `Results.ValidationProblem` mit **422** und feld-keyed Body `{ "errors": { "name": ["Name darf nicht leer sein."] } }`.
- **Frontend:** `apiError.ts` neuer Typ `FieldErrors` (mit `Partial<…>`, damit `fields.name` ehrlich `… | undefined` ist → `?.` echt nötig, keine eslint-disable). `ingredientsApi` parst 422 → `errAsync({ kind:'FieldErrors', … })`. `useResultMutation` mit `onSuccess`-Callback (Erfolg → Dialog schließen/Reset; Fehler → `setError`). `IngredientsPage` zeigt `nameError` an Name-TextField (`error` + `helperText`, aria-invalid).
- Beide Stryker **100%** (FE/BE-Hashes verifiziert), E2E grün.

### Validierungs-Architektur (festgelegt)
- **Server-seitige Validierungs-Logik** ist die Single Source; Client-seitige Validierungs-Logik aufgeschoben.
- **422-Body feld-keyed** nach RFC 9457 / ASP.NET `ValidationProblemDetails` → **ADR-S090-1** (supersedet die Body-Form aus ADR-S000-1). Frontend zeigt `errors[field]` an, ohne die Validierungs-Regel zu duplizieren.
- **Pflichtfeld-Affordances** (Markierung) als Minimum + **Fokus-auf-Fehler** als Erst-Formular-UX-Baseline: eigenes Szenario, kommt mit der Implementierung (nicht in dieser Session); Zeichenlimits nur gegen Abuse, keine Max-Length-Hints.

### Pfad-Fixes (Post-WSL-Migration)
- Veralteten `/mnt/c/Users/…`-Hardcode in 5 Hooks (`check-memory`, `pre-compact`, `session-start`, `session-end`, `task-completed`) → dynamische Repo-Wurzel (`${CLAUDE_PROJECT_DIR:-…}`). Ebenso in `test_dependency_allowlist.py` und der OBS-S085-1-Referenz.

### Doku / Tracking
- **ADR-S090-1** (feld-keyed 422); ADR-S000-1 als „Superseded" markiert.
- `coding-guideline-typescript.md` §4b: Erfolgs-Seiteneffekte via `onSuccess`-Callback, `matchState success` für Render.
- tech-debt: TD-S090-1..4 neu (collect-all + feld-tragender Fehlertyp; matchKind-Adoption; DTO non-nullable 400-vs-422; unchecked cast/shared contract); TD-S083-1 aktualisiert (POST gelöst, GET offen); TD-S083-5 Priorität Niedrig→Mittel.
- observations: OBS-S090-1 (vitest typ-blind), -2 (qa-check-Hash/Re-Stage), -3 (Alt-Hooks prüfen), -4 (Subagent-git-add umgeht Test-Gate), -5 (TD-Grooming-Lücke); Rezidiv-Notizen an OBS-S085-3 (grep/tail) + OBS-S085-8 (Modellwahl/Implementer-Default-Frage).
- **matchKind-Deferral** via Code-Kommentar (bewusst kein ADR – nur aufgeschoben) + TD-S090-2.
- Retroaktiv: `session_089.md` aus Transkript+Commit rekonstruiert, **#89**-Index-Zeile ergänzt.

## Probleme / Findings
- **LL-S090-1 (MITTEL):** Offener MUI-Dialog setzt den Hintergrund `aria-hidden` → `getByRole('listitem')` fand nichts (Komponente **und** E2E, derselbe latente Bug). Fix: `{ hidden: true }` (testing-library) / `{ includeHidden: true }` (Playwright).
- **E2E-Race + dirty-Postgres:** `itemsBefore` vor Laden erfasst + Residuen aus nicht zurückgesetzter DB → `waitForLoadState('networkidle')` + `toHaveCount`; bestätigt TD-S083-5.
- **qa-check-Hash-Mismatch nach Re-Staging** (2×): Hash rechnet über Index, nachträgliches Stagen invalidierte ihn → Extra-Stryker-Lauf. Erfasst als OBS-S090-2.

## Entscheidungen
- Validierung server-only + feld-keyed 422 (ADR-S090-1).
- matchKind-Konformität (ADR-S056-1) aufgeschoben → Code-Kommentar statt ADR.
- Commit-Split: (a) Szenario, (b) Pfad-Fixes.

## Offene Punkte
- Vor nächstem Szenario: `noUncheckedIndexedAccess` vorbereiten (TD-S083-5-Umfeld).
- `@US-904-error` weiter: „leere Einheit anlegen schlägt fehl" (+ Variante: beide leer).
- Affordance- + Fokus-auf-Fehler-Szenario(en); UX-Guideline-Regel landet mit der Implementierung; gherkin-workshop „Formular-UX-Baseline"-Checkliste.
- Backlog-OBS S090-3/-4/-5 + OBS-S085-3/-8-Rezidive → nächste Retro.

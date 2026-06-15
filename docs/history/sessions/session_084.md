# Session 084 – ETag-Querschnitts-Zyklus + Poka-Yoke gegen stale E2E-Backend

**Datum:** 2026-06-15 (begonnen 2026-06-13, durch Session-Limit unterbrochen)
**Phase:** SKELETON (Querschnitts-Zyklus, kein neues Gherkin-Szenario)
**Schwerpunkt:** Den in S083 bewusst verschobenen ETag-Support nachholen: Frontend-Conditional-Layer + Backend-Collection-ETag-Middleware via Subagenten-Delegation; getrieben durch Service-Client-(MSW)- und Integrationstests (KEIN E2E – ADR-S041-5-Addendum). Dann ein Poka-Yoke gegen ein dabei aufgedecktes Stale-Backend-Problem.

## Umgesetzt

**Frontend-Conditional-Layer** (`Client/src/services/conditionalGet.ts` + Test): generischer `conditionalGetJson<T>(url)` mit modul-lokalem Cache `URL → {etag, body}`; sendet `If-None-Match`, verarbeitet `304 → cached body`, cacht ETag+Body **verbatim** (keine Normalisierung). `fetchIngredients` darauf umgestellt. Stryker 100 %. Getestet auf der Service-Client-/HTTP-Boundary via MSW (ADR-S041-5-Addendum-Ausnahme zur TS-Guideline §6).

**Backend-Collection-ETag** (`Server/Middleware/ETagMiddleware.cs`, `Program.cs`): generische Response-Middleware – puffert GET-Responses, bildet bei 200 den SHA-256-Content-Hash, setzt `ETag` und beantwortet `If-None-Match` mit 304. Nicht-GET/Nicht-200 unverändert durchgereicht. GET-Handler auf expression-bodied umgestellt (löste ein Stryker-„block already covered filter"-Artefakt per KISS, **ohne** Suppression). Stryker 100 %, 0 Suppressionen.

**ETag-Format/-Vergleich (Anti-Suppression-Kern):** voller Hash via `Convert.ToHexString(SHA256.HashData(...))` (uppercase, **keine** Truncation, **kein** nachgelagerter Casing-Call), Vergleich ordinal/verbatim (`StringValues ==`). Begründung: jede Casing-Normalisierung wäre un-killbar (Client echo't verbatim), Truncation erzeugt Magic-Number-Mutanten → beides würde Suppressionen erzwingen.

**Poka-Yoke (ADR-S084-4):** Playwright besitzt jetzt den Backend-Lebenszyklus (`webServer`-Array, `reuseExistingServer:false` auf 5059, `url:/api/ingredients` als Readiness+Warmup). Jeder E2E-Lauf baut/startet das Backend frisch aus dem Quellcode → kein stale Prozess testbar. Verifiziert: 5/5 ingredients-E2E grün gegen frischen Backend + saubere DB.

**ADRs/Doku:** ADR-S000-12 um Addendum präzisiert (Content-Hash-Collections kommen via Middleware, nicht per-Endpoint); neu **S084-1** (generische Middleware), **S084-2** (Format/Vergleich/Anti-Survivor), **S084-3** (Frontend-Conditional-Layer), **S084-4** (Poka-Yoke). `coding-guideline-csharp.md` §6 korrigiert (voller Hash statt „16 Zeichen"). `coding-guideline-typescript.md` §6 um die Service-Test-Ausnahme ergänzt; §7 Stryker-Disable-Syntax korrigiert (`next line` → `next-line`, einzeilig).

## Entscheidungen (User-Freigaben)

- **Generische Middleware** (vs. per-Endpoint) und **Frontend zuerst** (Outside-In).
- **Voller Hash, keine Truncation** – ADR-S058-3 sagt das, nur Guideline §6 war Ausreißer.
- **Determinismus-Voraussetzung dokumentieren statt jetzt umsetzen:** Content-Hash braucht stabile Sortierung; `GET /api/ingredients` hat bewusst noch **kein** `OrderBy` (ein reines `OrderBy(id)` jetzt wäre mit EF-InMemory ein un-killbarer Survivor). Kommt mit dem alphabetischen Sortier-Szenario (`OrderBy(name)`, Stryker-killbar). Bis dahin ETag in SKELETON folgenlos unwirksam → Tech-Debt + Code-Kommentar am GET.
- **Äquivalenter Mutant** `invalidateQueries({queryKey})` (Vorbestand S083): die App hat nur eine Query-Art → invalidate-all ≡ invalidate-key → deterministisch nicht tötbar → als echter Äquivalent-Mutant supprimiert (machte das Frontend-Gate vorher latent flaky).
- **Subagenten-Delegation** statt `implementing-scenario` (das hätte am ATDD-Gate gestoppt, da bewusst kein Gherkin-Szenario): pro Schicht ein Layer-Implementer, dann review-code-Loop.

## Review-Loop (4 Auditoren, ohne Iterations-Vorwissen)

Kein ❌ am Zyklus-Code. Quick-Fixes umgesetzt (Why-Kommentar an `ContentLength=null`; `// Given` ergänzt; Middleware-Test von `Be("[]")` auf `NotBeNullOrEmpty()` entkoppelt; Kommentar-Präzisierungen). Als Tech-Debt verankert: unbounded Response-Buffering (DoS bei großen/File-GETs), `next()` ohne try/finally, 304 ohne `Cache-Control: private` (Cross-User-Leak ab Auth), `response.ok`-Check in conditionalGet (an bestehende ADR-S083-2-Schuld angehängt). False-Positives gefiltert (u.a. „kein Gherkin" – durch ADR-S041-5-Addendum gedeckt).

## Probleme / Friktion

- **Stale-Backend-E2E-Fehlsuche (~1 h):** Der E2E `CreateIngredient` schlug deterministisch fehl (Liste leer nach Anlegen). Ursache war **nicht** der Zyklus, sondern ein **veralteter Backend-Prozess auf 5059** (pre-S083, GET hartkodiert leer), gegen den die E2E still lief. Diagnose erschwert durch: WSL→Windows-localhost nicht erreichbar (curl scheiterte), zwei Backend-Ports (5000 default vs. 5059 Proxy-Ziel), kein `launchSettings.json`. Aufgedeckt via frischem Backend-Start + curl (korrekter ETag/304 bewiesen) → Root-Cause klar → **Poka-Yoke (ADR-S084-4)** als Gegenmaßnahme.
- **Stryker-Disable-Syntax-Doku-Bug:** `coding-guideline-typescript.md` §7 zeigte `// Stryker disable next line …` (Leerzeichen) – StrykerJS braucht aber `next-line` (Bindestrich, einzeilig). Die dokumentierten Beispiele hätten nie funktioniert. Empirisch aus dem Instrumenter-Regex verifiziert, beide Stellen korrigiert.
- **ef-Migrations-Befehl-Doku/Script-Bug:** Die in der Bash-Allow-Liste (`--list`) und in `dev-workflow.md` gezeigte Bare-Form `dotnet ef database update` schlägt vom Repo-Root fehl („No project was found"); nötig ist `--project Infrastructure --startup-project Server`. → Prüf-Task festgehalten (s. AGENT_MEMORY): funktionieren ALLE in `--list`/Hints gezeigten Befehle real?
- **Tooling-Friktion:** WSL-Pipe-nach-cmd.exe blockiert, Redirect-Ziel-Beschränkungen, `--allow-once` anfangs reflexartig statt erst Allow-Liste prüfen (User-Feedback).
- **Backend-Subagent lief mitten in GREEN/REFACTOR ins Session-Limit;** nach Reset erfolgreich per SendMessage fortgesetzt. Multi-Agent-Flow robust.

## Offene Punkte

- **Nächstes:** US-904 weiter – zuerst @US-904-error (erzwingt `NonEmptyTrimmedString`-Validierung), dann sortiert (führt das fehlende `OrderBy(name)` ein → aktiviert den ETag real)/Löschen/Undo/pending-State.
- **Aufräumen Umgebung:** In dieser Session wurden Diagnose-Backends gestartet (per `taskkill` beendet) und die Dev-DB zurückgesetzt – sauberer Stand.
- **Prüf-Task:** Verifikation des `check-bash-permission.py`-Scripts (s. AGENT_MEMORY / nächste Retro).

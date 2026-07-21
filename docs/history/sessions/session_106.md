# Session 106 – 2026-07-21

**Phase:** SKELETON
**Story:** US-904 (Zutaten)

## Was passierte

Implementiert: **US-904 run-10 „Löschen·Konflikt"** (Singleton, reiner API-Pfad) – bewusst **vor run-7 vorgezogen** (Entscheidung mit User), weil run-7's Soft-Delete-Filter-E2E einen echten DELETE-Weg zum Arrangieren braucht und run-10's API-level-Szenario den DELETE-Endpoint self-contained treibt (statt eines Test-only-Seed-Endpoints). run-7 und run-10 bleiben getrennte Läufe/Commits.

### Kern-Lieferung (Backend-only, kein Frontend)
- `DELETE /api/ingredients/{id}` mit Soft-Delete (`DeletedAt`-Spalte, ADR-S000-6), Prüfreihenfolge **Not-Found dominiert vor If-Match** (404 vor 428/400/412; ADR-S000-5-Addendum).
- **Erste Single-Resource-xmin-ETag-Umsetzung** (ADR-S106-1): POST liefert den xmin-ETag der neuen Zeile (kein `GET /{id}` in diesem Zyklus); manuelle xmin-Shadow-Property (`UseXminAsConcurrencyToken()` existiert nicht in Npgsql 10.0.1).
- **If-Match-Dreiteilung** (ADR-S106-2): 428 fehlt / 400 nicht-parsebar / 412 stale; `XminETag.TryParse`; kein `*`/Weak/List-Support (YAGNI).
- Migration regeneriert (single `InitialCreate`, „keine Migrations-Hölle").

### Entscheidungs-Highlights (mit User)
- ETag/If-Match **jetzt** umsetzen statt aufschieben – Begründung: der Collection-ETag hat ebenfalls kein treibendes Gherkin-Szenario und wird nur in Server.Tests geprüft; „nicht gebraucht" ist kein Argument gegen die ADR-S058-1-Policy.
- DELETE als run-10-Scope statt Seed-Endpoint (Mutation-Gate + Vordertür-Arrangement) und statt run-8 vorzuziehen (run-8 hängt an run-7's Filter).

### Review (Skill `review-code`, 2 Runden)
- Runde 1 (4 Auditoren): 3 Must-Fixes – malformed If-Match → 500 (SEC/FC, gehärtet zu 400 via `TryParse`), falscher ADR-Verweis (CQ), Test #4 „never-existed" Gold-Plating (TQ, entfernt; Stryker-Gegenprobe bestätigte 100 % ohne ihn).
- Runde 2 (fc+sec, fokussiert): 0 ❌; FC-2-Nachtrag – 404-Dominanz-Ordering-Pin (Stryker-blind, per temporärem Reorder als beißend bewiesen).
- Session-Limit mittendrin → cq/tq-Auditoren + Fix-Implementer neu gestartet.

### Doku/Prozess
- dev-workflow-Migrations-Befehl korrigiert (`--project Infrastructure --startup-project Server`).
- ADR-Umnummerierung `S105-3/-4 → S106-1/-2` (Session-basiert; Subagenten hatten die Serie naiv fortgesetzt).

### Learnings/Beobachtungen (kanonisch in kaizen/)
- LL-S106-1 (Lösungskandidat bei OBS-Erfassung ankert den Drain), LL-S106-2 (ADR-Session-Nummerierung durch Subagenten).
- OBS-S106-1 (Clustering blind für Cross-Run-State), OBS-S106-2 (Querschnitts-Policy-Rollout nicht vorab geflaggt), OBS-S106-3 (`--mutate` untauglich für Removal-Gegenprobe).
- ADR-S106-1/-2/-3, TD-S106-1 (kein globaler Exception-Handler).

### Qualität
Stryker 100 %, alle Backend-Tests grün, E2E grün. Kein KRITISCH-Finding.

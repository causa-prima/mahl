# Session 105 – 2026-07-21

**Phase:** SKELETON
**Story:** US-904 (Zutaten) – run-6 „Anlegen·Name-Eindeutigkeit" abgeschlossen

> Über zwei Kalendertage: Kern-Umbau am 18.7. (Orchestrator + Subagenten, ins Session-Limit gelaufen),
> Fortsetzung + Abschluss am 21.7.

## Implementiert

### US-904 run-6 „Name-Eindeutigkeit" (Full-Stack) – das Feature
- Anlegen mit bereits vorhandenem Namen wird abgelehnt – **exakt**, **case-insensitiv** und **getrimmt** (ADR-S051-3). Antwort: field-keyed 422 mit dynamischer Meldung „Eine Zutat mit dem Namen 'X' existiert bereits." (X = getrimmter Eingabewert), ADR-S090-1 + ADR-S004-1 Addendum S105 (field-keyed statt der ursprünglich geplanten plain-text-Klausel).
- Neuer payload-tragender Sum-Type-Case `NameDuplicate(enteredName)` in `IngredientValidationError` (ADR-S018-1 Variante A, `Match<T>` bricht compile-time für den Konsumenten).
- **Frontend:** keine neue Schicht – der generische `FieldErrors`-Konsum in `createIngredient` rendert die Meldung ohne Sonderbehandlung am Name-Feld.

### Durchsetzung + Test-Infra (der Enabler)
- **Eindeutigkeit DB-seitig** (ADR-S105-2): funktionaler `LOWER(name)`-Unique-Index (Raw-SQL in `InitialCreate`), Endpoint fängt die `DbUpdateException` (Postgres `23505`, präzisiert auf `ConstraintName: "IX_Ingredients_Name_Lower"`) → 422. Eliminiert das TOCTOU-Fenster des früheren App-Layer-Check-then-Insert.
- **Integrationstest-Provider EF-InMemory → Testcontainers-Postgres** (ADR-S105-1), damit der Constraint überhaupt testbar ist: echtes Postgres (`Testcontainers.PostgreSql`), ein geteilter Container pro Assembly-Lauf (`PostgresContainerFixture`/`PostgresCollectionDefinition`), Schema via `MigrateAsync`, per-Test-Reset geteilt mit E2E (`DatabaseResetExtensions`).

### Umlaut-Locale + Single Source
- Der Duplikat-Check hängt am DB-Locale: `docker-compose` erzwang `--locale=C` (ASCII-only-Folding) ↔ Testcontainer-Default `en_US.utf8` (faltet Umlaute) → Test≠Prod. Behoben durch **Single Source** `config/postgres.env`, die compose (`env_file:`) UND der Testcontainer (`PostgresTestConfig`) lesen → keine Divergenz mehr (CM-S105-1). Der case-insensitive Duplikat-Test nutzt jetzt „Öl"/„öl" (statt ASCII) und nagelt das Locale auf allen 3 Ebenen fest.
- **Tests:** Server.Tests 24/24 (inkl. `PostgresTestConfig`-Parser-Unit-Tests), E2E 25/25 (frisches Volume; neuer Seed-Helper `seedIngredientViaApi` legt die Duplikat-Vorbedingung per API vor dem Seiten-Load an). Umbau-Review (18.7.): 3 Auditoren, 0 ❌.

## Entscheidungen
- **Locale angleichen (en_US.utf8) statt C**, umgesetzt als Single-Source-Config statt per-Column-Collation (KISS; Root-Fix der getrennten Config-Quellen, nicht nur des Symptoms Locale).
- **Umlaut als Datenvariante** des bestehenden „abweichende Schreibweise"-Szenarios (Öl statt Tomaten auf allen 3 Ebenen), kein separates Szenario – ASCII-Faltung bleibt durchs Trim-Szenario gedeckt.
- **In-place-Ergänzung des Index** in `InitialCreate` (statt neuer Migration): Konsequenz „bereits migrierte Umgebungen bekommen den Index nicht automatisch" durch einmaligen `docker compose down -v` gelöst, nicht dokumentiert (einmalig, Skeleton-Phase, keine prod-Daten).
- **`.env` gitignored** (für spätere Secrets reserviert); geteilte NICHT-geheime DB-Config in `config/postgres.env`.
- Session-Nummer 105 (deckt sich mit ADR-S105-*). Vorbestehende Lücke: Session 104 (OBS-Drain, Commit `98e5d7a`) hat weder `session_104.md` noch Index-Zeile – hier nur vermerkt, nicht rückwirkend geschlossen.

## Erkenntnisse (Verweise)
- LL-S105-1 – False-Green durch Test↔Prod-Divergenz der DB-Engine-Config (Locale) (→ `lessons_learned.md`); Countermeasure CM-S105-1 (→ `countermeasures.md`).
- OBS-S105-2 – C#-String-Ops triggern unter `TreatWarningsAsErrors` kulturbezogene Analyzer (→ `observations.md`).

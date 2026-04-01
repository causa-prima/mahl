# Session 41 – 2026-03-26

## Typ
Reine Architektur- und Konzept-Diskussion. Kein Produktionscode geschrieben.

## Schwerpunkte
- CA1515-Analyse führte zu tiefer Diskussion über Testing-Architektur
- Umfassender Best-Practices-Audit (34 bereits implementiert, ~40 Gaps identifiziert)
- Grundsatzentscheidungen zur Zielarchitektur
- Entscheidung: Backend-Code verwerfen, Neustart mit ATDD/BDD

---

## Entscheidungen (vollständig in decisions.md dokumentiert)

### Architektur
- **Hexagonal Architecture / Ports & Adapters** – explizit als Leitprinzip adoptiert
- **Infrastructure Layer** (`mahl.Infrastructure`) – DbContext + DbTypes als eigenes öffentliches Projekt; Server bleibt internal; kein `InternalsVisibleTo`
- **Domain-Typen internal** – keine direkten Unit-Tests; Verhalten via Endpoint-Tests abgedeckt
- **Defensive Guards** – behalten für Sprachschutz; kein Test; Stryker disable mit Begründung

### Testing
- **BDD/Gherkin** – `.feature`-Dateien als ausführbare Spec (`playwright-bdd` / `SpecFlow`)
- **Outside-In ATDD / Double-Loop TDD** – Reihenfolge immer: Gherkin (rot) → Frontend-Test (rot) → Backend-Test (rot) → Code (grün); kein Backend-Test ohne darüberliegenden Test
- **E2E Quality Gate** – Spec-driven Checklist mit `@US-ID`-Tags + CI-Validator; Branch/Line-Coverage 100% projektübergreifend (alle Schichten), aber kein separater Coverage-Gate für E2E
- **Bidirektionale Traceability** – Spec→Test und Test→Spec; Test-Audit Teil jedes Reviews
- **Mutation Testing Ziel** – 100% bestätigt (war fälschlicherweise ≥90% in NFR.md; korrigiert)

### Vorgehen
- **Backend-Code verwerfen** – Neustart mit ATDD; Specs + decisions.md + lessons_learned.md bleiben
- **Spec-Audit vor Neustart** – prüfen ob Code Verhalten enthält das nicht in Specs steht

### Best Practices (Adopt/Skip/Defer)
| Praxis | Entscheidung |
|--------|-------------|
| Health Checks | Adopt |
| OpenAPI → TS Type Generation | Adopt (statt Pact) |
| Metrics/Telemetry | Adopt vor Produktion |
| Domain Events | Adopt V1 (ggf. MVP) |
| Aggregate Roots | Adopt inkrementell |
| Bounded Contexts | Adopt V1 + Domain Events |
| Property-Based Testing | Consider nach SKELETON (Endpoint-Ebene) |
| Snapshot Testing | Skip |
| API Versioning | Skip |
| Contract Testing (Pact) | Skip |
| Specification Pattern | Review-Hinweis |

---

## Offene Punkte / nächste Session

### Priorität 1: Dokumentations-Großüberarbeitung
Alle folgenden Dokumente müssen in der nächsten Session angepasst werden:

**Bestehende Docs anpassen:**
- `ARCHITECTURE.md` – Hexagonal Architecture (Sektion 0a), Infrastructure Layer (Sektion 4), internal/public Boundaries
- `CODING_GUIDELINE_CSHARP.md` – `internal`-Pflicht für Domain-Typen, Defensive Guards, Stryker-Kategorien
- `CODING_GUIDELINE_GENERAL.md` – Defensive-Guards-Subsection, Progressive Disclosure verbessern
- `CODING_GUIDELINE_TYPESCRIPT.md` – Progressive Disclosure verbessern (Score 5/10)
- `TDD_PROCESS.md` – Outside-In ATDD, Double-Loop TDD, BDD/Gherkin, Stryker-Survivor-Kategorien
- `REVIEW_CHECKLIST.md` – Test-Audit (Test→Spec Traceability), Assertion-Tiefe, Architecture-Layer-Checks
- `DEV_WORKFLOW.md` – Infrastructure-Projekt-Hinweise
- `CLAUDE.md` – Navigation zu neuen Konzepten

**Neue Dokumente:**
- `E2E_TESTING.md` – BDD/Gherkin, Spec-driven Gate, @US-ID-Tags, Assertion-Tiefe, Cross-Feature-Szenarien

**Skills anpassen:**
- `implementing-feature` – Architecture-Check um Infrastructure/internal erweitern
- `tdd-workflow` – ATDD-Reihenfolge, Stryker-Kategorien
- `review-code` – Infrastructure-Checks, Test-Audit
- `closing-session` – Progressive Disclosure Hinweis

**Hooks:**
- Neuer Check: Domain-Visibility (scannt `Server/Domain/*.cs` auf `public`-Typen)

### Priorität 2: Spec-Audit + Neustart
Nach Dokumentations-Großüberarbeitung: Audit des bestehenden Backend-Codes, Specs ergänzen, dann Backend verwerfen und mit ATDD neu starten.

---

## Bekannte Inkonsistenzen (behoben in dieser Session)
- `NFR.md`: ≥90% → 100% Mutation Coverage ✅
- `decisions.md`: Revisionsvermerk zur alten 90%-Entscheidung ✅
- `decisions.md`: Alle neuen Architekturentscheidungen dokumentiert ✅

## Was gut lief
- Debate-Agenten-Format (2× Pro, 2× Contra) lieferte unvoreingenommene, tiefe Analyse
- Grill-Me-Ansatz vor Entscheidungen sicherte gemeinsames Verständnis
- User stellte kritische Korrekturen (Playwright ohne UI, ATDD-Minimality) – gute Checks

## Was schwierig war / Fehler
- Falsch behauptet: "Playwright-Tests können nicht ohne UI geschrieben werden" → falsch; User korrigierte
- Ungenau: "ATDD beweist Minimalität" → ATDD beweist nur Code-Test-Kopplung; Spec-Test-Kopplung ist Prozess-Disziplin
- Kontext wurde sehr voll (lange Diskussions-Session ohne Code-Output)

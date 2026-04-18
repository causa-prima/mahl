# E2E Testing & BDD/Gherkin

<!--
wann-lesen: Beim Schreiben von Feature-Specs und E2E-Tests, beim Verstehen der Outside-In ATDD Reihenfolge, beim Setup des Spec-driven Quality Gates
kritische-regeln:
  - Reihenfolge immer: Gherkin (rot) → Frontend-Test (rot) → Backend-Test (rot) → Code (grün)
  - Kein Backend- oder E2E-Test ohne darüberliegendes Gherkin-Szenario
  - Jedes Szenario trägt @US-ID-Tag (z.B. @US-101)
  - Spec darf nicht nachträglich angepasst werden, um die Implementierung zu bestätigen
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Outside-In ATDD | Double-Loop TDD, Reihenfolge, Regeln | Vor dem Start jeder User Story |
| BDD/Gherkin | Feature-Dateien, Given/When/Then, Tags, Namenskonventionen | Beim Schreiben von Feature-Specs |
| Quality Gate | @US-ID-Tags, CI-Validator, Spec-driven Checklist | Beim Setup von CI oder beim Review |
| Assertion-Tiefe | Was E2E-Tests prüfen (und was nicht), Full State Assertion | Beim Schreiben von E2E-Test-Steps |
| Traceability | Bidirektionale Spec↔Test-Verlinkung, Test-Audit | Bei jedem Code-Review |

---

## Outside-In ATDD

Reihenfolge, Double-Loop-Diagramm und Regeln: → `docs/TDD_PROCESS.md` (Sektion "Outside-In ATDD / Double-Loop TDD")

---

## BDD/Gherkin

Feature-Dateien liegen im Verzeichnis `features/` (Projekt-Root-Level).

```gherkin
# features/recipes.feature
@US-201
Feature: Rezepte verwalten

  @US-201-happy-path
  Scenario: Neues Rezept anlegen
    Given ich bin angemeldet
    When ich ein Rezept mit gültigem Namen und gültigen Zutaten anlege
    Then wird das Rezept erfolgreich gespeichert
    And ich kann das neue Rezept in der Rezeptliste sehen

  @US-201-error
  Scenario: Rezept mit leerem Namen anlegen schlägt fehl
    Given ich bin angemeldet
    When ich ein Rezept ohne Namen anlege
    Then erhalte ich eine Fehlermeldung, dass der Name nicht leer sein darf
    And die Rezeptliste bleibt unverändert
```

Die Step-Definitionen (z.B. `When ich ein Rezept … anlege`) werden im Test-Code auf konkrete HTTP-Calls gemappt – die Spec selbst bleibt fachlich lesbar, technische Details (Route, Statuscode) stehen nur im Step-Code.

### Tag-Konventionen

| Tag | Ebene | Bedeutung |
|-----|-------|-----------|
| `@US-NNN` | Feature | User Story ID – alle Szenarien des Features gehören zu dieser Story |
| `@US-NNN-happy-path` | Szenario | Erfolgreicher Standardpfad |
| `@US-NNN-error` | Szenario | Fachlicher Fehlerfall (400/409/422) |
| `@US-NNN-edge-case` | Szenario | Grenzfall / Sonderverhalten |
| `@NFR-<domain>` | Feature | Querschnittliche NFR-Feature-Datei (z.B. `@NFR-resilience`) |
| `@NFR-<domain>-<typ>` | Szenario | NFR-Szenario nach Fehler-Typ (z.B. `@NFR-resilience-network`) |

NFR-Features haben keine US-ID. Der CI-Validator behandelt `@NFR-*`-Tags als eigene Klasse – Traceability-Pflicht gilt analog: jedes `@NFR-*`-Szenario braucht einen grünen E2E-Test.

---

## Quality Gate

### Spec-driven Checklist

Der CI-Validator prüft bidirektionale Traceability:
- **Spec→Test**: Jedes Szenario mit `@US-ID`-Tag hat mindestens einen grünen E2E-Test
- **Test→Spec**: Jeder E2E-Test referenziert einen existierenden `@US-ID`-Tag

Ein Feature gilt erst als „Done", wenn sein Gherkin-Szenario grün ist.

### Metriken & Gates

- **Branch/Line-Coverage**: 100% projektübergreifend (alle Schichten: Backend + Frontend + Infrastructure)
- **Mutation Score**: 100% (Stryker.NET / Stryker-JS) – kein Survivor ohne begründete Suppression
- **Kein separater Coverage-Gate für E2E allein** – der E2E-Gate ist die Spec-Traceability (alle @US-ID-Szenarien grün)

---

## Assertion-Tiefe

E2E-Tests prüfen **beobachtbares Verhalten**, nicht Implementierungsdetails:

| ✅ Prüfen | ❌ Nicht prüfen |
|----------|----------------|
| HTTP Status Code | Interne Domain-Typen |
| Response-Body (JSON-Struktur und Werte) | Welche Klasse intern verwendet wurde |
| DB-State nach Write-Operation (Full State) | Implementierungsdetails |
| Fehlermeldung im Response-Body | Stack Traces |

**Full State Assertion gilt auch in E2E-Steps:**
- Nach mutierenden Operationen: gesamten DB-Zustand prüfen (nicht nur einzelne Properties)
- Nach Fehler: DB-Zustand muss dem Ausgangszustand entsprechen

Vollständige Full-State-Assertion-Regeln: `docs/TDD_PROCESS.md` Abschnitt "Pflicht: Full State Assertion".

---

## Traceability

### Bidirektionale Verlinkung

Gherkin ist **dokumentarisch** (keine SpecFlow-Ausführung). Playwright ist der ausführbare äußere Loop.

```
Gherkin-Szenario (@US-201-happy-path)
  └─ Playwright E2E-Test (trägt @US-201-happy-path im describe/test-Namen: US201_HappyPath_...)
       └─ Backend-Integration-Test (Testname: US201_HappyPath_Create_ValidData_Returns201)
```

Alle drei Ebenen tragen denselben Identifier – das ermöglicht direktes Grep (`US201_HappyPath`) über alle Schichten.

**Testname-Format Backend:** `USxxx_ScenarioType_MethodName_Szenario_ErwartetesErgebnis`

`ScenarioType` = Gherkin-Tag-Suffix des Primär-Szenarios (das den Test im inneren ATDD-Loop erzwungen hat): `HappyPath`, `Error`, `EdgeCase`. Bei mehreren Szenarien, die dasselbe Verhalten exercisen: Primär-Szenario taggen, kein Mehrfach-Tagging.

**Pflicht:** Kein Backend-Integrationstest ohne erkennbare Szenario-Zuordnung (US-Tag + ScenarioType).

### Test-Audit (Teil jedes Reviews)

Bei jedem Code-Review prüfen:
- Trägt jeder neue E2E-Test mindestens einen `@US-ID`-Tag?
- Hat jedes neue Gherkin-Szenario mindestens einen grünen E2E-Test?
- Stimmt das Szenario noch mit dem implementierten Verhalten überein (kein Silent Drift)?
- Gibt es Backend- oder E2E-Tests ohne darüberliegendes Gherkin-Szenario? → Outside-In-Verletzung
- Wurden nur Tests angelegt, die das Szenario wirklich fordert? Kein Gold-Plating in Tests (YAGNI gilt auch für Tests)

Test-Audit-Checkliste: `docs/REVIEW_CHECKLIST.md` Abschnitt "Test-Audit".

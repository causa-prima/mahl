# Session 042 – 2026-03-26

## Typ
Dokumentations-Großüberarbeitung (kein Produktionscode).

## Schwerpunkte
Umsetzung der in Session 041 beschlossenen Dokumentations-Überarbeitung: Hexagonal Architecture, Outside-In ATDD/BDD, `internal`-Pflicht, Stryker-Defensive-Guards, neuer E2E-Testing-Guide, neuer Domain-Visibility-Hook.

---

## Umgesetztes

### Bestehende Dokumente angepasst

**`docs/ARCHITECTURE.md`**
- Neue Sektion 0c: Hexagonal Architecture / Ports & Adapters (Projekt-Visibility-Tabelle, Black-Box-Testing-Begründung, kein `InternalsVisibleTo`)
- Sektion 4 (Projekt-Struktur): auf Infrastructure/Server/Server.Tests umgestellt

**`docs/CODING_GUIDELINE_CSHARP.md`**
- `internal`-Pflicht für Typ-Deklarationen in `Server/` (kein `public` ohne Begründung; explizite Klarstellung: betrifft Typdeklaration, nicht Member-Sichtbarkeit)
- Stryker-Suppressionen für Defensive Guards: `Statement,String` (Parameterless-Ctor) und `Equality,String` (default(T)-Guard)

**`docs/TDD_PROCESS.md`**
- Neue Sektion "Outside-In ATDD / Double-Loop TDD" (Reihenfolge, Double-Loop-Diagramm, Regeln)
- Testname-Format auf `USxxx_MethodName_Szenario_ErwartetesErgebnis` aktualisiert
- Stryker-Kategorien-Tabelle für Defensive Guards (Statement,String / Equality,String / Statement,String für Match-Wildcard)

**`docs/REVIEW_CHECKLIST.md`**
- Neue Sektion "Architecture Layer" (internal-Typen, kein InternalsVisibleTo, Ports-only-Tests)
- Neue Sektion "Test-Audit" (US-Tag im Testnamen, Traceability, kein Gold-Plating, Outside-In-Verletzung)

**`CLAUDE.md`**
- `docs/E2E_TESTING.md` in Navigationstabelle ergänzt
- Backend-Endpoint-Zeile: Verweis auf Sektion 0c

**`docs/DEV_WORKFLOW.md`**
- Neuer Abschnitt "Projekt-Struktur (Infrastructure-Referenz)" mit Projektreferenz-Regeln

**Skills:**
- `implementing-feature`: Gherkin-Gate als Schritt 1 (ATDD-Gate – ohne Szenario kein Start); Architektur-Check um `internal`-Pflicht und Infrastructure-Trennung erweitert
- `tdd-workflow`: Testname-Format auf `USxxx_...` aktualisiert
- `review-code`: Test-Audit und Architecture-Layer in Autor-Selbstcheck-Liste
- `closing-session`: unverändert (kein Mehrwert durch spezifische Dateiliste)

### Neue Dokumente

**`docs/E2E_TESTING.md`** (neu)
- Outside-In ATDD / Double-Loop TDD
- BDD/Gherkin mit fachlich lesbaren Szenarien (Domänensprache, kein HTTP im Spec-Text)
- Tag-Konventionen (`@US-NNN`, `@US-NNN-happy-path`, `@US-NNN-error`)
- Quality Gate: Spec-driven Checklist + Metriken & Gates (Coverage 100%, Mutation Score 100%)
- Assertion-Tiefe (Full State auch in E2E)
- Traceability: US-Tag am Anfang des Testnamens (konsistent über alle Ebenen)
- Test-Audit-Checkliste mit YAGNI-Check und Outside-In-Verletzungs-Prüfung

### Neuer Hook

**`.claude/hooks/checks/domain_visibility.py`** + 11 Tests
- Erkennt `public` Typ-Deklarationen in `Server/` (Domain, Endpoints, Dtos, etc.)
- Ausnahme: `Infrastructure/`-Pfade
- In `check-code-quality-blocking.py` eingehängt
- Alle 68 Hook-Tests grün

---

## Korrekturen während der Session (User-Feedback)

| Feedback | Korrektur |
|----------|-----------|
| Neue Sektion sollte 0c (nach 0b) sein, nicht 0a/0b | Nummerierung angepasst: 0b bleibt 0b, neue Sektion ist 0c |
| Gherkin-Beispiel sollte fachlich lesbar sein (nicht HTTP-Details) | Schritte auf Domänensprache umgestellt; Hinweis auf Step-Code-Mapping ergänzt |
| `"internal-Pflicht"` könnte als "alles muss internal sein (auch private)" missverstanden werden | Formulierung präzisiert: "Typ-Deklarationen sind `internal` (kein `public`)" + explizite Klarstellung Member-Sichtbarkeit |
| Coverage-Sektion fehlt Mutation Testing; Name passt nicht mehr | Umbenannt in "Metriken & Gates", Mutation Score 100% ergänzt |
| Verlinkung im Backend-Test: US-Tag im Namen ist Pflicht, nicht Commit-Kommentar | US-Tag am Anfang des Testnamens als Pflicht festgelegt |
| US-Tag sollte auch bei E2E/Gherkin am Anfang stehen | Konsistente Regel über alle Ebenen: Tag immer am Anfang |
| "Kein Backend-Test" → korrekter "Kein Backend- oder E2E-Test" | In allen Dokumenten konsistent korrigiert |
| Gherkin-Gate sollte Schritt 1 sein (nicht 2b) | Als ersten Architektur-Check-Schritt in `implementing-feature` gesetzt |
| Stryker-Suppression: `Equality` allein reicht nicht – auch `String` für "Uninitialized" | `Equality,String` in Guideline und Beispiel korrigiert |

---

## Offene Punkte / nächste Session

1. **Spec-Audit**: Bestehenden Backend-Code auf Verhalten prüfen, das nicht in Specs steht → Specs ergänzen
2. **Neustart**: Backend verwerfen, mit BDD/Gherkin + Outside-In ATDD neu beginnen
3. **STJ/Deserialisierung verifizieren**: 400 vs. 500 bei ungültigem URI; STJ `OriginalString` unverifiziert
4. **CA1062**: HTTP-Grenz-Validierung (null-DTOs trotz NRT)
5. **Progressive Disclosure**: `CODING_GUIDELINE_GENERAL.md` + `CODING_GUIDELINE_TYPESCRIPT.md` (Score 5/10, war in Session 041 dokumentiert, wurde deprioritisiert)

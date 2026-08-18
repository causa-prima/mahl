# Architecture Decision Records

<!--
wann-lesen: Bevor eine Entscheidung getroffen wird die bereits getroffene Entscheidungen
            berühren könnte. Vor dem Schreiben von Tags:
            `python3 .claude/scripts/decisions.py tags` ausführen – listet alle
            verwendeten Kategorien und Tags.
aufnahmebedingung: Hier steht eine **entschiedene** Sache am Produkt (Code + Build-/Test-Kette),
            von der nach Behebung oder Ablösung ein **terminaler Rest** bleibt – etwas, das ohne
            diesen Eintrag unverständlich wäre. Operativer Test (Kurzfassung; kanonischer Wortlaut
            in `CLAUDE.md`): „Ist die Sache erledigt – bleibt dann etwas zu erklären übrig?"
            Ja → hierher (der Eintrag wird `Superseded` und bleibt stehen).
            Nein → `docs/tech-debt.md`. Noch nicht entschieden → `docs/open-questions.md`.
            Trägt eine Entscheidung einen Aufschub, gehört der Aufschub-Teil als eigener Eintrag
            nach `docs/tech-debt.md` – eine ADR trägt keinen Aufschub. Bei **neu** erfassten
            Einträgen mechanisch geprüft: `.claude/hooks/check-adr-capture.py` blockt
            Aufschub-Vokabular (Escape für bewusste Einzelfälle: `adr-ok`-Marker im Eintrag).
            Abgrenzung ADR/TD/OQ kanonisch: `CLAUDE.md`, Sektion „Ablage: ADR, TD oder offene Frage?"
kritische-regeln:
  - Jede selbst getroffene technische Entscheidung hier dokumentieren
  - Format: Status + Tags + Entscheidung + Begründung + Verworfen
  - Neue Tags nur nach Prozess (siehe oben) und Freigabe
-->

> Archiv aller technischen Entscheidungen. Discovery via `python3 .claude/scripts/decisions.py list`.
> Historisch überholte Einträge: `docs/history/decisions-archive.md`

---

> Gefilterte Suche: `python3 .claude/scripts/decisions.py list --tag resource:ingredients`
> Cross-cutting ADRs: `python3 .claude/scripts/decisions.py list --tag scope:cross-cutting`

---

## Architektur & Prozess

### ADR-S041-1: Hexagonal Architecture / Ports & Adapters

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:hexagonal

**Entscheidung:** Die Anwendung ist ein Hexagon mit klar definierten Ports: HTTP-Endpoints (eingehender Port) und DbContext (ausgehender Port). Tests exercisen die Anwendung ausschließlich über diese Ports – kein direkter Zugriff auf Server-Interna aus Tests.

**Verworfen:** Black-Box-Tests via InternalsVisibleTo – verletzt das Prinzip, da interne Typen direkt referenziert werden.

---

### ADR-S041-2: Infrastructure Layer als eigenes Projekt (mahl.Infrastructure)

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:hexagonal, tooling:build

**Entscheidung:** `MahlDbContext` und alle `*DbType`-Klassen ziehen in ein eigenes Projekt `mahl.Infrastructure` (public by design – sie sind der ausgehende Port). `mahl.Server` (Endpoints, Domain, DTOs) bleibt vollständig internal. Kein `InternalsVisibleTo` nötig – Tests referenzieren `mahl.Infrastructure` direkt.

**Verworfen:** `InternalsVisibleTo` – "fake encapsulation"; verletzt das Prinzip, während es Compliance vortäuscht.

---

### ADR-S041-3: Domain-Typen sind internal, keine direkten Unit-Tests

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:domain-type, testing:integration-test

**Entscheidung:** Alle Domain-Typen sind `internal`. Keine dedizierten Unit-Tests für Domain-Typen – ihr Verhalten wird vollständig über Endpoint-Integration-Tests abgedeckt. In einer Application (nicht Library) ist die HTTP-API die öffentliche Schnittstelle, nicht die Domain-Klassen.

---

### ADR-S041-4: BDD/Gherkin als Standard für E2E-Tests

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:gherkin, testing:e2e

**Entscheidung:** `.feature`-Dateien (Gherkin) sind die **dokumentarische** Spec – kein separates Spec-Dokument, kein BDD-Runner. Playwright (TypeScript) ist der ausführbare äußere Loop und trägt `@US-ID`-Tags im describe/test-Namen.

**Verworfen:** SpecFlow/Reqnroll – läuft nur in C#, kann damit nur die API testen, nicht das Full-Stack-Nutzerverhalten. Für das TypeScript-Frontend wäre trotzdem Playwright nötig → zwei parallele Test-Stacks mit demselben Gherkin, unlösbarer Stack-Mismatch.
**Verworfen:** Separate Spec-Dokumente + handgeschriebene Tests – erzeugt unvermeidliche Divergenz.

---

### ADR-S041-5: Outside-In ATDD / Double-Loop TDD

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:e2e, testing:gherkin, testing:integration-test

**Entscheidung:** Die Reihenfolge ist immer: Gherkin-Szenario (E2E, rot) → Frontend-Test (rot) → Backend-Integration-Test (rot) → Backend-Code (grün). Das Gherkin-Szenario wird zuerst geschrieben – auch wenn das Frontend noch nicht existiert. Kein Backend-Test darf existieren, ohne dass ein darüberliegender Test ihn fordert.

**Addendum (S083) – nicht-E2E-beobachtbare Anforderungen:** Anforderungen, die auf der E2E-/Nutzerebene **nicht beobachtbar** sind (HTTP-Caching-Header wie ETag, Concurrency-Token, sonstige Transport-/Protokoll-Eigenschaften), werden auf der **obersten Schicht getestet, auf der sie beobachtbar sind** – i.d.R. die Service-Client-/HTTP-Boundary (Frontend via MSW: `If-None-Match` gesendet, 304 verarbeitet) bzw. der Backend-Integrationstest (ETag-Header, 304 bei Match). Ein fehlender Gherkin-/E2E-Treiber ist für solche Querschnitts-Eigenschaften **kein** Outside-In-Verstoß; ein E2E-Test, der rohe HTTP-Mechanik durch den Browser prüft, wäre hier das falsche Werkzeug.

**Testnamen für scenario-lose Querschnitts-Tests:** Da kein `@US-NNN`-Szenario existiert, entfällt das `USxxx_ScenarioType_`-Pflichtpräfix (`docs/process/e2e-testing.md`). Solche Tests tragen stattdessen einen sprechenden, am Concern orientierten Namen (z.B. `ETagMiddleware_IfNoneMatchMatchesETag_Returns304WithoutBody`). Ein erzwungenes `US904`-Präfix auf einer endpoint-agnostischen Middleware wäre semantisch falsch.

---

### ADR-S041-6: E2E Quality Gate: Spec-driven Checklist (nicht Coverage-Metrik)

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:e2e, testing:gherkin

**Entscheidung:** Quality Gate für E2E-Tests = Spec-driven Checklist: Für jede User Story min. 1 Happy-Path-Szenario, für jede Rejection-Regel min. 1 Rejection-Szenario, für jeden Fehlerfall min. 1 Error-Szenario. Verifiziert via `@US-ID`-Tags + CI-Skript.

**Klarstellung Coverage:** 100% Branch/Line-Coverage wird projektübergreifend gehalten. Was abgelehnt wurde: ein *separater* Coverage-Gate exklusiv für E2E-Tests.

**Verworfen:** Separater Branch/Line-Coverage-Gate für E2E-Tests – misst Ausführung statt Korrektheit.

---

### ADR-S041-7: Bidirektionale Traceability: Spec ↔ Test

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:e2e, testing:gherkin

**Entscheidung:** Zwei-Richtungs-Prüfung: (1) Spec → Test: Gate schlägt fehl wenn Spec-Eintrag kein Szenario hat. (2) Test → Spec: CI-Check verifiziert dass jeder `@US-ID`-Tag auf einen gültigen Spec-Eintrag zeigt.

**Addendum (S088) – Link-Mechanismus `// Szenario:`-Kommentar:** Der konkrete Träger der Spec↔Test-Verknüpfung ist ein `// Szenario: <exakter Gherkin-Titel>`-Kommentar direkt über jedem Playwright-Testfall in `Client/e2e/**/*.spec.ts`. Der Titel (statt der Kategorie-Tags wie `@US-904-error`, die nicht pro Szenario eindeutig sind) ist der Schlüssel, weil er pro Szenario eindeutig ist und bereits in der Feature-Datei existiert (kein paralleler ID-Namespace).

Drei Invarianten, durchgesetzt vom **PreToolUse-Hook `check-e2e-scenario-ref.py`** (blockiert den Edit, exit 2, bevor ein Verstoß landet – Poka-Yoke):
- **Präsenz:** jeder Testfall (`test(`/`test.only|skip|fixme(`, nicht `describe`/Hooks) hat einen `// Szenario:`-Kommentar.
- **Gültigkeit:** jeder Kommentar-Titel matcht exakt ein Szenario in `features/`.
- **Eindeutigkeit:** kein Titel doppelt über E2E-Specs hinweg.

Verwertet werden die Kommentare von **`next_run.py`**: DONE-Erkennung (Titel kommt in einer Spec vor) speist `--open`/`--done` und die Auflösung des `{{NEXT_RUN}}`-Platzhalters in `AGENT_MEMORY.md` (Story → Feature-Datei via deren `@US-NNN`-Tag → erster offener Lauf in Datei-Reihenfolge; Priorität kann das via expliziten Anstrich überschreiben). `next_run.py --check` ist der repo-weite Beide-Richtungen-Verifier (fängt auch Feature-Retitle, der einen Kommentar verwaisen lässt). Der Mapping-Check ist bewusst **Orchestrator-Verantwortung** (nur dieser schreibt E2E-Tests) und **nicht** Teil des Subagenten-`qa-check.py`.

**Addendum (S097) – Umbenennung `next_scenario.py` → `next_run.py`:** Mit der Umstellung von `implementing-scenario` auf Szenario-Läufe (ein Lauf = ein oder mehrere Szenarien desselben Clusters, `# @run-N`-Kommentar-Tag, siehe `.claude/skills/gherkin-workshop/references/scenario-clustering.md`) löst das Script nicht mehr das nächste **Einzel**-Szenario auf, sondern den nächsten offenen **Lauf** (Gruppierung über `scenario["run"]["number"]`; Szenarien ohne Run-Tag bleiben rückwärtskompatibel Einzel-Läufe). Name und Platzhalter (`{{NEXT_SCENARIO}}` → `{{NEXT_RUN}}`) folgen dem allgemeineren Konzept, damit kein erneuter Rename fällig wird, wenn weitere Storys geclustert werden.

---

### ADR-S103-1: Navigation zwischen Seiten – eigenes Cross-Feature statt Story-Feature

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:gherkin, testing:e2e, frontend:react

**Entscheidung:** Sobald eine Story eine neue Seite/Route einführt und bereits mindestens eine andere Seite existiert, gehört das Szenario "wie kommt der Nutzer dorthin" nicht in das Feature-File der Entität, sondern in eine eigene, entitätsübergreifende Datei `features/navigation.feature`, getaggt mit der neuen Feature-Tag-Klasse `@CROSS-<domain>` (erste Instanz: `@CROSS-navigation`). `@CROSS-*` ergänzt `@NFR-*` (docs/process/e2e-testing.md): beide sind Feature-Tags ohne US-ID mit identischer Traceability-Pflicht, `@NFR-*` für nicht-funktionale, `@CROSS-*` für funktionale Querschnitts-Szenarien.

Die Prüfung "entsteht hier ein Navigations-Bedarf?" wird fester Bestandteil der UI-Verhaltens-Checkliste in Schritt 1 des `gherkin-workshop`-Skills (Aspekt "Erreichbarkeit (Navigation)") – für die erste Seite der Anwendung "Nicht relevant", ab der zweiten Seite relevant.

Zusätzlich strukturelle Vorgabe (Interaction Design, kein Szenario nötig dafür): jede Route bekommt einen Eintrag in der In-App-Navigation, erzwungen per Review – UX-Guideline `coding-guideline-ux.md` Prinzip 9.

**Begründung:** Ohne eigene Datei müsste beim Hinzufügen der zweiten Seite nachträglich ein bereits abgeschlossenes Feature-File (z.B. `ingredients.feature`) angepasst werden, nur weil eine andere Story einen neuen Nav-Weg dorthin braucht – das widerspricht dem Prinzip, dass abgenommene Specs nicht rückwirkend fremde Anforderungen aufnehmen. Eine eigene Story/Epic "Navigation" wurde verworfen (siehe unten), weil Navigation selbst i.d.R. keinen eigenständigen Business-Value hat (INVEST-Kriterium "Valuable" verletzt) und das Risiko eines vorab gebauten Nav-Frameworks ohne konkreten zweiten Bedarf birgt.

**Verworfen:** Eigene User Story/Epic "Navigation" – kein eigenständiger Business-Value, Gefahr von Premature-Abstraction (Nav-Framework vor dem zweiten konkreten Anwendungsfall).

---

## API-Validierung & Fehlerbehandlung (alle Endpoints)

### ADR-S000-1: Collect-all Validation: kein Fail-Fast für unabhängige Felder

**Status:** Superseded by ADR-S090-1 (Body-Form `string[]` → feld-keyed; collect-all-Prinzip bleibt gültig)
**Tags:** scope:cross-cutting, arch:validation, http:422

**Entscheidung:** Alle unabhängigen Felder werden vollständig validiert; alle Fehler werden gesammelt zurückgegeben (`422`, Body: `string[]`). Abhängige Validierungen (z.B. `unit` nur prüfen wenn `quantity` gesetzt) bleiben kurzschließend.

**Begründung:** Nutzer sollen alle ihre Fehler auf einmal sehen, nicht einen nach dem anderen.

**Hinweis (S090):** Das collect-all-Prinzip (alle unabhängigen Felder validieren, Fehler sammeln, abhängige Validierungen kurzschließend) bleibt unverändert gültig. Nur die **Body-Form** wurde von flachem `string[]` auf feld-keyed umgestellt – siehe ADR-S090-1.

---

### ADR-S090-1: 422-Fehler-Contract ist feld-keyed (RFC 9457), nicht flaches string[]

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:validation, http:422

**Entscheidung:** Der 422-Validierungsfehler-Body ist **feld-keyed** im Stil von RFC 9457 / ASP.NET `ValidationProblemDetails`: ein `errors`-Objekt, das jeden Feldnamen (= JSON-Property-Name des Requests, z.B. `name`, `baseUnit`) auf seine Fehlermeldungen (`string[]`) abbildet.

```json
{ "status": 422, "errors": { "name": ["Name darf nicht leer sein."] } }
```

Das Frontend konsumiert ausschließlich `errors` und ordnet jede Meldung ihrem Feld zu (Feld markieren + Helper-Text). Weitere Envelope-Felder (`type`/`title`/`status` aus ProblemDetails) sind erlaubt, aber kein Vertragsbestandteil. Die konkrete ASP.NET-Mechanik (`Results.ValidationProblem(errors, statusCode: 422)` o.ä.) wählt der Implementer unter TDD.

**Begründung:**
1. **Feld-Zuordnung ohne String-Matching:** Ein flaches `string[]` zwingt das Frontend, Meldungen per Textvergleich Feldern zuzuordnen – fragil und an die exakten deutschen Texte (ADR-S051-2) gekoppelt. Feld-Keys lösen das strukturell.
2. **Single Source of Truth bleibt server-seitig:** Reine Display-Information wandert ins Frontend, die Validierungs**logik** und die Texte bleiben einzig im Backend → kein Drift (Mutation Score schützt nachweislich *nicht* gegen Cross-Stack-Drift; nur ein Full-Stack-E2E am Grenzwert oder eine einzige Quelle tut das).
3. **Forward-kompatibel mit OpenAPI:** Feld-keyed ProblemDetails *ist* der RFC-9457-/ASP.NET-Standard; eine spätere OpenAPI-/Codegen-Migration baut darauf auf statt sie zu ersetzen.

**Geltungsbereich Feldnamen:** Keys = Request-JSON-Property-Namen. Collection-/Cross-Field-Fehler (z.B. Recipe `ingredients`/`steps` leer) keyen auf den jeweiligen Feldnamen; ein eventueller globaler Key wird festgelegt, sobald ein solcher Endpoint implementiert wird (derzeit nur Ingredients implementiert).

**Validierung bleibt server-only / Client-Validierung aufgeschoben:** Die Validierungslogik liegt ausschließlich im Backend; das Frontend zeigt die 422-Antwort. Client-seitige Validierungs*logik* (Submit-Blockieren, Instant-Feedback) ist **aufgeschoben aus YAGNI** – *nicht* weil Drift unlösbar wäre, sondern weil sich der Aufwand für den realistischen Bedarf derzeit nicht lohnt. Die maßgebliche Argumentkette (gilt auch für ein künftiges Wiederaufgreifen – diese Abwägung kam schon mehrfach auf, daher hier **front-loaded** festgehalten, damit sie nicht erneut von vorn aufgerollt wird):

1. **Nur Required braucht realistisch Client-Validierung.** maxLength ist abuse-only (valide Nutzer treffen das Limit nie → Instant-„zu lang" wertarm); Range/Regex werden in dieser trivialen Domäne selten falsch eingegeben. Der UX-Gewinn konzentriert sich auf „Pflichtfeld leer".
2. **Drift ist lösbar, nicht unmöglich.** Drift-frei wäre *backend-getriebene* Constraint-Metadaten: ein Constraints-Endpoint, der per Reflection aus den Domänen-Typen ableitet (z.B. Property-Typ `NonEmptyTrimmedString` ⇒ Pflicht-String) → generischer Client-Validator. Setzt voraus, dass Constraints als **reflektierbare Metadaten** am Domänen-Typ liegen (heute teils imperativ → Refactor nötig). OpenAPI-Codegen ist im harten Teil ~äquivalent (DTOs ≠ Domänen-Objekte; die Ableitung ist die eigentliche Arbeit). Native HTML-`required`/`maxLength` ist *nicht* der Weg (siehe Verworfen).
3. **Fokus-aufs-erste-Fehlerfeld bleibt ohnehin custom.** Uniqueness (Duplikat-Name) ist inhärent server-only → 422; Client-Validierung ersetzt das nicht. Die Affordance-/Fokus-Baseline (UX-Guideline Prinzip 8) ist also unabhängig von dieser Frage nötig.
4. **Cross-Stack-Contract-Test schützt nur mit geteilter Fixture**, die beide Stacks konsumieren (zwei separate Asserts pro Stack = wieder Drift); alternativ Pact.

Pflichtfeld-**Markierung** (Affordance, keine Logik) ist davon unberührt und per eigenem Szenario abgedeckt (UX-Guideline Prinzip 8).

**Cross-Stack-Drift-Strategie (konkreter Trigger):** Der 422-Body-Shape ist zwischen BE (`Results.ValidationProblem`) und FE (`FieldErrorBody`) nicht durch eine einzige Quelle abgesichert, sondern **behavioral pro Feld** über Full-Stack-E2E der geübten Fehlerfelder (Shape-Drift bricht das E2E). Das genügt, solange der Body nur **Display-Text** trägt – das FE rendert, verzweigt aber keine Logik auf der Struktur. Eine **einzige Quelle** (OpenAPI-Codegen; bewusst als YAGNI aufgeschoben, weil die Schnittstelle klein und feld-keyed-forward-kompatibel ist) wird eingeführt, **sobald das Frontend den 422-Body über reines Anzeigen hinaus für Logik konsumiert** (auf Body-Struktur/Codes verzweigt statt nur Text zu rendern). Der derzeitige ungeprüfte `as`-Cast in `createIngredient` ist bis dahin kosmetisch.

**Verworfen:**
- **Flaches `string[]`** (ADR-S000-1) – keine Feld-Zuordnung, Frontend müsste auf exakte Texte matchen.
- **Client-seitige Validierungslogik als hand-duplizierte zweite Quelle** (native HTML-`required`/`maxLength` o.ä.) – dupliziert Regeln → Drift-Fläche, und Browser-Default-Meldungen kollidieren mit unseren Texten (ADR-S051-2). Drift-*frei* wäre nur backend-getriebene Constraint-Metadaten (→ Aufschub-Begründung oben, Punkt 2) → als YAGNI aufgeschoben.
- **Shared Validation Schema (Zod/JSON-Schema über beide Seiten)** – scheitert am C#/TS-Sprachbruch (kein gemeinsamer Runtime).

---

### ADR-S051-1: Strings trimmen vor Validierung, getrimmten Wert speichern

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:validation

**Entscheidung:** Alle String-Felder werden im Request-Handler vor der Validierung getrimmt. Gespeichert wird der getrimmte Wert. Ein String der nach Trimming leer ist, verletzt die Nicht-Leer-Constraint.

---

### ADR-S051-2: 422-Fehlermeldungstexte (Deutsch, spezifisch, unveränderlich)

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:validation, http:422

**Entscheidung:** Die deutschen Fehlermeldungstexte sind feste Werte – Änderungen sind Breaking Changes (E2E-Tests schlagen fehl).

| Feld / Kontext | Text |
|----------------|------|
| `name` leer (Ingredient) | `"Name darf nicht leer sein."` |
| `name` zu lang (Ingredient, > 30 Zeichen) | `"Name darf maximal 30 Zeichen lang sein."` |
| `name` bereits vergeben (aktives Duplikat, ADR-S004-1) | `"Eine Zutat mit dem Namen '{name}' existiert bereits."` (`{name}` = getrimmter Request-Wert, nicht der gespeicherte) |
| `baseUnit` leer | `"Einheit darf nicht leer sein."` |
| `baseUnit` zu lang (> 20 Zeichen) | `"Einheit darf maximal 20 Zeichen lang sein."` |
| `title` leer (Recipe) | `"Titel darf nicht leer sein."` |
| `ingredients` leer | `"Rezept muss mindestens eine Zutat haben."` |
| `steps` leer | `"Rezept muss mindestens einen Schritt haben."` |
| `sourceUrl` nicht absolut | `"Quell-URL muss eine absolute URI sein."` |
| `quantity` ≤ 0 | `"Menge muss größer als 0 sein."` |
| `unit` leer bei gesetzter `quantity` | `"Einheit darf nicht leer sein."` |
| `instruction` leer | `"Schritt-Anweisung darf nicht leer sein."` |
| `ingredientId` nicht gefunden/soft-deleted | `"Eine oder mehrere Zutaten wurden nicht gefunden."` |

**Addendum (S111) – Zeile „Restore: bereits aktiv" gestrichen:** Die Tabelle führte für den Restore-Fall „bereits aktiv" den festen Text `"Zutat ist bereits aktiv."`. Die Zeile stammt aus S051, wurde nie implementiert und ist mit ADR-S111-1/-3 überholt – analog zur „plain text"-Klausel in ADR-S004-1, die Addendum S105 ersetzt hat. Zwei Gründe: (1) Der Fall ist kein 422-Feldfehler, sondern ein `409` mit strukturiertem Body, den der Client **logisch verarbeitet** – genau die Konsum-Art, die ADR-S090-1s Display-only-Strategie ausnimmt. (2) Ein fixer Text erklärt dem Nutzer nicht, *warum* seine Eingabe nicht gilt; die Meldung muss den gespeicherten Stand benennen und wird deshalb im Frontend aus dem 409-Body gebildet (Wortlaut in ADR-S111-3). Der Fall tritt zudem nur noch bei **abweichenden** Werten auf – bei identischen Werten gibt es keinen Fehler mehr (ADR-S111-1).

---

### ADR-S112-1: Fehlerantworten sind umgebungsunabhängig – `UseExceptionHandler` wird unbedingt registriert

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:error-handling, http:500, testing:integration

**Kontext/Problem:** ASP.NET registriert die Developer Exception Page automatisch als **erste** Middleware, sobald `ASPNETCORE_ENVIRONMENT=Development` ist (MS-Doku „ASP.NET Core middleware": „The project templates automatically register this middleware as the first middleware in the pipeline when the environment is `Development`"). Ohne eigenen Handler ist der Fehlerpfad damit umgebungsabhängig: Development liefert Stack-Trace und Quellcode-Ausschnitte im Body, jede andere Umgebung einen 500 **ohne** Body (Kestrel). Das ist doppelt unangenehm. (1) Die E2E-Suite läuft als Umgebung `E2E` und übt damit nie den Pfad aus, der in Produktion liefe – umgebungsabhängiges Verhalten ist per Konstruktion nicht E2E-testbar. (2) Ein Deployment mit versehentlich gesetztem `Development` leakt technische Details.

**Entscheidung:** `UseExceptionHandler` wird in `Server/Program.cs` **unbedingt** registriert – ausdrücklich nicht in einem `if (!IsDevelopment())`. Er mappt unbehandelte Exceptions generisch auf RFC-7807-ProblemDetails ohne technische Details und **loggt** den Stack-Trace serverseitig. Im Fehlerpfad existiert damit kein Umgebungs-Zweig mehr.

**Begründung:** Der explizit registrierte Handler liegt **innerhalb** der Developer Exception Page (die als erste Middleware außen sitzt) und fängt die Exception daher zuerst – nach außen propagiert nichts mehr, die Dev-Seite kommt nie zum Zug. Ein Verhalten ohne Umgebungs-Zweig ist in *jeder* Umgebung dasselbe; damit übt E2E denselben Pfad aus wie Produktion, und die Umgebungs-Divergenz **verschwindet, statt getestet werden zu müssen**. Der Stack-Trace geht nicht verloren, er wandert ins Log – so von `docs/process/nfr.md` (Sektion Security) gefordert.

**Verworfen:**
- **Handler nur außerhalb Development** (`if (!IsDevelopment())`) – erhält genau den Umgebungs-Zweig, der das Problem ist, und lässt den Leak-Pfad bestehen.
- **Nur dokumentieren, dass Development nicht deployt wird** – Konvention statt Konstruktion; verlässt sich auf Disziplin.

**Kosten:** Lokal keine Developer Exception Page im Browser; der Stack-Trace steht im Server-Log. Bewusst akzeptiert – einheitliches, testbares Verhalten wiegt schwerer als der Debug-Komfort.

**Grenze / offen:** Das „Log", in das der Stack-Trace wandern soll, **existiert als gestaltete Senke noch nicht**: `appsettings.json` hat keine `Logging`-Sektion, im Backend gibt es keine `ILogger`-Nutzung, und `nfr.md` kennt keine Observability-Anforderung. Vorhanden ist allein der Framework-Default (Console-/Debug-Provider) – flüchtig, unkonfiguriert. Ein Logging-/Observability-Konzept ist Voraussetzung dafür, dass diese Entscheidung ihren Zweck erfüllt, und muss vor der Umsetzung geklärt sein. – Die Reihenfolge-Semantik (expliziter Handler schlägt Developer Page) ist aus der MS-Doku **abgeleitet, nicht empirisch geprüft** – beim Umsetzen mit einem Integrationstest verifizieren. Der Test soll die Zusicherung über **alle** registrierten Umgebungen fahren (`WebApplicationFactory.UseEnvironment(...)`, Umgebungsliste aus ADR-S112-2); er ist dabei kein Vollständigkeitsbeweis, sondern Regressionswächter gegen ein später eingeführtes `if (IsDevelopment())`. Umsetzung ab MVP, weil der tragende Security-NFR ab MVP gilt.

---

## Ingredients-Endpoints

### ADR-S004-1: POST /api/ingredients – 409 bei soft-deleted: strukturiertes Objekt + Client-Orchestrierung

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, http:409, arch:error-handling

**Entscheidung:** `POST /api/ingredients` mit einem Namen, der bereits soft-deleted existiert, gibt `409 Conflict` zurück mit Body `{ "code": "ingredient_soft_deleted", "id": Guid }`. Aktiver Duplikat-Name (nicht soft-deleted) liefert `422 Unprocessable Content` als field-keyed Body auf `name` (ADR-S090-1): `{ "errors": { "name": ["Eine Zutat mit dem Namen '{name}' existiert bereits."] } }`.

Der Client erkennt den Code und ruft automatisch den Restore-Endpoint auf (transparent für den Nutzer).

**`{name}` in Duplikat-Fehlermeldung = Request-Wert (getrimmt):** Der interpolierte Name ist der Wert wie er im Request gesendet wurde (nach Trimming) – nicht der gespeicherte aktive Name. Beispiel: Request sendet `"tomaten"`, gespeicherter Wert ist `"Tomaten"` → Fehlermeldung: `"Eine Zutat mit dem Namen 'tomaten' existiert bereits."` Standard für Validierungsfehler: Fehler referenzieren die Eingabe, nicht den DB-Zustand.

**Begründung:** Das strukturierte Objekt ermöglicht dem Frontend, den `id`-Wert auszulesen und einen "Wiederherstellen"-CTA anzubieten, ohne Text parsen zu müssen.

**Addendum (S105) – Aktiver Duplikat: 422 field-keyed statt plain text (Konflikt-Auflösung mit ADR-S090-1):** Die ursprüngliche „plain text"-Klausel für den *aktiven* Duplikat-Fall stammt aus der Zeit vor dem field-keyed-422-Contract (ADR-S090-1) und wurde nie implementiert. Sie wird ersetzt: aktives Duplikat läuft über denselben field-keyed 422-Pfad wie alle anderen Feld-Validierungsfehler (`name`-Key, dynamische Meldung) → das Frontend rendert die Meldung ohne Sonderbehandlung am Name-Feld (generischer `FieldErrors`-Konsum in `createIngredient`). **Unberührt bleibt** der soft-deleted-Fall: `409 Conflict` + strukturierter `{ code, id }`-Body – dort verzweigt der Client Logik (Restore-Orchestrierung), was ADR-S090-1s Display-only-422 bewusst *nicht* abdeckt (dessen Drift-Strategie nimmt Body-Logik-Konsum explizit aus). Die beiden Duplikat-Zweige liefern damit unterschiedliche Codes (aktiv 422 / soft-deleted 409), gerechtfertigt durch unterschiedliches Client-Verhalten (anzeigen vs. orchestrieren).

**Durchsetzungs-Mechanismus (S105, s. ADR-S105-2):** Die aktive-Duplikat-Prüfung ist ein **DB-Constraint** (funktionaler Unique-Index auf `LOWER(name)`), kein App-Layer-`AnyAsync`-Check. Der POST fängt die `DbUpdateException` (Postgres `23505`) und mappt sie auf dasselbe field-keyed 422. Das eliminiert das TOCTOU-Fenster eines Check-then-Insert. Der 422-*Contract* oben bleibt unverändert – nur der Mechanismus.

**Verworfen:** Transparentes Server-seitiges Reaktivieren – bricht POST-Semantik, zwei Pfade in einem Endpoint.
**Verworfen:** Immer 409 ohne Restore-Möglichkeit – Sackgasse für den Nutzer.
**Verworfen:** Neu anlegen neben soft-deletem Eintrag – erzeugt stille Inkonsistenz (zwei "Butter"-Einträge mit verschiedenen IDs).
**Verworfen (S105):** App-Layer-`AnyAsync`-Check als alleinige Durchsetzung – TOCTOU-Race unter Nebenläufigkeit (zwei parallele POSTs passieren beide die Prüfung → Duplikat), nicht durch einen Test absicherbar. Ersetzt durch den DB-Constraint (ADR-S105-2).

---

### ADR-S105-1: Integrationstest-Provider: EF-InMemory → Testcontainers-Postgres

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:integration-test, tooling:build

**Entscheidung:** Die `Server.Tests`-Integrationstests laufen gegen ein **echtes Postgres in einem Testcontainer** (`Testcontainers.PostgreSql`) statt gegen den EF-Core-InMemory-Provider. Container-Lebenszyklus: ein geteilter Container pro Test-Lauf (xUnit-Collection-/Class-Fixture), Schema via `MigrateAsync` (dieselben Migrations wie E2E/Prod), Daten-Reset pro Test.

**Begründung:** Der InMemory-Provider ist keine relationale DB – er erzwingt **weder Unique-Constraints noch funktionale Indizes** (`LOWER(name)`). Integritätsregeln wie die case-insensitive Namens-Eindeutigkeit (ADR-S105-2) sind dort strukturell nicht testbar; ein DB-Constraint wäre unverifiziert. Testcontainers nutzt die **identische Engine wie Prod** → kein Dialekt-Drift, alle Constraints/Indizes/Collations greifen im Test exakt wie in Produktion. Deckt sich mit der offiziellen EF-Core-Testing-Guidance (InMemory nicht für Verhalten, das relationale Semantik braucht).

**Konsequenz/Trade-off:** Docker-Abhängigkeit für den Test-Lauf; langsamer als InMemory, insbesondere unter Stryker (Test-Suite pro Mutant) – gemildert durch Container-Wiederverwendung + schnellen per-Test-Reset.

**Verworfen:**
- **EF-InMemory beibehalten** – kann den DB-Constraint nicht durchsetzen → die Kernregel dieses Runs bliebe untestbar, der `DbUpdateException`→422-Zweig ein untestbarer Survivor.
- **SQLite in-memory** – schneller/kein Docker, aber anderer Dialekt und **ASCII-only `LOWER()`** (Umlaute wie „Ä"/„ä" folden nicht) → Umlaut-Case-Insensitivität nicht prod-treu.

**Addendum (S105) – DB-Locale muss umlaut-faltend sein (`en_US.utf8`, nicht `C`):** Ob `LOWER('Ö')='ö'` gilt, hängt am **`LC_CTYPE` der DB**, nicht am Postgres-Dialekt oder Encoding an sich (unter `--locale=C` faltet `LOWER()` nur ASCII, auch bei UTF8-Encoding). Der funktionale `LOWER(name)`-Unique-Index (ADR-S105-2) setzt die Umlaut-Case-Insensitivität (ADR-S051-3) also nur unter einem umlaut-faltenden Locale korrekt durch. Empirisch bestätigt: Der Testcontainer (`postgres:15-alpine`) nutzt Default `en_US.utf8` und faltet Umlaute. `docker-compose.yml` erzwang zunächst `--locale=C` (Test≠Prod-Divergenz) → der Override wurde entfernt, damit initdb denselben Default `en_US.utf8` erbt. Guard: Der case-insensitive Duplikat-Test verwendet bewusst „Öl"/„öl" (nicht ASCII) – auf E2E-Ebene der **einzige** Test, der eine regressierte compose-Locale fängt (Server.Tests nutzt immer den Container-Default). Verworfen: `--locale=en_US.utf8` explizit setzen (Risiko, dass ein künftiges Alpine-Image die Locale nicht generieren kann; der Image-Default ist beweisbar vorhanden).

**Addendum (S105) – Trade-off geteilte Collection (Inter-Klassen-Parallelität):** Ein *einziger* geteilter Container für die ganze Assembly (via `[CollectionDefinition]`) bindet alle Testklassen in **eine** xUnit-Collection → sie laufen **seriell**, nicht klassen-parallel. Bewusst akzeptiert (Container-Start dominiert; ein Container pro Klasse wäre teurer). Die Suite ist gegenüber EF-InMemory rund **4,6× langsamer** (gemessen S105) – spürbar, aber nicht kritisch. Skalierungsrisiko v. a. unter Stryker (Suite pro Mutant) → falls die Suite-Dauer kritisch wird, hier ansetzen (mehrere Collections + Container-Pool).

---

### ADR-S105-2: Eindeutigkeit DB-seitig durchsetzen (DB-only), nicht per App-Layer-Check-then-Insert

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:validation, db:constraint

**Entscheidung (allgemeines Prinzip):** Eindeutigkeitsregeln werden per **Unique-Index in der Datenbank** durchgesetzt, nicht per vorgelagertem App-Layer-`AnyAsync`-Check-then-Insert. Der schreibende Endpoint fängt die `DbUpdateException` (Postgres SqlState `23505`) beim `SaveChangesAsync` und mappt sie auf das field-keyed 422 (ADR-S090-1); der Key ist das/die verletzende(n) Request-Feld(er). Funktionale/partielle/case-insensitive Indizes werden als **Raw-SQL in der Migration** angelegt (nicht per Model-Config ausdrückbar; als Migration vom Mutation-Testing ausgenommen).

**Begründung:** Single source of truth = die DB. Ein App-Layer-Check + separater Insert ist ein **TOCTOU-Race** (zwei parallele Requests passieren beide die Prüfung, bevor der jeweils andere committet), das ohne DB-Constraint weder schließbar noch testbar ist. DB-only eliminiert das Race; da **jeder** Verstoß den Constraint auslöst, ist der 422-Pfad durch die regulären Szenario-Tests deterministisch abgedeckt – kein nur-im-Race-erreichbarer Branch, keine Coverage-Suppression. Voraussetzung ist ein constraint-durchsetzender Test-Provider (ADR-S105-1).

**Geltungsbereich & Grenze:** Gilt für den **einfachen „Verstoß ablehnen"-Fall**. Hängt die Antwort von weiterem Zustand ab, inspiziert der App-Layer diesen Zustand bewusst, und der DB-Constraint bleibt der Integritäts-Backstop – Beispiel: ein *soft-deleted* Duplikat liefert `409` + Restore-Orchestrierung, **nicht** 422 (ADR-S004-1/S000-2, run-11); dort fängt der Endpoint die `23505` und verzweigt nach Soft-Delete-Zustand (409 vs. 422). Die **Index-Form** (case-sensitiv/-insensitiv, funktional, partiell z. B. `WHERE deleted_at IS NULL`, mehrspaltig) ist pro Constraint zu wählen; sie ist **nicht** Teil dieses allgemeinen Prinzips.

**Abgrenzung Feld-Validierung vs. Cross-Entity:** Feld-Validierung (leer/zu lang) bleibt im Domain-Typ/Endpoint vor dem Insert (ADR-S090-1, collect-all). Eindeutigkeit ist ein **Cross-Entity-Constraint** und gehört an die einzige Stelle, die ihn atomar garantieren kann – die DB (vgl. `architecture.md`: Cross-Entity-Constraints nicht im Typ ausdrückbar).

**Erste Anwendung – Ingredient-Name (run-6):** funktionaler Unique-Index auf `LOWER(name)` (case-insensitiv, ADR-S051-3) über alle Zeilen; `POST /api/ingredients` mappt `23505` → 422 `name` → „Eine Zutat mit dem Namen '{eingegebener getrimmter Name}' existiert bereits." (ADR-S004-1/-S051-2).

**Verworfen:**
- **App-Layer-`AnyAsync`-Check (allein)** – TOCTOU-Race, s. o.
- **App-Check + DB-Constraint + `DbUpdateException`-Handler** – der Handler-Zweig wäre nur durch einen echten Race auslösbar (App-Check fängt sequentielle Fälle vorher ab) → nicht deterministisch testbar, Coverage-Suppression nötig. DB-only vermeidet das.
- **`citext`-Spaltentyp** – Postgres-Extension, zusätzliche Schema-Abhängigkeit; funktionaler `LOWER()`-Index genügt.

---

### ADR-S051-3: Ingredient-Feldregeln: max. Länge, Case-Insensitivität, kein Auto-Capitalize

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, arch:validation

**Entscheidung:**
- `name`: max. 30 Zeichen (nach Trimming gemessen). Case-insensitiver Duplikat-Check: `"Tomaten"` und `"tomaten"` gelten als dieselbe Zutat. Kein Auto-Capitalize – gespeichert wird exakt der getippte Wert nach Trimming (z.B. `"tomaten"` bleibt `"tomaten"`).
- `baseUnit`: max. 20 Zeichen (nach Trimming gemessen).

**Begründung max. Länge:** Keine realen deutschen Zutaten- oder Einheitenbezeichnungen überschreiten diese Grenzen. Verhindert UI-Überlauf.

**Begründung case-insensitiv:** Zutaten sind fachlich identisch unabhängig von Groß-/Kleinschreibung. Nutzer können Schreibfehler nachträglich korrigieren (Update-Vorgang).

---

### ADR-S051-4: Restore via POST /api/ingredients: übernimmt Name und Einheit aus Request

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, db:soft-delete

**Entscheidung:** Wenn `POST /api/ingredients` eine soft-deleted Zutat trifft und der Client daraufhin `POST /api/ingredients/{id}/restore` aufruft, übernimmt der Restore-Endpoint den `name` und die `baseUnit` aus dem ursprünglichen POST-Request. Die Zutat erscheint anschließend mit dem neuen Namen und der neuen Einheit.

**Parallelfall (Restore antwortet 409 "bereits aktiv"):** Der Client zeigt die Zutat ohne Fehlerhinweis als aktiv an. Name und Einheit der bereits aktiven Zutat sind nicht kontrollierbar (hängen vom parallelen Restore ab) – daher kein Guarantee über die angezeigte Einheit.

**Präzisiert durch ADR-S111-1 (run-11):** Der Parallelfall zerfällt in zwei Fälle. Trägt die parallel wiederhergestellte Zeile **dieselben** Werte, antwortet der Restore `200` und die Einheit ist sehr wohl vorhersagbar. Nur bei **abweichenden** Werten gilt der Absatz oben – dann kommt `409`, und der Client zeigt den Konflikt an, statt ihn zu verschweigen (ADR-S111-3).

---

### ADR-S051-5: DELETE /api/ingredients/{id}: UI-Fehlermeldung bei 404

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:delete, http:404

**Entscheidung:** `DELETE /api/ingredients/{id}` antwortet mit 404 wenn die Zutat nicht existiert oder bereits soft-deleted ist. UI-Fehlermeldungstext: `"Zutat wurde nicht gefunden."`

---

### ADR-S000-2: Check-Reihenfolge POST /api/ingredients: soft-deleted vor active-duplicate

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, arch:validation

**Entscheidung:** Soft-deleted-Check läuft **vor** Active-Duplicate-Check. Dadurch ist es über die API nicht möglich, eine aktive Zutat mit demselben Namen wie eine soft-deleted Zutat anzulegen – der Caller bekommt immer zuerst den 409-Restore-Hinweis.

---

### ADR-S068-1: POST /api/ingredients – 201-Response-Body und Location-Header

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, http:201, http:location-header

**Entscheidung:** `POST /api/ingredients` antwortet bei Erfolg mit `201 Created`, Body `{ "id": Guid, "name": string, "baseUnit": string }` und `Location: /api/ingredients/{id}`.

**Begründung:** Body vermeidet einen zweiten GET-Request im Client. Location ist REST-konform. `baseUnit` statt `unit` für Konsistenz mit dem Domänenmodell.

**Verworfen:** 201 ohne Body – Client müsste sofort GET /api/ingredients aufrufen, um die neue Zutat zu kennen.
**Verworfen:** 200 OK – verletzt REST-Semantik für Ressourcen-Erstellung.

---

### ADR-S000-5: DELETE-Semantik: 404 vs. idempotent 204

**Status:** Accepted
**Tags:** scope:cross-cutting, http:delete, http:404, http:204

**Entscheidung:** Die DELETE-Endpoints verhalten sich unterschiedlich je nach Ressource:

| Endpoint | Verhalten bei nicht-existenter / bereits-gelöschter Ressource |
|----------|---------------------------------------------------------------|
| `DELETE /api/ingredients/{id}` | 404 – auch bei bereits soft-deleted |
| `DELETE /api/recipes/{id}` | 404 – auch bei bereits soft-deleted |
| `DELETE /api/weekly-pool/recipes/{recipeId}` | 204 (idempotent) – auch wenn nicht im Pool |

**Begründung DELETE → 404:** Nicht-idempotent by design. Ein Client der zweimal DELETE aufruft, soll beim zweiten Mal einen Fehler erhalten – verdeckt echte Fehler (z.B. doppelter Aufruf durch Bug).

**Begründung Weekly-Pool → 204:** Der Pool ist ein Set ohne Ownership-Semantik. "Ist nicht drin" und "wurde gerade entfernt" sind äquivalente Zustände. Race-Conditions sollen transparent sein.

**Addendum – Reihenfolge relativ zum If-Match-Check:** Seit `DELETE /api/ingredients/{id}` als erster mutierender Single-Resource-Endpoint auch If-Match prüft (ADR-S058-1), stellt sich die Frage, welcher Check zuerst greift, wenn beide zuschlagen (Ressource nicht (mehr) aktiv UND If-Match fehlt/ist stale). Entscheidung: **Not-Found-Check läuft immer zuerst.** Eine bereits soft-deleted oder nie existente Ressource liefert 404, unabhängig davon ob If-Match fehlt (sonst 428) oder stale ist (sonst 412). Begründung: 404 ist die eindeutigere, für den Client handlungsleitendere Aussage ("es gibt nichts zu aktualisieren") – ein 412 würde fälschlich suggerieren, die Ressource existiere noch und ein Retry mit frischem ETag könnte helfen. Gilt analog für `DELETE /api/recipes/{id}`, sobald dort If-Match eingeführt wird.

**Addendum – gleichzeitiges Doppel-DELETE:** Zwei Clients löschen dieselbe aktive Ressource gleichzeitig, beide mit demselben (zum Zeitpunkt des Sendens gültigen) If-Match. Der erste Request gewinnt (204, Soft-Delete). Der zweite Request findet die Ressource beim Not-Found-Check noch als aktiv vor (Race gegen den ersten Commit) und erreicht den EF-Concurrency-Check – dessen `OriginalValue` ist inzwischen stale → **412**, nicht 404. Das ist optimistic-concurrency-korrekt (kein Re-Read zwischen Not-Found-Check und Save) und self-healing: ein Retry des Verlierers liest die Ressource neu ein und erhält dann korrekt 404 (jetzt soft-deleted).

---

### ADR-S108-1: GET /api/ingredients liefert per-Zeile xmin-ETag im DTO (If-Match-Quelle für DELETE aus der Liste)

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:get, http:etag, db:xmin, arch:caching

**Entscheidung:** `GET /api/ingredients` nimmt in jedes `IngredientDto` ein Feld `etag` auf – der xmin-Wert der Zeile, hex-kodiert im selben Format wie der Single-Resource-ETag (`XminETag.Format`, lowercase `"{xmin:x8}"`, ADR-S106-1). Die GET-Query selektiert xmin je Zeile mit (`EF.Property<uint>(i, "xmin")`). Das Frontend verwendet diesen Wert als `If-Match` beim `DELETE` (und künftig PUT/PATCH) einer aus der Liste geladenen Zutat.

**Begründung:** Der mutierende Single-Resource-`DELETE` verlangt If-Match (ADR-S058-1/-2, 428 ohne). Für eine aus dem Collection-GET geladene Zutat gab es bisher keine ETag-Quelle: der Collection-ETag (Content-Hash im Response-Header, ADR-S058-3/S084-1) identifiziert die *ganze* Liste, nicht die einzelne Zeile, und ein Single-Resource-`GET /{id}` existiert bewusst nicht (ADR-S106-1). Der per-Zeile-ETag im Body schließt die Lücke ohne Extra-Roundtrip.

**Abgrenzung zweier ETag-Mechanismen (koexistieren):** (1) **Collection-Content-Hash-ETag** im *HTTP-Response-Header* (`If-None-Match` → 304, Caching der ganzen Liste) – unverändert von der Middleware gebildet. (2) **Per-Zeile-xmin-ETag** als *Body-Feld* je DTO (`If-Match` → Optimistic Concurrency der einzelnen Zeile). Unterschiedliche Träger (Header vs. Body), unterschiedliche Zwecke – kein Konflikt.

**Geltungsbereich – `IngredientDto` bleibt ein Typ, der POST-201-Body trägt `etag` mit:** `IngredientDto` wird von `GET /api/ingredients` und `POST /api/ingredients` (201) geteilt. Das `etag`-Feld wird dem gemeinsamen Record hinzugefügt; der POST füllt es aus dem xmin, den er für den `ETag`-Response-Header (ADR-S106-1) ohnehin bereits liest. Begründung: (1) der Frontend-Typ `Ingredient` (`services/ingredientsApi.ts`) führt `etag` als *required* und ist Rückgabetyp von `createIngredient` – ein POST ohne `etag` machte den Typ zur Lüge und lieferte beim direkten Weiterverwenden der POST-Antwort ein `If-Match: undefined`; (2) ein zweites, fast identisches Listen-DTO kostet einen Typ plus Mapping ohne Gegenwert. Der Wert ist per Integrationstest abgedeckt (Kategorie-1-Protokolltest nach ADR-S106-3, kein US-Tag) – nicht ungetestet mitgeschleppt.

**Verworfen:** Single-Resource-`GET /{id}` als ETag-Quelle – zusätzlicher Roundtrip vor jedem DELETE; ADR-S106-1 hatte ihn bewusst weggelassen. DELETE ohne If-Match für den Listen-Flow – Verstoß gegen ADR-S058-1. Separates `IngredientListItemDto` nur für den GET – strikteste YAGNI-Lesart, aber Typ+Mapping-Kosten ohne Gegenwert und lässt die Frontend-Typ-Lüge bestehen.

---

### ADR-S108-2: Restore-Endpoint POST /api/ingredients/{id}/restore – minimaler Undo-Restore, ohne If-Match

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, db:soft-delete, http:etag

**Entscheidung:** Der Restore-Endpoint `POST /api/ingredients/{id}/restore` reaktiviert eine soft-deleted Zutat (`DeletedAt = null`). In seiner ersten Fassung – der direkte „Rückgängig"-Undo unmittelbar nach dem eigenen Löschen – arbeitet er **ohne Request-Body** (Name und Einheit der Zeile bleiben unverändert) und **ohne If-Match-Pflicht**. 404, wenn die id nicht existiert.

**If-Match-Ausnahme (bewusste Abweichung von ADR-S058-1):** ADR-S058-1 verlangt If-Match für *alle* mutierenden Single-Resource-Endpoints. Restore ist ausgenommen, weil: (1) Mahl ist eine Single-User-App (ADR-S054-4) – kein reales Concurrency-Fenster; (2) der Undo folgt direkt auf das eigene DELETE, dessen 204-Response keinen neuen ETag liefert – ein If-Match-Zwang würde einen künstlichen ETag-Rücktransport im DELETE-Response erzwingen, ohne Concurrency-Nutzen (YAGNI). Die Ausnahme ist auf diesen Endpoint begrenzt; DELETE/PUT/PATCH behalten If-Match.

**Geltungsbereich:** Nur der minimale id-basierte Restore ohne Body. Werte-Übernahme aus einem Request, die POST-409-Orchestrierung und der „bereits aktiv"-409-Fall (ADR-S004-1/S051-4/S051-2) sind nicht Teil dieser Entscheidung.

**Überholt durch ADR-S111-1 (run-11):** Der Body ist inzwischen Pflicht und der Erfolgs-Status `200` + DTO statt `204`. Unverändert gültig bleiben die If-Match-Ausnahme und der 404-Pfad samt Test-Autorisierung unten.

**404-Pfad ist test-autorisiert, obwohl kein Gherkin-Szenario ihn fordert (Addendum S108):** Der Test `RestoreIngredient_NonExistentId_Returns404WithNotFoundDetail` trägt bewusst keinen US-Tag. Begründung: Der Null-Check im Endpoint ist **strukturell erzwungen**, nicht optional – ohne ihn liefe der Restore auf einer nicht existenten id in eine `NullReferenceException` und damit, mangels globalem Exception-Handler, in einen rohen 500. Der Guard muss also existieren, und die 404-Antwort ist oben in dieser ADR bereits als Kontrakt festgelegt. Der Test deckt genau diesen ADR-festgelegten Kontrakt ab und ist damit ein Protokolltest im Sinne von ADR-S106-3 Kategorie 1. **Abgrenzung:** Das ist *keine* Vorwegnahme der Restore-Fehler-UI (späterer Lauf) – getestet wird ausschließlich die Server-Antwort, nicht die Reaktion des Frontends darauf. Der Erfolgspfad-Test des Restore ist demgegenüber szenario-getrieben und trägt deshalb den `US904_HappyPath_`-Tag.

**Verworfen:** Restore mit If-Match – bräuchte ETag-Rücktransport im DELETE-204 ohne Concurrency-Nutzen (Single-User-App). Undo über den POST-409-Reaktivierungs-Flow – das ist Sache der Reaktivierungs-Funktion; ihn für den Undo vorzubauen zöge sie vor. Undo via Neu-Anlegen (neuer POST, neue id) – erzeugt stille Inkonsistenz (ADR-S004-1 verworfen).

---

### ADR-S108-3: Undo-Toast deckt nur den letzten Löschvorgang ab (kein Snackbar-Stacking)

**Status:** Accepted
**Tags:** scope:feature, story:us-904, frontend:react, arch:error-handling

**Entscheidung:** Der „Rückgängig"-Undo nach dem Löschen einer Zutat hält **genau einen** Löschvorgang vor – den zuletzt ausgeführten. Löscht der Nutzer eine zweite Zutat, bevor er den ersten Undo-Toast genutzt hat, ersetzt der neue Toast den alten; der Undo-Weg für die erste Zutat entfällt ersatzlos. Snackbar-Stacking (mehrere gleichzeitige Undo-Toasts) wird bewusst **nicht** implementiert.

**Begründung:** Der Zustand ist als `DeletedIngredient | null` modelliert (ein Wert, kein Stack) – das hält „Toast offen ohne zugehörige Zutat" strukturell unmöglich. Mehrfach-Undo fordert kein Szenario, und der Aufwand (Map-Modellierung, gestapelte Toasts, Positionierung, eigene Szenarien und Tests) steht in keinem Verhältnis zum Nutzen: Der Sonderfall verlangt zwei Löschungen innerhalb der 6-Sekunden-Toast-Dauer.

**Bekannte Konsequenz (bewusst getragen):** Für die überschriebene Zutat existiert derzeit **kein** UI-Weg zurück – es gibt keinen Papierkorb und keine Liste gelöschter Zutaten. Die Zeile ist nur soft-deleted (`DeletedAt`, ADR-S000-6), also nicht verloren, aber bis zur Reaktivierungs-Funktion (run-11: erneutes Anlegen unter gleichem Namen reaktiviert die Zeile) nur über die API erreichbar. Das ist eine Abweichung vom Wortlaut der UX-Guideline Prinzip 5 Stufe 1 („Soft-Delete + Wiederherstellungsmöglichkeit im UI") für diesen Sonderfall – hier dokumentiert statt stillschweigend in Kauf genommen. Quelle: functional-correctness-auditor, Review run-8.

**Verworfen:** Snackbar-Stacking via Map (id → DeletedIngredient) – korrekt, aber ein eigener Entwurfsschritt weit über den Lauf hinaus. Undo-Weg über einen Papierkorb-Screen – neue Fläche ohne Story. Zweites Löschen sperren, solange ein Undo offen ist – bestraft den Normalfall für einen Randfall.

---

### ADR-S111-1: Restore-Contract mit Pflicht-Body – idempotent bei gleichen Werten, 409 bei abweichenden

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, http:409, db:soft-delete, arch:validation

**Entscheidung:** `POST /api/ingredients/{id}/restore` verlangt ab run-11 einen **Pflicht-Body** `{ name, baseUnit }` und antwortet:

| Zustand der Zeile | Antwort |
|---|---|
| soft-deleted | `200` + `IngredientDto` – `DeletedAt = null`, Name und Einheit aus dem Request übernommen (ADR-S051-4) |
| aktiv, Werte **exakt identisch** zum Request | `200` + `IngredientDto` – kein Schreibvorgang nötig, der Zielzustand ist bereits erreicht |
| aktiv, Werte **abweichend** | `409` + `{ "code": "ingredient_already_active", "ingredient": { id, name, baseUnit, etag } }` – der aktuelle Stand geht mit, damit der Client ihn benennen kann (ADR-S111-3) |
| id existiert nicht | `404` (unverändert, ADR-S108-2) |

Der Body durchläuft **dieselbe Validierung wie der POST** (`ToDomain()`, field-keyed 422 nach ADR-S090-1/S051-2/S051-3). Ohne sie ließe sich über den Restore ein leerer oder zu langer Name persistieren, den der POST verbietet – die Invariante aus ADR-S051-3 gälte dann nur für einen der beiden Schreibpfade. Der Validierungs-Zweig ist damit **strukturell erzwungen** und trägt einen Protokolltest nach ADR-S106-3 Kategorie 1 (kein US-Tag), analog zur 404-Autorisierung in ADR-S108-2.

**Prüfreihenfolge im Restore: Body-Validierung (422) vor Ressourcen-Auflösung (404).** Ein kaputter Body wird beantwortet, bevor die id nachgeschlagen wird – die übliche Reihenfolge; liefe die Validierung per Filter/Attribut, käme sie ohnehin zuerst. Das ist **kein** Widerspruch zu ADR-S000-5s Addendum „Not-Found dominiert": Dort ging es um Not-Found vs. **Precondition** (If-Match), und die Begründung war, dass ein `412` fälschlich suggeriert, die Ressource existiere noch und ein Retry mit frischem ETag könne helfen. Ein `422` erhebt diese Suggestion nicht – es redet über den Request-Body, nicht über den Zustand der Ressource. Die Dominanz-Regel gilt also weiterhin gegenüber Preconditions, nicht gegenüber Body-Validierung.

**Gleichheit ist exakt-ordinal auf beiden Feldern.** Auch eine abweichende Schreibweise (`"mehl"` vs. `"Mehl"`) ist ein Konflikt, obwohl der Duplikat-Check case-insensitiv arbeitet (ADR-S051-3). Begründung: Die Case-Insensitivität beantwortet die Frage „ist das dieselbe Zutat?", hier steht aber die andere Frage im Raum – „verändere ich einen Wert, den jemand anders gesetzt hat?". Auf die antwortet nur ein zeichengenauer Vergleich. Eine Ausnahme für Schreibweisen wäre ein Sonderfall ohne scharfe Grenze.

**Warum idempotent statt durchgängig 409 (Abgrenzung zu ADR-S051-4):** Der Endpoint hat kein If-Match (ADR-S108-2), Lost Update ist also nicht generell ausgeschlossen. Ein 409 allein für „Zeile ist bereits aktiv" finge nur einen von mehreren Überschreib-Wegen ab und suggerierte einen Schutz, den der Endpoint konstruktiv nicht bietet. Entscheidend ist nicht der Zustand, sondern ob der Request fremde **Werte** verändert – deshalb löst der Wertevergleich aus, nicht die Zustandsprüfung. Sind die Werte gleich, gibt es nichts zu schützen: der Client wollte genau diesen Zustand und bekommt ihn.

**Addendum zu ADR-S051-4 (Parallelfall präzisiert):** Dort hieß es, im Parallelfall antworte der Restore mit 409 und Name/Einheit der aktiven Zutat seien „nicht kontrollierbar". Das gilt ab hier nur noch für den Fall **abweichender** Werte. Bei identischen Werten ist die Einheit sehr wohl vorhersagbar – das treibende Szenario („Reaktivierung gelingt auch wenn Zutat parallel mit denselben Daten wiederhergestellt wurde") assertiert sie deshalb.

**Addendum zu ADR-S108-2 (Body und Erfolgs-Status revidiert):** Der bodylose Restore mit `204` entfällt. Der Undo-Pfad (run-8/9) schickt die unveränderten Werte der gelöschten Zutat mit – für ihn ein No-op, der aber einen einzigen Codepfad im Endpoint erhält. `DeletedIngredient` trägt dafür zusätzlich `baseUnit`. Unverändert gültig bleiben aus ADR-S108-2: die If-Match-Ausnahme und der 404-Pfad samt Test-Autorisierung.

**Addendum (run-11-Nachbesserung) – zwei Fehlerzweige des Schreibpfads ergänzt.** Mit diesem ADR wurde der Restore vom bloßen `DeletedAt`-Clear zu einem allgemeinen Schreib-Endpoint und braucht damit dieselbe Exception-Behandlung wie jeder andere Schreibpfad – das Projekt hat keinen globalen Exception-Handler, jeder Schreibpfad behandelt seine DB-Fehler selbst. Zwei Fälle schlugen sonst als roher `500` durch:

- **Zwei überlappende Restores derselben soft-deleted Zeile → `200` oder `409`, nie `500`.** `xmin` ist in `Infrastructure/MahlDbContext.cs` auf **Entity**-Ebene als Concurrency-Token konfiguriert – EF hängt es an *jedes* UPDATE, nicht nur an das des DELETE mit If-Match. Lesen beide Requests die Zeile, bevor der erste committed hat, fliegt der Verlierer mit `DbUpdateConcurrencyException`. Fachlich ist das genau der Fall „aktiv, als der Schreibvorgang ankam": Die Zeile wird neu geladen und die Antwort an dieselbe Wertevergleich-Logik delegiert wie bei einer von vornherein aktiven Zeile, statt sie zu duplizieren. Nur so bekommt der häufigste reale Auslöser – Doppelklick auf „Rückgängig", also identische Werte – korrekt `200` statt eines fälschlichen Konflikts. Das Race-Fenster ist dabei enger, als „Doppelklick" nahelegt: Ist der erste Restore schon committed, wenn der zweite liest, läuft der zweite ohne Exception durch den Aktiv-Zweig.
- **Request-Name kollidiert mit einer *anderen* Zeile → `422` `name_duplicate`.** Der Restore schreibt auf die eindeutigkeitsbeschränkte Name-Spalte (ADR-S105-2/S051-3); ein Name, der eine andere Zeile trifft, verletzt `IX_Ingredients_Name_Lower` genauso wie beim POST und wird deshalb auf denselben field-keyed 422 abgebildet (ADR-S090-1). Über die aktuelle UI nicht erreichbar – der Client sendet nur LOWER-gleiche Namen –, über die API sehr wohl.

**Kein Test für den Concurrency-Zweig, stattdessen begründete Stryker-Suppression (ADR-S041-9).** Beim DELETE lässt sich ein stale `xmin` von außen über den If-Match-Header injizieren; der Restore nimmt kein If-Match (s. o.), lesendes SELECT und schreibendes UPDATE liegen beide innerhalb **desselben** Requests, ohne Injektionspunkt dazwischen. Ein echter `Task.WhenAll`-Race wäre interleaving-abhängig und damit flaky – ein flaky Test ist schlechter als eine ehrliche, begründete Suppression. Der Index-Kollisions-Zweig ist dagegen direkt testbar und trägt einen Protokolltest nach ADR-S106-3 Kategorie 1. Quelle: functional-correctness-auditor, Review run-11.

**Verworfen:** Optionaler Body (bodylos → 204 für den Undo, mit Body → 200 für die Reaktivierung) – ließe run-8/9 unberührt, kostet aber zwei Erfolgs-Statuscodes und zwei dauerhaft zu testende Zweige an einem Endpoint, dessen zweiter Pfad nur historisch existiert. Durchgängiges 409 bei aktiver Zeile (Wortlaut ADR-S051-4) – dritter Antwort-Zweig, und `createIngredient` könnte im 409-Fall kein `Ingredient` liefern, was den Rückgabetyp zur Lüge machte (dasselbe Argument wie in ADR-S108-1). Idempotenz **ohne** Wertevergleich (immer 200, letzter Schreiber gewinnt) – überschreibt fremde Werte ohne jeden Hinweis.

---

### ADR-S111-2: POST-Konflikt-Verzweigung via Lookup **nach** der Unique-Violation

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, http:409, arch:validation, db:constraint

**Entscheidung:** `POST /api/ingredients` unterscheidet die beiden Duplikat-Fälle (aktiv → 422, soft-deleted → 409 `{ code, id }`, ADR-S004-1/S000-2) anhand eines Lookups, der **erst nach** der abgelehnten Insert-Operation läuft: Die `DbUpdateException` (Postgres `23505` auf `IX_Ingredients_Name_Lower`) wird wie bisher gefangen, das nicht persistierte Entity aus dem ChangeTracker gelöst, dann die konfligierende Zeile über `LOWER(name)` gelesen. `DeletedAt != null` → 409, sonst → 422.

**Begründung:** ADR-S105-2 verwirft einen App-Layer-Check *als Durchsetzungsmechanismus* der Eindeutigkeit (TOCTOU). Dieser Lookup setzt nichts durch – die Eindeutigkeit hat die DB bereits durchgesetzt, der Insert ist abgelehnt. Er entscheidet nur noch, **welche** Fehlerantwort der Client bekommt, und liegt damit außerhalb der von ADR-S105-2 adressierten Race. Der Index umfasst bewusst auch soft-deleted Zeilen (ADR-S000-2), weshalb genau diese Verzweigung nötig ist.

**Bekannte Race (bewusst getragen):** Ändert sich der Zustand der Zeile zwischen Violation und Lookup, bekommt der Client die jeweils andere der beiden Antworten. Beide Zweige sind für ihn behandelbar (422 zeigt die Meldung, 409 startet die Reaktivierung), der Ausgang ist also in beiden Richtungen definiert.

**Findet der Lookup keine Zeile,** obwohl die DB gerade eine Unique-Violation gemeldet hat, ist das strukturell unerreichbar (es gibt keinen Hard-Delete). Der Guard fällt auf die 422-Duplikat-Antwort zurück und trägt eine begründete Stryker-Suppression – ein Test dafür ließe sich nicht schreiben.

**Verworfen:** Vorab-Prüfung „existiert der Name (auch soft-deleted)?" vor dem Insert – genau das Check-then-Insert-Muster, das ADR-S105-2 aus TOCTOU-Gründen verwirft. Partieller Unique-Index nur auf aktive Zeilen (`WHERE DeletedAt IS NULL`) – erlaubte zwei Zeilen gleichen Namens nebeneinander und bricht ADR-S000-2.

---

### ADR-S111-3: Reaktivierungs-Konflikt im UI – Dialog schließt, Snackbar nennt den gespeicherten Stand

**Status:** Accepted
**Tags:** scope:feature, story:us-904, resource:ingredients, frontend:react, arch:error-handling

**Entscheidung:** Antwortet der Restore mit `409 ingredient_already_active` (ADR-S111-1), **schließt der Anlege-Dialog** wie im Erfolgsfall, die Liste wird neu geladen, und der Nutzer bekommt eine Snackbar mit dem Text:

> `'{eingegebener Name}' wurde zwischenzeitlich an anderer Stelle wiederhergestellt (z. B. auf einem anderen Gerät). Gespeichert ist '{aktueller Name}' mit der Einheit '{aktuelle Einheit}'.`

Die Werte für den zweiten Satz stammen aus dem `ingredient`-Objekt des 409-Bodys; der Text wird im Frontend gebildet (wie bei allen 409-Antworten, die der Client logisch verarbeitet – ADR-S004-1/S090-1). Der eingegebene Name geht **getrimmt** in den Text – jede andere nutzersichtbare Wiedergabe einer Eingabe ist es auch (ADR-S051-1/S051-2), und ein Wert mit unsichtbaren Leerzeichen in Anführungszeichen arbeitet gegen den Zweck der Meldung.

**Der Text nennt bewusst nur den gespeicherten Stand, nicht die eigene Eingabe.** Naheliegend wäre, die Differenz auszuformulieren („…, nicht '{eigene Einheit}'"). Das scheitert an der Generik: Der Konflikt kann ebenso im **Namen** liegen (abweichende Schreibweise bei gleicher Einheit) – dann stünde dort „Einheit 'g', nicht 'g'". Der Nutzer sieht seine eigene Eingabe ohnehin gerade noch im Dialog; was ihm fehlt, ist der fremde Stand.

**Auto-Hide 10000 ms – bewusst länger als der Undo-Toast (6000 ms).** Die ursprüngliche Festlegung „identisch zum Undo-Toast" war ein Konsistenz-Default ohne Blick auf die Textlänge: Diese Meldung ist rund zehnmal so lang wie „X gelöscht", besteht aus zwei Sätzen und führt ein Konzept ein (parallele Reaktivierung), das im UI sonst nirgends vorkommt. MUIs Pause-bei-Hover greift auf dem priorisierten Touch-Gerät nicht. Die Dauern der beiden Toasts sind damit **absichtlich verschieden** – sie gehören nicht in eine gemeinsame Konstante. Quelle: ux-ui-auditor, Review run-11.

**Begründung Dialog schließt:** Der Vorgang ist abgeschlossen – die Zutat existiert danach, nur mit fremden Werten. Im Dialog gäbe es nichts zu korrigieren: erneutes Speichern liefe in den 422-Duplikat-Fehler, weil die Zeile jetzt aktiv ist. Ein offen bleibender Dialog mit Fehlermeldung (das Muster der Feld-Validierung) suggerierte eine Korrekturmöglichkeit, die es nicht gibt. Die Meldung nennt beide Seiten – die eigene Eingabe und den gespeicherten Stand – damit der Nutzer die Differenz selbst sieht, statt nur zu erfahren, dass „etwas schiefging".

**Bekannte Konsequenz (bewusst getragen):** Löscht der Nutzer erst eine Zutat (Undo-Toast steht) und läuft unmittelbar danach in diesen Konflikt, sind zwei Snackbars gleichzeitig sichtbar. Kein Stacking-Konzept – dieselbe Abwägung wie in ADR-S108-3, verschärft weder Datenlage noch Bedienbarkeit.

**Ein erfolgreiches Anlegen verwirft den Undo-Zustand (Addendum run-11-Nachbesserung).** Der `onSuccess` des Anlege-Vorgangs ruft `dismissUndo()`. Grund: Vor run-11 konnte eine soft-deleted Zeile ausschließlich durch den Undo selbst wieder aktiv werden – der Toast konnte gar nicht veralten. Die Reaktivierung ist ein **zweiter** Weg zurück und macht die Aussage „X gelöscht" samt „Rückgängig"-Button falsch, sobald sie greift: Der Toast behauptete einen Zustand, den es nicht mehr gibt (UX-Guideline Prinzip 1), und ein Klick darauf liefe in den `409`-Zweig, den der Client als Erfolg wertet – die Aktion verpuffte ohne Wirkung und ohne Rückmeldung (Prinzip 3). Bemerkenswert: Der Wertevergleich aus ADR-S111-1 verhindert dabei bereits das Schlimmere – ohne ihn würde der veraltete Undo die soeben eingegebene Einheit still durch die alte ersetzen, ein Lost Update auf den eigenen Daten des Nutzers. Quelle: functional-correctness-auditor, Review run-11.

**Verworfen:** Fehlermeldung im geöffneten Dialog (Muster der 422-Feldfehler) – suggeriert eine nicht existierende Korrekturmöglichkeit. Stiller Erfolg ohne Hinweis – der Nutzer glaubte sonst, seine Einheit sei gespeichert. Meldungstext vom Server – der 409 ist eine vom Client logisch verarbeitete Antwort, sein Body trägt Daten, keine Anzeige-Texte (Abgrenzung zu den fixen 422-Texten aus ADR-S051-2).

---

## Recipes-Endpoints

### ADR-S027-1: StepNumber: serverside vergeben, nicht im DTO

**Status:** Accepted
**Tags:** scope:feature, resource:recipes, arch:domain-type

**Entscheidung:** `StepNumber` wird vom Server als `(Index + 1)` der eingehenden Steps-Liste vergeben (1-basiert). Es erscheint ausschließlich in der DB-Entität (`Step.StepNumber`) und zur Sortierung. Es ist **nicht** Teil des Domain-Objekts und **nicht** Teil des `StepDto` – das DTO enthält nur `instruction`.

**Begründung:** Clients senden eine geordnete Liste – die Listenposition ist die Reihenfolge. Eine separate `stepNumber`-Angabe wäre redundant und fehleranfällig (Inkonsistenz zwischen Listenposition und Wert möglich).

---

### ADR-S020-1: Quantity: `Quantity`-Sum-Type, NULL = "nach Geschmack"

**Status:** Accepted
**Tags:** scope:feature, resource:recipes, arch:sum-type, arch:domain-type, db:ef-core

**Entscheidung:** `RecipeIngredient.Quantity` ist ein `Quantity`-Sum-Type mit zwei Varianten: `PositiveDecimal` und `Unspecified`. `Unspecified` bedeutet "nach Geschmack" / Menge nicht angegeben. 0 ist kein gültiger Wert. `Unit` ist ebenfalls `Unspecified` wenn `Quantity` `Unspecified` ist, ansonsten NOT NULL.

In der DB: `decimal(7,3)?`, NULL = `Unspecified`. `decimal?` als **Parameter** von `Create()` bleibt erlaubt (Systemgrenze zu DTO/Primitives).

Generierungslogik: `Unspecified` = 0 bei Aggregation; wenn alle `Unspecified` → Ergebnis `Unspecified`.

**Verworfen:** `Quantity = 0` als Sentinel – 0 ist ein valider Eingabefehler, kein fachlicher Zustand.
**Verworfen:** `decimal?` als Domain-Property-Typ – verletzt "Make Illegal States Unrepresentable".

---

### ADR-S012-1: RecipeSource: Mutual Exclusion zwischen URL und Bild

**Status:** Accepted
**Tags:** scope:feature, resource:recipes, arch:domain-type, arch:validation

**Entscheidung:** Ein Rezept kann entweder eine `SourceUrl` (externe URL) oder ein Quellbild (`HasSourceImage = true`) haben, nie beides. In Request und Response sind `sourceUrl` und `sourceImageBase64`/`sourceImageUrl` gegenseitig exklusiv.

---

### ADR-S039-1: `System.Uri` als BCL-Primitive in `Create()`-Parametern

**Status:** Accepted
**Tags:** scope:feature, resource:recipes, arch:domain-type, arch:validation

**Entscheidung:** `System.Uri` wird direkt als Parameter in `Recipe.Create(Uri? sourceUrl)` akzeptiert. `new Uri("")` wirft `UriFormatException`, `new Uri(null)` wirft `ArgumentNullException` – ein leeres/null Uri-Objekt ist nicht konstruierbar. Fachliche Invarianten (Absolutheit) werden per Guard in `Create()` geprüft.

**Verworfen:** `NonEmptyUri` als eigener Typ – unnötig, da `Uri` die strukturelle Garantie bereits mitbringt.

---

### ADR-S039-2: STJ serialisiert `Uri` via `OriginalString` – Round-Trip ohne Normalisierung

**Status:** Accepted
**Tags:** scope:feature, resource:recipes, db:ef-core

**Entscheidung:** `url.OriginalString` in `explicit operator string?` für das DB-Mapping. STJ nutzt intern ebenfalls `OriginalString` zur Serialisierung. Round-Trip konsistent: POST-Body `"https://example.com"` → DB → GET-Response `"https://example.com"`.

**Verworfen:** `url.AbsoluteUri` – normalisiert beim Speichern (`"https://example.com"` → `"https://example.com/"`), Originalstring des Clients geht verloren.

---

### ADR-S039-3: `GET /api/recipes`: 500 bei korrupter DB-URL (kein silent null)

**Status:** Accepted
**Tags:** scope:feature, resource:recipes, http:get, arch:error-handling

**Entscheidung:** `GetAll` und `GetById` liefern `500` + `application/problem+json` wenn eine `SourceUrl` in der DB korrupt ist (`ToSummaryDtoOrError()` + `Sequence()`). `null` hat keinen validen semantischen Wert – "korrupte Daten ignorieren" wurde abgelehnt.

---

## WeeklyPool-Endpoints

### ADR-S007-1: POST /api/weekly-pool: 422 (nicht 404) bei Rezept nicht gefunden

**Status:** Accepted
**Tags:** scope:feature, resource:weekly-pool, http:post, http:422, arch:validation

**Entscheidung:** `POST /api/weekly-pool/recipes/{recipeId}` antwortet mit `422`, wenn das Rezept nicht existiert oder soft-deleted ist – nicht mit `404`. Der Request ist semantisch ungültig (ungültige `recipeId`), nicht "Ressource nicht gefunden". Konsistent mit Collect-all-Validation-Konvention für referenzielle Integrität.

---

### ADR-S008-1: WeeklyPool: Keine Duplikate (409 bei bereits enthaltenem Rezept)

**Status:** Accepted
**Tags:** scope:feature, resource:weekly-pool, http:post, http:409

**Entscheidung:** `POST /api/weekly-pool/recipes/{recipeId}` mit einem Rezept das bereits im Pool ist → `409 Conflict`.

**Begründung:** Im Familienkontext ist ein doppeltes Rezept in der Wochenplanung wahrscheinlicher ein Versehen als Absicht. Bewusste Einschränkung, kein fachliches Gesetz.

---

## Datenbank & Persistenz

### ADR-S030-1: UUIDv7 für alle Primärschlüssel (serverside generiert)

**Status:** Accepted
**Tags:** scope:cross-cutting, db:uuid, db:ef-core

**Entscheidung:** Alle PKs sind `Guid` (UUIDv7, serverside generiert via `Guid.CreateVersion7()`). Keine client-seitigen IDs, keine `int`-Autoincrement-Schlüssel.

**Begründung:** Zeitlich sortierbar (monoton steigend), kein DB-Sequenz-Contention, ID-Generierung ohne DB-Roundtrip.

**Verworfen:** UUIDv4 – nicht sortierbar (Index-Fragmentierung). `int` – vorhersagbar (Security), Migrations-schwierig.

---

### ADR-S000-6: Soft-Delete: `DeletedAt` (timestamptz?) statt `IsDeleted` (bool)

**Status:** Accepted
**Tags:** scope:cross-cutting, db:soft-delete

**Entscheidung:** Soft-Delete wird via `DeletedAt`-Timestamp implementiert, nicht via `IsDeleted`-Bool.

**Begründung:** Enthält mehr Information (wann gelöscht?), ermöglicht Audit-Queries und automatisches Aufräumen.

---

## Domain-Typen & Sum-Types

### ADR-S018-1: Sum-Type-Design: private Subtypen, `Match<T>` als einzige Schnittstelle

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:sum-type, arch:domain-type

**Entscheidung:** Zwei erlaubte Varianten:

- **Variante A – verschachtelte `private` Subtypen:** Stärkste Kapselung. `private SumType() { }` verhindert jede externe Ableitung. Standard für Wert-Träger-Sum-Types (reine Zustandscontainer).
- **Variante B – `file`-scoped Subtypen + `private protected` Konstruktor:** Wenn alle Operationen als Extension Methods in derselben Datei geführt werden sollen. `private protected` statt `private`, weil top-level `file`-Records keinen privaten Basiskonstruktor aufrufen können.

`Match<T>` ist immer die **einzige** öffentliche Schnittstelle für Consumer. **public** für Wert-Träger-Sum-Types (Mapping-Layer braucht Zugriff), **internal** für operationale Sum-Types.

Konvertierungsoperatoren: `implicit` wenn verlustfrei und reversibel, `explicit` wenn Information verloren geht.

**Verworfen:** Öffentliche Subtypen – keine Exhaustiveness-Garantie, externe Subtypen möglich.
**Verworfen:** `internal` Subtypen – gesamtes Assembly kann subtypen, keine strukturelle Garantie.

---

### ADR-S040-1: Switch + `SumType.Unreachable<T>()` als einziges erlaubtes Dispatch-Pattern

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:sum-type, testing:stryker

**Entscheidung:**
1. `Match<T>` nutzt immer `switch` mit `_ => SumType.Unreachable<T>()`. Der Helper `SumType.Unreachable<T>()` liegt in `Server/Types/SumType.cs` – Stryker-Suppress einmal dort, nicht in jeder Implementierung.
2. Kein Ternary (`this is X u ? ... : ...`) – bei einer neuen Variante die in `Match<T>` vergessen wird, ruft Ternary still den falschen Arm auf; Switch wirft klar.
3. `[ExcludeFromCodeCoverage]` auf `Match<T>` (strukturell unerreichbarer `_`-Arm).
4. **S3060 pro Sum-Type-Datei unterdrücken (S091):** SonarAnalyzer S3060 feuert auf den `this switch`-Typ-Test in `Match<T>` (will polymorphen Dispatch, der hier nach Punkt 2 bewusst verworfen ist). Pro Sum-Type-Datei einen `[<pfad>]`-Block mit `dotnet_diagnostic.S3060.severity = none` in `.editorconfig` (Muster S091, analog zu S1118/MA0048). **Nicht** projektweit – S3060 hat außerhalb von Sum-Types legitime Treffer (Typ-Test-Verzweigung, die Polymorphie sein sollte).

**Verworfen:** Ternary – besser für Coverage, schlechter für Korrektheit bei Erweiterungen.
**Verworfen (S091):** Polymorpher Dispatch (abstrakte `Match<T>` je Subtyp, was S3060 will) – S3060-konform und suppression-frei, aber das Hinzufügen einer Variante ändert die `Match<T>`-Signatur und zwingt damit Edits in **jedem** bestehenden Subtyp-Override (O(N)); der zentrale Switch ist O(1) je neuer Variante. Der einmalige Setup-Preis (S3060-Suppression + `SumType.cs`) wiegt leichter als die wiederkehrende O(N)-Steuer.
**Verworfen:** Switch ohne `_`-Arm – Coverlet trackt die compiler-generierte `throw new SwitchExpressionException()`-Branch auf IL-Ebene, Branch Coverage fällt auf ~98%. Kein Gewinn gegenüber dem expliziten `_`-Arm.

---

### ADR-S018-2: Äquivalenter Mutant: `"Unreachable."` String in Sum-Type Match

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:sum-type, testing:stryker

**Entscheidung:** Der `_ => throw new InvalidOperationException("Unreachable.")` Zweig in Sum-Type `Match`-Methoden ist strukturell nie erreichbar. Stryker-String-Mutation auf diesem String ist ein äquivalenter Mutant. Exclusion per `// Stryker disable once StringMutation` direkt über der Zeile.

**Gilt für:** Alle `_ => throw new InvalidOperationException("Unreachable.")` Zeilen in Sum-Type `Match`-Implementierungen (`RecipeSource.cs`, `Quantity.cs`, und zukünftige Sum-Types).

---

### ADR-S035-1: S4581: `== default` statt `== Guid.Empty` für uninitialisierten Guid-Guard

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:domain-type, tooling:analyzer

**Entscheidung:** In Domain-Typen mit `readonly record struct` + `Guid`-Backing-Feld bleibt `_id == default` erlaubt und wird per `#pragma warning disable S4581` suppressiert. `default` signalisiert "strukturell uninitialisiert" – semantisch identisch mit `== Guid.Empty`, aber sprachlich präziser.

**Einschränkung:** Diese Suppression ist **nur** für uninitialisierten Value-Type-Guard erlaubt. S4581 an anderen Stellen muss evaluiert werden – dort kann es auf einen echten Bug hinweisen.

---

### ADR-S119-1: Parametrisierte Einschränkungen stehen im Constraint-Typ – Marker-Typ je Grenzwert

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:domain-type, arch:validation

**Entscheidung:** Eine parametrisierte Einschränkung (`max. N Zeichen` und Analoges) wird **Teil des Typs**, nicht eine Prüfung in der `Create()` des Domänentyps. Der Domänentyp trägt sie als Typ seines privaten Feldes:

```csharp
private readonly Bounded<NonEmptyTrimmedString, Max30> _value;
```

Bausteine in `Server/Types/`: `IStringConstraint<TSelf>` (CRTP mit `static abstract Create`), `IMaxLength` als Marker-Interface, die Träger `NonEmptyTrimmedString` und `Bounded<TInner, TMax>` und ein Marker-Typ **je Grenzwert** (`Max30`, `Max20`). Die Träger melden `StringViolation` (`Empty`, `TooLong`); der Domänentyp faltet das in seine Fehlerfälle auf (ADR-S051-2 bleibt unberührt; die Fälle gehören zum Konzept, nicht zum Feld – ADR-S120-1). Ausformulierter Code: `docs/history/sessions/session_119.md`, Abschnitt „Volltext zur Constraint-Parametrisierung", Variante A – dort noch mit der ursprünglich vorgesehenen Träger-Trennung, siehe nächster Absatz.

**Warum `NonEmptyTrimmedString` statt `NonEmpty<TrimmedString>` (S120):** Ursprünglich waren zwei orthogonale Träger vorgesehen – `TrimmedString` normalisiert, `NonEmpty<TInner>` prädiziert. Beim Umbau zeigte sich, dass diese Trennung einen **nicht killbaren Mutanten** erzeugt: Ein rein normalisierender Träger muss im JSON-`null`-Fall einen *Wert* liefern (`""`), und `""` aus `null` ist von `""` aus `""` nicht unterscheidbar – jeder Mutant, der die Null-Behandlung entfernt, wirkt sich nur bei `{"feld": null}` aus, wofür kein Szenario existiert. Im ungetrennten Träger fällt die Leer-Entscheidung dagegen im selben Schritt und kann einen **Fehler** zurückgeben, dessen Entfernung über HTTP sofort beobachtbar ist. Eine Suppression schied aus: Der Zweig ist erreichbar, das ist eine Testlücke und keine Unerreichbarkeit (ADR-S041-9 greift nicht).

Der Ertrag dieser Entscheidung bleibt davon unberührt – die Grenze steht weiterhin als Typ des privaten Feldes und ist nicht vergessbar. Betroffen ist nur die Träger-**Liste**.

**Erweiterungspfad:** Die Trennung wird nötig, sobald ein Feld **getrimmt werden muss, aber leer sein darf** (z.B. eine optionale Beschreibung). `NonEmptyTrimmedString` kann das nicht ausdrücken. Dann kommt `TrimmedString` hinzu und das betroffene Feld wird `Bounded<TrimmedString, MaxN>`; bestehende Felder können auf `Bounded<NonEmpty<TrimmedString>, MaxN>` nachziehen, sobald ein `null`-Szenario den Mutanten oben killbar macht. Der Schritt ist additiv, kein Umbau – die heutige Form ist deshalb vollständig für die heutigen Felder und nicht ein Zwischenstand (KISS: ein getrimmt-aber-leer-erlaubtes Feld existiert nicht).

Erneut geprüft und verworfen: das Prädikat im **Rohwert** von `NonEmpty<TInner>` messen (`IsNullOrWhiteSpace(input)` statt `inner.Value.Length == 0`) – killbar, koppelt den Träger aber verdeckt an „mein innerer Träger trimmt" und wäre mit einem anderen inneren Träger schlicht falsch, ohne dass der Compiler es merkt.

**Begründung:** Der Grenzwert ist damit nicht vergessbar – der Feldtyp deklariert ihn, und ein neuer Domänentyp kann ihn nicht stillschweigend auslassen. Das ist ein Mechanismus statt Lese-Disziplin (`docs/kaizen/principles.md`). Die Alternative sichert die Grenze nur über das je begrenztem Feld ohnehin geforderte „zu lang"-Szenario ab – bei einem **neuen** Domänentyp existiert dieses Szenario aber noch nicht, wenn die Zeile vergessen wird.

**Warum ein Marker-Typ je Grenzwert:** C# kennt keine const generics (`dotnet/csharplang#7508` ist seit 2023 Draft, in C# 15 nicht enthalten), also lässt sich `Bounded<…, 30>` nicht schreiben. Bemerkenswert für spätere Leser: Rust *hat* const generics, und `nutype` nutzt trotzdem Proc-Macro-Codegen statt typseitiger Komposition – das Ergonomieproblem ist keine C#-Schwäche und verschwindet nicht, wenn die Sprache nachzieht.

**Bekannte Kosten, bewusst getragen:** Eine Grenzwertänderung (30→40) heißt Marker umbenennen – der Grenzwert ist Typidentität – oder einen Marker je Feld führen (O(F)-Boilerplate). Die Violation muss durch alle Generic-Ebenen gereicht und am Domänentyp aufgefaltet werden. Gegenüber der Alternative entstehen in der umgesetzten Form drei Typen und ein Enum zusätzlich (`IStringConstraint`, `IMaxLength`, `Bounded`, `StringViolation`) plus ein Marker je Grenzwert.

**Verworfen:** `private const int MaxLength` im Domänentyp + Längenprüfung in dessen `Create()` – null neue Typen, Fehlerunterscheidung direkt am Ort der Prüfung, ein Token je Grenzwertänderung. Verworfen, weil die Prüfzeile opt-in und damit vergessbar bleibt.
**Verworfen:** `StringRule` als fluent Prädikat-Pipeline (`For(x).NonEmpty().MaxLength(30).Build()`) – jeder Schritt ist opt-in, ein vergessenes `.NonEmpty()` erlaubt still leere Werte; dieselbe Vergessbarkeit wie oben, ohne den Ertrag des Typs.
**Verworfen:** `CheckedString` als neutraler Träger allein für den `default(T)`-Guard – spart über vier Felder nur 8→6 Suppressions, zu dünn für einen eigenen Typ und ein eigenes Konzept.
**Verworfen:** NRT statt des `default(T)`-Guards – trägt nicht: `default(T)` null-initialisiert bei structs auch ein als non-nullable deklariertes Feld, ohne Compiler-Warnung.

---

### ADR-S119-2: Fehler-sammelnde Validierung als `Collect` – ein Overload je Arity

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:error-handling, arch:validation

**Entscheidung:** Collect-All-Validierung (ADR-S090-1: der 422-Body nennt alle Feldfehler gleichzeitig) läuft über einen Applicative-Kombinator `Collect` in `Server/OneOfExtensions.cs`, mit **einem Overload je Stelligkeit**:

```csharp
internal static OneOf<TOut, IReadOnlyList<TError>> Collect<T1, T2, TOut, TError>(
    OneOf<T1, TError> first, OneOf<T2, TError> second, Func<T1, T2, TOut> combine);
// … analog für 3, 4, 5 Eingänge
```

`Collect` wertet seine Eingänge unabhängig aus und konkateniert deren Fehler. Anwendungsbeispiel: `coding-guideline-csharp.md`, Sektion „Kanonisches Beispiel".

**Begründung:** `Bind` kann strukturell nicht sammeln – es schließt beim ersten Fehler kurz. Sammeln ist ein Applicative, kein Monad. Ohne einen solchen Kombinator entsteht die Ersatzkonstruktion, die der Bestand zeigt (`IngredientsEndpoints.cs`): Fehler werden per `ErrorOrEmpty()` aus dem `OneOf` ausgepackt, parallel zur Kette in einer Liste gesammelt und am Ende per `MapError(_ => errors)` wieder eingeschleust. Das `_` verwirft den tatsächlichen Fehler des Fehlerkanals – der Kanal trägt die Information nicht mehr, und das Auspacken ist verkapptes `.AsT1`. Beides widerspricht der ROP-Pflicht (`csharp-rop.md`).

**Warum ein Overload je Arity:** Der Preis ist einmalige Boilerplate in **einer** Bibliotheksdatei; realistisch werden Arity 2 bis ~5 gebraucht (`Recipe` hat die meisten Felder). Die Aufrufer sind viele und bleiben lesbar.

**Verworfen:** Currying + ein einzelnes `Apply` (das kanonische `<*>`) – kommt mit **einer** Signatur für jede Arity aus und ist damit die einzige echte Alternative. Verlagert die Boilerplate aber vom einmaligen Bibliotheks-Code an jeden Aufrufort: handgecurriete Lambdas und ausgeschriebene `Func<,>`-Typen, weil C# verschachtelte Funktionstypen schlecht inferiert. Einmalige Kosten gegen dauerhafte eingetauscht.
**Verworfen:** LINQ-Query-Syntax (`from n in name from u in unit select …`) – eine Signatur, beliebige Arity, sehr lesbar, aber `SelectMany` ist monadisch und schließt beim ersten Fehler kurz. Query-Syntax kann grundsätzlich kein Applicative sein.
**Verworfen:** Tupel-Akkumulation (`r1.Zip(r2).Zip(r3)`) – die Tupel verschachteln sich zu `((a,b),c)`, und C# erlaubt keine Dekonstruktion in Lambda-Parameterlisten. Am Aufrufort unbrauchbar.
**Verworfen:** `params`-Array – verliert die Typen zur Compile-Zeit und damit den Zweck.

### ADR-S120-1: Ein Validierungs-Fehlertyp je Domänentyp – feldagnostisch, Feldbezug an der Grenze

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:domain-type, arch:error-handling, arch:validation

**Entscheidung:** Jeder Domänentyp bekommt einen **eigenen** Fehlertyp, dessen Fälle die Fehlerfälle *seines Fachkonzepts* sind – nicht die des darunterliegenden Constraint-Typs und nicht die eines Feldes. `IngredientName.Create` liefert `OneOf<IngredientName, IngredientNameError>`, `Unit.Create` liefert `OneOf<Unit, UnitError>`. Der Fehlertyp trägt **keinen** Feldnamen; der Feldbezug entsteht an der API-Grenze, die statisch weiß, welches Feld sie gerade validiert:

```csharp
// Grenze – der akkumulierte Fehlertyp IST das Antwortformat (ADR-S090-1), keine Zwischenstufe.
internal readonly record struct FieldError(string Key, string Message);

OneOfExtensions.Collect(
    IngredientName.Create(dto.Name).MapError(DescribeName),
    Unit.Create(dto.BaseUnit).MapError(DescribeBaseUnit),
    (name, unit) => (Name: name, BaseUnit: unit));
```

Ein geteilter Domänentyp (`Unit`, §2 Regel 2) bekommt **je Verwendungsstelle** eine eigene `Describe`-Zuordnung – die Rezept-Einheit später mit anderem Key und anderem Label. Der Typ bleibt einer.

**Präzisiert ADR-S119-1:** Dort heißt es, der Domänentyp falte `StringViolation` „in seine feldspezifischen Fehlerfälle (`NameEmpty`, `NameTooLong`)" auf. Die Faltung bleibt, ihr Ziel ist aber **konzept**-, nicht feldspezifisch (`IngredientNameError.Empty`). ADR-S051-2 (Fall → fester deutscher Text an der Grenze) bleibt unberührt.

**Folge für `IngredientValidationError`:** Der Typ verliert seine vier Feld×Prüfung-Fälle. Übrig bliebe `NameDuplicate` – ein Fehler, den kein Domänentyp erzeugen kann, weil er die Datenbank braucht und ohnehin erst nach der abgelehnten Insert-Operation entsteht (ADR-S111-2), also bereits an der Grenze. Ein Sum-Type mit genau einem Fall trägt nichts; der Duplikat-Fehler wird dort direkt zum `FieldError`, und der Typ entfällt.

**Begründung:** Regel 1 aus `coding-guideline-csharp.md` §2 verlangt, dass Constraint-Typen nicht in Signaturen stehen. Gäbe der Domänentyp `StringViolation` direkt zurück, müsste jeder Aufrufer wissen, was `Empty` *für dieses Konzept* bedeutet, und der absehbare Wechsel `Unit`: string → Enum (Fehlerfälle dann `Unknown` statt `Empty`/`TooLong`) bräche jede Aufrufstelle statt einer Datei. Ein eigener Fehlertyp je Konzept hält diesen Wechsel lokal.

**Bekannte Kosten, bewusst getragen:** ein zusätzlicher kleiner Typ je Domänentyp, und die Meldungstexte werden je Verwendungsstelle eines geteilten Typs erneut zugeordnet (Duplikation genau dann, wenn zwei Felder Label und Text teilen).

**Verworfen:** Domänentyp reicht `StringViolation` durch – null neue Typen, der Domänentyp schrumpft auf drei Zeilen. Verworfen wegen des Regel-1-Lecks oben: er hat dann keine eigene Aussage mehr, sondern ist ein Alias auf seinen Constraint-Stack.
**Verworfen:** ein Violation-Typ **je Prüfung** mit Feld-Payload (`NonEmpty(field)`, `MaxLength(field, max)`) – ergäbe die kompakteste Grenze, einen Template-Renderer plus Override-Tabelle statt eines Match je Fall. Verworfen aus zwei unabhängigen Gründen. (1) Ein geteilter Domänentyp kennt seine Verwendungsstelle nicht; der Feldname müsste als Parameter in `Create(field, input)` – damit kennt die Domäne das Request-Format, und ein Tippfehler im Feldnamen kompiliert klaglos. (2) Nicht jeder `Create`-Aufrufer kommt von einem Request: der Read-Pfad DB-Zeile → Domain (heute umgangen, siehe ADR-S108-1), Seeding, Import. Für die gibt es keinen sinnvollen Feldnamen, und ein zweiter Overload ohne `field` hebt die Garantie des Parameters wieder auf.
**Verworfen:** `IngredientValidationError` als Zwischenstufe beibehalten, mit dem neuen Fehlertyp davor – übersetzt dieselbe Information dreimal (`StringViolation` → `UnitError` → `IngredientValidationError` → Text), ohne Gegenwert gegenüber der ersten verworfenen Variante.

---

## Querschnittliche Fehlerbehandlung (Frontend)

### ADR-S056-1: Service-Layer + Custom Hooks + match()-Pflicht

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react, frontend:typescript, frontend:hooks, arch:error-handling

**Entscheidung:** Drei-Schichten-Muster für alle Backend-Aufrufe:

```
Service-Funktion   →  ResultAsync<T, DomainError>    (Fehler explizit im Typ)
Custom Hook        →  MutationState<T, DomainError>  (Discriminated Union)
Komponente         →  match() mit Pflichtfeldern      (Compile-Fehler bei fehlendem Fall)
QueryCache.onError →  Toast                          (Netzwerk/500 ohne Boilerplate)
```

**Enforcement:** `match()` nutzt Mapped Types – `{ [K in TError['kind']]: ... }`. Fehlt ein Fall im übergebenen Objekt → Compile-Fehler. Gilt für Fehler-Unions, Success-Unions und äußere Zustände (idle/pending/success/error). Details: `docs/guidelines/coding-guideline-typescript.md` Abschnitt 4b.

**Implementierungsdetail:** Domain-Fehler (`Err`) reisen als Rückgabewert durch React Querys Success-Pfad – kein `throw` für erwartete Fehler. Der generische Wrapper `useResultMutation<TData, TError, TVariables>` kapselt React Query vollständig; Custom Hooks reduzieren sich auf eine Zeile.

**Allgemeine Fehler** (Netzwerk, 5xx) werfen nativ und werden von `QueryCache.onError` zentral als Toast angezeigt – Komponenten sehen nur domänenspezifische Fehler.

**Verworfen:**
- Plain Promise allein: Fehlerfall unsichtbar im Typ, kein Enforcement möglich
- F# + Fable + Elmish: Agenten schreiben diesen Stack zu unzuverlässig – Versions-Drift zwischen Fable 2/3/4, Interop-Halluzinationen, schwache Fehlerdiagnose bei Fable-Compiler-Fehlern

---

### ADR-S054-1: Fehler-Kategorien: drei Typen, globaler HTTP-Interceptor

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react, arch:error-handling

**Entscheidung:** Das Frontend unterscheidet genau drei Fehler-Kategorien. Alle werden global im HTTP-Interceptor behandelt – kein per-Endpoint-Code für technische Fehler.

| Kategorie | Auslöser | Verhalten |
|-----------|----------|-----------|
| Netzwerkfehler | `TypeError` (kein Response) + HTTP 504 | Toast: „Server nicht erreichbar. Bitte Verbindung prüfen." |
| Serverfehler | HTTP 500, 502, 503 | Toast: „Ein unerwarteter Fehler ist aufgetreten." |
| Auth-Fehler | HTTP 401, 403 | Kein Toast – Redirect zur Login-Seite + Rückkehr-URL |

4xx (außer 401/403) sind Business-Fehler – werden per-Komponente behandelt, nicht global.

504 fällt unter Netzwerkfehler (Semantik: Server hat die Anfrage nie verarbeitet), nicht unter Serverfehler.

**Verworfen:** Per-Endpoint-Texte für technische Fehler – nicht skalierbar, kein UX-Mehrwert.

---

### ADR-S054-2: Toast: nicht-blockierend, ~5 Sekunden Auto-Dismiss

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react, arch:error-handling

**Entscheidung:** Technische Fehler erscheinen als Toast (nicht-blockierend, oben rechts), auto-dismiss nach ~5s.

**Verworfen:** Modal – zu aggressiv für transiente Fehler. Banner – sinnvoll erst für anhaltende Fehler (Offline-Modus, V1-Scope).

---

### ADR-S054-3: Console.error Format

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:typescript, arch:error-handling

**Entscheidung:** `[API Error] METHOD /path | Status: NNN | TraceId: xxx`

Beispiel: `[API Error] POST /api/ingredients | Status: 500 | TraceId: 00-abc123...`

URL (inkl. Pfad- und Query-Parameter) wird geloggt. Request-Body wird **nicht** geloggt – Security-Konvention, auch wenn aktuelle Daten nicht sensibel sind. TraceId aus `ProblemDetails.traceId` ist der Verbindungspunkt zum Backend-Log.

---

### ADR-S054-4: Kein automatisches Retry

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react, arch:error-handling

**Entscheidung:** Der Interceptor unternimmt keinen automatischen Retry. Manueller Retry-Button im Toast: V1-Scope.

**Begründung:** Retry bei nicht-idempotenten Operationen (POST, DELETE) riskiert Duplikate oder Doppellöschungen. Komplexität überwiegt Nutzen für Single-User-App.

---

### ADR-S054-5: Draft-Saving-Prinzip: per Feature, nicht global

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react

**Entscheidung:** Formulare mit nicht-trivialem Eingabeaufwand speichern ihren Zustand in `localStorage` – pro Feature implementiert, nicht im globalen Interceptor.

**Begründung:** Der Interceptor kennt keinen Formular-Zustand. Draft-Saving ist eine Feature-Entscheidung.

**Trigger im Gherkin-Workshop:** Schritt 1 fragt explizit: „Hat diese Story Formulare mit nicht-trivialem Eingabeaufwand? → Falls ja: Draft-Saving-Szenario einplanen."

---

### ADR-S054-6: ProblemDetails: Standard für Exceptions, `errorCode` für Domain-Fehler

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:error-handling, http:problem-details

**Entscheidung:**
- Unbehandelte Exceptions → Standard-ProblemDetails (ASP.NET Core Default). Kein `errorCode`, kein `detail`.
- Behandelte Domain-Fehler → Standard-ProblemDetails erweitert um `errorCode` (maschinenlesbar) + `detail` (menschenlesbar, deutsch):

```json
{
  "type": "...",
  "title": "...",
  "status": 409,
  "detail": "Eine Zutat mit dem Namen 'Tomaten' existiert bereits.",
  "errorCode": "INGREDIENT_DUPLICATE",
  "traceId": "00-abc123..."
}
```

**Begründung `errorCode`:** Frontend brancht zuverlässig ohne Text zu parsen. `detail` ist änderbar, `errorCode` ist API-Vertrag.

---

### ADR-S054-7: Backend-Logging: Applikationslogs und Access Logs getrennt

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:error-handling

**Entscheidung:** Applikationslogs (Exceptions, Domain-Events, TraceIds) und Access Logs (HTTP-Requests) sind getrennte Concerns. Access Logs in Produktion auf `Warning`+ gedrosselt.

**Scope:** Serilog und Produktions-Log-Infrastruktur sind kein MVP-Scope. Development: Console-Output von ASP.NET Core reicht. TraceId ist der zentrale Debug-Pfad (Frontend `console.error` → Backend-Log).

---

## Frontend & TypeScript

### ADR-S001-1: Frontend-Framework: React 18+ mit Material UI (MD3)

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react, frontend:typescript, tooling:dependencies

**Entscheidung:** React 18+ mit MUI v9 (Material Design 3). Ursprünglich v7 (S001), in S067 bewusst auf **v9** angehoben (kein v8; Alignment mit MUI X, „Foundations"-Release ohne Design-Redesign, MD3-Support bleibt); Slots-API (`slotProps`/`slots` statt deprecatetem `PaperProps`) ist Teil dieses Stands.

**Begründung:** MUI bietet vollständigen MD3-Support (stabil). Offline-Support (US-306) ist MVP – React-Ökosystem überlegen (Workbox, React Query). Mutation Testing mit Stryker-JS etabliert.

**Verworfen:** Blazor WebAssembly. Vue 3 + Vuetify. Svelte – kein MUI-Äquivalent (Svelte Material UI implementiert MD2, nicht MD3); Svelte 5 Runes sind explizit mutationsbasiert, Immutability-Kernprinzip würde gegen das Framework laufen.

---

### ADR-S003-1: TypeScript ROP-Bibliothek: `neverthrow`

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:typescript, tooling:dependencies

**Entscheidung:** `neverthrow`. API: `.andThen()`, `.match()`. 1M+ wöchentliche npm-Downloads, beste Community-Dokumentation.

**Risiko:** Maintenance verlangsamt sich (viele offene PRs). Bevorzugter Nachfolger: `@praha/byethrow` (serialisierbare Results, API-nah).

**Verworfen:** `effect` – Komplexität und Bundle-Größe übersteigen den Scope. `fp-ts` – akademisch, steile Lernkurve.

---

### ADR-S000-7: Einheiten-Konvention: Frontend normalisiert auf Basiseinheit

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:typescript, arch:validation

**Entscheidung:** Das Frontend normalisiert Mengenangaben auf metrische Basiseinheiten (Gewicht → g, Volumen → ml) vor dem API-Aufruf. Das Backend empfängt und speichert **immer** die Basiseinheit. Nicht-metrische Einheiten (EL, TL, Stück, Prise etc.) werden als Freitext gespeichert, unverändert.

**Begründung:** US-902 (Einheiten-Management mit Umrechnungsfaktoren) ist MVP. Bis dahin einfachste Lösung ohne Backend-Logik.

---

### ADR-S067-1: Einkaufsliste UX-Referenz: Bring!

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react

**Entscheidung:** Die Einkaufsliste orientiert sich am UX-Muster von Bring! – Kachel-Layout mit Icon (Strichzeichnung) und zweizeiligem Text (Name inkl. Modifizierer + Menge). Dieses Designprinzip gilt ab SKELETON, nicht erst ab V1.

**Begründung:** Bring! ist im Familienshopping-Kontext etabliert und auf Touch-Geräten gut bedienbar. US-304 (Visuelle Darstellung & Varianten) wurde aufgelöst, weil das Layout kein Feature-Increment ist, sondern ein Designprinzip – die Kachel-Entscheidung fällt einmalig und ist kein eigenständiges Implementierungsticket.

---


### ADR-S112-4: Domänenregeln setzt das Backend durch; Frontend-Brands sind nominal

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:typescript, arch:validation, story:us-306

**Kontext/Problem:** `coding-guideline-typescript.md` §2 verlangte Branded Types mit **validierender** Factory (Beispiel `makeRecipeId` mit Nicht-leer-Prüfung). Der Code geht seit S083 einen anderen Weg: `formNoValidate` am Speichern-Button schaltet die Browser-Durchsetzung ab, damit die Server-Meldungen sichtbar bleiben (`IngredientsPage.tsx`); durchgesetzt wird allein in `IngredientsEndpoints.ToDomain` (ADR-S051-3). Die Guideline hätte den nächsten Umsetzer also in eine zweite Regel-Durchsetzung im Frontend geführt. Zugleich trugen die Frontend-Domänentypen (`Ingredient`, `NewIngredient`) vier nackte `string`-Felder, obwohl §2 Kapselung fordert – die Guideline wurde in beide Richtungen nicht befolgt.

**Entscheidung:** Die Guideline wird **angepasst statt kommentiert**. §2 beschreibt Brands ab jetzt als rein **nominal** (Vergabe an der API-Grenze, keine Regelprüfung); der neue **§4c** trägt die Validierungs-Regel samt Ausnahme für Bereiche, in denen Zustandsänderungen ohne erreichbares Backend entgegengenommen werden. Die operative Regel steht dort, nicht hier.

**Begründung:** Eine Guideline, deren Beispiel dem gelebten Code widerspricht, ist die Fehlerquelle – eine ADR, die bloß die Abweichung erklärt, würde sie dauerhaft konservieren. Nominale Brands kosten fast nichts und tragen trotzdem: `restoreIngredient(id, name, baseUnit)` reiht drei gleichartige Strings aneinander, der Compiler fängt Vertauscher ohne einen einzigen Test. Die Offline-Ausnahme folgt nicht aus Bequemlichkeit, sondern aus der Abwesenheit des Servers.

**Verworfen:** Validierende Factories im Frontend als Normalfall – sie duplizieren ADR-S051-3, und E2E deckt Drift in Richtung Lockerung nicht auf: Ein Szenario müsste genau das freigewordene Wertband ausüben, sonst bleibt die zu strenge Frontend-Regel unbemerkt.

**Umfang zum Zeitpunkt der Entscheidung:** Einzig offline-schreibfähiger Bereich ist die Einkaufsliste (US-306, MVP; `docs/stories/szenario_3_einkauf.md`: „Alle Lese- und Schreiboperationen funktionieren offline"). §4c nennt diese Zuordnung bewusst **nicht**, weil sie sich mit dem Funktionsumfang ändert – dort steht das Kriterium, hier der Stand.

**Grenze / offen:** In der Offline-Ausnahme liegen Regeln zwangsläufig doppelt vor. Wie die Duplikate gegen Drift gesichert werden – geteiltes Artefakt, Vertragstest oder bewusst getragenes Restrisiko bei minimalem Regelsatz – ist **offen** und mit US-306 zu entscheiden. Die Richtwerte in §4c (Cache-Größenordnung, LOC-Budget) sind ungeprüfte Anhaltspunkte, keine beschlossenen Grenzen.

---

### ADR-S000-8: Bildformat: WEBP (nicht JPG), Format-Erkennung via Magic Bytes

**Status:** Accepted
**Tags:** scope:feature, resource:recipes, frontend:typescript

**Entscheidung:** Server konvertiert hochgeladene Bilder serverseitig zu WEBP. Pfadkonvention: `/uploads/recipe-sources/{recipeId}/original.webp` (deterministisch aus Recipe-ID ableitbar). Format-Erkennung via Magic Bytes – kein expliziter `Content-Type` oder Typ-Parameter im Request nötig.

**Verworfen:** `original.jpg` – WEBP bietet signifikant bessere Kompression bei gleicher Qualität. Expliziter Typ-Parameter – Client/Server-Inkonsistenz wenn Client falschen Typ angibt.

---

## Test-Tooling & Stryker

### ADR-S041-8: Mutation Testing Ziel: 100%

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:stryker

**Entscheidung:** Ziel ist 100% Mutation Score. Strukturell unerreichbarer Code (z.B. `_ => throw` in Sum-Type-Switch-Default) wird mit begründeten Suppressions behandelt, nicht mit gesenktem Zielwert. Die Praxis hat gezeigt, dass 100% realistisch erreichbar ist.

---

### ADR-S092-1: Stryker Mutation-Level „Standard" beibehalten (nicht auf Advanced anheben)

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:stryker, tooling:build

**Entscheidung:** Das Stryker-Mutation-Level bleibt auf „Standard" (Default) – es wird nicht auf Advanced angehoben. Advanced ist das einzige höhere Level mit zusätzlichen Mutator-Kategorien: Regex, Math Methods, **String Methods**. „Complete" ist laut Stryker.NET-Doku **deckungsgleich mit Advanced** (verifiziert S092: die Level-Tabelle listet keine Complete-exklusiven Mutationen, nur die Beschreibung „all possible mutations") – die einzige relevante Schwelle ist also Standard → Advanced.

**Begründung:**
1. **Der Anlass schließt den Blindspot nicht:** String-Method-Mutationen (z.B. `Trim()`) sind erst ab Advanced aktiv. Der einzige Advanced-Mutant für `input?.Trim()` ist `Trim() → ""` – er macht jeden Wert leer und wird vom Happy-Path-Test trivial getötet. Trim-*Korrektheit* (Whitespace wird entfernt, getrimmter Wert gespeichert) pinnt damit **kein** Mutation-Level, sondern nur ein szenariogetriebener Verhaltenstest auf den gespeicherten/zurückgegebenen Wert.
2. **Advanced verteuert das 100%-Gate (ADR-S041-8):** mehr Mutanten, mehr *äquivalente* Mutanten → mehr begründete Suppressions + Triage, langsamere Läufe – ohne proportionalen Korrektheitsgewinn, da die hochwertigen Verhaltensweisen (Trim, Casing, URL) ohnehin szenariogetrieben gepinnt werden.
3. **Standard ist der Upstream-Default** (einfachere Baseline).

**Revisit-Trigger:** Advanced neu bewerten, sobald regex-/string-method-schwerer Code entsteht – konkret die `sourceUrl`-Validierung (Regex) oder die Duplikat-Erkennung „abweichende Schreibweise" (falls via `.ToUpper()`/`.ToLower()` statt `StringComparer.OrdinalIgnoreCase`). Dann ist der Nutzen an einem konkreten Codepfad messbar.

**Verworfen:** Jetzt auf Advanced anheben – Gate-Mehraufwand ohne aktuellen Nutzen; schließt den Trim-Blindspot nicht (s.o.). (Complete ist keine separate Option, da laut Doku ≡ Advanced.)

---

### ADR-S041-9: Defensive Guards: kein Test, Stryker disable mit Begründung

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:stryker, arch:domain-type

**Entscheidung:** Guards wie parameterloser Konstruktor (`throw`) und `default(T)`-Property-Guards schützen gegen Sprachmissbrauch (Framework-Magie, versehentliches `new T()`). Sie sind strukturell unerreichbar. Kein Test. `// Stryker disable once` mit expliziter Begründung: `"Guard against language/framework misuse – unreachable via external interfaces"`.

**Kategorien:** Parameterloser Ctor: `Statement,String`. `default(T)` NullCoalescing-Guard (z.B. `_value ?? throw ...`): `NullCoalescing,String`. Equality-Guard (z.B. `_id == default`): `Equality,String`. Die `String`-Kategorie ist jeweils zusätzlich nötig weil Stryker auch den Exception-Meldungstext mutiert. Ist der Equality-Guard als Ternär formuliert (`_id == default ? throw new InvalidOperationException("…") : _id` – die kanonische Form für `Guid`), erzeugt Stryker zusätzlich einen `Conditional`-Mutanten → `Equality,String,Conditional`.

---

### ADR-S000-9: Stryker `additional-timeout`: 15000ms (statt Default 5000ms)

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:stryker, testing:integration-test

**Entscheidung:** `additional-timeout: 15000` in `stryker.conf.json`.

**Begründung:** Bei Partial-Runs (`--mutate Domain/Foo.cs`) traten Timeout-Mutanten auf, die keine echten Kills waren. Strykers Timeout-Formel `baseline × 1.5 + additional-timeout` liefert bei kurzer Partial-Run-Baseline (~15s) nur ~27.5s. Integration-Tests mit WebApplicationFactory-Start + DB-Verbindung haben variable Laufzeiten. 15000ms erhöht den Puffer auf ~32.5s ohne Auswirkung bei echten Infinite-Loop-Mutations.

---

### ADR-S000-10: Stryker `coverage-analysis: "off"` für Integration-Tests

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:stryker, testing:integration-test

**Entscheidung:** `coverage-analysis: "off"` in `stryker.conf.json`.

**Begründung:** `coverage-analysis` instrumentiert den Code um festzustellen welche Tests welche Mutanten abdecken. Für Tests mit `WebApplicationFactory` funktioniert das nicht – die Instrumentierung überlebt den Out-of-Process-Start nicht.

---

### ADR-S000-11: TestWebApplicationFactory: InMemoryDatabaseRoot für DB-Sichtbarkeit über Context-Grenzen

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:integration-test, db:ef-core

**Entscheidung:** `TestWebApplicationFactory` verwendet `InMemoryDatabaseRoot _dbRoot = new()` und übergibt es als zweites Argument an `UseInMemoryDatabase(_dbName, _dbRoot)`. `_dbName` ist eine per-Instanz eindeutige GUID (statt Guid.NewGuid() im Lambda).

**Begründung:** Der ursprüngliche Ansatz (`Guid.NewGuid()` im Options-Lambda + `UseInternalServiceProvider`) stellte keine verlässliche DB-Sichtbarkeit zwischen dem Test-DbContext (`_db` aus `_scope`) und dem Request-DbContext der WebApplicationFactory sicher. EF Core in-memory ohne expliziten `InMemoryDatabaseRoot` garantiert keine gemeinsame Store-Sicht über verschiedene DbContext-Instanzen. `InMemoryDatabaseRoot` ist der offizielle EF-Core-Mechanismus für diesen Fall (dokumentiert in EF Core Docs "Sharing databases between tests"). `UseInternalServiceProvider` bleibt erhalten um den Npgsql-Konflikt zu vermeiden.

**Verworfen:** `Guid.NewGuid()` im Lambda (→ potentiell neue GUID pro Auflösung, obwohl `DbContextOptions` Singleton ist – fragil). Kein `UseInternalServiceProvider` – erzeugt "two providers registered" Konflikt mit Npgsql.

---

### ADR-S057-1: HTTP-Mocking in Frontend-Tests: MSW statt `vi.stubGlobal('fetch', ...)`

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:msw, frontend:typescript

**Entscheidung:** Alle Frontend-Tests, die HTTP-Calls involvieren, verwenden MSW (`msw/node`) als einzigen Mocking-Layer auf HTTP-Ebene.

**Begründung:** `vi.stubGlobal('fetch', ...)` mockt die Implementierung (die Funktion `fetch`), nicht den HTTP-Kontrakt. Ein Test der `expect(mockFetch).toHaveBeenCalledWith('/api/ingredients')` prüft, ist beim Wechsel von `fetch` auf `axios` sofort rot – nicht weil die URL falsch ist, sondern weil die Implementierung sich ändert. MSW intercepted auf Netzwerk-Ebene und ist damit unabhängig davon, welches HTTP-Primitiv (`fetch`, `axios`, `XMLHttpRequest`) die Service-Funktion intern nutzt.

**Konsequenz:** Tests gegen Service-Funktionen (`ingredientsApi.ts` etc.) und Komponenten-Tests die HTTP-Calls auslösen, setzen Handler via `server.use(http.get('/api/...', () => HttpResponse.json(...)))` und kennen keine Implementierungsdetails der Service-Schicht.

**Verworfen:** `vi.stubGlobal('fetch', ...)` – koppelt Test an Implementierung statt Kontrakt. `nock` – unterstützt kein modernes `fetch`. `fetchMock`/`jest-fetch-mock` – gleicher falscher Schnitt wie stubGlobal.

---

### ADR-S055-1: Stryker-JS: `main.tsx` aus `mutate` ausgeschlossen

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:stryker, frontend:typescript

**Entscheidung:** `!src/main.tsx` in `Client/stryker.config.json`.

**Begründung:** Bootstrap-Code (`createRoot`, `QueryClientProvider`, `StrictMode`) – kein testbarer Domänen- oder Anwendungslogik-Anteil. Kein sinnvoller Unit-Test möglich.

---

### ADR-S063-1: Stryker.NET + xUnit v3: MTP Runner erforderlich

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:stryker, tooling:build

**Entscheidung:** `"test-runner": "mtp"` in `stryker-config.json`. Test-Projekt: `OutputType=Exe`, `UseMicrosoftTestingPlatformRunner=true`, `TestingPlatformDotnetTestSupport=true` in `Server.Tests/mahl.Server.Tests.csproj`.

**Begründung:** Stryker.NET 4.x unterstützt xUnit v3 (`xunit.v3`) nicht über den klassischen VSTest-Runner – Mutanten werden als "Survived" reportiert, obwohl Tests sie korrekt killen würden (verifiziert: manuell falsche Route → Test schlägt fehl, aber Stryker sieht es nicht). xUnit v3 nutzt ein anderes Ausführungsmodell als xUnit v2. Der MTP (Microsoft Testing Platform) Runner, verfügbar ab Stryker 4.13, löst die Inkompatibilität. `TestingPlatformDotnetTestSupport=true` stellt sicher, dass `dotnet test` weiterhin funktioniert.

**Verworfen:** Weiterhin VSTest-Runner – 0% Mutation Score für alle Endpoints trotz korrekter Tests.

---

### ADR-S089-1: MTP-natives Coverage-Gate (coverlet.MTP bevorzugt)

**Status:** Proposed
**Tags:** scope:cross-cutting, tooling:build

**Kontext:** Das Test-Projekt nutzt den MTP-Runner (ADR-S063-1). Darunter ist `coverlet.collector` (VSTest-DataCollector) wirkungslos. Beim WSL-/ext4-Umzug (S089) zeigte sich, dass das Branch-Coverage-Gate dadurch nur über veraltete cobertura-Reports „bestand" (Stale-Masking).

**Entscheidung:** Das Coverage-Gate läuft über eine **MTP-native** Engine, bevorzugt **`coverlet.MTP`** (in der Dependency-Allowlist). Die Umsetzung ist vertagt; operativer Stand + Trigger: **TD-S089-1**. <!-- ref-ok: bewusster ADR→TD-Statusverweis (Entscheidung stabil, Umsetzungs-Tracking im TD) -->

**Begründung:** `coverlet.MTP` reproduziert die bisherige Mess-Semantik (gleiche Engine; `--coverlet-skip-auto-props` schließt **präzise** nur Auto-Properties aus, nicht async/yield) → „100%" behält dieselbe Bedeutung; cobertura ist coverlet-nativ (Parser-kompatibel); OSS/inspizierbar.

**Verworfen:**
- **`coverlet.collector` (VSTest)** – unter dem MTP-Runner wirkungslos (Ursache des Stale-Maskings).
- **`Microsoft.Testing.Extensions.CodeCoverage`** – Auto-Props nur via breitem `CompilerGeneratedAttribute`-Exclude (schließt async/yield mit aus → überzeichnet ein 100%-Branch-Gate); Closed-Source. Bleibt **Fallback**.
- **Zurück zu VSTest** – Rückschritt gegen die xunit-v3/MTP-Wahl (ADR-S063-1).

**Status Proposed (nicht Accepted):** vor der realen Nutzung ist noch eine MTP-Versions-Kompatibilität zu lösen – Details und Trigger in TD-S089-1. <!-- ref-ok: bewusster ADR→TD-Statusverweis (Entscheidung stabil, Umsetzungs-Tracking im TD) -->

---

## Code-Qualität & Abhängigkeiten

### ADR-S041-10: CA1515: `internal`-Pflicht via Analyzer erzwungen

**Status:** Accepted
**Tags:** scope:cross-cutting, tooling:analyzer

**Entscheidung:** CA1515 (`warning`) in `.editorconfig` für `{Server,Server/**}/*.cs`. Erzwingt die in `CODING_GUIDELINE_CSHARP.md` beschriebene `internal`-Pflicht statisch – Compiler blockiert `public`-Typen in `Server/`.

---

### ADR-S044-1: AwesomeAssertions statt FluentAssertions

**Status:** Accepted
**Tags:** scope:cross-cutting, tooling:dependencies, testing:integration-test

**Entscheidung:** `AwesomeAssertions` (Apache 2.0, permanent). Identisches API zu FluentAssertions v7 – Drop-in-Ersatz ohne Lizenzrisiko.

**Begründung:** FluentAssertions v8 wechselte zu kommerzieller Xceed-Lizenz. AwesomeAssertions entstand als Community-Fork auf Basis der letzten Apache-2.0-Commits.

**Verworfen:** FluentAssertions v7 – nur noch Security-Updates. FluentAssertions v8 – kostenpflichtige Lizenz.

---

### ADR-S044-2: xUnit v3 (`xunit.v3`) statt v2

**Status:** Accepted
**Tags:** scope:cross-cutting, tooling:dependencies, testing:integration-test

**Entscheidung:** `xunit.v3`. Modernere Architektur (Test-Projekte als standalone Executables), bessere Async-Unterstützung, aktive Entwicklung.

**Verworfen:** xUnit v2 – stabile API, aber keine neuen Features mehr.

---

### ADR-S044-3: DEPENDENCIES.md ohne Versionsnummern

**Status:** Accepted
**Tags:** scope:cross-cutting, tooling:dependencies

**Entscheidung:** Die Allowlist (`DEPENDENCIES.md`) enthält nur Package-Namen, keine Versionen. Versionen gehören ausschließlich in `.csproj`/`package.json`. Die Allowlist ist ein Zugangskontroll-Mechanismus, kein Versionsmanagement-Tool – Pinning erzeugt eine dritte Quelle die zwangsläufig divergiert und den Dependency-Hook bei legitimen Updates blockiert.

**Verworfen:** Versionen in Allowlist – Divergenzrisiko, unklare Semantik, Wartungsaufwand ohne Sicherheitsgewinn (CVEs besser via `dotnet list package --vulnerable` / `npm audit`).

---

## HTTP-Caching & Optimistic Concurrency

### ADR-S058-1: Globale ETag-Policy: alle mutierbaren Ressourcen

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching

**Entscheidung:** Alle Endpoints erhalten ETags – keine Ausnahmen.

**Begründung:** Jeder GET-Endpoint profitiert von HTTP-Caching (304). PUT/PATCH/DELETE brauchen zusätzlich If-Match für Optimistic Concurrency. Die Unterscheidung "mutierbar vs. nicht mutierbar" ist irrelevant – ETags sind auf GET unabhängig davon sinnvoll. Cross-Cutting-Concern: sobald die Grundstruktur steht, kostet jede weitere Entity minimal.

---

### ADR-S058-2: Zwei Verwendungszwecke: HTTP-Caching und Optimistic Concurrency

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching, http:412

**Entscheidung:** Derselbe ETag-Wert wird für beide Zwecke eingesetzt:

| Zweck | Request-Header | Response-Status |
|-------|---------------|-----------------|
| HTTP-Caching | `If-None-Match: "..."` bei GET | 304 Not Modified |
| Optimistic Concurrency | `If-Match: "..."` bei PUT/PATCH/DELETE | 412 Precondition Failed |

---

### ADR-S058-3: ETag-Quelle: xmin (Single Resource) / Content-Hash (Collection)

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching, db:xmin

**Entscheidung:**

**Single-Resource-Endpoints** (`GET /api/ingredients/{id}` etc.):
ETag = PostgreSQL `xmin`-Wert des Rows, hex-kodiert (z.B. `"a3f2c1b4"`).
EF Core Npgsql: `UseXminAsConcurrencyToken()`. Keine extra Spalte – PostgreSQL pflegt xmin automatisch.

**Collection-Endpoints** (`GET /api/ingredients` etc.):
ETag = SHA-256-Hash der serialisierten JSON-Response-Body (hex-kodiert).

**Begründung Single-Resource xmin:**
xmin koppelt HTTP-ETag und EF Core Concurrency-Token in einem Mechanismus. EF Core wirft `DbUpdateConcurrencyException` automatisch wenn xmin beim UPDATE nicht mehr übereinstimmt → 412. 304-Check ist ein billiger `SELECT xmin`-Query ohne Full-Row-Fetch.

Content-Hash für Single Resources würde zwei getrennte Checks erfordern (Hash-Vergleich + EF Core xmin intern) – redundant und inkonsistent.

**Begründung Collection Content-Hash:**
Kein einzelner DB-Wert bildet den Collection-Zustand korrekt ab. `MAX(xmin)` ist DELETE-blind. `SUM(xmin)` wäre für modernes PostgreSQL (9.4+: VACUUM FREEZE ändert xmin nicht mehr) korrekt und günstig, ist aber kein etabliertes Muster und PostgreSQL-spezifisch. Content-Hash ist portabel, verständlich und für diese App schnell genug.

**Verworfen:** `MAX(xmin)` für Collections – blind gegenüber Deletes.
**Verworfen:** `SUM(xmin)` für Collections – korrekt für PostgreSQL 9.4+, aber kein etabliertes Muster; eingeschränkte Portabilität.
**Verworfen:** Content-Hash für Single Resources – bricht die EF Core Concurrency-Token-Kopplung.

---

### ADR-S106-1: Erste Single-Resource-xmin-ETag-Umsetzung: POST als ETag-Quelle, manuelle xmin-Konfiguration

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching, db:xmin

**Entscheidung:** `DELETE /api/ingredients/{id}` (US-904 run-10) ist der erste mutierende Single-Resource-Endpoint im Projekt und damit die erste konkrete Umsetzung von ADR-S058-1/ADR-S058-3 (xmin-ETag + If-Match). Zwei Abweichungen von der ursprünglichen Formulierung dieser ADRs:

1. **Kein `GET /api/ingredients/{id}`.** `POST /api/ingredients` liefert den xmin-ETag der neu angelegten Zeile im `ETag`-Response-Header – das ist der ETag, den ein Client für ein nachfolgendes `If-Match` bei DELETE/PUT/PATCH braucht. Ein dedizierter Single-Resource-GET-Endpoint ist bewusst nicht Teil dieser Umsetzung.
2. **`UseXminAsConcurrencyToken()` existiert nicht** in `Npgsql.EntityFrameworkCore.PostgreSQL` 10.0.1 (per Assembly-Introspektion verifiziert – frühere Annahme aus allgemeinem Wissen, keine belastbare Quelle). Stattdessen manuelle Shadow-Property-Konfiguration in `MahlDbContext.OnModelCreating`:
   ```csharp
   modelBuilder.Entity<IngredientDbType>()
       .Property<uint>("xmin")
       .HasColumnType("xid")
       .ValueGeneratedOnAddOrUpdate()
       .IsConcurrencyToken();
   ```
   Funktional identisch zum (nicht vorhandenen) Helper: `xmin` bleibt eine reine Postgres-Systemspalte (keine Migrations-DDL), EF Core wirft `DbUpdateConcurrencyException` bei stale `OriginalValue` automatisch.

**Begründung:** Beide Punkte sind reine Implementierungsdetails, keine Abweichung von der Kernentscheidung (xmin als Single-Resource-ETag-Quelle, ADR-S058-3 bleibt unverändert gültig). Dokumentiert, damit zukünftige Single-Resource-Endpoints (z.B. Recipes) dasselbe Muster übernehmen, statt den fehlenden Helper erneut zu suchen.

---

### ADR-S106-2: If-Match-Fehlerbehandlung: 428/400/412-Dreiteilung, kein `*`/Weak/List-Support

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, http:delete, http:400

**Entscheidung:** Ein If-Match-Header auf `DELETE /api/ingredients/{id}` fällt in genau eine von drei Kategorien:

| Zustand | Status |
|---------|--------|
| Header fehlt komplett | 428 Precondition Required |
| Header vorhanden, aber nicht zu einem xmin parsebar (non-hex, Overflow, leer, `*`, weak `W/"..."`, Multi-Value-Liste) | **400 Bad Request** |
| Header vorhanden, wohlgeformt, aber stale (parst, matcht aber nicht den aktuellen xmin) | 412 Precondition Failed |

400-Body (analog `NotFoundProblem`, ADR-S054-6): `detail: "Der If-Match-Header ist ungültig."`, `errorCode: "INVALID_IF_MATCH"`.

`*` (RFC-7232-Wildcard), weake ETags und Multi-Value-Listen werden bewusst **nicht** unterstützt (YAGNI) – konsistent zum bereits bestehenden Nichtsupport in `ETagMiddleware` (nur Single-Tag-Ordinal-Vergleich). Ein solcher Wert fällt in die 400-Kategorie statt eine eigene Semantik zu bekommen.

Technisch: `XminETag.TryParse(string, out uint)` statt einer werfenden `Parse`-Variante (die bei malformed Input eine unbehandelte `FormatException`/`OverflowException` → 500 durchschlagen ließe, Stack-Trace-Leak-Risiko). `TryParse` folgt dem Standard-.NET-Idiom (wie `uint.TryParse` selbst) statt OneOf/ROP: ein nicht-parsebarer If-Match ist ein technischer HTTP-Protokoll-Parsing-Fehler, kein Domänen-/Validierungsfehler (docs/guidelines/csharp-rop.md: ROP gilt für Domänenfehler).

**Verworfen:** `*`/Weak/List-Support jetzt einführen – kein Konsument, YAGNI (konsistent zur bestehenden ETagMiddleware-Entscheidung).
**Verworfen:** `Parse` als werfende Methode behalten und im Endpoint mit `try/catch` abfangen – `TryParse` ist das idiomatische .NET-Muster für einen erwarteten Fehlerfall ohne Exception-Overhead.

---

### ADR-S106-3: Querschnitts-Protokoll-/Invarianten-Tests ohne treibendes Gherkin-Szenario tragen keinen US-Tag

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:integration-test, testing:gherkin

**Entscheidung:** Backend-Integrationstests, die reines Querschnitts-Verhalten absichern und NICHT von einem Gherkin-Szenario getrieben sind, tragen bewusst KEINEN `USxxx_`-Tag. Zwei Kategorien:
1. **Protokoll-/Infrastruktur-Mechanik** – HTTP-Precondition-Verhalten aus einer Querschnitts-ADR (ETag-Format, `If-Match`-Pflicht 428/400/412, POST-liefert-ETag; ADR-S058-1/-3, ADR-S106-1/-2). Präzedenz: die `ETagMiddleware`-Tests (Collection-ETag) tragen ebenfalls keinen US-Tag.
2. **Stryker-blinde Invarianten** – Tests, die eine bewusste Reihenfolge-/Prioritäts-Invariante gegen Refactoring-Regression pinnen, die Stryker strukturell nicht fangen kann (Statement-Reorder ist kein Mutant; z.B. die 404-vor-If-Match-Dominanz, ADR-S000-5-Addendum). Dieselbe Klasse wie ein Fokus-Prioritäts-Pin, den ein 100 %-Mutation-Score über Einzelfälle allein nicht absichert.

**Begründung:** `docs/process/e2e-testing.md` verlangt US-Tag + ScenarioType als Spec↔Test-Traceability für **szenario-getriebene** Tests. Ein Querschnitts-/Invarianten-Test hat per Definition kein einzelnes treibendes Szenario; ein erzwungener US-Tag wäre eine falsche Traceability-Behauptung. Zentral hier dokumentiert, statt in jedem betroffenen Test einzeln (vermeidet die Kommentar-Wiederholung über die betroffenen Tests und deren Drift).

**Guard (Abgrenzung zu Gold-Plating):** Ein US-Tag-loser Test MUSS per Kommentar als Kategorie 1 oder 2 ausgewiesen sein (welche ADR / welche Invariante). Prüft ein Test hingegen Domänen-/Szenario-Verhalten, ist US-Tag + Gherkin-Szenario Pflicht – fehlt beides, ist es eine Outside-In-Verletzung / Gold-Plating (review-checklist.md „Test-Audit").

**Verworfen:** Die Ausnahme pro betroffenem Test als Kommentar wiederholen – driftet und macht die Grenze „legitime Infra-Ausnahme vs. Gold-Plating" für jeden Review neu verhandelbar.

---

### ADR-S000-12: Implementierungsreihenfolge ETag-Support

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching

**Entscheidung:** ETag-Support wird pro Endpoint beim Szenario-Schritt eingebaut, der den Endpoint erstmalig mit echten DB-Daten belegt. Nicht in Skeleton-Stubs (hardcoded Antworten haben keinen sinnvollen ETag).

`GET /api/ingredients` erhält ETag-Support in US-904 Szenario 2 (erster GET mit echten DB-Rows).

**Addendum (S084) – Präzisierung für Content-Hash-Collections:** Diese „pro Endpoint / nicht in Stubs"-Regel gilt **nur noch für xmin-Single-Resource-ETags** – die brauchen einen echten DB-Row, ein Stub ohne Row hat keinen sinnvollen xmin. Für **Content-Hash-Collection-ETags gilt sie nicht**: Sie werden von einer generischen Middleware (ADR-S084-1) für jede GET-200-Response gebildet, sobald die Middleware registriert ist – es gibt kein per-Endpoint-Opt-in. Die ursprüngliche Begründung „hardcoded Antworten haben keinen sinnvollen ETag" trifft auf Content-Hashes nicht zu: der SHA-256-Hash eines hartkodierten `[]`-Body ist stabil und valide. Der ETag für `GET /api/ingredients` wurde daher nicht „im GET-Szenario", sondern nachgelagert im ETag-Querschnitts-Zyklus (S084) als Middleware umgesetzt.

---

### ADR-S084-1: Collection-ETag via generische Response-Middleware

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching

**Entscheidung:** Der Collection-Content-Hash-ETag (ADR-S058-3) wird von einer **einzigen generischen Response-Middleware** gebildet, nicht pro Endpoint. Die Middleware puffert jede **GET**-Response, bildet bei **Status 200** den SHA-256-Content-Hash des serialisierten Body, setzt ihn als `ETag`-Header und behandelt `If-None-Match` → 304 uniform. Nicht-GET- und Nicht-200-Responses werden unverändert durchgereicht. Registrierung einmalig in `Program.cs` vor dem Endpoint-Mapping (`app.UseCollectionETag()`).

**Begründung:** Content-Hash ist endpoint-agnostisch (er hasht nur den Body) – eine generische Middleware erfüllt die „alle Endpoints"-Policy (ADR-S058-1) mit einer Implementierung (DRY). Die 304-Logik ist ein echter Querschnitts-Concern.

**Voraussetzung – deterministische Serialisierungs-Reihenfolge:** Der Content-Hash ist nur dann ein stabiles Caching-Token, wenn der Endpoint die Collection in **deterministischer Reihenfolge** serialisiert. Ohne `ORDER BY` ist die PostgreSQL-Reihenfolge undefiniert → der Hash variiert bei identischen Daten → `If-None-Match` matcht nie → 304 feuert nie (Daten bleiben korrekt, das Caching ist aber wirkungslos – ein Effektivitäts-, kein Korrektheits-Bug). Jeder Collection-Endpoint mit Content-Hash-ETag muss daher deterministisch sortieren.

---

### ADR-S084-2: ETag-Format & -Vergleich: voller Hash, ordinal, keine Casing-Normalisierung

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching, testing:mutation

**Entscheidung:**
- **Format:** Collection-ETag = `$"\"{Convert.ToHexString(SHA256.HashData(body))}\""` – **voller** SHA-256-Hash als Uppercase-Hex in doppelten Quotes. **Keine Truncation.**
- **Casing:** Uppercase entsteht direkt aus `Convert.ToHexString` – **kein** nachgelagerter `.ToUpperInvariant()`/`.ToLowerInvariant()`-Call.
- **Vergleich:** `If-None-Match` wird **ordinal/verbatim** mit dem ETag verglichen (`StringValues ==` ist ordinal) – **nie** case-insensitive. Der Frontend-Client echo't den ETag verbatim zurück (RFC 7232: opake, octet-genaue Tokens; verbatim auch im Frontend-Cache, ADR-S084-3).

**Begründung (Anti-Stryker-Survivor):** Jede Casing-Normalisierung (`.ToUpper()/.ToLower()` auf Vergleichsseite) ist **un-killbar**: Da der Client verbatim echo't, stimmt die Schreibweise immer schon überein – der Mutant „Normalisierung entfernt" ändert das Ergebnis nie. Ebenso erzeugt `Substring(0, 16)` (Truncation) eine Magic-Number-Mutante, die ohne zusätzliche Längen-Assertion überlebt. Voller Hash + ordinaler Vergleich + Casing direkt aus dem Encoder = **0 Suppressionen**. Diese Regel gilt für alle künftigen ETag-Endpoints.

**Verhältnis zu bestehenden Docs:** Präzisiert ADR-S058-3 (dort nur „SHA-256-Hash … hex-kodiert"). Die Notiz in `coding-guideline-csharp.md` §6 „erste 16 Zeichen hex genügen" wird auf den vollen Hash korrigiert. **Kosmetische Divergenz:** xmin-Single-Resource nutzt lowercase (`{xmin:x8}`), Collection-Content-Hash uppercase – akzeptiert, da unabhängige opake Tokens, die nie miteinander verglichen werden.

---

### ADR-S084-3: Frontend-Conditional-Layer (HTTP-Conditional-Requests)

**Status:** Accepted
**Tags:** scope:cross-cutting, http:etag, arch:caching, frontend:react

**Entscheidung:** Ein generischer Service-Helper `conditionalGetJson<T>(url)` (`Client/src/services/conditionalGet.ts`) hält einen modul-lokalen Cache `URL → { etag, body }`, sendet bei vorhandenem ETag `If-None-Match` und liefert bei `304` den gecachten Body. Bei `200` werden ETag + Body (verbatim, keine Normalisierung) gecacht. `fetchIngredients` nutzt diesen Helper.

**Begründung:** react-query macht von Haus aus **keine** HTTP-Conditional-Requests. Ohne diese Schicht hätte der Backend-ETag keinen Konsumenten – der 304-Spareffekt entsteht nur, wenn der Client `If-None-Match` sendet. Eine Frontend-seitige Cache-Invalidierung ist nicht nötig: Nach einem POST ändert sich der Backend-Content-Hash → `If-None-Match` matcht nicht mehr → 200 mit neuem Body → der Cache aktualisiert sich selbst.

**Testung:** Auf der Service-Client-/HTTP-Boundary via MSW (ADR-S041-5-Addendum), nicht E2E – die Conditional-Mechanik ist auf E2E-Ebene nicht beobachtbar (gerenderter Output identisch bei 200 und 304).

**Addendum (S111) – zweite Ursache für „auf der Komponente nicht beobachtbar": React Query verschluckt Fehler aus `onSuccess`.** Bisher lag der Grund für einen Service-Client-Test stets darin, dass die Mechanik im DOM keine Spur hinterlässt (If-None-Match, If-Match). In run-11 kam ein anderer Fall dazu: Ein Mutant in `restoreIngredient`s Status-Verzweigung lässt den Konflikt-Zweig auf eine `200`-Antwort laufen, deren Body das erwartete Feld nicht hat → `TypeError` beim Aufbau der Snackbar. Dieser Fehler wird von React Query **innerhalb** des `onSuccess`-Callbacks abgefangen, erreicht also weder eine Error-Boundary noch den Testlauf; `closeDialog` und der Listen-Refetch sind zu dem Zeitpunkt bereits gelaufen und stammen ohnehin aus dem GET, nicht aus dem geparsten Wert. Der Komponenten-Test bleibt deshalb grün, obwohl der Code defekt ist. Konsequenz: Nicht nur DOM-lose Mechanik, sondern auch **Logik, deren Fehlschlag in einem Framework-Callback verschluckt wird**, gehört auf die Service-Client-Schicht. Quelle: frontend-layer-implementer, run-11.

---

### ADR-S084-4: Playwright besitzt den Backend-Lebenszyklus für E2E (Poka-Yoke gegen stale Backend)

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:e2e, tooling:build

**Kontext/Problem:** Playwright startete nur Vite (`reuseExistingServer:true`); das Backend war ein separat/manuell verwalteter Prozess (`ASPNETCORE_URLS=…5059 dotnet run`). Ein **veralteter** Backend-Prozess (z.B. von vor einem Code-Change) wurde von der E2E-Suite **still mitgetestet** → irreführende Ergebnisse. In S084 kostete genau das ~1 h Fehlersuche: ein pre-S083-Prozess lieferte hartkodiert leere GETs, wodurch der „Zutat anlegen"-E2E scheinbar fehlschlug, obwohl der aktuelle Code korrekt war.

**Entscheidung:** Playwright besitzt den Backend-Lebenszyklus für E2E. `playwright.config.ts` → `webServer`-Array mit Backend-Eintrag (`dotnet run --project ../Server`, `env: { ASPNETCORE_URLS: 'http://localhost:5059' }`, `reuseExistingServer: false`, `url: /api/ingredients`). Jeder E2E-Lauf **baut & startet das Backend frisch aus dem Quellcode** und fährt es danach herunter. Vite bleibt `reuseExistingServer:true` (nie stale dank Hot-Reload).

**Begründung:** `reuseExistingServer:false` macht es **strukturell unmöglich**, dass ein veralteter Prozess mitgetestet wird (einzige Variante mit echter Garantie). Die `url`-Readiness-Probe (`/api/ingredients`) verifiziert die DB-Verbindung und wärmt EF/JIT → mindert zugleich das Cold-Start-Race. Fehlerfälle werden **laut**: Port belegt → Konflikt; Build-Fehler → webServer-Start scheitert; DB down → Readiness-Timeout.

**Verworfen:**
- **Status quo** (manuelles Backend, kein Check) – kein Poka-Yoke, verlässt sich auf Disziplin.
- **Leichter Pre-Flight-Guard** (Probe auf ETag-Header) – fängt nur „down"/„pre-ETag-stale", keine echte Build-Identität.
- **Build-Identitäts-Guard** (Git-SHA-Endpoint vs. HEAD) – leck bei dirty working tree (uncommittete Änderungen ≠ HEAD-SHA), zusätzliche Infra nötig.

**Kosten:** wenige Sekunden Mehraufwand pro E2E-Lauf (Build/Start/Warmup); kein paralleles eigenes Backend auf 5059 während E2E; Postgres muss laufen.

**Addendum (S098) – E2E-DB-Isolation (per-Test) & eigene E2E-Datenbank (löst die vormalige Tech-Debt „E2E-Postgres ohne Per-Run-Reset"):** Der hier etablierte E2E-`webServer` bekommt zusätzlich `ASPNETCORE_ENVIRONMENT: 'E2E'`. Damit:
- **Eigene DB:** `appsettings.E2E.json` → `Database=mahl_e2e` – die E2E fasst die dev/prod-DB `mahl` nie an.
- **Schema pro Lauf:** In der E2E-Umgebung führt `Program.cs` beim Start `MigrateAsync()` aus (provisioniert `mahl_e2e` bei Bedarf) und mappt einen **nur dann existierenden** Test-Support-Endpoint `POST /api/test/reset` (`E2ETestSupport.cs`). Außerhalb E2E existieren beide nicht → kein dev/prod-Runtime-Risiko.
- **Per-Test-Isolation:** Ein Playwright-`beforeEach` ruft den Reset vor **jedem** Test. Der Reset **TRUNCATEt alle Tabellen generisch aus dem EF-Modell** (`db.Model` – kein Pflegeaufwand bei neuen Entitäten). TRUNCATE statt DROP+Recreate, weil die laufende App eine offene Verbindung zu `mahl_e2e` hält (DROP scheitert an aktiven Connections) und TRUNCATE keinen Schema-Rebuild pro Test braucht. `RESTART IDENTITY` ist bei UUIDv7-PKs (ADR-S030-1) folgenlos, aber future-proof; `CASCADE` löst die FK-Reihenfolge.

**Warum echtes Postgres statt EF-InMemory (Kontrast zu ADR-S000-11):** Die Backend-Integrationstests dürfen EF-InMemory nutzen (In-Process-Logikprüfung, ADR-S000-11). E2E lebt dagegen von Produktions-Fidelity: EF-InMemory ist keine relationale DB und würde Unique-Constraints (US-904 „Name-Eindeutigkeit"), `xmin`-basierte ETags (ADR-S058-3), `maxlength` und die Migrations-Korrektheit **nicht** abdecken. Der Reset läuft bewusst über einen HTTP-Port (ADR-S041-1: Tests sprechen die App über ihre Ports an), nicht über einen direkten DB-Client.

**Mutation-Testing:** `E2ETestSupport.cs` ist aus der Backend-Stryker-`mutate`-Liste ausgeschlossen (analog `Program.cs`-Bootstrap) – E2E-only-Scaffolding, das von den Backend-Unit-Tests nicht ausgeführt wird und keine Domänen-/Applikationslogik trägt; seine Korrektheit wird von der E2E-Suite selbst belegt (die loud `expect(status).toBe(204)`-Reset-Assertion im `beforeEach`).

**Grenze / offen:** Reset ist per-Test bei Single-Worker (aktuelle Config). Seed-Daten (später): idempotenter Insert nach dem Truncate im Reset-Endpoint.

---

### ADR-S112-2: E2E erbt die Produktions-Konfiguration; Umgebungsnamen sind allow-gelistet

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:e2e, tooling:build

**Kontext/Problem:** E2E läuft als eigene Umgebung (`ASPNETCORE_ENVIRONMENT=E2E`, ADR-S084-4 Addendum). Jede Konfigurationsabweichung zwischen E2E und Produktion ist damit ein blinder Fleck: Ein grüner E2E-Lauf sagt über Produktion nur so viel aus, wie beide Konfigurationen übereinstimmen. Der Ist-Zustand ist gut – `appsettings.E2E.json` überschreibt ausschließlich den Connection-String, eine `appsettings.Production.json` existiert gar nicht – beruhte aber allein auf Disziplin und war nirgends festgehalten.

**Entscheidung:**
1. **Layering:** Alles Gemeinsame steht in `appsettings.json`. Umgebungsspezifische Dateien enthalten **nur Abweichungen**, und zwar nur pfad-artige (Connection-String, Log-Ziele). Jede weitere Abweichung braucht eine Begründung mit ADR-Bezug.
2. **Prüfung:** Ein Test hält die Schlüssel der umgebungsspezifischen Dateien gegen eine Allow-Liste; ein nicht gelisteter Override schlägt fehl.
3. **Umgebungs-Allow-Liste:** Beim Start prüft die App ihren `EnvironmentName` gegen eine feste Liste und bricht andernfalls mit einer Meldung ab, die die erlaubten Werte nennt. **Dieselbe Liste** treibt die Umgebungs-Aufzählung im Fehlerpfad-Test aus ADR-S112-1.

**Begründung:** Punkt 1 ist gängige Konfigurations-Praxis und macht Divergenz sichtbar statt möglich. Punkt 3 verhindert, dass eine nie getestete Umgebung überhaupt startet, und koppelt Betrieb und Test an eine einzige Quelle – ohne diese Kopplung driften Test-Aufzählung und Realität auseinander. Ein Umgebungs-Tippfehler wird dadurch zum lauten Startabbruch statt zu stiller Divergenz.

**Kosten:** Eine neue Umgebung erfordert eine Code-Änderung (Eintrag in der Liste). Das ist gewollt: Sie landet damit zwangsläufig auch im Test.

**Grenze / offen:** Das schließt **nicht** aus, dass die Konfigurationsdatei einer erlaubten Umgebung im Betrieb verändert wird – dagegen hülfe nur Konfiguration im Code, was für diese Anwendung unverhältnismäßig ist (bewusst gezogene Grenze: keine Höchstsicherheits-Ansprüche, nur keine unnötigen Lücken). Der Startup-Guard muss auch greifen, wenn der Host von Werkzeugen gebaut wird (`dotnet ef`, `WebApplicationFactory`); beide laufen als `Development` und stehen damit auf der Liste – beim Umsetzen **verifizieren**, nicht annehmen. Umsetzung ab MVP gemeinsam mit ADR-S112-1.

---

### ADR-S112-3: E2E fälscht keine Backend-Antworten – Fehlerzustände werden real ausgelöst

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:e2e, arch:error-handling

**Kontext/Problem:** Die `@NFR-resilience`-Szenarien fordern Fehlerzustände (Backend nicht erreichbar, Serverfehler), die im Normalbetrieb nicht auftreten. Die E2E-Suite nutzt `page.route` bisher **ausschließlich** mit `route.continue()` – sie verzögert echte Anfragen, fabriziert aber nie Antworten. Eine Politik dazu fehlte; damit stand bei jedem neuen Fehler-Szenario neu zur Debatte, ob `route.fulfill()` erlaubt ist.

**Entscheidung:**
1. **In E2E wird nichts gemockt, soweit möglich.** Ein Fehlerzustand wird **real ausgelöst**, nicht als Antwort fabriziert.
2. **Test-Support-Endpoints** (E2E-only, gegatet wie `/api/test/reset`) sind zulässig, wenn die realen Alternativen unverhältnismäßig wären.
3. **Muster für Serverfehler:** ein Fault-Endpoint, der **out-of-band** scharfgestellt wird (`POST /api/test/fault` mit einem Matcher für den nächsten Request); der nächste passende Request wirft dann in der **echten** Pipeline. Das Frontend ruft nichts Künstliches auf – es wird ganz normal bedient und trifft den echten Endpoint.
4. **Nicht herstellbare Vorbedingungen:** Ist eine Zusicherung in Produktion realistisch, im E2E-Harness aber nicht echt herstellbar, wird sie **nicht** per gefälschter Antwort in E2E erzwungen, sondern als Querschnitts-/Infra-Test unterhalb E2E nachgewiesen (Ausnahme aus ADR-S106-3, Ausweispflicht per Kommentar gilt).

**Begründung:** Eine gefälschte Antwort testet den Client gegen eine Erfindung des Tests, nicht gegen das System – und maskiert genau die Abweichungen zwischen simuliertem und echtem Verhalten, die E2E aufdecken soll. Punkt 3 hält die Fälschungsfreiheit auch für Fehlerpfade aufrecht: Echt sind Request, Pipeline, Exception, Antwort, Netzwerkweg und Frontend-Pfad; gestellt ist allein der Zeitpunkt des Auslösers. Punkt 4 verhindert, dass „lässt sich in E2E nicht herstellen" zur Generalvollmacht fürs Mocken wird – die Alternative ist eine Ebene tiefer, nicht eine Fälschung höher.

**Anwendungsfall (S112):** „Die UI zeigt keine technischen Fehlerdetails an, falls der Server doch welche sendet." In Produktion realistisch (Fehlkonfiguration), in E2E nicht herstellbar – der Server sendet dort nach ADR-S112-1 per Konstruktion keine Details. Fällt damit unter Punkt 4: Infra-Test auf Komponentenebene, **kein** Gherkin-Szenario. Ein zwischenzeitlich in `features/resilience.feature` eingefügter Schritt dafür wurde wieder entfernt.

**Verworfen:**
- **`route.fulfill()` als Normalfall** – billigste, aber unehrlichste Variante; testet gegen eine Erfindung.
- **Zweiter Stub-Server, der 500 liefert** – wirkt „echter", weil eigener Prozess, umgeht aber denselben Server, dessen Konfiguration geprüft werden soll. Kein Fake (kein Verhalten), nur ein Out-of-Process-Stub.
- **DB-Container stoppen** – erzeugte zwar einen echten Fehler, reißt aber die geteilte Dev-DB mit ab (`docker-compose.yml`: ein Postgres für `mahl` und `mahl_e2e`) und macht Folgetests kaputt.

**Grenze / offen:** Für „Backend nicht erreichbar" (F-NET) bleibt die Umsetzung offen; sie wird mit der Offline-Funktionalität entschieden (dann bevorzugt über einen Proxy, der die Verbindung real unterbricht). „Sitzung abgelaufen" (`@NFR-resilience-auth`) wird mit der Auth-Arbeit entschieden und braucht dann entweder eine begründete Konfigurations-Abweichung nach ADR-S112-2 (kurze Token-Lebensdauer) oder ein Test-Support-Mittel nach Punkt 2.

---

### ADR-S112-5: Querschnitts-Verhalten wird durch geteilte Implementierung garantiert, nicht durch wiederholte Szenarien

**Status:** Accepted
**Tags:** scope:cross-cutting, testing:e2e, frontend:react, arch:testing

**Kontext/Problem:** Verhalten wie Pending-Sperren, Undo-Toast oder Fokusführung ist nicht feature-spezifisch – es soll in **jeder** Liste und auf **jeder** Seite gleich sein. Die Konvention der Querschnitts-Feature-Dateien (`resilience.feature`, `interaction.feature`) lautet „eine Seite als Vertreter". Ein Vertreter belegt das Verhalten aber nur für seine eine Instanz; was die übrigen Seiten tun, ist damit nicht gesichert. Solange genau **eine** Liste existiert, fallen Vertreter und Gesamtheit zusammen – die Lücke entsteht erst mit der zweiten Seite (US-602).

**Entscheidung – vier Schichten, jede mit eigener Aufgabe:**

| Ebene | Mittel | Leistet |
|-------|--------|---------|
| Implementierung | geteilte Komponente/Hook (`useDeleteWithUndo<T>`, `<PendingButton>`) | verhindert Drift **durch Konstruktion** |
| Umgehungsschutz | Import-Guard (ESLint `no-restricted-imports`) | verhindert, dass Verhalten danebengebaut wird |
| Nachweis | eine Testsuite, parametrisiert über ein Page-Object-Interface je Seite | belegt Gleichverhalten dort, wo Konstruktion es nicht erzwingt |
| Geltungsbereich | Fähigkeits-Deklaration je Seite | nicht jede Seite zeigt jedes Querschnittsverhalten – jede deklariert, welche Verträge für sie gelten |

**Migrationsreihenfolge:** (1) Querschnitts-Szenarien identifizieren – erledigt S112. (2) Page-Object-Interface definieren. (3) Bestehende Tests in die parametrisierte Suite überführen. (4) Implementierung extrahieren. (5) Szenarien umziehen + umtaggen + Tests umbenennen. (6) Import-Guard setzen. **(2) und (3) sind vor der zweiten Seite machbar und werden vorgezogen** – sie strukturieren nur Testcode und erzeugen keine verfrühte Abstraktion im Produktionscode. (4) bis (6) gehören an die zweite Seite; (5) reist mit (4), damit Testnamen nur einmal angefasst werden.

**Verworfen:** *Szenario je Seite ohne geteilte Suite* – N-facher Aufwand, wächst mit jeder Seite und **entdeckt** Drift, statt ihn zu verhindern; genau das, was ADR-S103-1 für Navigation vermeiden wollte. *Konvention/Checkliste als alleinige Absicherung* – hängt daran, dass jemand liest und anwendet.

**Quellenlage (in S112 geprüft, mit unterschiedlichem Ergebnis):**
- *Shared Examples* – **belegt** (rspec.info): „Shared examples let you describe behaviour of classes or modules"; das Doku-Beispiel lässt eine Gruppe gegen `Array` **und** `Set` laufen. Das ist die Nachweis-Schicht unter ihrem etablierten Namen.
- *Architectural Fitness Function* – **belegt** (Thoughtworks Radar): „provides an objective integrity assessment of some architectural characteristics"; popularisiert in *Building Evolutionary Architectures*. Das ist die Umgehungsschutz-Schicht.
- *Page Object* – Definition **belegt** (martinfowler.com), die Verwendung als Parametrisierung für seitenübergreifende Testwiederverwendung jedoch **nicht**: Der Artikel behandelt das gegenteilige Anliegen. Diese Kombination ist eine Ableitung dieses Projekts, keine zitierbare Lehrmeinung.
- *„Contract Test"* wurde als Bezeichnung **verworfen** – Fowlers `ContractTest` prüft Test-Doubles gegen einen echten externen Service und meint etwas anderes.
- *Meszaros' „Abstract Test Case"* – **ungeprüft**, xunitpatterns.com ist nur über HTTP erreichbar.

**Grenze / offen:** Für `@CROSS-...`-Szenarien fehlt eine Testnamens-Konvention – `docs/process/e2e-testing.md` (Traceability) kennt nur US-Tags und verlangt sie in `:146` sogar ausdrücklich. Das betrifft bereits die vorhandenen `interaction.feature`-Szenarien und wird mit Schritt (5) entschieden.

---

## Offline-Sync-Strategie (US-306)

### ADR-S000-13: Offline-Sync-Strategie (US-306)

**Status:** Accepted
**Tags:** scope:feature, story:us-306, frontend:react, tooling:dependencies

**Entscheidung:** Service Worker via Workbox, IndexedDB für lokale Datenhaltung, Last-Write-Wins mit Nutzer-Transparenz als Konfliktlösung.

**Cache-Strategie:**
- Cache-First für Lesezugriffe
- Network-First mit Fallback für Schreiboperationen
- Background-Sync: Änderungen bei Reconnect synchronisieren

**Konfliktlösung:**
1. Jede Änderung bekommt einen Client-Timestamp
2. Bei Konflikt: Jüngerer Timestamp gewinnt + Toast "Deine Änderung wurde überschrieben. [Undo]"
3. Abhaken: kein Konflikt (deterministisch)
4. Additive Änderungen gewinnen über Delete/Reduce

**Polling:** Einkaufsliste prüft alle 3–5 Sekunden auf Server-Updates (nur wenn App im Vordergrund).

**Verworfen:** Merge-basierte Konfliktlösung – zu komplex für den MVP-Scope.

**Hinweis:** Service Worker funktioniert nur mit HTTPS (oder localhost in Dev).

---

## Test-Tooling Frontend

### ADR-S080-1: Testing-Library `jest-dom` + `user-event`

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:typescript, tooling:dependencies, testing:unit-test

**Entscheidung:** `@testing-library/jest-dom` und `@testing-library/user-event` als devDependencies. jest-dom registriert in `src/test/setup.ts` via `import '@testing-library/jest-dom/vitest'`.

**Begründung jest-dom:** DOM-aware Matcher (`toHaveValue`, `toBeInTheDocument` etc.) ersetzen Type-Casts wie `(el as HTMLInputElement).value` und liefern bei Fehlschlag das Element samt Ist-Wert statt nackter Primitiv-Diffs. Eigenbau (Vitest-`expect.extend` + Typdeklarationen + Diff-Ausgabe) liegt deutlich über 20 Zeilen und reimplementiert fehleranfällig den De-facto-Standard.

**Begründung user-event:** Simuliert vollständige Event-Sequenzen (`keydown→input→keyup` pro Zeichen) statt eines synthetischen Direkt-Setzens wie `fireEvent.change`. Deckt Bugs in Eingabe-Handlern auf, die `fireEvent` durchwinkt (disabled/readOnly-Felder, zeichenweise Filter-/Trim-Logik), erhöht die Stryker-Mutanten-Tötung auf Input-Pfaden und reduziert die Divergenz zu Playwright.

**Status der Pakete:** Beide aus der Testing-Library-Org (gleiche Maintainer wie das bereits genutzte `@testing-library/react`), aktiv gepflegt, kein `deprecated`-Flag, keine bekannte CVE (Snyk). jest-dom `6.9.1`, user-event `14.6.1`.

**Verworfen:** Status quo (Cast + `.value`, `fireEvent` für Eingaben) – dokumentierte Testschuld, schwache Fehlermeldungen, maskierte Handler-Bugs. Eigen-Matcher – Aufwand/Nutzen schlecht.

---

### ADR-S100-1: Autofokus im Dialog via `onEntered` – Fokus-Steal-Guard verworfen (nicht deterministisch testbar)

**Status:** Accepted
**Tags:** scope:feature, story:us-904, frontend:react, testing:stryker

**Kontext:** Der „Zutat anlegen"-Dialog soll beim Öffnen den Fokus aufs Name-Feld setzen (UX-Guideline Prinzip 8). `autoFocus` am TextField wird von echten Browsern ignoriert, weil MUIs Öffnen-Transition das Paper anfangs auf `visibility: hidden` setzt; der Fokus wird daher erst nach Transition-Ende via `slotProps.transition.onEntered` gesetzt.

**Entscheidung:** Der `onEntered`-Fokus wird **bedingungslos** gesetzt. Ein Guard „Fokus nur setzen, wenn der Nutzer nicht bereits ein Feld fokussiert hat" (gegen den theoretischen Race, dass extrem schnelles Tippen ins zweite Feld vor Transition-Ende durch den verzögerten Fokus zurückgerissen wird) wird **bewusst nicht** implementiert.

**Begründung:** Der Race ist real, aber (a) praktisch nicht auslösbar — beim Öffnen ist nichts fokussiert; um vor der ~225 ms-Transition ins zweite Feld zu tippen, müsste der Nutzer es erst fokussieren (Klick/Tab), was die Transition ohnehin überdauert; (b) der einzige bekannte Guard ist **nicht deterministisch testbar** — der „Guard-aus"-Mutant überlebt Stryker deterministisch (der Race ist timing-abhängig, kein Test zwingt das Verhalten reproduzierbar), was die 100%-Mutation-Disziplin (ADR-S041-8) bräche. Ungetesteter Band-Aid-Code über einem Timing-Race ist schlechter als die dokumentierte Akzeptanz.

**Verworfen:** Fokus-Steal-Guard (`if (document.activeElement?.tagName === 'INPUT') return`) — in Session 100 testweise gebaut und wieder entfernt: unerreichbarer `TEXTAREA`-Arm + deterministisch überlebender „Guard-aus"-Mutant. Wer ihn „hilfreich" wieder einbaut, bricht die 100%-Mutation-Disziplin.

**Testfolge:** Damit der verzögerte Autofokus die keystroke-basierten Komponenten-Tests nicht stört, warten diese vor dem ersten `user.type` auf den abgeschlossenen Autofokus (Helper `awaitDialogAutofocus` in `IngredientsPage.test.tsx`).

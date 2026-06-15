# Architecture Decision Records

<!--
wann-lesen: Bevor eine Entscheidung getroffen wird die bereits getroffene Entscheidungen
            berühren könnte. Vor dem Schreiben von Tags:
            `python3 .claude/scripts/decisions.py tags` ausführen – listet alle
            verwendeten Kategorien und Tags.
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

---

## API-Validierung & Fehlerbehandlung (alle Endpoints)

### ADR-S000-1: Collect-all Validation: kein Fail-Fast für unabhängige Felder

**Status:** Accepted
**Tags:** scope:cross-cutting, arch:validation, http:422

**Entscheidung:** Alle unabhängigen Felder werden vollständig validiert; alle Fehler werden gesammelt zurückgegeben (`422`, Body: `string[]`). Abhängige Validierungen (z.B. `unit` nur prüfen wenn `quantity` gesetzt) bleiben kurzschließend.

**Begründung:** Nutzer sollen alle ihre Fehler auf einmal sehen, nicht einen nach dem anderen.

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
| `defaultUnit` leer | `"Einheit darf nicht leer sein."` |
| `defaultUnit` zu lang (> 20 Zeichen) | `"Einheit darf maximal 20 Zeichen lang sein."` |
| `title` leer (Recipe) | `"Titel darf nicht leer sein."` |
| `ingredients` leer | `"Rezept muss mindestens eine Zutat haben."` |
| `steps` leer | `"Rezept muss mindestens einen Schritt haben."` |
| `sourceUrl` nicht absolut | `"Quell-URL muss eine absolute URI sein."` |
| `quantity` ≤ 0 | `"Menge muss größer als 0 sein."` |
| `unit` leer bei gesetzter `quantity` | `"Einheit darf nicht leer sein."` |
| `instruction` leer | `"Schritt-Anweisung darf nicht leer sein."` |
| `ingredientId` nicht gefunden/soft-deleted | `"Eine oder mehrere Zutaten wurden nicht gefunden."` |
| Restore: bereits aktiv | `"Zutat ist bereits aktiv."` |

---

## Ingredients-Endpoints

### ADR-S004-1: POST /api/ingredients – 409 bei soft-deleted: strukturiertes Objekt + Client-Orchestrierung

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, http:409, arch:error-handling

**Entscheidung:** `POST /api/ingredients` mit einem Namen, der bereits soft-deleted existiert, gibt `409 Conflict` zurück mit Body `{ "code": "ingredient_soft_deleted", "id": Guid }`. Aktiver Duplikat-Name liefert dagegen plain text: `"Eine Zutat mit dem Namen '{name}' existiert bereits."`.

Der Client erkennt den Code und ruft automatisch den Restore-Endpoint auf (transparent für den Nutzer).

**`{name}` in Duplikat-Fehlermeldung = Request-Wert (getrimmt):** Der interpolierte Name ist der Wert wie er im Request gesendet wurde (nach Trimming) – nicht der gespeicherte aktive Name. Beispiel: Request sendet `"tomaten"`, gespeicherter Wert ist `"Tomaten"` → Fehlermeldung: `"Eine Zutat mit dem Namen 'tomaten' existiert bereits."` Standard für Validierungsfehler: Fehler referenzieren die Eingabe, nicht den DB-Zustand.

**Begründung:** Das strukturierte Objekt ermöglicht dem Frontend, den `id`-Wert auszulesen und einen "Wiederherstellen"-CTA anzubieten, ohne Text parsen zu müssen.

**Verworfen:** Transparentes Server-seitiges Reaktivieren – bricht POST-Semantik, zwei Pfade in einem Endpoint.
**Verworfen:** Immer 409 ohne Restore-Möglichkeit – Sackgasse für den Nutzer.
**Verworfen:** Neu anlegen neben soft-deletem Eintrag – erzeugt stille Inkonsistenz (zwei "Butter"-Einträge mit verschiedenen IDs).

---

### ADR-S051-3: Ingredient-Feldregeln: max. Länge, Case-Insensitivität, kein Auto-Capitalize

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, arch:validation

**Entscheidung:**
- `name`: max. 30 Zeichen (nach Trimming gemessen). Case-insensitiver Duplikat-Check: `"Tomaten"` und `"tomaten"` gelten als dieselbe Zutat. Kein Auto-Capitalize – gespeichert wird exakt der getippte Wert nach Trimming (z.B. `"tomaten"` bleibt `"tomaten"`).
- `defaultUnit`: max. 20 Zeichen (nach Trimming gemessen).

**Begründung max. Länge:** Keine realen deutschen Zutaten- oder Einheitenbezeichnungen überschreiten diese Grenzen. Verhindert UI-Überlauf.

**Begründung case-insensitiv:** Zutaten sind fachlich identisch unabhängig von Groß-/Kleinschreibung. Nutzer können Schreibfehler nachträglich korrigieren (Update-Vorgang).

---

### ADR-S051-4: Restore via POST /api/ingredients: übernimmt Name und Einheit aus Request

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, db:soft-delete

**Entscheidung:** Wenn `POST /api/ingredients` eine soft-deleted Zutat trifft und der Client daraufhin `POST /api/ingredients/{id}/restore` aufruft, übernimmt der Restore-Endpoint den `name` und die `defaultUnit` aus dem ursprünglichen POST-Request. Die Zutat erscheint anschließend mit dem neuen Namen und der neuen Einheit.

**Parallelfall (Restore antwortet 409 "bereits aktiv"):** Der Client zeigt die Zutat ohne Fehlerhinweis als aktiv an. Name und Einheit der bereits aktiven Zutat sind nicht kontrollierbar (hängen vom parallelen Restore ab) – daher kein Guarantee über die angezeigte Einheit.

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

**Entscheidung:** `POST /api/ingredients` antwortet bei Erfolg mit `201 Created`, Body `{ "id": Guid, "name": string, "defaultUnit": string }` und `Location: /api/ingredients/{id}`.

**Begründung:** Body vermeidet einen zweiten GET-Request im Client. Location ist REST-konform. `defaultUnit` statt `unit` für Konsistenz mit dem Domänenmodell.

**Verworfen:** 201 ohne Body – Client müsste sofort GET /api/ingredients aufrufen, um die neue Zutat zu kennen.
**Verworfen:** 200 OK – verletzt REST-Semantik für Ressourcen-Erstellung.

---

### ADR-S000-3: GET /api/ingredients – soft-delete filter: Stryker-Suppression

**Status:** Accepted – **noch nicht implementiert** (geplant für das Soft-Delete-/Löschen-Szenario)
**Tags:** scope:feature, resource:ingredients, http:get, testing:stryker, db:soft-delete

**Entscheidung:** `// Stryker disable once Equality` auf der `Where(i => i.DeletedAt == null)` Zeile in `IngredientsEndpoints.cs`.

**Begründung:** In den happy-path-Tests existieren keine soft-deleted Einträge – die DB ist leer oder enthält nur aktive Einträge. Damit ist `== null` und `!= null` im Testkontext äquivalent (beide liefern das gleiche Ergebnis). Das Verhalten mit soft-deleted Einträgen wird durch ein dediziertes Soft-Delete-Szenario (künftiger Zyklus) getestet. Keine Vorabtestung außerhalb des vorgesehenen Szenarios.

**Stand US-904 Happy-Path (Session 083):** Weder die `DeletedAt`-Spalte (`IngredientDbType`) noch der `Where`-Filter existieren bislang – bewusst YAGNI, da noch kein Soft-Delete-/Löschen-Szenario implementiert ist. Diese ADR beschreibt die **geplante** Suppression, die zusammen mit der `DeletedAt`-Spalte im Soft-Delete-Zyklus eingeführt wird. Bis dahin liefert `GET /api/ingredients` bewusst ungefiltert alle Rows. Kein Code-↔-ADR-Drift, sondern dokumentierte Reihenfolge.

---

### ADR-S000-4: POST /api/ingredients – Validierungs-Fehlermeldungsstrings: Stryker-Suppression

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:post, testing:stryker, arch:validation

**Entscheidung:** `// Stryker disable once String` auf den beiden `NonEmptyTrimmedString.Create(...)` Aufrufen mit Fehlermeldungs-Strings in `IngredientsEndpoints.cs`.

**Begründung:** Die Fehlerpfade (ungültiger `name` / `defaultUnit`) werden bewusst erst im @US-904-error Szenario getestet. Die Strings sind korrekt und notwendig, aber der happy-path-Testlauf ruft diese Pfade nicht auf. Eine Vorabtestung der Fehlermeldungen in diesem Szenario würde das Single-Responsibility-Prinzip der Szenarien verletzen.

---

### ADR-S083-1: GET /api/ingredients – Read-Pfad mappt DB→DTO direkt (ToDomain aufgeschoben)

**Status:** Accepted
**Tags:** scope:feature, resource:ingredients, http:get, arch:domain-type, arch:error-handling

**Entscheidung:** Der Happy-Path-`GET /api/ingredients` projiziert `IngredientDbType` **direkt** auf `IngredientDto` (`db.Ingredients.Select(i => new IngredientDto(i.Id, i.Name, i.DefaultUnit))`), ohne den Read-Pfad `DbType → ToDomain() → OneOf<Ingredient, Error> → DTO`. Eine `ToDomain()`-Funktion und das Skip-/Log-Verhalten für korrupte DB-Rows werden **nicht** in diesem Zyklus implementiert.

**Begründung:** Der `ToDomain()`-Roundtrip führt einen DB-Inkonsistenz-Fehlerzweig ein (z.B. leerer `Name` in der DB → `NonEmptyTrimmedString.Create` schlägt fehl), den der Happy-Path nicht ausübt und für den keine genehmigte Suppression vorliegt – er würde einen Stryker-Survivor erzeugen oder eine Vorab-Suppression außerhalb des vorgesehenen Szenarios erzwingen. Der DB-Inkonsistenz-Pfad (Skip+Log bei Listen, 500 bei Einzel-Ressource) gehört in ein dediziertes DB-Inkonsistenz-Szenario – analog zur bereits getroffenen Entscheidung für Recipes (ADR-S039-3). Bewusste Abweichung von der kanonischen Read-Pfad-Architektur (architecture.md 4b) für den SKELETON-Happy-Path, hier dokumentiert (Doku-Pflicht für Abweichungen).

**Verworfen:** `ToDomain()`-Read-Pfad jetzt + Suppression auf dem ungeübten Inkonsistenz-Zweig – Vorabtestung/Suppression außerhalb des treibenden Szenarios.

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

**Verworfen:** Ternary – besser für Coverage, schlechter für Korrektheit bei Erweiterungen.
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

### ADR-S001-1: Frontend-Framework: React 18+ mit Material UI v7

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:react, frontend:typescript, tooling:dependencies

**Entscheidung:** React 18+ mit MUI v7 (Material Design 3).

**Begründung:** MUI v7 bietet vollständigen MD3-Support (stabil). Offline-Support (US-306) ist MVP – React-Ökosystem überlegen (Workbox, React Query). Mutation Testing mit Stryker-JS etabliert.

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

---

### ADR-S083-2: useResultQuery/useResultMutation – minimale Modellierung (YAGNI), volle Union aufgeschoben

**Status:** Accepted
**Tags:** scope:cross-cutting, frontend:typescript, frontend:hooks, frontend:react

**Entscheidung:** Die Hooks `useResultQuery`/`useResultMutation` (`Client/src/hooks/`) werden zunächst **minimal** modelliert: `useResultQuery` liefert `TData | undefined` (nur success-Zweig); `useResultMutation` liefert `(vars) => void` + `onSuccess`-Callback (nur Erfolgs-Seiteneffekt). Es gibt **kein** vollständiges `MutationState`-Discriminated-Union (`idle|pending|success|error`), **kein** `matchState()`/`matchKind()` und **kein** `throwOnError: true` – abweichend von der kanonischen Spezifikation in `coding-guideline-typescript.md` Abschnitt 4b und ADR-S056-1.

**Begründung:** Eingeführt im US-904-Happy-Path „Zutat anlegen" (Session 083). Dieses Szenario übt nur den success-Pfad aus (befüllte Liste rendern, nach POST invalidieren). Eine volle Union würde unausgeübte `pending`/`error`/`idle`-Zweige erzeugen → Stryker-Survivors → Suppressions außerhalb des treibenden Szenarios. Bewusste YAGNI-Entscheidung des Nutzers, um genau diese Suppressions zu vermeiden. Die Erweiterung auf die volle Union + `matchState` + `throwOnError` erfolgt mit den Szenarien, die sie ausüben: „Speichern-Button deaktiviert während des Speicherns" (pending) und die @US-904-error-Szenarien (error).

**Bekannte Konsequenzen (technische Schuld bis zur Erweiterung):** (1) Name-Kollision mit den kanonischen Wrappern – ein Leser der Guideline erwartet das `MutationState`-Tupel. (2) `onSuccess` feuert auch bei einem `Err`-Result, da `Promise.resolve(ResultAsync)` den `Err` nicht wirft – im success-only-Happy-Path harmlos, aber vor dem Error-Szenario auf `result.match(onSuccess, onError)` umzustellen. (3) Fehlendes `throwOnError` → bei Netzwerkfehler bliebe `query.data` undefined und der Empty-State würde fälschlich gerendert.

**Verworfen:** Volle 4er-Union jetzt – erzeugt unausgeübte Zweige + Suppressions vor dem treibenden Szenario (widerspricht der Suppression-Minimierung).

**Begründung:** Bring! ist im Familienshopping-Kontext etabliert und auf Touch-Geräten gut bedienbar. US-304 (Visuelle Darstellung & Varianten) wurde aufgelöst, weil das Layout kein Feature-Increment ist, sondern ein Designprinzip – die Kachel-Entscheidung fällt einmalig und ist kein eigenständiges Implementierungsticket.

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

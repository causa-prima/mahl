# Technische Entscheidungen

<!--
wann-lesen: Wenn unklar ist warum etwas so implementiert wurde, oder bevor eine ähnliche Entscheidung getroffen wird
kritische-regeln:
  - Jede selbst getroffene technische Entscheidung (Validierungsregeln, Error Codes, Schema-Details) hier dokumentieren
  - Format: Kontext → Entscheidung → Begründung → Verworfen
-->

> Archiv aller getroffenen technischen Entscheidungen. Bei Fragen "Warum wurde X so entschieden?" hier nachschlagen.
> Historisch überholte Einträge: `docs/history/decisions-archive.md`

---

## Schnell-Zugriff nach Aufgabe

| Aufgabe | Relevante Abschnitte |
|---------|----------------------|
| `POST /api/ingredients` implementieren | [API-Validierung](#api-validierung--fehlerbehandlung), [Ingredients-Endpoints](#ingredients-endpoints), [Datenbank](#datenbank--persistenz) |
| `POST /api/recipes` implementieren | [API-Validierung](#api-validierung--fehlerbehandlung), [Recipes-Endpoints](#recipes-endpoints), [Domain-Typen](#domain-typen--sum-types) |
| DELETE-Endpoint implementieren | [Ingredients-Endpoints – DELETE-Semantik](#delete-semantik-404-vs-idempotent-204) |
| WeeklyPool-Endpoint implementieren | [WeeklyPool-Endpoints](#weeklypool-endpoints), [API-Validierung](#api-validierung--fehlerbehandlung) |
| Domain-Typ / Sum-Type schreiben | [Domain-Typen & Sum-Types](#domain-typen--sum-types) |
| E2E-Test / Gherkin-Szenario schreiben | [Architektur & Prozess](#architektur--prozess) |
| Frontend-Komponente schreiben | [Frontend & TypeScript](#frontend--typescript) |
| Mutation Testing / Stryker konfigurieren | [Test-Tooling & Stryker](#test-tooling--stryker) |

---

## Architektur & Prozess

### Hexagonal Architecture / Ports & Adapters

**Entscheidung:** Die Anwendung ist ein Hexagon mit klar definierten Ports: HTTP-Endpoints (eingehender Port) und DbContext (ausgehender Port). Tests exercisen die Anwendung ausschließlich über diese Ports – kein direkter Zugriff auf Server-Interna aus Tests.

**Verworfen:** Black-Box-Tests via InternalsVisibleTo – verletzt das Prinzip, da interne Typen direkt referenziert werden.

---

### Infrastructure Layer als eigenes Projekt (mahl.Infrastructure)

**Entscheidung:** `MahlDbContext` und alle `*DbType`-Klassen ziehen in ein eigenes Projekt `mahl.Infrastructure` (public by design – sie sind der ausgehende Port). `mahl.Server` (Endpoints, Domain, DTOs) bleibt vollständig internal. Kein `InternalsVisibleTo` nötig – Tests referenzieren `mahl.Infrastructure` direkt.

**Verworfen:** `InternalsVisibleTo` – "fake encapsulation"; verletzt das Prinzip, während es Compliance vortäuscht.

---

### Domain-Typen sind internal, keine direkten Unit-Tests

**Entscheidung:** Alle Domain-Typen sind `internal`. Keine dedizierten Unit-Tests für Domain-Typen – ihr Verhalten wird vollständig über Endpoint-Integration-Tests abgedeckt. In einer Application (nicht Library) ist die HTTP-API die öffentliche Schnittstelle, nicht die Domain-Klassen.

---

### BDD/Gherkin als Standard für E2E-Tests

**Entscheidung:** `.feature`-Dateien (Gherkin) sind die **dokumentarische** Spec – kein separates Spec-Dokument, kein BDD-Runner. Playwright (TypeScript) ist der ausführbare äußere Loop und trägt `@US-ID`-Tags im describe/test-Namen.

**Verworfen:** SpecFlow/Reqnroll – läuft nur in C#, kann damit nur die API testen, nicht das Full-Stack-Nutzerverhalten. Für das TypeScript-Frontend wäre trotzdem Playwright nötig → zwei parallele Test-Stacks mit demselben Gherkin, unlösbarer Stack-Mismatch.
**Verworfen:** Separate Spec-Dokumente + handgeschriebene Tests – erzeugt unvermeidliche Divergenz.

---

### Outside-In ATDD / Double-Loop TDD

**Entscheidung:** Die Reihenfolge ist immer: Gherkin-Szenario (E2E, rot) → Frontend-Test (rot) → Backend-Integration-Test (rot) → Backend-Code (grün). Das Gherkin-Szenario wird zuerst geschrieben – auch wenn das Frontend noch nicht existiert. Kein Backend-Test darf existieren, ohne dass ein darüberliegender Test ihn fordert.

---

### E2E Quality Gate: Spec-driven Checklist (nicht Coverage-Metrik)

**Entscheidung:** Quality Gate für E2E-Tests = Spec-driven Checklist: Für jede User Story min. 1 Happy-Path-Szenario, für jede Rejection-Regel min. 1 Rejection-Szenario, für jeden Fehlerfall min. 1 Error-Szenario. Verifiziert via `@US-ID`-Tags + CI-Skript.

**Klarstellung Coverage:** 100% Branch/Line-Coverage wird projektübergreifend gehalten. Was abgelehnt wurde: ein *separater* Coverage-Gate exklusiv für E2E-Tests.

**Verworfen:** Separater Branch/Line-Coverage-Gate für E2E-Tests – misst Ausführung statt Korrektheit.

---

### Bidirektionale Traceability: Spec ↔ Test

**Entscheidung:** Zwei-Richtungs-Prüfung: (1) Spec → Test: Gate schlägt fehl wenn Spec-Eintrag kein Szenario hat. (2) Test → Spec: CI-Check verifiziert dass jeder `@US-ID`-Tag auf einen gültigen Spec-Eintrag zeigt.

---

## API-Validierung & Fehlerbehandlung (alle Endpoints)

### Collect-all Validation: kein Fail-Fast für unabhängige Felder

**Entscheidung:** Alle unabhängigen Felder werden vollständig validiert; alle Fehler werden gesammelt zurückgegeben (`422`, Body: `string[]`). Abhängige Validierungen (z.B. `unit` nur prüfen wenn `quantity` gesetzt) bleiben kurzschließend.

**Begründung:** Nutzer sollen alle ihre Fehler auf einmal sehen, nicht einen nach dem anderen.

---

### Strings trimmen vor Validierung, getrimmten Wert speichern

**Entscheidung:** Alle String-Felder werden im Request-Handler vor der Validierung getrimmt. Gespeichert wird der getrimmte Wert. Ein String der nach Trimming leer ist, verletzt die Nicht-Leer-Constraint.

---

### 422-Fehlermeldungstexte (Deutsch, spezifisch, unveränderlich)

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

### POST /api/ingredients – 409 bei soft-deleted: strukturiertes Objekt + Client-Orchestrierung

**Entscheidung:** `POST /api/ingredients` mit einem Namen, der bereits soft-deleted existiert, gibt `409 Conflict` zurück mit Body `{ "code": "ingredient_soft_deleted", "id": Guid }`. Aktiver Duplikat-Name liefert dagegen plain text: `"Eine Zutat mit dem Namen '{name}' existiert bereits."`.

Der Client erkennt den Code und ruft automatisch den Restore-Endpoint auf (transparent für den Nutzer).

**`{name}` in Duplikat-Fehlermeldung = Request-Wert (getrimmt):** Der interpolierte Name ist der Wert wie er im Request gesendet wurde (nach Trimming) – nicht der gespeicherte aktive Name. Beispiel: Request sendet `"tomaten"`, gespeicherter Wert ist `"Tomaten"` → Fehlermeldung: `"Eine Zutat mit dem Namen 'tomaten' existiert bereits."` Standard für Validierungsfehler: Fehler referenzieren die Eingabe, nicht den DB-Zustand.

**Begründung:** Das strukturierte Objekt ermöglicht dem Frontend, den `id`-Wert auszulesen und einen "Wiederherstellen"-CTA anzubieten, ohne Text parsen zu müssen.

**Verworfen:** Transparentes Server-seitiges Reaktivieren – bricht POST-Semantik, zwei Pfade in einem Endpoint.
**Verworfen:** Immer 409 ohne Restore-Möglichkeit – Sackgasse für den Nutzer.
**Verworfen:** Neu anlegen neben soft-deletem Eintrag – erzeugt stille Inkonsistenz (zwei "Butter"-Einträge mit verschiedenen IDs).

---

### Ingredient-Feldregeln: max. Länge, Case-Insensitivität, kein Auto-Capitalize

**Entscheidung:**
- `name`: max. 30 Zeichen (nach Trimming gemessen). Case-insensitiver Duplikat-Check: `"Tomaten"` und `"tomaten"` gelten als dieselbe Zutat. Kein Auto-Capitalize – gespeichert wird exakt der getippte Wert nach Trimming (z.B. `"tomaten"` bleibt `"tomaten"`).
- `defaultUnit`: max. 20 Zeichen (nach Trimming gemessen).

**Begründung max. Länge:** Keine realen deutschen Zutaten- oder Einheitenbezeichnungen überschreiten diese Grenzen. Verhindert UI-Überlauf.

**Begründung case-insensitiv:** Zutaten sind fachlich identisch unabhängig von Groß-/Kleinschreibung. Nutzer können Schreibfehler nachträglich korrigieren (Update-Vorgang).

---

### Restore via POST /api/ingredients: übernimmt Name und Einheit aus Request

**Entscheidung:** Wenn `POST /api/ingredients` eine soft-deleted Zutat trifft und der Client daraufhin `POST /api/ingredients/{id}/restore` aufruft, übernimmt der Restore-Endpoint den `name` und die `defaultUnit` aus dem ursprünglichen POST-Request. Die Zutat erscheint anschließend mit dem neuen Namen und der neuen Einheit.

**Parallelfall (Restore antwortet 409 "bereits aktiv"):** Der Client zeigt die Zutat ohne Fehlerhinweis als aktiv an. Name und Einheit der bereits aktiven Zutat sind nicht kontrollierbar (hängen vom parallelen Restore ab) – daher kein Guarantee über die angezeigte Einheit.

---

### DELETE /api/ingredients/{id}: UI-Fehlermeldung bei 404

**Entscheidung:** `DELETE /api/ingredients/{id}` antwortet mit 404 wenn die Zutat nicht existiert oder bereits soft-deleted ist. UI-Fehlermeldungstext: `"Zutat wurde nicht gefunden."`

---

### Check-Reihenfolge POST /api/ingredients: soft-deleted vor active-duplicate

**Entscheidung:** Soft-deleted-Check läuft **vor** Active-Duplicate-Check. Dadurch ist es über die API nicht möglich, eine aktive Zutat mit demselben Namen wie eine soft-deleted Zutat anzulegen – der Caller bekommt immer zuerst den 409-Restore-Hinweis.

---

### DELETE-Semantik: 404 vs. idempotent 204

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

### StepNumber: serverside vergeben, nicht im DTO

**Entscheidung:** `StepNumber` wird vom Server als `(Index + 1)` der eingehenden Steps-Liste vergeben (1-basiert). Es erscheint ausschließlich in der DB-Entität (`Step.StepNumber`) und zur Sortierung. Es ist **nicht** Teil des Domain-Objekts und **nicht** Teil des `StepDto` – das DTO enthält nur `instruction`.

**Begründung:** Clients senden eine geordnete Liste – die Listenposition ist die Reihenfolge. Eine separate `stepNumber`-Angabe wäre redundant und fehleranfällig (Inkonsistenz zwischen Listenposition und Wert möglich).

---

### Quantity: `Quantity`-Sum-Type, NULL = "nach Geschmack"

**Entscheidung:** `RecipeIngredient.Quantity` ist ein `Quantity`-Sum-Type mit zwei Varianten: `PositiveDecimal` und `Unspecified`. `Unspecified` bedeutet "nach Geschmack" / Menge nicht angegeben. 0 ist kein gültiger Wert. `Unit` ist ebenfalls `Unspecified` wenn `Quantity` `Unspecified` ist, ansonsten NOT NULL.

In der DB: `decimal(7,3)?`, NULL = `Unspecified`. `decimal?` als **Parameter** von `Create()` bleibt erlaubt (Systemgrenze zu DTO/Primitives).

Generierungslogik: `Unspecified` = 0 bei Aggregation; wenn alle `Unspecified` → Ergebnis `Unspecified`.

**Verworfen:** `Quantity = 0` als Sentinel – 0 ist ein valider Eingabefehler, kein fachlicher Zustand.
**Verworfen:** `decimal?` als Domain-Property-Typ – verletzt "Make Illegal States Unrepresentable".

---

### RecipeSource: Mutual Exclusion zwischen URL und Bild

**Entscheidung:** Ein Rezept kann entweder eine `SourceUrl` (externe URL) oder ein Quellbild (`HasSourceImage = true`) haben, nie beides. In Request und Response sind `sourceUrl` und `sourceImageBase64`/`sourceImageUrl` gegenseitig exklusiv.

---

### `System.Uri` als BCL-Primitive in `Create()`-Parametern

**Entscheidung:** `System.Uri` wird direkt als Parameter in `Recipe.Create(Uri? sourceUrl)` akzeptiert. `new Uri("")` wirft `UriFormatException`, `new Uri(null)` wirft `ArgumentNullException` – ein leeres/null Uri-Objekt ist nicht konstruierbar. Fachliche Invarianten (Absolutheit) werden per Guard in `Create()` geprüft.

**Verworfen:** `NonEmptyUri` als eigener Typ – unnötig, da `Uri` die strukturelle Garantie bereits mitbringt.

**Tech Debt:** Verhalten des JSON-Deserializers bei syntaktisch ungültigem URI-String nicht verifiziert (400 oder 500? → erst ab US-602 relevant).

---

### STJ serialisiert `Uri` via `OriginalString` – Round-Trip ohne Normalisierung

**Entscheidung:** `url.OriginalString` in `explicit operator string?` für das DB-Mapping. STJ nutzt intern ebenfalls `OriginalString` zur Serialisierung. Round-Trip konsistent: POST-Body `"https://example.com"` → DB → GET-Response `"https://example.com"`.

**Verworfen:** `url.AbsoluteUri` – normalisiert beim Speichern (`"https://example.com"` → `"https://example.com/"`), Originalstring des Clients geht verloren.

---

### `GET /api/recipes`: 500 bei korrupter DB-URL (kein silent null)

**Entscheidung:** `GetAll` und `GetById` liefern `500` + `application/problem+json` wenn eine `SourceUrl` in der DB korrupt ist (`ToSummaryDtoOrError()` + `Sequence()`). `null` hat keinen validen semantischen Wert – "korrupte Daten ignorieren" wurde abgelehnt.

---

## WeeklyPool-Endpoints

### POST /api/weekly-pool: 422 (nicht 404) bei Rezept nicht gefunden

**Entscheidung:** `POST /api/weekly-pool/recipes/{recipeId}` antwortet mit `422`, wenn das Rezept nicht existiert oder soft-deleted ist – nicht mit `404`. Der Request ist semantisch ungültig (ungültige `recipeId`), nicht "Ressource nicht gefunden". Konsistent mit Collect-all-Validation-Konvention für referenzielle Integrität.

---

### WeeklyPool: Keine Duplikate (409 bei bereits enthaltenem Rezept)

**Entscheidung:** `POST /api/pool` mit einem Rezept das bereits im Pool ist → `409 Conflict`.

**Begründung:** Im Familienkontext ist ein doppeltes Rezept in der Wochenplanung wahrscheinlicher ein Versehen als Absicht. Bewusste Einschränkung, kein fachliches Gesetz.

---

## Datenbank & Persistenz

### UUIDv7 für alle Primärschlüssel (serverside generiert)

**Entscheidung:** Alle PKs sind `Guid` (UUIDv7, serverside generiert via `Guid.CreateVersion7()`). Keine client-seitigen IDs, keine `int`-Autoincrement-Schlüssel.

**Begründung:** Zeitlich sortierbar (monoton steigend), kein DB-Sequenz-Contention, ID-Generierung ohne DB-Roundtrip.

**Verworfen:** UUIDv4 – nicht sortierbar (Index-Fragmentierung). `int` – vorhersagbar (Security), Migrations-schwierig.

---

### Soft-Delete: `DeletedAt` (timestamptz?) statt `IsDeleted` (bool)

**Entscheidung:** Soft-Delete wird via `DeletedAt`-Timestamp implementiert, nicht via `IsDeleted`-Bool.

**Begründung:** Enthält mehr Information (wann gelöscht?), ermöglicht Audit-Queries und automatisches Aufräumen.

---

## Domain-Typen & Sum-Types

### Sum-Type-Design: private Subtypen, `Match<T>` als einzige Schnittstelle

**Entscheidung:** Zwei erlaubte Varianten:

- **Variante A – verschachtelte `private` Subtypen:** Stärkste Kapselung. `private SumType() { }` verhindert jede externe Ableitung. Standard für Wert-Träger-Sum-Types (reine Zustandscontainer).
- **Variante B – `file`-scoped Subtypen + `private protected` Konstruktor:** Wenn alle Operationen als Extension Methods in derselben Datei geführt werden sollen. `private protected` statt `private`, weil top-level `file`-Records keinen privaten Basiskonstruktor aufrufen können.

`Match<T>` ist immer die **einzige** öffentliche Schnittstelle für Consumer. **public** für Wert-Träger-Sum-Types (Mapping-Layer braucht Zugriff), **internal** für operationale Sum-Types.

Konvertierungsoperatoren: `implicit` wenn verlustfrei und reversibel, `explicit` wenn Information verloren geht.

**Verworfen:** Öffentliche Subtypen – keine Exhaustiveness-Garantie, externe Subtypen möglich.
**Verworfen:** `internal` Subtypen – gesamtes Assembly kann subtypen, keine strukturelle Garantie.

---

### Switch + `SumType.Unreachable<T>()` als einziges erlaubtes Dispatch-Pattern

**Entscheidung:**
1. `Match<T>` nutzt immer `switch` mit `_ => SumType.Unreachable<T>()`. Der Helper `SumType.Unreachable<T>()` liegt in `Server/Types/SumType.cs` – Stryker-Suppress einmal dort, nicht in jeder Implementierung.
2. Kein Ternary (`this is X u ? ... : ...`) – bei einer neuen Variante die in `Match<T>` vergessen wird, ruft Ternary still den falschen Arm auf; Switch wirft klar.
3. `[ExcludeFromCodeCoverage]` auf `Match<T>` (strukturell unerreichbarer `_`-Arm).

**Verworfen:** Ternary – besser für Coverage, schlechter für Korrektheit bei Erweiterungen.
**Verworfen:** Switch ohne `_`-Arm – Coverlet trackt die compiler-generierte `throw new SwitchExpressionException()`-Branch auf IL-Ebene, Branch Coverage fällt auf ~98%. Kein Gewinn gegenüber dem expliziten `_`-Arm.

---

### Äquivalenter Mutant: `"Unreachable."` String in Sum-Type Match

**Entscheidung:** Der `_ => throw new InvalidOperationException("Unreachable.")` Zweig in Sum-Type `Match`-Methoden ist strukturell nie erreichbar. Stryker-String-Mutation auf diesem String ist ein äquivalenter Mutant. Exclusion per `// Stryker disable once StringMutation` direkt über der Zeile.

**Gilt für:** Alle `_ => throw new InvalidOperationException("Unreachable.")` Zeilen in Sum-Type `Match`-Implementierungen (`RecipeSource.cs`, `Quantity.cs`, und zukünftige Sum-Types).

---

### S4581: `== default` statt `== Guid.Empty` für uninitialisierten Guid-Guard

**Entscheidung:** In Domain-Typen mit `readonly record struct` + `Guid`-Backing-Feld bleibt `_id == default` erlaubt und wird per `#pragma warning disable S4581` suppressiert. `default` signalisiert "strukturell uninitialisiert" – semantisch identisch mit `== Guid.Empty`, aber sprachlich präziser.

**Einschränkung:** Diese Suppression ist **nur** für uninitialisierten Value-Type-Guard erlaubt. S4581 an anderen Stellen muss evaluiert werden – dort kann es auf einen echten Bug hinweisen.

---

## Frontend & TypeScript

### Frontend-Framework: React 18+ mit Material UI v7

**Entscheidung:** React 18+ mit MUI v7 (Material Design 3).

**Begründung:** MUI v7 bietet vollständigen MD3-Support (stabil). Offline-Support (US-306) ist MVP – React-Ökosystem überlegen (Workbox, React Query). Mutation Testing mit Stryker-JS etabliert.

**Verworfen:** Blazor WebAssembly. Vue 3 + Vuetify. Svelte – kein MUI-Äquivalent (Svelte Material UI implementiert MD2, nicht MD3); Svelte 5 Runes sind explizit mutationsbasiert, Immutability-Kernprinzip würde gegen das Framework laufen.

---

### TypeScript ROP-Bibliothek: `neverthrow`

**Entscheidung:** `neverthrow`. API: `.andThen()`, `.match()`. 1M+ wöchentliche npm-Downloads, beste Community-Dokumentation.

**Risiko:** Maintenance verlangsamt sich (viele offene PRs). Bevorzugter Nachfolger: `@praha/byethrow` (serialisierbare Results, API-nah).

**Verworfen:** `effect` – Komplexität und Bundle-Größe übersteigen den Scope. `fp-ts` – akademisch, steile Lernkurve.

---

### Einheiten-Konvention: Frontend normalisiert auf Basiseinheit

**Entscheidung:** Das Frontend normalisiert Mengenangaben auf metrische Basiseinheiten (Gewicht → g, Volumen → ml) vor dem API-Aufruf. Das Backend empfängt und speichert **immer** die Basiseinheit. Nicht-metrische Einheiten (EL, TL, Stück, Prise etc.) werden als Freitext gespeichert, unverändert.

**Begründung:** US-902 (Einheiten-Management mit Umrechnungsfaktoren) ist MVP. Bis dahin einfachste Lösung ohne Backend-Logik.

---

### Bildformat: WEBP (nicht JPG), Format-Erkennung via Magic Bytes

**Entscheidung:** Server konvertiert hochgeladene Bilder serverseitig zu WEBP. Pfadkonvention: `/uploads/recipe-sources/{recipeId}/original.webp` (deterministisch aus Recipe-ID ableitbar). Format-Erkennung via Magic Bytes – kein expliziter `Content-Type` oder Typ-Parameter im Request nötig.

**Verworfen:** `original.jpg` – WEBP bietet signifikant bessere Kompression bei gleicher Qualität. Expliziter Typ-Parameter – Client/Server-Inkonsistenz wenn Client falschen Typ angibt.

---

## Test-Tooling & Stryker

### Mutation Testing Ziel: 100%

**Entscheidung:** Ziel ist 100% Mutation Score. Strukturell unerreichbarer Code (z.B. `_ => throw` in Sum-Type-Switch-Default) wird mit begründeten Suppressions behandelt, nicht mit gesenktem Zielwert. Die Praxis hat gezeigt, dass 100% realistisch erreichbar ist.

---

### Defensive Guards: kein Test, Stryker disable mit Begründung

**Entscheidung:** Guards wie parameterloser Konstruktor (`throw`) und `default(T)`-Property-Guards schützen gegen Sprachmissbrauch (Framework-Magie, versehentliches `new T()`). Sie sind strukturell unerreichbar. Kein Test. `// Stryker disable once` mit expliziter Begründung: `"Guard against language/framework misuse – unreachable via external interfaces"`.

---

### Stryker `additional-timeout`: 15000ms (statt Default 5000ms)

**Entscheidung:** `additional-timeout: 15000` in `stryker.conf.json`.

**Begründung:** Bei Partial-Runs (`--mutate Domain/Foo.cs`) traten Timeout-Mutanten auf, die keine echten Kills waren. Strykers Timeout-Formel `baseline × 1.5 + additional-timeout` liefert bei kurzer Partial-Run-Baseline (~15s) nur ~27.5s. Integration-Tests mit WebApplicationFactory-Start + DB-Verbindung haben variable Laufzeiten. 15000ms erhöht den Puffer auf ~32.5s ohne Auswirkung bei echten Infinite-Loop-Mutations.

---

### Stryker `coverage-analysis: "off"` für Integration-Tests

**Entscheidung:** `coverage-analysis: "off"` in `stryker.conf.json`.

**Begründung:** `coverage-analysis` instrumentiert den Code um festzustellen welche Tests welche Mutanten abdecken. Für Tests mit `WebApplicationFactory` funktioniert das nicht – die Instrumentierung überlebt den Out-of-Process-Start nicht.

---

## Code-Qualität & Abhängigkeiten

### CA1515: `internal`-Pflicht via Analyzer erzwungen

**Entscheidung:** CA1515 (`warning`) in `.editorconfig` für `{Server,Server/**}/*.cs`. Erzwingt die in `CODING_GUIDELINE_CSHARP.md` beschriebene `internal`-Pflicht statisch – Compiler blockiert `public`-Typen in `Server/`.

---

### AwesomeAssertions statt FluentAssertions

**Entscheidung:** `AwesomeAssertions` (Apache 2.0, permanent). Identisches API zu FluentAssertions v7 – Drop-in-Ersatz ohne Lizenzrisiko.

**Begründung:** FluentAssertions v8 wechselte zu kommerzieller Xceed-Lizenz. AwesomeAssertions entstand als Community-Fork auf Basis der letzten Apache-2.0-Commits.

**Verworfen:** FluentAssertions v7 – nur noch Security-Updates. FluentAssertions v8 – kostenpflichtige Lizenz.

---

### xUnit v3 (`xunit.v3`) statt v2

**Entscheidung:** `xunit.v3`. Modernere Architektur (Test-Projekte als standalone Executables), bessere Async-Unterstützung, aktive Entwicklung.

**Verworfen:** xUnit v2 – stabile API, aber keine neuen Features mehr.

---

### DEPENDENCIES.md ohne Versionsnummern

**Entscheidung:** Die Allowlist (`DEPENDENCIES.md`) enthält nur Package-Namen, keine Versionen. Versionen gehören ausschließlich in `.csproj`/`package.json`. Die Allowlist ist ein Zugangskontroll-Mechanismus, kein Versionsmanagement-Tool – Pinning erzeugt eine dritte Quelle die zwangsläufig divergiert und den Dependency-Hook bei legitimen Updates blockiert.

**Verworfen:** Versionen in Allowlist – Divergenzrisiko, unklare Semantik, Wartungsaufwand ohne Sicherheitsgewinn (CVEs besser via `dotnet list package --vulnerable` / `npm audit`).

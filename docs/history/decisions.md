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
| Frontend-Fehlerbehandlung implementieren | [Querschnittliche Fehlerbehandlung](#querschnittliche-fehlerbehandlung-frontend) |
| Mutation Testing / Stryker konfigurieren | [Test-Tooling & Stryker](#test-tooling--stryker) |
| ETag / If-None-Match / If-Match implementieren | [HTTP-Caching & Optimistic Concurrency](#http-caching--optimistic-concurrency) |

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

## Querschnittliche Fehlerbehandlung (Frontend)

### Service-Layer + Custom Hooks + match()-Pflicht

**Entscheidung:** Drei-Schichten-Muster für alle Backend-Aufrufe:

```
Service-Funktion   →  ResultAsync<T, DomainError>    (Fehler explizit im Typ)
Custom Hook        →  MutationState<T, DomainError>  (Discriminated Union)
Komponente         →  match() mit Pflichtfeldern      (Compile-Fehler bei fehlendem Fall)
QueryCache.onError →  Toast                          (Netzwerk/500 ohne Boilerplate)
```

**Enforcement:** `match()` nutzt Mapped Types – `{ [K in TError['kind']]: ... }`. Fehlt ein Fall im übergebenen Objekt → Compile-Fehler. Gilt für Fehler-Unions, Success-Unions und äußere Zustände (idle/pending/success/error). Details: `docs/CODING_GUIDELINE_TYPESCRIPT.md` Abschnitt 4b.

**Implementierungsdetail:** Domain-Fehler (`Err`) reisen als Rückgabewert durch React Querys Success-Pfad – kein `throw` für erwartete Fehler. Der generische Wrapper `useResultMutation<TData, TError, TVariables>` kapselt React Query vollständig; Custom Hooks reduzieren sich auf eine Zeile.

**Allgemeine Fehler** (Netzwerk, 5xx) werfen nativ und werden von `QueryCache.onError` zentral als Toast angezeigt – Komponenten sehen nur domänenspezifische Fehler.

**Aktueller Code-Stand:** `src/services/ingredientsApi.ts` nutzt noch plain Promise – Migration auf dieses Muster ausstehend (wird bei US-904 Szenario 2 mitgemacht).

**Verworfen:**
- Plain Promise allein: Fehlerfall unsichtbar im Typ, kein Enforcement möglich
- F# + Fable + Elmish: Agenten schreiben diesen Stack zu unzuverlässig – Versions-Drift zwischen Fable 2/3/4, Interop-Halluzinationen, schwache Fehlerdiagnose bei Fable-Compiler-Fehlern

---

### Fehler-Kategorien: drei Typen, globaler HTTP-Interceptor

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

### Toast: nicht-blockierend, ~5 Sekunden Auto-Dismiss

**Entscheidung:** Technische Fehler erscheinen als Toast (nicht-blockierend, oben rechts), auto-dismiss nach ~5s.

**Verworfen:** Modal – zu aggressiv für transiente Fehler. Banner – sinnvoll erst für anhaltende Fehler (Offline-Modus, V1-Scope).

---

### Console.error Format

**Entscheidung:** `[API Error] METHOD /path | Status: NNN | TraceId: xxx`

Beispiel: `[API Error] POST /api/ingredients | Status: 500 | TraceId: 00-abc123...`

URL (inkl. Pfad- und Query-Parameter) wird geloggt. Request-Body wird **nicht** geloggt – Security-Konvention, auch wenn aktuelle Daten nicht sensibel sind. TraceId aus `ProblemDetails.traceId` ist der Verbindungspunkt zum Backend-Log.

---

### Kein automatisches Retry

**Entscheidung:** Der Interceptor unternimmt keinen automatischen Retry. Manueller Retry-Button im Toast: V1-Scope.

**Begründung:** Retry bei nicht-idempotenten Operationen (POST, DELETE) riskiert Duplikate oder Doppellöschungen. Komplexität überwiegt Nutzen für Single-User-App.

---

### Draft-Saving-Prinzip: per Feature, nicht global

**Entscheidung:** Formulare mit nicht-trivialem Eingabeaufwand speichern ihren Zustand in `localStorage` – pro Feature implementiert, nicht im globalen Interceptor.

**Begründung:** Der Interceptor kennt keinen Formular-Zustand. Draft-Saving ist eine Feature-Entscheidung.

**Trigger im Gherkin-Workshop:** Schritt 1 fragt explizit: „Hat diese Story Formulare mit nicht-trivialem Eingabeaufwand? → Falls ja: Draft-Saving-Szenario einplanen."

---

### ProblemDetails: Standard für Exceptions, `errorCode` für Domain-Fehler

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

### Backend-Logging: Applikationslogs und Access Logs getrennt

**Entscheidung:** Applikationslogs (Exceptions, Domain-Events, TraceIds) und Access Logs (HTTP-Requests) sind getrennte Concerns. Access Logs in Produktion auf `Warning`+ gedrosselt.

**Scope:** Serilog und Produktions-Log-Infrastruktur sind kein MVP-Scope. Development: Console-Output von ASP.NET Core reicht. TraceId ist der zentrale Debug-Pfad (Frontend `console.error` → Backend-Log).

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

### HTTP-Mocking in Frontend-Tests: MSW statt `vi.stubGlobal('fetch', ...)`

**Entscheidung:** Alle Frontend-Tests, die HTTP-Calls involvieren, verwenden MSW (`msw/node`) als einzigen Mocking-Layer auf HTTP-Ebene.

**Begründung:** `vi.stubGlobal('fetch', ...)` mockt die Implementierung (die Funktion `fetch`), nicht den HTTP-Kontrakt. Ein Test der `expect(mockFetch).toHaveBeenCalledWith('/api/ingredients')` prüft, ist beim Wechsel von `fetch` auf `axios` sofort rot – nicht weil die URL falsch ist, sondern weil die Implementierung sich ändert. MSW intercepted auf Netzwerk-Ebene und ist damit unabhängig davon, welches HTTP-Primitiv (`fetch`, `axios`, `XMLHttpRequest`) die Service-Funktion intern nutzt.

**Konsequenz:** Tests gegen Service-Funktionen (`ingredientsApi.ts` etc.) und Komponenten-Tests die HTTP-Calls auslösen, setzen Handler via `server.use(http.get('/api/...', () => HttpResponse.json(...)))` und kennen keine Implementierungsdetails der Service-Schicht.

**Verworfen:** `vi.stubGlobal('fetch', ...)` – koppelt Test an Implementierung statt Kontrakt. `nock` – unterstützt kein modernes `fetch`. `fetchMock`/`jest-fetch-mock` – gleicher falscher Schnitt wie stubGlobal.

---

### Stryker-JS: `main.tsx` aus `mutate` ausgeschlossen

**Entscheidung:** `!src/main.tsx` in `Client/stryker.config.json`.

**Begründung:** Bootstrap-Code (`createRoot`, `QueryClientProvider`, `StrictMode`) – kein testbarer Domänen- oder Anwendungslogik-Anteil. Kein sinnvoller Unit-Test möglich.

---

### Stryker.NET + xUnit v3: MTP Runner erforderlich

**Entscheidung:** `"test-runner": "mtp"` in `stryker-config.json`. Test-Projekt: `OutputType=Exe`, `UseMicrosoftTestingPlatformRunner=true`, `TestingPlatformDotnetTestSupport=true` in `Server.Tests/mahl.Server.Tests.csproj`.

**Begründung:** Stryker.NET 4.x unterstützt xUnit v3 (`xunit.v3`) nicht über den klassischen VSTest-Runner – Mutanten werden als "Survived" reportiert, obwohl Tests sie korrekt killen würden (verifiziert: manuell falsche Route → Test schlägt fehl, aber Stryker sieht es nicht). xUnit v3 nutzt ein anderes Ausführungsmodell als xUnit v2. Der MTP (Microsoft Testing Platform) Runner, verfügbar ab Stryker 4.13, löst die Inkompatibilität. `TestingPlatformDotnetTestSupport=true` stellt sicher, dass `dotnet test` weiterhin funktioniert.

**Verworfen:** Weiterhin VSTest-Runner – 0% Mutation Score für alle Endpoints trotz korrekter Tests.

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

---

## HTTP-Caching & Optimistic Concurrency

### Globale ETag-Policy: alle mutierbaren Ressourcen

**Entscheidung:** Alle Endpoints erhalten ETags – keine Ausnahmen.

**Begründung:** Jeder GET-Endpoint profitiert von HTTP-Caching (304). PUT/PATCH/DELETE brauchen zusätzlich If-Match für Optimistic Concurrency. Die Unterscheidung "mutierbar vs. nicht mutierbar" ist irrelevant – ETags sind auf GET unabhängig davon sinnvoll. Cross-Cutting-Concern: sobald die Grundstruktur steht, kostet jede weitere Entity minimal.

---

### Zwei Verwendungszwecke: HTTP-Caching und Optimistic Concurrency

**Entscheidung:** Derselbe ETag-Wert wird für beide Zwecke eingesetzt:

| Zweck | Request-Header | Response-Status |
|-------|---------------|-----------------|
| HTTP-Caching | `If-None-Match: "..."` bei GET | 304 Not Modified |
| Optimistic Concurrency | `If-Match: "..."` bei PUT/PATCH/DELETE | 412 Precondition Failed |

---

### ETag-Quelle: xmin (Single Resource) / Content-Hash (Collection)

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

### Implementierungsreihenfolge

**Entscheidung:** ETag-Support wird pro Endpoint beim Szenario-Schritt eingebaut, der den Endpoint erstmalig mit echten DB-Daten belegt. Nicht in Skeleton-Stubs (hardcoded Antworten haben keinen sinnvollen ETag).

`GET /api/ingredients` erhält ETag-Support in US-904 Szenario 2 (erster GET mit echten DB-Rows).

# Technische Entscheidungen

<!--
wann-lesen: Wenn unklar ist warum etwas so implementiert wurde, oder bevor eine ähnliche Entscheidung getroffen wird
kritische-regeln:
  - Jede selbst getroffene technische Entscheidung (Validierungsregeln, Error Codes, Schema-Details) hier dokumentieren
  - Format: Datum → Kontext → Entscheidung → Verworfen
-->

> Archiv aller getroffenen technischen Entscheidungen. Bei Fragen "Warum wurde X so entschieden?" hier nachschlagen.

---

## 2026-03-31 (Spec & Guidelines Review)

### TypeScript ROP-Bibliothek: `neverthrow`

**Kontext:** Im Rahmen eines Guideline-Reviews wurden vier ROP-Bibliotheken evaluiert: `neverthrow`, `@praha/byethrow`, `effect`, `fp-ts`.

**Entscheidung:** `neverthrow`. Begründung: 1M+ wöchentliche npm-Downloads, beste Community-Dokumentation, etabliertes API (`.andThen()`, `.match()`), ausreichende Stabilität für diesen Anwendungsfall.

**Verworfen:**
- `@praha/byethrow` – aktiver gewartet, serialisierbare Results (nützlich für Server Components), aber kleinere Community und weniger Lernmaterial. Bevorzugter Nachfolger falls `neverthrow` inaktiv wird.
- `effect` – sehr mächtig, aber Komplexität und Bundle-Größe übersteigen den Scope dieser App.
- `fp-ts` – akademisch, steile Lernkurve, nicht idiomatisch für React-Teams.

**Risiko:** `neverthrow`-Maintenance verlangsamt sich (viele offene PRs). Monitoring empfohlen; Migration zu `@praha/byethrow` wäre API-nah.

---

### CA1515 aktiviert: `internal`-Pflicht für Server/-Typen per Analyzer erzwungen

**Kontext:** CA1515 ("Types can be made internal") war für `Server/` unterdrückt mit dem Kommentar "bis InternalsVisibleTo-Refactoring fertig ist". Die Architektur schließt InternalsVisibleTo aber grundsätzlich aus (ARCHITECTURE.md 0c).

**Entscheidung:** CA1515 auf `warning` gesetzt in `.editorconfig` für `{Server,Server/**}/*.cs`. Erzwingt die in `CODING_GUIDELINE_CSHARP.md` beschriebene `internal`-Pflicht statisch.

---

## 2026-03-26 (Session 41 – Architektur-Grundsatzentscheidungen)

### Hexagonal Architecture / Ports & Adapters als explizites Architekturprinzip

**Kontext:** Das Projekt hatte diese Struktur implizit, ohne sie zu benennen. Im Rahmen einer umfassenden Architektur-Diskussion wurde sie explizit als Leitprinzip adoptiert.

**Entscheidung:** Die Anwendung ist ein Hexagon mit klar definierten Ports: HTTP-Endpoints (eingehender Port) und DbContext (ausgehender Port). Tests exercisen die Anwendung ausschließlich über diese Ports – kein direkter Zugriff auf Server-Interna aus Tests.

**Verworfen:** Black-Box-Tests via InternalsVisibleTo – verletzt das Prinzip, da interne Typen direkt referenziert werden.

---

### Infrastructure Layer als eigenes Projekt (mahl.Infrastructure)

**Kontext:** CA1515 und die Hexagonal-Architecture-Entscheidung erforderten eine saubere Lösung für die Frage "Was ist public, was ist internal?".

**Entscheidung:** `MahlDbContext` und alle `*DbType`-Klassen ziehen in ein eigenes Projekt `mahl.Infrastructure` (public by design – sie sind der ausgehende Port). `mahl.Server` (Endpoints, Domain, DTOs) bleibt vollständig internal. Kein `InternalsVisibleTo` nötig – Tests referenzieren `mahl.Infrastructure` direkt.

**Verworfen:** `InternalsVisibleTo` – ist "fake encapsulation"; verletzt das Prinzip, während es Compliance vortäuscht.

---

### Domain-Typen sind internal, keine direkten Unit-Tests

**Kontext:** Domain-Typen (`Ingredient`, `Recipe`, `Quantity`, `NonEmptyTrimmedString` etc.) waren public ohne zwingenden Grund.

**Entscheidung:** Alle Domain-Typen sind `internal`. Keine dedizierten Unit-Tests für Domain-Typen – ihr Verhalten wird vollständig über Endpoint-Integration-Tests abgedeckt. In einer Application (nicht Library) ist die HTTP-API die öffentliche Schnittstelle, nicht die Domain-Klassen.

---

### Defensive Guards: kein Test, Stryker disable mit Begründung

**Kontext:** Guards wie parameterloser Konstruktor (`throw`) und `default(T)`-Property-Guards schützen vor Sprachmissbrauch (Framework-Magie, versehentliches `new T()`). Sie sind von außen nicht erreichbar.

**Entscheidung:** Guards behalten (schützen gegen Sprachlücken). Kein Test (strukturell unerreichbar). `// Stryker disable once` mit expliziter Begründung ("Guard against language/framework misuse – unreachable via external interfaces").

---

### BDD/Gherkin als Standard für E2E-Tests

**Kontext:** E2E-Tests sollen gleichzeitig ausführbare Spezifikation sein. Trennung zwischen Spec-Dokument und Test erzeugt Duplikation und Drift.

**Entscheidung:** `.feature`-Dateien (Gherkin) sind die **dokumentarische** Spec – kein separates Spec-Dokument, kein BDD-Runner. Playwright (TypeScript) ist der ausführbare äußere Loop und trägt `@US-ID`-Tags im describe/test-Namen. Jedes Szenario trägt `@US-ID`-Tags für bidirektionale Traceability.

**Verworfen:** SpecFlow/Reqnroll als Testrunner – SpecFlow läuft nur in C# und kann damit nur die API testen, nicht das Full-Stack-Nutzerverhalten das Gherkin-Szenarien beschreiben. Für das TypeScript-Frontend wäre trotzdem Playwright nötig → zwei parallele Test-Stacks mit demselben Gherkin, unlösbarer Stack-Mismatch.

**Verworfen:** Separate Spec-Dokumente + handgeschriebene Tests – erzeugt unvermeidliche Divergenz.

---

### Outside-In ATDD / Double-Loop TDD als Standard

**Kontext:** Konsequente Außen-nach-innen-Entwicklung garantiert, dass jede Codezeile von einem E2E-Test angetrieben wird.

**Entscheidung:** Die Reihenfolge ist immer: Gherkin-Szenario (E2E, rot) → Frontend-Test (rot) → Backend-Integration-Test (rot) → Backend-Code (grün). Das Gherkin-Szenario wird zuerst geschrieben – auch wenn das Frontend noch nicht existiert. Es schlägt dann aus dem richtigen Grund fehl ("UI existiert nicht"), und die inneren Loops werden von oben nach unten erschlossen. Kein Backend-Test darf existieren, ohne dass ein darüberliegender Test ihn fordert.

---

### E2E Quality Gate: Spec-driven Checklist (nicht Coverage-Metrik)

**Kontext:** Branch/Line-Coverage für E2E-Tests wurde evaluiert und abgelehnt (Goodhart's Law, falsche Granularität, Instrumentierungskosten).

**Entscheidung:** Quality Gate für E2E-Tests = Spec-driven Checklist: Für jede User Story min. 1 Happy-Path-Szenario, für jede Rejection-Regel min. 1 Rejection-Szenario, für jeden Fehlerfall min. 1 Error-Szenario. Verifiziert via `@US-ID`-Tags + CI-Skript (Tag → gültiger Spec-Eintrag).

**Klarstellung Coverage:** Branch- und Line-Coverage werden projektübergreifend auf 100% gehalten (alle Test-Schichten zusammen) – das ist unverändert. Was abgelehnt wurde: ein *separater* Coverage-Gate exklusiv für E2E-Tests. E2E-Tests tragen zur Gesamt-Coverage bei, ihr spezifischer Quality Gate ist aber spec-driven, nicht coverage-basiert.

**Verworfen:** Separater Branch/Line-Coverage-Gate nur für E2E-Tests – misst Ausführung statt Korrektheit; incentiviert falsches Testdesign auf E2E-Ebene.

---

### Bidirektionale Traceability: Spec ↔ Test

**Kontext:** Spec-driven Gate kann nur prüfen "hat jede Spec einen Test?" – nicht "hat jeder Test eine Spec?".

**Entscheidung:** Zwei-Richtungs-Prüfung: (1) Spec → Test: Gate schlägt fehl wenn Spec-Eintrag kein Szenario hat. (2) Test → Spec: CI-Check verifiziert dass jeder `@US-ID`-Tag auf einen gültigen Spec-Eintrag zeigt. Test-Audit ist Teil jedes Reviews: "Werden alle Tests von der Spec gefordert?"

---

### Backend-Code verwerfen, Neustart mit ATDD

**Kontext:** Der Backend-Code wurde im "luftleeren Raum" entwickelt (ohne UI-Consumer, ohne echte Outside-In-Disziplin). Zu viele zentrale Architekturentscheidungen ändern sich (Hexagonal, Infrastructure Layer, BDD, ATDD).

**Entscheidung:** Backend-Code wird verworfen. Bewahrt werden: Specs (`SKELETON_SPEC.md`, `MVP_SPEC.md`), `decisions.md`, `lessons_learned.md`, alle Guidelines und Skills. Vor dem Verwerfen: Audit ob Code Verhalten enthält das nicht in den Specs steht – ggf. Specs ergänzen. Neustart mit BDD/Gherkin als äußerem Loop.

**Verworfen:** Retrofit des bestehenden Codes – nicht ohne erheblichen Aufwand möglich, und Outside-In-Disziplin wäre nachträglich nicht verifizierbar.

---

### Adopt/Skip/Defer: Best-Practices-Entscheidungen (Session 41)

| Praxis | Entscheidung | Notizen |
|--------|-------------|---------|
| Health Checks | **Adopt** | Trivial, relevant für Docker-Startsequenz |
| OpenAPI → TS Type Generation | **Adopt** | Statt Pact; single-developer tauglich |
| Metrics/Telemetry | **Adopt** | Vor Produktion; .NET Diagnostics.Metrics |
| Domain Events | **Adopt V1** | Ggf. MVP; Basis für History-Features |
| Aggregate Roots | **Adopt inkrementell** | Wo Invarianten Kinder überspannen (z.B. Recipe) |
| Bounded Contexts | **Adopt V1** | Zusammen mit Domain Events; heute Monolith |
| Property-Based Testing | **Consider nach SKELETON** | Auf Endpoint-Ebene, nicht Value-Object-Ebene |
| Snapshot Testing | **Skip** | BeEquivalentTo + Mutation Testing reichen aus |
| API Versioning | **Skip** | Single-developer, single-client, kein externer Consumer |
| Contract Testing (Pact) | **Skip** | Ersetzt durch OpenAPI → TS Type Generation |
| Specification Pattern | **Review-Hinweis** | Anwenden wo Query-Duplikation es rechtfertigt |

---

## 2026-03-26 (Session 40)

### Switch + `_ => SumType.Unreachable<T>()` statt Ternary in `Match<T>`

**Kontext:** Bei der Coverlet-Integration wurde `Match<T>` auf Ternary (`this is UrlCase u ? ... : ...`) refactored, weil das 100% Branch Coverage erreicht ohne unreachbaren Arm. Die Frage: Ist Ternary oder Switch die bessere Wahl für Sum-Type-Dispatch?

**Entscheidung:** Switch mit `_ => SumType.Unreachable<T>()`. Begründung: Bei einer neuen Variante, die intern hinzugefügt aber in `Match<T>` vergessen wird, fällt der Switch zur Laufzeit klar auf (throw). Der Ternary ruft still `onNone()` auf — falsches Verhalten ohne Fehlermeldung.

**Verworfen:** Ternary — besser für Coverage, schlechter für Korrektheit bei Erweiterungen.

**Konsequenz:** `[ExcludeFromCodeCoverage]` auf `Match<T>` (Stryker-Suppress bleibt in `SumType.Unreachable<T>()`). Branch-Level-Suppression ist in keinem .NET-Tool verfügbar (microsoft/codecoverage#23).

**Auch verworfen — Switch ohne `_`-Arm:** Empirisch getestet: Coverlet trackt die compiler-generierte `throw new SwitchExpressionException()`-Branch auf IL-Ebene, auch wenn sie keine Quellposition im PDB hat. Ergebnis: Line Coverage bleibt 100%, Branch Coverage fällt auf ~98%. Kein Gewinn gegenüber dem expliziten `_`-Arm.

---

### `SumType.Unreachable<T>()` als zentraler Helper

**Kontext:** Jede `Match<T>`-Implementierung in Sum Types hatte identisch `// Stryker disable once String,Statement : unreachable due to private ctor` + `throw new InvalidOperationException("Unreachable.")`.

**Entscheidung:** Extraktion in `Server/Types/SumType.cs`. Stryker-Suppress liegt einmal in der Helper-Methode, nicht in jeder `Match<T>`-Implementierung. Zukünftige Sum Types schreiben nur `_ => SumType.Unreachable<T>()`.

---

## 2026-03-25

### `System.Uri` als akzeptiertes BCL-Primitive in `Create()`-Parametern

**Kontext:** CA1054/CA1056-Fix: `SourceUrl` in DTOs und Domain von `string?` auf `Uri?` umgestellt. Die Frage war: Brauchen wir einen eigenen `NonEmptyUri`-Typ, analog zu `NonEmptyTrimmedString`?

**Entscheidung:** Nein. `System.Uri` wird direkt als Parameter in `Recipe.Create(Uri? sourceUrl)` akzeptiert. `new Uri("")` wirft `UriFormatException`, `new Uri(null)` wirft `ArgumentNullException` — ein leeres oder null-Uri-Objekt ist nicht konstruierbar. Fachliche Invarianten (z.B. Absolutheit) werden zusätzlich per Guard in `Create()` geprüft (`IsAbsoluteUri: false` → `Error<string>`).

**Verworfen:** `NonEmptyUri` als eigener Typ — unnötig, da `Uri` die strukturelle Garantie bereits mitbringt.

**Offen (Tech Debt):** Verhalten des JSON-Deserializers bei syntaktisch ungültigem URI-String noch nicht verifiziert (400 oder 500? → Session 040).

---

### STJ serialisiert `Uri` via `OriginalString` — Round-Trip ohne Normalisierung

**Kontext:** `RecipeSource`'s `explicit operator string?` muss den URL für die DB zurückgeben. `Uri.ToString()` und `Uri.AbsoluteUri` normalisieren (`"https://example.com"` → `"https://example.com/"`). `Uri.OriginalString` liefert den Originalstring. STJ nutzt intern ebenfalls `OriginalString` zur Serialisierung.

**Entscheidung:** `url.OriginalString` in `explicit operator string?`. Damit ist der Round-Trip konsistent: POST-Body `"https://example.com"` → DB-Wert `"https://example.com"` → GET-Response `"https://example.com"` (STJ serialisiert via `OriginalString`).

**Verworfen:** `url.AbsoluteUri` — würde beim Speichern normalisieren; der Originalstring des Clients geht verloren.

---

### `GET /api/recipes` gibt bei korrupter DB-URL ebenfalls 500 zurück

**Kontext:** Beide `GET /api/recipes` und `GET /api/recipes/{id}` sollen konsistent 500 + `application/problem+json` liefern, wenn eine `SourceUrl` in der DB korrupt ist. Ein Review-Agent hatte „silent null" als Performance-Tradeoff vorgeschlagen — das wurde abgelehnt, weil `null` keinen validen semantischen Wert hat (SourceUrl ist entweder eine gültige URI oder es gibt keine — nicht „korrupte Daten ignorieren").

**Entscheidung:** `GetAll` nutzt `ToSummaryDtoOrError()` + `Sequence()` → bei Fehler `Results.Problem(detail, 500)`. Damit konsistent zu `GetById`.

---

## 2026-03-24

### S4581: `== default` statt `== Guid.Empty` für uninitialisierten Guid-Guard

**Kontext:** Sonar S4581 schlägt vor, `== default` durch `== Guid.Empty` zu ersetzen. Die Regel existiert primär um versehentlich leere Guid-Instanziierungen (`new Guid()`) zu finden, flaggt aber auch `== default`-Vergleiche.

**Entscheidung:** In Domain-Typen, die per `default(T)` uninitialisiert sein können (`readonly record struct` mit `Guid`-Backing-Feld), bleibt `_id == default` erlaubt und wird per `#pragma warning disable S4581` suppressiert. Diese spezifische Verwendung ist:
- kein Bug-Risiko (der Vergleich gegen `default` ist semantisch identisch mit `== Guid.Empty`)
- bewusst formuliert: `default` signalisiert "strukturell uninitialisiert" – unabhängig vom konkreten Typ
- in der Codebasis ausschließlich für diesen einen Zweck (uninitialisierten Value-Type-Guard) verwendet

**Einschränkung:** Diese Suppression ist **nur** für dieses spezifische Muster erlaubt (Guard gegen `default(T)` bei einem Backing-Feld das keinen sinnvollen Null-Wert hat). S4581 an anderen Stellen muss zunächst evaluiert werden – dort kann es auf einen echten Bug oder mangelnde Explizitheit hinweisen.

---

## 2026-03-18

### Stryker `additional-timeout` auf 15000ms erhöht

**Kontext:** Bei Partial-Runs (`--mutate Domain/Foo.cs`) traten Timeout-Mutanten auf, die keine echten Kills waren (z.B. String-Mutation `"Recipes"` → `""` in `.WithTags()`). Ursache: Strykers Timeout-Formel `baseline × 1.5 + additional-timeout` liefert bei kurzer Partial-Run-Baseline (~15s) nur ~27.5s pro Mutant. Integration-Tests mit echtem DB-Backend haben variable Laufzeiten (WebApplicationFactory-Start, DB-Verbindung, GC-Pausen), was diesen Puffer gelegentlich überschreitet. Im Full-Run ist die absolute Puffergröße wegen längerer Baseline unkritisch.

**Entscheidung:** `additional-timeout: 15000` (statt Default 5000ms). Erhöht den Puffer auf ~32.5s bei Partial-Runs, ohne das Laufzeitverhalten bei echten Infinite-Loop-Mutations nennenswert zu beeinflussen.

**Verworfen:** Timeouts im Score nicht mitzählen – wäre bei echten Detections (echter Infinite Loop) falsch. Stattdessen: Warnung im Summary-Script wenn Timeouts > 0 auftreten.

---

## 2026-03-17

### `RecipeIngredient.IngredientId` Property entfernt

**Kontext:** Nach der UUID-v7-Migration trägt `Ingredient` eine eigene `Guid Id`. `RecipeIngredient` hatte zuvor ein separates `_ingredientId`-Backing-Field (Workaround, weil `Ingredient` keine Id hatte) und ein `IngredientId`-Property, das darauf delegierte. Nach dem Hinzufügen von `Ingredient.Id` wurde `_ingredientId` entfernt und `IngredientId` zunächst auf `_ingredient.Id` umgestellt.

**Entscheidung:** `IngredientId` vollständig entfernt. Das Property ist redundant – `recipeIngredient.Ingredient.Id` ist semantisch identisch. Eine Delegation (`IngredientId => _ingredient.Id`) würde YAGNI/DRY verletzen ohne Kapselungsgewinn, da `Ingredient` kein Implementierungsdetail ist, sondern ein fachlicher Bestandteil von `RecipeIngredient`.

**Verworfen:** Flache Delegation beibehalten (`IngredientId => _ingredient.Id`) – kein Mehrwert gegenüber direktem Zugriff auf `Ingredient.Id`.

---

## 2026-03-05

### Äquivalenter Mutant: `"Unreachable."` in Sum-Type `Match`-Methoden

**Kontext:** Sum-Type `Match`-Methoden enthalten einen `_ => throw new InvalidOperationException("Unreachable.")` Zweig als Sicherheitsnetz. Da der private Konstruktor externe Subtypen verhindert, ist dieser Zweig per Design nie erreichbar. Stryker mutiert den String `"Unreachable."` → `""` – dieser Mutant überlebt, weil kein Test ihn triggern kann.

**Entscheidung:** Äquivalenter Mutant. Die Codezeile hat keine beobachtbare Auswirkung auf das Verhalten. Exclusion per `// Stryker disable once StringMutation` Inline-Kommentar direkt über der Zeile.

**Gilt für:** Alle `_ => throw new InvalidOperationException("Unreachable.")` Zeilen in Sum-Type `Match`-Implementierungen (`RecipeSource.cs`, `Quantity.cs`, und zukünftige Sum-Types).

---

### Sum-Type-Design: Nur private Subtypen, zwei Varianten

**Kontext:** Bisher wurden Sum-Types (`RecipeSource`) mit öffentlichen Subtypen modelliert. Öffentliche Subtypen erlauben es Consumern, `switch`-Ausdrücke ohne Exhaustiveness-Garantie zu schreiben, externe Subtypen zu definieren und Subtypen direkt zu konstruieren.

**Entscheidung:**
Öffentliche Subtypen sind verboten. Zwei erlaubte Varianten:

- **Variante A – verschachtelte `private` Subtypen:** Stärkste Kapselung. `private RecipeSource() { }` verhindert jede externe Ableitung. Transitionen als Methoden auf dem Basistyp. Für Wert-Träger-Sum-Types (reine Zustandscontainer ohne eigenes Domänenverhalten) und als Standard.
- **Variante B – `file`-scoped Subtypen + `private protected` Konstruktor:** Wenn alle Operationen inklusive Transitionen als Extension Methods in derselben Datei geführt werden sollen (Guideline 6). `private protected` statt `private`, weil top-level `file`-Records keinen privaten Basiskonstruktor aufrufen können. Externe Assemblies können trotzdem nicht subtypen; innerhalb des Assembly gilt Konvention + Code-Review.

`Match<T>` ist immer die einzige öffentliche Schnittstelle für Consumer. Alle Methoden auf dem Basistyp und Extension Methods nutzen `Match<T>` intern statt direktem `switch` auf Subtypen – Exhaustiveness-Pflege ist so an einer Stelle zentriert.

`Match<T>` ist **public** für Wert-Träger-Sum-Types (Mapping-Layer benötigt Zugriff), **internal** für operationale Sum-Types.

Konvertierungsoperatoren: `implicit` wenn verlustfrei und reversibel, `explicit` wenn Information verloren geht.

**Verworfen:** Öffentliche Subtypen (keine Exhaustiveness-Garantie, externe Subtypen möglich). `internal` Subtypen (gesamtes Assembly kann subtypen, keine strukturelle Garantie).

---

## 2026-02-26

### Workflow-Enforcement: Skills + Hooks statt reiner Guidelines

**Kontext:** TDD-Guidelines in `ARCHITECTURE.md` wurden nicht zuverlässig angewendet
(zu viel Code im GREEN-Schritt, mehrere Tests auf einmal). Guidelines sind passiv –
sie werden gelesen, können aber im Laufe langer Sessions "vergessen" werden.

**Entscheidung:**
1. **Skills** (`.claude/skills/`) für Auto-Triggering: Claude lädt den `tdd-workflow`-Skill
   automatisch wenn es Backend-Endpoints implementiert oder Tests schreibt – ohne explizite
   Nutzer-Eingabe. Skills haben YAML-`description`-Frontmatter, der das Matching steuert.
2. **Commands** (`.claude/commands/`) bleiben für explizit gesteuerte mehrstufige Prozesse
   (AUTOR-REVIEW, REVIEW-AGENTEN, LEARNINGS in `/feature`).
3. **Hooks** für deterministisches Enforcement: `check-one-test.py` blockt mehr-als-ein-Test
   Edits. Auf Python umgestellt (kein jq-Abhängigkeits-Problem mehr).
4. **ARCHITECTURE.md** bleibt die "ground truth" – Skills/Commands referenzieren sie.

**Verworfen:** Rein text-basierte Guidelines ohne aktive Enforcement-Mechanismen.

### Hook-Implementierung: Python statt Bash+jq

**Kontext:** `check-one-test.sh` nutzte `jq` für JSON-Parsing. Bei fehlendem `jq`
crashte der Hook ohne exit 1 → Claude Code zeigte "hook error" statt "hook block"
→ TDD-Verstoß ging trotzdem durch.

**Entscheidung:** Hook auf Python umgestellt (`check-one-test.py`). Python ist in der
WSL-Umgebung zuverlässig verfügbar, hat eingebautes JSON-Parsing und klar definiertes
Fehlerverhalten. Der Bash-Wrapper delegiert direkt an Python.

---

## 2026-02-17

### Frontend-Framework: React 18+ mit Material UI v7
- Offline-Support (US-306) ist MVP – React-Ökosystem überlegen (Workbox, React Query)
- MUI v7 bietet vollständigen Material Design 3 Support (stabil)
- Bestehender Blazor-Code rudimentär, keine Weiterverwendung
- Mutation Testing mit Stryker-JS etabliert
- **Verworfen:** Blazor WebAssembly, Vue 3 + Vuetify

### Datenbank: PostgreSQL 15+
- Bessere JSON-Unterstützung für zukünftige Erweiterungen
- Npgsql EF Core Provider ausgereift
- Migration von MariaDB später möglich
- **Flexibilität:** Keine PostgreSQL-spezifischen Features in V1 (JSONB, Arrays)

### API Error Handling: Problem Details (RFC 7807)
- Standardisiertes Format, einheitliche UX via MUI Snackbar

### SKELETON-Scope: 4 User Stories (US-904, US-602, US-803, US-201/303)
- Echter "Walking Skeleton" soll minimal sein
- **Verschoben zu MVP:** US-501, US-505, US-506, US-605, US-614, US-801

### ~~Mutation Testing Ziel: ≥ 90%~~ *(revidiert Session 41, 2026-03-26)*
- ~~100% unrealistisch (Generated Code, Logging, Boilerplate)~~
- ~~Hybrid-Ansatz: Volltest am Ende jeder Phase, `--files` während Entwicklung~~
- **Revidiert:** Ziel ist 100%. Strukturell unerreichbarer Code (z.B. `_ => throw` in Sum-Type-Switch-Default) wird mit begründeten Suppressions behandelt, nicht mit einem gesenkten Zielwert. Die Praxis hat gezeigt, dass 100% realistisch erreichbar ist.

### Authentifizierung SKELETON: Optional / keine Auth
- Fokus auf Datenfluss; echtes Auth kommt in MVP

### Einheiten-Konvertierung SKELETON: Keine Umrechnung
- US-902 (Einheiten-Management) ist MVP
- Duplikate auf Einkaufsliste akzeptiert ("200g Mehl" + "1 EL Mehl" = zwei Einträge)

### AlwaysInStock-Flag: Feld angelegt, UI erst MVP
- Vorbereitung für US-906, spart Migration-Aufwand

### Abhaken-Verhalten: BoughtAt-Timestamp, nicht löschen
- US-303 spezifiziert "verschieben in 'Zuletzt gekauft'"
- Ermöglicht Undo-Funktion (US-401, V1)

### Einkaufslisten-Generierung: Einfache Variante in SKELETON
- Löscht alte Items, schreibt alle Pool-Rezepte neu
- KEIN Tracking welche Zutat aus welchem Rezept
- Limitation akzeptiert: Bei Pool-Änderung muss User manuell neu generieren

### Bilder-Speicherung: Filesystem statt DB
- `Server/wwwroot/uploads/recipe-sources/{recipeId}/original.jpg`
- DB bleibt klein, einfaches Serving via wwwroot
- Backup: pg_dump (DB) + tar (Filesystem)

### Soft-Delete: `DeletedAt` (timestamptz?) statt `IsDeleted` (bool)
- Mehr Information (wann gelöscht?), ermöglicht Audit-Queries und automatisches Aufräumen

---

## 2026-02-18

### ShoppingListItemSource: Separate Tabelle statt JSON-Feld
- Datenintegrität (Foreign Keys, CASCADE)
- Einfachere Queries, DB-agnostisch
- Performance bei ~80 Items kein Problem
- **Verworfen:** JSON-Feld (keine Foreign Keys, schwierige Queries)

### Einkaufsliste UI: Kachel-Layout (Bring!-Stil)
- Große Touch-Buttons (min. 80×80px)
- Offen = volle Farbe, Gekauft = Grau + reduzierte Opacity (KEIN Durchstrich)
- V1: Icons pro Zutat; V2+: LLM-generierte Icons

### Entwicklungs-Workflow: Drop + Recreate vor Production
- Schnellere Iteration, keine Migrations-Hölle
- User haben noch keine echten Daten → kein Verlustrisiko
- Ab Production: Normale Migrations

### Seed-Data: C# Extension Method (`app.SeedDatabase()`)
- Type-safe, versioniert mit Code
- Eleganter als Raw SQL, nutzbar in Tests
- Aufruf: `dotnet run --project Server -- --seed-data`
- Enthält: 10 Rezepte + 45 Zutaten in `Server/Data/SeedDataExtensions.cs`

### Frontend-Navigation: Burger (mobil) vs. Tabs (Desktop)
- Breakpoint: 768px (MUI Standard)
- Mobile-First Ansatz

### Frontend Migration: Blazor → React (Client/ komplett neu)
- Blazor-Code in `Client/` gelöscht, React-Projekt neu aufgesetzt
- `npm create vite@latest Client -- --template react-ts`

### Stryker-Konfiguration: `coverage-analysis: "off"`
- Notwendig für WebApplicationFactory in Integrationstests

---

## 2026-02-19 (Session 1 – SKELETON Abschluss)

### Material UI v7 statt v6
- npm hat neueste Version installiert, v7 statt der geplanten v6
- Grid-API leicht anders, aber kein Problem → v7 beibehalten

### dotnet in WSL: Windows-Pfad erforderlich
- `which dotnet` gibt nichts zurück in WSL
- Wrapper: `cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet <command>"`

---

## 2026-02-24 (Session 4 – TDD-Neustart)

### ~~Quantity nullable in RecipeIngredient und ShoppingListItem~~ *(revidiert, siehe 2026-03-03)*
- ~~`RecipeIngredient.Quantity`: NULL = "nach Geschmack" (keine definierte Menge)~~
- ~~`ShoppingListItem.Quantity`: NULL = Menge nicht angegeben (semantisch: 1)~~
- ~~Generierungslogik: NULL-Mengen als 0 behandeln bei Aggregation; wenn alle NULL → Ergebnis NULL~~

### POST /api/ingredients – Verhalten bei Soft-Delete-Namenskonflikt: 409 + Client-Orchestrierung
- **Entschieden:** `POST /api/ingredients` mit einem Namen, der bereits soft-deleted existiert, gibt `409 Conflict` zurück mit Body `{ "code": "ingredient_soft_deleted", "id": <id> }`.
- Der Client erkennt den Code und ruft automatisch den Restore-Endpoint auf (transparent für den Nutzer).
- **Verworfen:** Transparentes Server-seitiges Reaktivieren (Option B) – bricht POST-Semantik, zwei Pfade in einem Endpoint, schwerer testbar.
- **Verworfen:** Immer 409 ohne Restore-Möglichkeit (Option C) – Sackgasse für den Nutzer.
- **Verworfen:** Neu anlegen neben soft-deletem Eintrag (Option A) – erzeugt stille Inkonsistenz (zwei "Butter"-Einträge mit verschiedenen IDs).

### TDD-Neustart: Alten SKELETON-Code löschen und neu implementieren
- Alle SKELETON-Endpoints und -Tests wurden gelöscht und via striktem TDD neu implementiert.
- Grund: Bestehender Code wurde nicht mit TDD oder aktuellen Guidelines erstellt – keine Garantie auf Korrektheit oder Sauberkeit.
- Frontend (Client/) bleibt vorerst bestehen (separater Aufwand).

---

## 2026-03-03 (Session 17)

### WeeklyPool: Keine Duplikate
- `POST /api/pool` mit einem Rezept das bereits im Pool ist → `409 Conflict`.
- Begründung: Für den Familienkontext ist ein doppeltes Rezept in der Wochenplanung wahrscheinlicher ein Versehen als Absicht – wird daher mit minimalem Aufwand verhindert. Bewusste Einschränkung, kein fachliches Gesetz.

### StepNumber nicht im DTO
- `StepNumber` wird nicht im `CreateStepDto` übergeben.
- Berechnung im POST-Handler: `StepNumber = idx + 1` (1-basiert, Reihenfolge aus der DTO-Liste).
- Begründung: Clients sollen nicht für Konsistenz der Nummerierung verantwortlich sein.

### Quantity: eigener Summentyp statt `decimal?`
- **Revidiert:** Die Session-4-Entscheidung (`decimal?` in Domain-Typen) wird rückgängig gemacht.
- `decimal?` als Property-Typ in Domain-Typen verletzt die Guideline ("Make Illegal States Unrepresentable") und die REVIEW_CHECKLIST.
- **Neu:** Eigener Typ `Quantity` als `readonly record struct` mit internem `OneOf<PositiveDecimal, Unspecified>`.
- `decimal?` als **Parameter** von `Create()` bleibt erlaubt (Systemgrenze zu DTO/Primitives).
- Generierungslogik: `Unspecified` = 0 bei Aggregation; wenn alle `Unspecified` → Ergebnis `Unspecified`.

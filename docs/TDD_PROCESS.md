# TDD-Prozess (verbindlich)

<!--
wann-lesen: Vor und während jeder Code-Änderung (Features, Bugfixes, Refactorings) – TDD gilt für jeden Produktionscode
kritische-regeln:
  - IMMER EIN TEST AUF EINMAL – erst RED→GREEN→REFACTOR abschließen, dann nächster Test
  - GREEN = kleinstmögliche Implementierung; hardcodierte Rückgabe ist erlaubt und erwünscht
  - Jede Zeile ohne erzwingenden roten Test ist Gold-Plating → löschen
  - Full State Assertion bei mutierenden Tests – ExcludingMissingMembers verboten
  - Stryker-Ziel: 100% Mutation Coverage (Pflicht am Ende jeder Phase)
  - Branch-Coverage-Ziel: 100% (Coverlet / V8) – Unterschreitung = Build-Fehler
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Outside-In ATDD | Three-Loop TDD: äußer (Gherkin/E2E), mittler (Integration), inner (Unit je Schicht); Regeln | Vor dem Start jeder User Story |
| Phase 1 – RED | Einen Test schreiben, fehlschlagen bestätigen, Business-Entscheidungen dokumentieren | Vor jeder neuen Implementierung |
| Phase 2 – GREEN | Kleinstmögliche Implementierung, Gold-Plating-Check, alle Tests grün | Während der Implementierung |
| Phase 3 – REFACTOR | Checkliste: Minimalität, Duplikate, Lesbarkeit, Guideline-Compliance | Nach jedem GREEN |
| Test-Setup | Unit Tests / Integration Tests / Test-Utilities, Test-Namen-Format | Beim Einrichten neuer Test-Projekte |
| Test-Data-Builder | Builder-Methoden in EndpointsTestsBase, Schutz vor Schemaänderungen | Beim Anlegen neuer Entities |
| Parametrisierte Tests | TestCase / TestCaseSource, TDD-Kompatibilität, wann NICHT parametrisieren | Beim Testen gleichartiger Eingaben |
| Full State Assertion | BeEquivalentTo-Pflicht, Excluding-Regeln, API-Response vs. DB-State | Bei allen mutierenden Operationen (POST/PUT/DELETE) |
| Mutation Testing | Stryker-Konfiguration, Ziel 100%, Ausnahmen, Stryker-Kategorien für Defensive Guards | Am Ende jeder Phase und während Entwicklung |
| Branch Coverage | Coverlet (C#) / V8 (TS), Ziel 100%, Suppressionen | Nach jedem vollständigen Test-Lauf |

---

TDD bedeutet **Red → Green → Refactor** in dieser Reihenfolge, mit expliziten Verifikationsschritten. Tests nach der Implementierung schreiben ist **kein TDD**.

**Kernregel: IMMER EIN TEST AUF EINMAL.**
Erst wenn der aktuelle RED→GREEN→REFACTOR-Zyklus vollständig abgeschlossen ist, kommt der nächste Test. Nie mehrere Tests auf einmal schreiben, bevor die bisherigen grün sind.

## Outside-In ATDD / Double-Loop TDD

Beim Implementieren einer User Story gilt immer diese Reihenfolge:

```
1. Gherkin-Szenario schreiben         →  rot (noch kein Step-Code)
2. Frontend E2E-Test schreiben        →  rot (Backend nicht implementiert)
3. Backend Integration-Test schreiben →  rot (Endpoint nicht implementiert)
4. Implementierung je Schicht         →  pro Schicht: eigener roter Unit-Test → grün → Refactor
5. Refactor (Integration-Ebene)
```

Es gibt drei Loop-Ebenen. Der äußere Loop treibt den mittleren, der mittlere treibt den inneren:

```
äußere Schleife:  Gherkin → E2E-Test → rot
  mittlere Schleife:  Integration-Test → rot → (Schichten implementieren) → grün → Refactor
    innere Schleife:  Unit-Test (je Schicht) → rot → minimale Implementierung → grün → Refactor
    innere Schleife:  Unit-Test (nächste Schicht) → rot → ...
  → mittlere Schleife: Integration-Test grün? → weiter; sonst nächste Schicht
→ äußere Schleife fortsetzen bis Gherkin grün
```

**Schichten, die einen eigenen roten Unit-Test brauchen (Beispiele):**
- C# Custom Value Types (z. B. `IngredientName`, `Unit`) – eigener Konstruktor-/Validierungstest (entsteht im Inner Loop, wenn der Outer Loop eine Validierungsregel fordert – kein proaktives Schreiben)
- TypeScript Branded Types / Domain-Objekte (z. B. `IngredientId`, `ingredient.ts`) – eigener Unit-Test (analog: im Inner Loop, wenn durch Outer Loop gefordert)
- Services / Use-Case-Klassen – Unit-Test vor der Implementierung
- Repository-Logik (soweit nicht durch Integration-Test abgedeckt)
- React-Komponenten – Vitest-Komponenten-Test vor der Implementierung

**Regeln:**
- Kein Backend- oder E2E-Test ohne darüberliegendes Gherkin-Szenario
- Kein Produktionscode für eine Schicht ohne fehlschlagenden Test auf dieser Schicht
- Kein Produktionscode ohne fehlschlagenden Backend-Test
- Das Gherkin-Szenario ist die Spec – es darf nicht nachträglich angepasst werden, um die Implementierung zu bestätigen

**Vollständige BDD/Gherkin-Dokumentation:** `docs/E2E_TESTING.md`

---

## Phase 1 – RED (EIN Test schreiben)

**Vor-Bedingung (Before RED):**
- Existiert ein Gherkin-Szenario mit `@US-NNN`-Tag in `features/`?
- Nein → STOP. Szenario zuerst schreiben (`docs/E2E_TESTING.md`).
- Ja → Tag notieren – Test-Klasse erhält denselben Tag.

1. Schreibe **GENAU EINEN** Test, der das nächste konkrete Verhalten beschreibt
2. **Vor dem Schreiben prüfen:** Kodiert der Test eine Business-Entscheidung (Konfliktstrategie, fachliche Fehlerbehandlung)? → Per CLAUDE.md-Regel prüfen ob selbst entscheidbar oder nachfragen nötig. Selbst getroffene Entscheidungen in `docs/history/decisions.md` dokumentieren.
3. Führe diesen Test aus (nur diesen reicht – alle Tests mitlaufen lassen schadet nicht)
4. **PFLICHT-OUTPUT:** Bestätige explizit: *"Test [TestName] schlägt fehl mit: [Fehlermeldung]"*
5. Erst dann weiter zu Phase 2

Wenn der Test auf Anhieb grün ist, ist das ein **nachgelagertes Symptom**: Entweder wurde in Phase 2 Gold-Plating betrieben (hätte dort oder spätestens in Phase 3 auffallen müssen), oder der Test beschreibt kein neues Verhalten.
- **PFLICHT-OUTPUT:** *"Test [TestName] ist sofort grün. Ursache: [Gold-Plating in Phase 2 / Test testet nichts Neues]"*
- Bei Gold-Plating: Den vorzeitig geschriebenen Code **rückgängig machen**, den Test als RED bestätigen, dann minimal implementieren.
- Bei sinnlosem Test: Test löschen oder anpassen, sodass er echtes neues Verhalten beschreibt.

## Phase 2 – GREEN (Minimale Implementierung)

**"Fake it till you make it"** – das ist kein Cheat, sondern TDD-Methodik:
Die einfachste grüne Implementierung DARF und SOLL eine hardcodierte Rückgabe sein.

```csharp
// Erster Test: Get_EmptyList_Returns200WithEmptyLists
// Korrekte minimale Implementierung:
group.MapGet("/", () => Results.Ok(new ShoppingListResponseDto([], [])));

// FALSCH (Gold-Plating im GREEN-Schritt – echte DB-Logik noch nicht erzwungen):
group.MapGet("/", async (MahlDbContext db) => {
    var items = await db.ShoppingListItems.Select(...).ToListAsync();
    // ...
});
```

Der nächste Test (z.B. mit Items in der Liste) wird die hardcodierte Rückgabe zwingen,
durch echte Logik ersetzt zu werden. So entsteht nur Code, der durch Tests erzwungen ist.

**Prüffrage vor dem Schreiben:** *"Könnte ich diesen Test mit einem hardcodierten Return-Wert grün machen?"*
Wenn ja: tue es. Nächste Tests erzwingen die Generalisierung.

1. Schreibe die **kleinstmögliche** Implementierung, die **diesen einen** Test grün macht
2. **PFLICHT-CHECK vor dem Speichern:** Gehe jede neue Zeile durch und frage: *"Erzwingt der aktuelle rote Test diese Zeile?"* Wenn nein → Zeile löschen (oder auf hardcoded Wert reduzieren).
3. Führe **alle** Tests aus (sicherstellt, dass nichts kaputt gegangen ist)
4. **PFLICHT-OUTPUT:** Bestätige explizit: *"Alle [N] Tests grün"*
5. Erst dann weiter zu Phase 3

Jede Zeile, die kein roter Test erzwingt, ist Gold-Plating – auch wenn sie "offensichtlich sinnvoll" wirkt.

## Phase 3 – REFACTOR (Qualität herstellen)

Führe diese Checkliste explizit durch und dokumentiere das Ergebnis:

> **Tests sind gleichwertig mit Produktionscode.** Bei 100 % Testabdeckung sind sie sogar wichtiger:
> Sie bilden die vollständige Spezifikation ab. Der gesamte Produktionscode könnte weggeworfen und
> neu geschrieben werden – solange die Tests grün sind, ist die Anwendung noch "dieselbe".
> Der REFACTOR-Schritt gilt daher **immer für beides**: Produktionscode UND Tests.

- [ ] **Minimalität (zuerst prüfen!):** Gibt es Code, der durch keinen bisher existierenden Test erzwungen wird? → Löschen. Frage: *"Welcher Test würde fehlschlagen, wenn ich diese Zeile entferne?"* Kein Test → Zeile löschen.
- [ ] Gibt es Duplikate oder Copy-Paste zwischen diesem und bestehendem **Code oder Tests**?
- [ ] **Test-Lesbarkeit:** Ist jeder neue Test auf das Wesentliche reduziert? Gibt es Duplikation im Test-Setup, die durch einen **Test-Data-Builder** (`ACreateXxxDto(...)`, `AnIngredient(...)` etc.) beseitigt werden sollte? Builder für Request-DTOs gehören ebenfalls in `EndpointsTestsBase`.
- [ ] Sind alle neuen Namen klar und nach Ubiquitärer Sprache (GLOSSARY.md)?
- [ ] Haben neue Properties einen passenden Custom Value Type verdient?
- [ ] Ist eine Methode > ~20 Zeilen? → Extraktion erwägen
- [ ] Ist die Verschachtelung > 3 Ebenen? → Vereinfachung erwägen
- [ ] **Guideline-Compliance (C# Endpoints):** Nutzt der Endpoint Railway-Oriented Programming? (Sync-Validierung via `.Bind()/.Map()/.MapError()`, Async DB via `.BindAsync()`, Terminal via `.MatchAsync()` – kein `.IsT0/.IsT1` im Endpoint-Body.) Referenz: `docs/CODING_GUIDELINE_CSHARP.md`
- [ ] **Guideline-Compliance (TypeScript):** Werden Branded Types für IDs und andere Domain-Konzepte verwendet? Werden Fehler via `neverthrow` / `Result<T, E>` kommuniziert? Referenz: `docs/CODING_GUIDELINE_TYPESCRIPT.md`

**PFLICHT-OUTPUT:** *"Refactoring: [Was wurde geändert]"* oder *"Kein Refactoring nötig, weil: [Begründung]"*

Führe die Tests nochmals aus und bestätige grün.

---

**Wichtig:** Wenn du merkst, dass du Tests erst nach der Implementierung schreibst, halte an, dokumentiere das als Learning in `docs/kaizen/lessons_learned.md`, und schreibe für den Rest der Story Tests zuerst.

## Test-Ausführung

Ausführungsbefehle (`dotnet-test.py`, `dotnet-stryker.py`, Timeouts): `docs/DEV_WORKFLOW.md` – Sektion "Tests & Mutation Testing".

## Test-Setup

- **Alle Tests:** `Server.Tests/` – Domain Logic + API Endpoints (NUnit + FluentAssertions + Microsoft.AspNetCore.Mvc.Testing + EF InMemory)

> **Hinweis:** Production nutzt PostgreSQL – die Testinfrastruktur verwendet bewusst EF InMemory. Jeder Test läuft gegen eine isolierte, frische In-Memory-DB (`InstancePerTestCase` + `EnsureDeletedAsync`).
>
> **Bekannte Einschränkung:** EF InMemory erzwingt keine DB-Constraints (UNIQUE, FK). Tests für Constraint-Verletzungen (z.B. Duplicate-Name-409) müssen über explizite Endpoint-Logik abgesichert sein – nicht durch DB-Constraints. Das ist gewollt: Constraint-Logik gehört in den Endpoint-Layer, nicht in die DB. Wer PostgreSQL-spezifisches Verhalten testen will (z.B. Transaktionsisolation), braucht Testcontainers – das ist im SKELETON nicht vorgesehen.

Test-Namen-Format: `USxxx_ScenarioType_MethodName_Szenario_ErwartetesErgebnis`

`ScenarioType` entspricht exakt dem Gherkin-Tag-Suffix des Szenarios, das diesen Test im inneren ATDD-Loop erzwungen hat:

| Gherkin-Tag | ScenarioType |
|-------------|-------------|
| `@US-NNN-happy-path` | `HappyPath` |
| `@US-NNN-error` | `Error` |
| `@US-NNN-edge-case` | `EdgeCase` |

Beispiele: `US201_HappyPath_Create_ValidData_Returns201`, `US201_Error_Create_EmptyName_Returns422`

Wird dasselbe Verhalten von mehreren Szenarien exercised: Primär-Szenario taggen (das Szenario, das diesen Test im inneren Loop erzwungen hat). Kein Mehrfach-Tagging.

## Test-Data-Builder

Alle DB-Entities werden über Builder-Methoden in `EndpointsTestsBase` angelegt. Das schützt vor
Schemaänderungen: Kommt ein neues Pflichtfeld hinzu, wird nur der Builder angepasst.

```csharp
// In EndpointsTestsBase:
protected static IngredientDbType AnIngredient(
    string name = "Butter", string unit = "g",
    bool alwaysInStock = false, DateTimeOffset? deletedAt = null) =>
    new() { Name = name, DefaultUnit = unit, AlwaysInStock = alwaysInStock, DeletedAt = deletedAt };

// Im Test:
SeedIngredients([AnIngredient("Salz"), AnIngredient("Pfeffer", deletedAt: DateTimeOffset.UtcNow)]);
```

Für jede neue Entity-Art eine entsprechende Builder-Methode ergänzen.

## Parametrisierte Tests

**Vor jedem neuen Test prüfen: eigener Test oder weiterer `[TestCase]`?**

Bevor ein neuer Test geschrieben wird, zunächst fragen: *Ist das ein neues Szenario oder nur eine weitere Variation desselben Verhaltens?*

| Kriterium | Eigener Test | Weiterer `[TestCase]` |
|---|---|---|
| Setup-Logik | Unterschiedlich | Identisch |
| Assertion-Logik | Unterschiedlich | Identisch |
| Fachliche Bedeutung | Eigene Invariante / eigener Fehlerpfad | Gleiche Invariante, nur Input variiert |

Beispiele:
- `""`, `"   "`, `"\t"` für einen ungültigen Namen → alle testen dieselbe Invariante „leer oder nur Whitespace ist ungültig" → **`[TestCase]`**
- „Name leer" vs. „Name bereits vorhanden" → unterschiedliche fachliche Fehlerpfade → **eigene Tests**
- 1 ungültige Zutat vs. 2 Zutaten von denen eine ungültig ist → dieselbe Validierungsinvariante, nur Kontext variiert → **`[TestCase]`**

Gleichartige Testlogik mit variierenden Inputs/Outputs wird als ein parametrisierter Test geschrieben.
`[TestCase]` für einfache Werte, `[TestCaseSource]` für komplexe Objekte.

```csharp
[TestCase("",      "g",  "Name darf nicht leer sein")]
[TestCase("   ",   "g",  "Name darf nicht leer sein")]
[TestCase("Butter","",   "Einheit darf nicht leer sein")]
public async Task Create_InvalidInput_Returns422(string name, string unit, string expectedMessage) { ... }
```

**TDD-Kompatibilität:** Ersten Testfall als eigenen RED-Zyklus schreiben. Weitere Varianten
desselben Verhaltens in der REFACTOR-Phase als neue `[TestCase]`-Zeilen ergänzen.

**Nicht parametrisieren** wenn die Setup-Logik zwischen Fällen unterschiedlich ist oder der
ExpectedState dynamisch vom InitialState abhängt – dort eigene Testmethoden.

## Pflicht: Full State Assertion bei mutierenden Operationen

Endpoint-Tests, die Daten **anlegen, ändern oder löschen**, prüfen nach dem HTTP-Call den **vollständigen** DB-Zustand ("Full State Assertion") – nicht nur ob ein bestimmtes Item vorhanden ist. Nur so werden unerwartete Seiteneffekte (Extra-Rows, veränderte bestehende Einträge) sicher erkannt.

Da jeder Test in einer isolierten, frischen DB läuft (`InstancePerTestCase` + `EnsureDeletedAsync`), ist der Initialzustand immer bekannt – Full State Assertions sind daher einfach zu schreiben und zu lesen.

```csharp
// FALSCH: Nur Response geprüft
var response = await _client.PostAsJsonAsync("/api/ingredients", dto);
response.StatusCode.Should().Be(HttpStatusCode.Created);
created!.Name.Should().Be("Butter"); // → testet nur Serialisierung, nicht Persistenz

// FALSCH: Nur Teilzustand geprüft (ein Extra-Row bleibt unentdeckt)
GetAllIngredients().Should().ContainSingle(i => i.Name == "Butter");

// RICHTIG: Vollständiger Endzustand – DB-State-Assertion mit Excluding für auto-gen Id
var response = await _client.PostAsJsonAsync("/api/ingredients", dto);
response.StatusCode.Should().Be(HttpStatusCode.Created);
var created = await response.Content.ReadFromJsonAsync<IngredientDto>();
created!.Name.Should().Be("Butter");
GetAllIngredientsFromDb().Should().BeEquivalentTo(
    [new IngredientDbType { Name = "Butter", DefaultUnit = "g" }],
    o => o.Excluding(x => x.Id));
// Excluding(x => x.Id): Id ist auto-generiert – explizit benennen, was ignoriert wird.
// ExcludingMissingMembers() ist VERBOTEN (ignoriert stillschweigend alle fehlenden Properties).
```

**`BeEquivalentTo` ist die Standardmethode.** `HaveCount`, `ContainSingle` etc. sind nur unterstützend erlaubt, wenn `BeEquivalentTo` allein nicht ausreicht (z. B. für Zusatzprüfungen wie `DeletedAt != null`). `HaveCount(n)` allein ist kein Full State.

**`.Should().Contain(...)` ist verboten** – auch auf Strings. Es ist immer eine partielle Assertion:
- Für exakte String-Werte (inkl. Response-Bodies in Plain-Text) → `.Should().Be(exactString)`
- Für JSON-Response-Bodies → `ReadFromJsonAsync<T>()` + typisierte Assertion auf Properties

**Lesbarkeit in Expected-Objekten:**
Bei der Konstruktion datenführender Typen (Records, Structs, Klassen als Datencontainer) **müssen** benannte Argumente verwendet werden, damit sofort klar ist, welches Property welchen Wert hat:
```csharp
// FALSCH: Positionale Parameter ohne Namen – welcher Wert ist Name, welcher DefaultUnit?
new IngredientDto(id, "Butter", "g", false)

// RICHTIG: Benannte Argumente – jedes Property spricht für sich
new IngredientDto(Id: id, Name: "Butter", DefaultUnit: "g", AlwaysInStock: false)
```
Für `class`-basierte DB-Entities (EF Core) gilt dies nicht – dort werden ohnehin Object-Initializer mit Property-Namen verwendet: `new IngredientDbType { Name = "Butter", ... }`.

**Property-Ausschlüsse:**
- `Excluding(x => x.PropName)` – erlaubt, wenn eine Property genuinen Ignorierungsgrund hat (auto-generierte Id, Timestamp). Muss explizit begründbar sein.
- `ExcludingMissingMembers()` – **verboten**. Ignoriert stillschweigend alle fehlenden Properties; neue Properties im DTO bleiben ungetestet.

**API-Response vs. DB-State:**
- **API-Response (DTO):** Id aus DB holen (`GetAllXxxFromDb()[0].Id`) und vollständig vergleichen – testet, dass die API die korrekte Id zurückgibt.
- **DB-State nach Write:** `Excluding(x => x.Id)` verwenden – Id aus DB gegen DB wäre zirkulär.

Für Fehlerfälle gilt dasselbe – der erwartete Zustand nach einem Fehler ist der Ausgangszustand:
```csharp
// Nach einem fehlgeschlagenen POST: DB leer (war vorher leer)
GetAllIngredients().Should().BeEmpty();

// Nach einem fehlgeschlagenen POST auf eine DB mit Pre-Seed: Ausgangszustand unverändert
SeedIngredients([new() { Name = "Butter", DefaultUnit = "g" }]);
var stateBeforeAction = GetAllIngredients();
// ... POST mit Duplikat-Namen ...
GetAllIngredients().Should().BeEquivalentTo(stateBeforeAction); // exakt unverändert
```

Diese Regel gilt für POST (anlegen), PUT/PATCH (ändern), DELETE (löschen/soft-delete).

## Mutation Testing (Stryker.NET / Stryker-JS)

- **Ziel:** 100% Mutation Score
- **Ende jeder Phase:** Vollständiger Lauf (PFLICHT)
- **Während Entwicklung:** Nur geänderte Files: `python3 .claude/scripts/dotnet-stryker.py --mutate Endpoints/IngredientsEndpoints.cs`
- **Konfiguration:** `stryker-config.json` im Root (mit `coverage-analysis: "off"` für WebApplicationFactory)
- **Ausnahmen** (äquivalente Mutanten, müssen dokumentiert werden): Generated Code (EF Migrations), Framework-Boilerplate (Program.cs)

## Branch Coverage

- **C# Backend:** Coverlet (collector) mit `coverlet.runsettings` – automatisch bei vollem Test-Lauf (`dotnet-test.py` ohne `--filter`). Threshold: 100% Branch + Line.
- **TypeScript Frontend:** Vitest mit V8-Provider – `npm run test:coverage`. Threshold: 100% Branches, Functions, Lines, Statements.
- **Suppressionen:** C# via `[ExcludeFromCodeCoverage]` + Begründung in `docs/history/decisions.md`; TS via `/* v8 ignore next */` + Begründung. Suppressionen ohne Begründung sind verboten.

### Stryker-Survivor behandeln

**Ein Survivor bedeutet: Es fehlt eine Test-Assertion für echtes Verhalten.**

Die richtige Frage bei einem Survivor ist nie „Wie töte ich diesen Mutanten?", sondern immer: **„Welches Verhalten ist in meinen Tests bisher nicht dokumentiert?"** Stryker zeigt nur, wo die Lücke ist – der Test soll das fehlende Verhalten beschreiben, nicht den Mutanten erwähnen.

```
❌ "Test_KillsMutantAtLine48"
✅ "Create_UniqueName_WhenOtherActiveIngredientsExist_Returns201"
```

**Vorgehen bei einem Survivor:**

1. **Spec-Check:** Ist das Verhalten explizit durch die Spezifikation gefordert?
   - **Nein** → Code löschen (Gold-Plating). Alle Tests GREEN bestätigen. Stryker auf die Datei ausführen → Survivor darf nicht mehr erscheinen.
   - **Unsicher** → Nachfragen.
   - **Ja** → weiter zu 2.
2. **Überlebenden Code löschen.** Nur so ist RED im nächsten Schritt garantiert – Code, der bereits existiert, macht einen neuen Test sofort grün und verhindert den korrekten TDD-Zyklus.
3. **Test schreiben → RED bestätigen.**
4. **Code neu schreiben → GREEN bestätigen.**
5. **Stryker auf die Datei ausführen → Survivor darf nicht mehr erscheinen.**

**`// Stryker disable`** ist ausschließlich für echte äquivalente Mutanten erlaubt – d. h. wenn es beobachtbar keinen Unterschied macht, ob der Mutant überlebt (z. B. Route-String `"/"` vs. `""` in ASP.NET Core = identisches Routing-Verhalten). Jede Suppression muss in `docs/history/decisions.md` begründet werden. Suppression als Erstreaktion auf einen Survivor ist **verboten**.

**Bekannte äquivalente Mutanten – Defensive Guards:**

| Guard | Stryker-Kategorien | Begründung |
|-------|-------------------|------------|
| Parameterless-Ctor (`public T() => throw ...`) | `Statement,String` | Unerreichbar via normale Konstruktion (Factory Methods) |
| `default(T)`-Equality-Guard (`_id == default ? throw ...`) | `Equality,String` | Unerreichbar via normale Konstruktion |
| `Match`-Wildcard (`_ => throw new InvalidOperationException(...)`) | `Statement,String` | Unerreichbar durch privaten Konstruktor (externe Subtypen ausgeschlossen) |

Syntax und vollständige Kategorienliste: `docs/CSharp-Stryker.md`.

Stryker-Bezüge (Zeilennummern, Mutantentypen) gehören **nicht** in Test-Namen oder Kommentare.

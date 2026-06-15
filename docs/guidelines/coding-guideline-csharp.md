# Guideline für das Generieren von C#-Code

<!--
wann-lesen: Bevor du C#-Produktionscode oder Tests schreibst (nach docs/guidelines/coding-guideline-general.md)
kritische-regeln:
  - readonly record struct für Domain-Typen (Ausnahme: readonly struct bei Generics wie NonEmptyList<T>)
  - Create() nimmt Domain-Typen oder Primitives – kein DTO, kein DbType
  - ROP: .Bind()/.Map()/.MatchAsync() – kein .IsT0/.IsT1/.AsT0 im Produktionscode
  - throw nur für nicht-behebbare technische Ausnahmen – Domänenfehler via OneOf
  - Kein From() in Domain-Typen – DB-Rekonstruktion via ToDomain() → OneOf<Domain, Error<string>> im Mapping-Layer; Endpoints nutzen Results.Problem() statt throw bei Inkonsistenz
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| 1. Immutability & Typen | Typen-Tabelle (class/record/struct), keine public Setter, ImmutableList | Beim Erstellen neuer Klassen oder Typen |
| 2. Primitive Obsession | Value Objects statt string/int/Guid, Konvertierungsoperatoren | Beim Modellieren von Fachkonzepten |
| 3. Illegal States Unrepresentable | Private Ctors, Factory-Methoden, Default-Ctor bei struct absichern | Beim Erstellen von Domain-Typen |
| 4. Pure Functions & Extension Methods | Extension Methods für Geschäftslogik, OneOf als Rückgabe | Beim Kapseln von Logik ohne Seiteneffekte |
| 5. Domain-Typen (Architektur) | Systemgrenz-Architektur (Write/Read-Pfad), Dependency Rule, Typ-Deklarationen sind `internal`, Typ-Struktur, Datei-Orte, kanonisches Beispiel | Beim Anlegen neuer Entities oder Umstrukturierung des Domain-Layers |
| 6. Endpoints: ETag-Pflicht | ETag für alle Endpoints: xmin (Single Resource), Content-Hash (Collection), 304/412/428-Muster | Bei jedem neuen Endpoint |
| 7. Test-Code | Given/When/Then-Struktur (Pflicht), Full-State-Assertions (`BeEquivalentTo`) | Beim Schreiben von Backend-Tests |

**Ergänzende Richtlinien (separate Dateien):**

| Datei | Wann lesen |
|-------|------------|
| `docs/guidelines/csharp-rop.md` | Beim Schreiben von Endpoints oder Validierungsketten (`.Bind()/.Map()/.MatchAsync()`) |
| `docs/guidelines/csharp-sumtypes.md` | Beim Modellieren neuer Domain-Typen mit Zustandsvarianten (z.B. `RecipeSource`, `Quantity`) |
| `docs/guidelines/csharp-stryker.md` | Beim Behandeln von Stryker-Survivors in Phase 3 (REFACTOR) |

> **Voraussetzung:** Lies zuerst `docs/guidelines/coding-guideline-general.md` (KISS, Naming, Komplexität, übergreifende Paradigmen). Diese Datei beschreibt nur die C#-spezifische Umsetzung.

1. Unveränderlichkeit (Immutability) & Typen:

Verwende den richtigen Typ je nach Rolle:

| Rolle | Typ | Begründung |
|-------|-----|------------|
| EF-Core-Entity (Datenbanktabelle) | `class` | EF Change Tracking und Proxy-Support erfordern Referenztyp mit mutierbaren Properties |
| DTO (Request/Response, JSON) | `record` (mit `init;`) | Vollständig kompatibel mit `System.Text.Json`; immutabel nach Deserialisierung |
| Value Object / Domain-Typ | `readonly record struct` | Wertsemantik, strukturelle Gleichheit, kein Overhead durch Heap-Allokation |

- Eigenschaften dürfen keine öffentlichen Setter haben. Erlaubt: `get; init;` (DTOs/records) oder `get;` mit Konstruktor-Zuweisung (Value Objects).
- EF-Entities dürfen `private set;` für Change-Tracking nutzen – nirgendwo sonst.
- Verwende für Collections ausschließlich unveränderliche Strukturen (z.B. `IImmutableSet<T>`, `ImmutableList<T>`, `IEnumerable<T>`). Ändern einer Liste bedeutet, eine neue Liste zurückzugeben.

**Ausnahmen** (von diesen Regeln bewusst ausgenommen):
- `Infrastructure/DatabaseTypes/**` – EF-Entities als `class` mit `private set;` erlaubt
- `Infrastructure/Migrations/**` – generierter Code, keine Kontrolle
- `**/*Options.cs`, `**/*Settings.cs` – ASP.NET Options-Pattern erfordert `class`

2. Vermeidung von "Primitive Obsession":

- Verwende keine Primitives (string, int, Guid) direkt in den Geschäftsmodellen. Kapsle sie stattdessen in stark typisierte Value Objects (z.B. Username, EmailAddress, ItemId).
- Implementiere implizite/explizite Konvertierungsoperatoren (implicit operator, explicit operator) für eine ergonomische Nutzung der Value Objects.
- **Ausnahme – BCL-Typen mit struktureller Garantie:** `System.Uri` darf direkt als Parameter in `Create()` verwendet werden, weil `new Uri("")` und `new Uri(null)` eine `UriFormatException` bzw. `ArgumentNullException` werfen – ein leeres oder null-Uri-Objekt ist schlicht nicht konstruierbar. `Uri` repräsentiert damit immer eine syntaktisch gültige, nicht-leere URI. Fachliche Invarianten (z.B. Absolutheit) werden trotzdem explizit im Domain-Guard geprüft. `Guid`, `int`, `decimal` und `DateTimeOffset` fallen **nicht** in diese Ausnahme – sie haben keine strukturellen Garantien (z.B. `Guid.Empty`, `DateTimeOffset.MinValue` sind valid konstruierbar).

**Zwei-Ebenen-Regel (wichtig):**

| Ebene | `Create()`-Signatur | Begründung |
|---|---|---|
| **Value Object** (`NonEmptyTrimmedString`, `Quantity` …) | Nimmt Primitives (`string`, `decimal?`) | *Hier ist* die Validierung – das ist der Sinn des Value Objects |
| **Domain Entity** (`Ingredient`, `Recipe` …) | Nimmt Domain-Typen (`NonEmptyTrimmedString`, …) | Vertraut den Typen; prüft nur Entity-Invarianten (Cross-Field, etc.) |

`string` und andere ungesicherte Primitive gehören **nicht in Entity-`Create()`-Parameter**. Ein roher `string` landet weder als Parameter noch als Property in einer Domain-Entity. Die Validierung liegt beim Aufrufer (Endpoint oder `ToDomain()`). So macht der Compiler ungültige Aufrufe unmöglich, und Entity-`Create()` hat keine gemischte Verantwortung (String-Validierung + Entity-Invarianten).

3. "Make Illegal States Unrepresentable" (Sichere Instanziierung):

- Konstruktoren für Domänen-Objekte müssen private sein.
- Objekte dürfen nur über statische Factory-Methoden (z.B. Create(...), New(...)) instanziiert werden.
- **`new T()` absichern:** Der parameterlose Konstruktor bei `readonly record struct` muss `throw new InvalidOperationException("Uninitialized")` enthalten. Das fängt `new T()` ab.
- **`default(T)` absichern:** `default(T)` ruft den Konstruktor **nicht** auf – er null-initialisiert alle Felder. Properties, die auf Felder zeigen, die dadurch einen ungültigen Zustand haben können, müssen einen Guard enthalten:
  - Referenztypen (z. B. `string _value`): `_value ?? throw new InvalidOperationException("Uninitialized")`
  - Value Types ohne sinnvollen Default (z. B. `Guid _id`): `_id == default ? throw new InvalidOperationException("Uninitialized") : _id`
  - Domain-Typen, die selbst einen Guard haben (z. B. `NonEmptyTrimmedString _name`), werfen transitiv beim Zugriff auf deren Property – kein zusätzlicher Guard nötig.
**Defensive Guards – Konzept:**

"Make Illegal States Unrepresentable" schützt zur Compile-Zeit. Manche Sprachfeatures umgehen das: `new T()` auf Structs und `default(T)` rufen den privaten Konstruktor nicht auf. Ein Defensive Guard ist ein Laufzeit-Check der diese Sprach-Bypasses auffängt – **kein Business-Code**. Er ist defensiv, wenn er über normalen Aufrufpfaden strukturell unerreichbar ist.

**Defensive Guards und Stryker-Suppressionen:**

Parameterless-Ctor-Guards und `default(T)`-Guards sind in der Hexagonal Architecture nicht testbar: Domain-Typen sind `internal`, kein `InternalsVisibleTo` – Testcode kann `new T()` und `default(T)` nicht aufrufen. Stryker markiert sie daher immer als Survivors. Pflicht-Unterdrückung direkt vor der betroffenen Zeile:

```csharp
// Stryker disable once Statement,String : parameterless ctor unreachable via normal construction
public Ingredient() => throw new InvalidOperationException("Uninitialized");

// Stryker disable once Equality,String,Conditional : default(T) guard unreachable via normal construction
public Guid Id => _id == default ? throw new InvalidOperationException("Uninitialized") : _id;
```

Jede Suppression zusätzlich in `docs/history/adr.md` begründen (einmalig pro Typ-Kategorie genügt).

4. Reine Funktionen (Pure Functions) & Extension Methods:

- Geschäftslogik, die den Zustand eines Objekts "verändert", wird oft als statische Klasse mit Extension Methods implementiert, die den alten Zustand aufnimmt und ein OneOf<NeuerZustand, Error<string>> zurückgibt.

## Code-Beispiel als Referenz-Stil:

### Value Object (nimmt Primitives – hier findet die Validierung statt)

```csharp
public readonly record struct ValidName
{
    private readonly string _value;
    public string Value => _value ?? throw new InvalidOperationException("Uninitialized");

    private ValidName(string value) => _value = value;

    // Value Objects nehmen rohe Primitives – sie SIND die Validierungsebene.
    public static OneOf<ValidName, Error<string>> Create(string input)
    {
        var trimmed = input?.Trim();
        if (string.IsNullOrEmpty(trimmed))
            return new Error<string>("Name cannot be empty.");

        return new ValidName(trimmed);
    }

    public static implicit operator string(ValidName name) => name.Value;
}
```

### Domain Entity (nimmt Domain-Typen – vertraut den Typen, prüft nur Entity-Invarianten)

Das kanonische Entity-Beispiel steht weiter unten (Sektion "Kanonisches Beispiel"): `Ingredient.Create(Guid, NonEmptyTrimmedString, NonEmptyTrimmedString)` – kein roher `string`.

Halte dich bei allem von dir erstellem oder gereviewtem Code strikt an dieses Paradigma. Prüfe: Hält Code mutable state (set), exceptions für Business Logic und nackte Primitive (wie string title) aus Entitäts-Konstruktoren heraus? Das ist der Maßstab.

5. Domain-Typen (Pflicht für alle Entities mit Create-Vorgängen):

### `internal`-Pflicht für Typ-Deklarationen

Alle Typ-Deklarationen (`class`, `record`, `struct`, `interface`, `enum`) in `Server/` sind **`internal`** – kein `public` ohne explizite Begründung. Das betrifft die Typdeklaration selbst, nicht Member-Sichtbarkeit – Member bleiben `private`/`protected` wo nötig.

```csharp
// ✅ Korrekt
internal readonly record struct Ingredient { ... }
internal static class IngredientsEndpoints { ... }
internal record CreateIngredientDto(...);
file static class IngredientMappings { ... }  // file-scoped ist implizit internal

// ❌ Falsch – public ohne Begründung
public readonly record struct Ingredient { ... }
public static class IngredientsEndpoints { ... }
```

**Ausnahme:** `Infrastructure/`-Typen (`MahlDbContext`, `*DbType`) sind `public` – das ist das einzige öffentliche Projekt.

**Begründung:** Erzwingt, dass Tests ausschließlich über HTTP-Ports exercisen (Black-Box-Testing, Hexagonal Architecture). Ohne `InternalsVisibleTo` kann Testcode keine Domain-Typen direkt instantiieren. Vollständige Begründung: `docs/reference/architecture.md` Sektion 0c.

### Systemgrenz-Architektur

- **Write-Pfad**: `CreateDto` → `Domain.Create(dto)` (alle Validierungen) → DbType (Persistenz-Mapping)
- **Read-Pfad**: DbType → `ToDomain()` → `OneOf<Domain, Error<string>>` (Rekonstruktion im Mapping-Layer) → bei Fehler `Results.Problem(detail, statusCode: 500)` → bei Erfolg DTO
- Die Domäne vertraut weder Request-Daten noch DB-Daten – `Create()` ist die einzige Einstiegsmethode
- **Layer-Isolation:** DB-Inkonsistenz (fehlerhafte Daten in der Datenbank) darf kein unbehandeltes `throw` auslösen. `Results.Problem(detail, statusCode: 500)` gibt strukturiertes `application/problem+json` zurück – testbar per ContentType und Body-Assertion. Unbehandelte Exceptions geben HTML/plain-text zurück und sind nicht testbar.

### Dependency Rule

```
Endpoint-Datei (Mapping-Layer)
  ↓ kennt alle drei Welten
Domain-Typ    DbType    DTO
  (keine gegenseitigen Abhängigkeiten zwischen den drei)
```

- Domain-Typen kennen **weder** DbTypes **noch** externe Infrastruktur
- `Create(...)` nimmt Domain-Typen oder Primitives als Input
- Mapping-Code (DbType ↔ Domain, Domain → DTO) lebt in **`file static class`-Extension Methods** in der jeweiligen Endpoint-Datei (z.B. `IngredientsEndpoints.cs`). Nicht zwischen Endpoints geteilt – `file`-Sichtbarkeit erzwingt das und verhindert stilles Drift.
- **Kein `From()`**: DB-Rekonstruktion via `ToDomain()` → `OneOf<Domain, Error<string>>` im Mapping-Layer. Endpoints behandeln Fehler mit `Results.Problem(detail, statusCode: 500)` – kein `throw` im Endpoint-Body.

### Typ-Struktur

- `readonly record struct` – Compiler-generierte Equality, parameterlosen Konstruktor public lassen und mit `throw new InvalidOperationException("Uninitialized")` absichern
- Ausnahme: `readonly struct` (statt `readonly record struct`) wenn ein **privater** parameterloser Konstruktor benötigt wird – z.B. `NonEmptyList<T>`. `record struct` erzwingt einen `public` parameterlosen Ctor (nur Runtime-Guard möglich). `readonly struct` erlaubt `private T() {}` → `new NonEmptyList<T>()` wird **Compile-Fehler**. (Hinweis: `record struct` unterstützt Generics problemlos – das ist nicht der Grund.)
- `Create(...)` → `OneOf<DomainType, Error<string>>` für User-Input und für Validierung beim Lesen aus der DB
- Keine `ToDto()`/`ToDbType()`-Methoden am Domain-Typ selbst

### Ort

- `Server/Domain/` für Domain-Entities (Rezept, Zutat, etc.)
- `Server/Types/` für generische Value Objects (z.B. `NonEmptyTrimmedString`, `NonEmptyList<T>`)

### Kanonisches Beispiel

```csharp
// Server/Domain/Ingredient.cs
internal readonly record struct Ingredient
{
    private readonly Guid _id;
    private readonly NonEmptyTrimmedString _name;
    private readonly NonEmptyTrimmedString _defaultUnit;

    // Guid hat keinen sinnvollen default – Guard gegen default(Ingredient).Id:
    public Guid Id => _id == default ? throw new InvalidOperationException("Uninitialized") : _id;
    // NonEmptyTrimmedString wirft selbst transitiv – kein zusätzlicher Guard nötig:
    public NonEmptyTrimmedString Name => _name;
    public NonEmptyTrimmedString DefaultUnit => _defaultUnit;

    // Parameterless ctor must be public (record struct limitation) – fängt new Ingredient() ab:
    public Ingredient() => throw new InvalidOperationException("Uninitialized");
    private Ingredient(Guid id, NonEmptyTrimmedString name, NonEmptyTrimmedString defaultUnit)
    {
        _id = id; _name = name; _defaultUnit = defaultUnit;
    }

    // Guid id als erstes Primitive – für neue Entities: Guid.CreateVersion7(), für DB: db.Id
    // Create() akzeptiert nur validierte Domain-Typen – kein OneOf nötig wenn keine Cross-Field-Invarianten
    public static Ingredient Create(Guid id, NonEmptyTrimmedString name, NonEmptyTrimmedString defaultUnit) =>
        new Ingredient(id, name, defaultUnit);
}

// IngredientsEndpoints.cs – file-level mapping
file static class IngredientMappings
{
    // DB-Rekonstruktion: Validierung hier, weil DB-Strings zu Domain-Typen konvertiert werden müssen
    public static OneOf<Ingredient, Error<string>> ToDomain(this IngredientDbType db) =>
        NonEmptyTrimmedString.Create(db.Name)
            .MapError(_ => new Error<string>($"DB inconsistency in Ingredient #{db.Id}: Name is empty"))
            .Bind(name => NonEmptyTrimmedString.Create(db.DefaultUnit)
                .MapError(_ => new Error<string>($"DB inconsistency in Ingredient #{db.Id}: DefaultUnit is empty"))
                .Map(unit => Ingredient.Create(db.Id, name, unit)));

    public static IngredientDto ToDto(this Ingredient domain, bool alwaysInStock) =>
        new(domain.Id, domain.Name.Value, domain.DefaultUnit.Value, alwaysInStock);
}
```

Endpoint – lesender Pfad mit `Results.Problem()`:
```csharp
group.MapGet("/{id:int}", async (int id, MahlDbContext db) =>
{
    var ingredient = await db.Ingredients.Where(i => i.Id == id && i.DeletedAt == null).FirstOrDefaultAsync();
    if (ingredient is null) return Results.NotFound();
    return ingredient.ToDomain().Match(
        domain => Results.Ok(domain.ToDto(ingredient.Id, ingredient.AlwaysInStock)),
        e      => Results.Problem(e.Value, statusCode: StatusCodes.Status500InternalServerError));
});
```

## 6. Endpoints – ETag-Pflicht

Alle Endpoints implementieren ETag-Support.
Entscheidung + Begründung: `docs/history/adr.md` → Sektion "HTTP-Caching & Optimistic Concurrency".

**ETag-Quelle:**
- Single-Resource-Endpoint: `xmin`-Wert des Rows (PostgreSQL, via Npgsql `UseXminAsConcurrencyToken()`), hex-kodiert: `$"\"{xmin:x8}\""`. Zugriff: `(uint)db.Entry(row).Property("xmin").CurrentValue!`
- Collection-Endpoint: **voller** SHA-256-Hash der serialisierten Response-Body, gebildet von einer generischen Middleware (ADR-S084-1). Format & Vergleich (ADR-S084-2): `$"\"{Convert.ToHexString(SHA256.HashData(body))}\""` (Uppercase-Hex aus dem Encoder, **keine** Truncation, **kein** nachgelagerter `.ToUpper()/.ToLower()`-Call); `If-None-Match` ordinal/verbatim vergleichen (nie case-insensitive). Gründe: vermeidet un-killbare Stryker-Survivor (Casing-Normalisierung + Magic-Number-Truncation). **Voraussetzung:** Collection deterministisch sortieren – sonst variiert der Hash und 304 feuert nie.

**Pflicht-Verhalten:**
| Endpoint | Situation | Header | Response |
|----------|-----------|--------|----------|
| GET | ETag unverändert | `If-None-Match` trifft zu | 304 |
| GET | ETag geändert | – | 200 + `ETag`-Header |
| PUT/PATCH/DELETE | `If-Match` fehlt | – | 428 |
| PUT/PATCH/DELETE | `If-Match` stimmt nicht | `If-Match` ≠ aktuellem ETag | 412 |
| PUT/PATCH/DELETE | `If-Match` stimmt | EF Core prüft `xmin` beim `SaveChanges` nochmals | – |

`UseXminAsConcurrencyToken()` in `OnModelCreating` konfigurieren, bevor der erste GET-Endpoint für eine Entity gebaut wird.

## 7. Test-Code – Struktur und Assertions

### Given/When/Then-Struktur in Tests (Pflicht)

Jeder neue Test muss durch `// Given`, `// When`, `// Then`-Kommentare gegliedert sein. Die Kommentare helfen beim Review, jede Assertion dem passenden Akzeptanzkriterium des Gherkin-Szenarios zuzuordnen.

```csharp
[Fact]
public async Task GetIngredients_ReturnsList()
{
    // Given
    var ingredient = new IngredientDbType { Id = Guid.NewGuid(), Name = "Tomaten", DefaultUnit = "kg" };
    DbContext.Ingredients.Add(ingredient);
    await DbContext.SaveChangesAsync();

    // When
    var response = await Client.GetAsync("/api/ingredients");

    // Then
    response.StatusCode.Should().Be(HttpStatusCode.OK);
    var body = await response.Content.ReadFromJsonAsync<List<IngredientDto>>();
    body.Should().ContainSingle(i => i.Name == "Tomaten");
}
```

### Full-State-Assertions

Bei `BeEquivalentTo`-Aufrufen müssen alle verglichenen Properties durch ein Akzeptanzkriterium des Szenarios gedeckt sein.

- `Excluding(...)` ist erlaubt, muss aber mit einem Kommentar begründet werden.
- Unchecked oder excluded Properties ohne Begründung sind ein Gold-Plating-Signal: Sie deuten auf Produktionscode hin, der nicht durch ein Szenario gefordert ist.

```csharp
// ✓ Korrekt – alle Properties durch AKs gedeckt
result.Should().BeEquivalentTo(new { Name = "Tomaten", DefaultUnit = "kg" });

// ✓ Erlaubt mit Begründung
result.Should().BeEquivalentTo(expected, options => options
    .Excluding(x => x.Id));
// Id wird in separater Assertion geprüft

// ✗ Ohne Begründung – Gold-Plating-Signal
result.Should().BeEquivalentTo(expected, options => options
    .Excluding(x => x.DeletedAt));
```
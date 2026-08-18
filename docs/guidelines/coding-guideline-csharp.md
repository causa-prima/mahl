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
| 2. Primitive Obsession | Drei-Ebenen-Regel (Constraint-Typ / Domänentyp / Entity) und ihre fünf Regeln, Konvertierungsoperatoren | Beim Modellieren von Fachkonzepten |
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
| Constraint-Typ, Domänentyp, Domain-Entity (§2) | `readonly record struct` | Wertsemantik, strukturelle Gleichheit, kein Overhead durch Heap-Allokation |

> **Zwei Bedeutungen von „Entity":** Zeile 1 meint die **EF-Core-Entity** (Persistenz, `Infrastructure/DatabaseTypes/`). §2 meint die **Domain-Entity** (`Ingredient`, `readonly record struct`, `Server/Domain/`). Verschiedene Ebenen, gleicher Name – im Zweifel den Ordner ansehen.

- Eigenschaften dürfen keine öffentlichen Setter haben. Erlaubt: `get; init;` (DTOs/records) oder `get;` mit Konstruktor-Zuweisung (Value Objects).
- EF-Entities dürfen `private set;` für Change-Tracking nutzen – nirgendwo sonst.
- Verwende für Collections ausschließlich unveränderliche Strukturen (z.B. `IImmutableSet<T>`, `ImmutableList<T>`, `IEnumerable<T>`). Ändern einer Liste bedeutet, eine neue Liste zurückzugeben.

**Ausnahmen** (von diesen Regeln bewusst ausgenommen):
- `Infrastructure/DatabaseTypes/**` – EF-Entities als `class` mit `private set;` erlaubt
- `Infrastructure/Migrations/**` – generierter Code, keine Kontrolle
- `**/*Options.cs`, `**/*Settings.cs` – ASP.NET Options-Pattern erfordert `class`
- Reine **E2E-/Test-Support-Endpoints** (nur in der E2E-Umgebung gemappt, z.B. `E2ETestSupport.cs`; ADR-S084-4 Addendum) – dürfen direkt auf `MahlDbContext` zugreifen und sind von den Domain-Typ-/DTO-/Mapping-Pflichten (auch Sektion 5, „Endpoints") ausgenommen; sie tragen keine Domänenlogik. **Nicht** als Vorlage für produktive Endpoints verwenden.

2. Vermeidung von "Primitive Obsession":

- Verwende keine Primitives (string, int, Guid) direkt in den Geschäftsmodellen. Kapsle sie stattdessen in stark typisierte Value Objects (z.B. Username, EmailAddress, ItemId). „Value Object" ist dabei der Oberbegriff; die Drei-Ebenen-Regel unten trennt ihn in **Constraint-Typ** und **Domänentyp**, und nur der Domänentyp steht in Signaturen.
- Implementiere implizite/explizite Konvertierungsoperatoren (implicit operator, explicit operator) für eine ergonomische Nutzung der Value Objects.
- **Ausnahme – BCL-Typen mit struktureller Garantie:** `System.Uri` darf direkt als Parameter in `Create()` verwendet werden, weil `new Uri("")` und `new Uri(null)` eine `UriFormatException` bzw. `ArgumentNullException` werfen – ein leeres oder null-Uri-Objekt ist schlicht nicht konstruierbar. `Uri` repräsentiert damit immer eine syntaktisch gültige, nicht-leere URI. Fachliche Invarianten (z.B. Absolutheit) werden trotzdem explizit im Domain-Guard geprüft. `Guid`, `int`, `decimal` und `DateTimeOffset` fallen **nicht** in diese Ausnahme – sie haben keine strukturellen Garantien (z.B. `Guid.Empty`, `DateTimeOffset.MinValue` sind valid konstruierbar).

**Drei-Ebenen-Regel:**

| Ebene | Ort | `Create()`-Signatur | Rolle |
|---|---|---|---|
| **Constraint-Typ** (`NonEmptyTrimmedString`, `Bounded<…>` …) | `Server/Types/` | Nimmt Primitives (`string`, `decimal`) | Ein **Prädikat über einer Repräsentation** – feldagnostisch, über Fachkonzepte hinweg wiederverwendbar. *Hier ist* die Validierungsmechanik |
| **Domänentyp** (`IngredientName`, `Unit` …) | `Server/Domain/` | Nimmt Primitives | Eine **Rolle in der Fachsprache** – an *ein* Fachkonzept gebunden, dort aber überall geteilt (Regel 2). Baut sich aus Constraint-Typen und trägt die Feldregeln |
| **Entity** (`Ingredient`, `Recipe` …) | `Server/Domain/` | Nimmt Domänentypen | Vertraut den Typen; prüft nur Entity-Invarianten (Cross-Field, etc.) |

`string` und andere ungesicherte Primitive gehören **nicht in Entity-`Create()`-Parameter**. Ein roher `string` landet weder als Parameter noch als Property in einer Domain-Entity. Die Validierung liegt beim Aufrufer (Endpoint oder `ToDomain()`). So macht der Compiler ungültige Aufrufe unmöglich, und Entity-`Create()` hat keine gemischte Verantwortung (String-Validierung + Entity-Invarianten).

### Domänentyp und Constraint-Typ – fünf Regeln

**Regel 1 – Der Domänentyp ist die Schnittstelle, der Constraint-Typ die Implementierung.**
Der Domänentyp *benutzt* Constraint-Typen als Baumaterial; **Constraint-Typen stehen nie in Signaturen** – weder in `Create()`-Parametern noch in Properties einer Entity. Wird die zulässige Menge eines Domänentyps später aufzählbar (Enum) oder strukturiert (Sum-Type), verschwindet der Constraint-Typ ersatzlos. Genau das ist der Ertrag: Steht der Constraint-Typ in Signaturen, ist ein Implementierungsdetail geleckt, und der absehbare Wechsel `Unit`: string → Enum wird zur Breaking Change an jeder Signatur statt zur Änderung in einer Datei.

**Regel 2 – Rolle ≠ Typ.**
`BaseUnit`, Alternativeinheiten, Rezept- und Einkaufslisten-Einheit sind alle `Unit` – ein geteilter Domänentyp, kein Typ je Verwendungsstelle. Der Grund ist nicht Sparsamkeit: Mehrere Typen für dasselbe Konzept verteilen seine Regeln auf mehrere **Änderungsorte**; eine spätere Verschärfung muss an jedem nachgezogen werden, und ein vergessener ist unsichtbar. Die Regel „keine rohen Primitive" (oben) verbietet nur das Primitive – **nicht** einen eigenen Typ je Property fürs selbe Konzept. Das leistet erst diese Regel.

*Ausnahme, eng zu halten:* eine Rolle mit **eigener Invariante** bekommt einen eigenen Typ. Beispiel: `Amount` und `ConversionFactor` – dieselbe Repräsentation (beide über einem `float > 0`-Constraint-Typ), verschiedene Bedeutung. Der Test ist das **Verhalten unter Operationen**, nicht der Name: `Amount × ConversionFactor = Amount` ist sinnvoll, `Amount + ConversionFactor` ist Unsinn. Ein bloßes Synonym (`CustomerName`/`ClientName`) ist ein *Begriff*, kein Konzept, und bekommt keinen Typ.

**Regel 3 – Verwechslungsschutz ist Nebenprodukt, kein Entwurfsziel.**
Nie fragen „brauche ich hier einen Typ gegen Vertauschen?", sondern „ist das ein eigenes Fachkonzept?". Zwei Parameter desselben Konzepts dürfen denselben Typ haben. Sonst beginnt die Rutschbahn zu einem Typ pro Parameter.

**Regel 4 – Abwesenheit ist keine Einschränkung.**
Bevor ein Wert einen Sonderfall bekommt (`Guid.Empty`, `-1`, `""`), prüfen, ob eigentlich Optionalität gemeint ist. Optionalität gehört out-of-band (Union/`Option`), nie ins Wertband des Domänentyps – ein In-band-Sentinel ist genau der Zustand, den „Make Illegal States Unrepresentable" ausschließen soll.

**Regel 5 – Regeln in den Domänentyp, Meldungen an die Grenze.**
Die Feldregeln (Länge, Wertebereich) leben im Typ. Die Zuordnung *Fehlerfall → deutscher Text* bleibt an der API-Grenze, die das Request-Format kennt (ADR-S051-2). Ein Domänentyp gibt einen Fehler**fall** zurück, nie einen Meldungstext.

Der Fehlertyp gehört dabei zum **Konzept**, nicht zum Feld und nicht zur Entität (ADR-S120-1): `IngredientName.Create` liefert `IngredientNameError`, `Unit.Create` liefert `UnitError`. Er trägt keinen Feldnamen – den kennt die Grenze statisch, und ein geteilter Domänentyp (Regel 2) kennt seine Verwendungsstelle ohnehin nicht. Ein geteilter Typ bekommt deshalb **je Verwendungsstelle** eine eigene Zuordnung zum Meldungstext, bleibt aber ein Typ.

**Parametrisierte Einschränkungen stehen im Typ (ADR-S119-1).** Eine Grenze wie „max. 30 Zeichen" ist kein handgeschriebener Check in `Create()`, sondern der Typ des privaten Feldes – so ist sie nicht vergessbar. Da C# keine const generics kennt, trägt ein Marker-Typ je Grenzwert den Wert:

```csharp
// Server/Domain/IngredientName.cs
internal readonly record struct IngredientName
{
    private readonly Bounded<NonEmptyTrimmedString, Max30> _value;   // ADR-S051-3: Grenze steht im Typ
    public string Value => _value.Value;                             // wirft transitiv

    // Stryker disable once Statement,String : parameterless ctor (ADR-S041-9)
    public IngredientName() => throw new InvalidOperationException("Uninitialized");
    private IngredientName(Bounded<NonEmptyTrimmedString, Max30> value) => _value = value;

    // Regel 5: der Typ liefert die Fehlerfälle SEINES Konzepts, keine Texte und keinen Feldbezug.
    public static OneOf<IngredientName, IngredientNameError> Create(string input) =>
        Bounded<NonEmptyTrimmedString, Max30>.Create(input)
            .MapError<Bounded<NonEmptyTrimmedString, Max30>, StringViolation, IngredientNameError>(v => v switch
            {
                StringViolation.Empty   => IngredientNameError.Empty,
                StringViolation.TooLong => IngredientNameError.TooLong,
                _ => SumType.Unreachable<IngredientNameError>(),
            })
            .Map(v => new IngredientName(v));
}
```

Die Träger (`IStringConstraint<TSelf>`, `IMaxLength`, `NonEmptyTrimmedString`, `Bounded<TInner, TMax>`, Marker je Grenzwert) liegen in `Server/Types/StringConstraints.cs` – bewusst eine Datei, weil sie nur gemeinsam les- und änderbar sind (dafür ein `MA0048`-Block in `.editorconfig`). Warum Trimmen und Nicht-Leer in **einem** Träger stecken statt in zwei komponierbaren, und wann die Aufspaltung fällig wird: ADR-S119-1, Abschnitt „Warum `NonEmptyTrimmedString`".

Ein geteilter Domänentyp wie `Unit` (Regel 2) baut sich genauso, nur mit `Max20` und `UnitError` – der Fehlertyp gehört zum Konzept, nicht zur Entität, und trägt deshalb über alle Entitäten (ADR-S120-1).

> **Sollform, nicht Bauauftrag.** Wie die Beispiele hier zu lesen sind – insbesondere, dass eine 1:1-Umsetzung ohne treibendes Szenario gegen vorrangige Regeln verstößt – steht in `coding-guideline-general.md`, Sektion „Wie Code-Beispiele in Guidelines zu lesen sind". Neuer Code folgt der Sollform; bestehender wird bei Berührung nachgezogen.

**Geltungsbereich:** Die Regeln enden an der DTO-/DbType-Grenze. `mahl.Infrastructure` ist `public`, `mahl.Server` `internal` – ein Domänentyp kann dort gar nicht auftauchen (`docs/reference/architecture.md`). `Name` und `BaseUnit` bleiben im DTO und im DbType deshalb `string`.

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

### Constraint-Typ (nimmt Primitives – hier findet die Validierung statt)

```csharp
internal readonly record struct TrimmedNonEmpty
{
    private readonly string _value;
    public string Value => _value ?? throw new InvalidOperationException("Uninitialized");

    private TrimmedNonEmpty(string value) => _value = value;

    // Constraint-Typen nehmen rohe Primitives – sie SIND die Validierungsebene (§2, Ebene 1).
    // Sie liefern einen Verstoß, keinen Meldungstext: der Typ ist feldagnostisch und kennt
    // weder Feldnamen noch Request-Format (Regel 5, ADR-S051-2).
    public static OneOf<TrimmedNonEmpty, StringViolation> Create(string input)
    {
        var trimmed = input?.Trim();
        if (string.IsNullOrEmpty(trimmed))
            return StringViolation.Empty;

        return new TrimmedNonEmpty(trimmed);
    }
}
```

### Domain Entity (nimmt Domänentypen – vertraut den Typen, prüft nur Entity-Invarianten)

Das kanonische Entity-Beispiel steht weiter unten (Sektion „Kanonisches Beispiel") – ausschließlich Domänentypen als Parameter, kein rohes `Guid`/`string`.

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

- **Write-Pfad**: `CreateDto` → `ToDomain(dto)` im Mapping-Layer (baut die Domänentypen, **sammelt alle** Feldfehler – ADR-S090-1) → DbType (Persistenz-Mapping). Das DTO bleibt im Mapping-Layer; `Domain.Create(...)` sieht es nie (Dependency Rule unten)
- **Read-Pfad**: DbType → `ToDomain()` → `OneOf<Domain, Error<string>>` (Rekonstruktion im Mapping-Layer) → bei Fehler `Results.Problem(detail, statusCode: 500)` → bei Erfolg DTO
- Die Domäne vertraut weder Request-Daten noch DB-Daten – `Create()` ist die einzige Einstiegsmethode
- **Layer-Isolation:** DB-Inkonsistenz (fehlerhafte Daten in der Datenbank) darf kein unbehandeltes `throw` auslösen. `Results.Problem(detail, statusCode: 500)` gibt strukturiertes `application/problem+json` zurück – testbar per ContentType und Body-Assertion. Unbehandelte Exceptions geben HTML/plain-text zurück und sind nicht testbar.

### Provider-/Assembly-spezifische Aufrufe nicht inline in `Program.Main`

- Provider-/Assembly-spezifische Aufrufe (EF-Relational `MigrateAsync()`, Npgsql o.ä.), die nur unter einer bestimmten Umgebung laufen (z.B. hinter `if (env.IsE2E)`), **nicht inline** in `Program.<Main>$` setzen, sondern in eine **eigene Methode** auslagern.
- Grund: JIT ist per-Methode lazy, löst aber **innerhalb** einer Methode beim Kompilieren alle referenzierten Assemblies auf – ein *nicht genommener* `if`-Branch schützt nicht. Ein Test-Host mit anderem Provider (`WebApplicationFactory` + InMemory) scheitert sonst schon beim JIT von `Main` mit `FileNotFoundException` auf der Relational-Assembly, obwohl der Zweig nie ausgeführt wird. Der Body der ausgelagerten Methode JITtet erst beim tatsächlichen Aufruf.

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

- `Server/Domain/` für **Domain-Entities** (Rezept, Zutat, …) **und Domänentypen** (`IngredientName`, `Unit`) – beide Ebenen der Drei-Ebenen-Regel aus §2 liegen hier
- `Server/Types/` ausschließlich für **Constraint-Typen** (z.B. `NonEmptyTrimmedString`, `Bounded<TInner, TMax>`) und geteilte Bausteine (`SumType`, `NonEmptyList<T>`)

### Kanonisches Beispiel

```csharp
// Server/Domain/Ingredient.cs
internal readonly record struct Ingredient
{
    // Ausschließlich Domänentypen – kein rohes Guid/string (§2, Drei-Ebenen-Regel).
    private readonly IngredientId _id;
    private readonly IngredientName _name;
    private readonly Unit _baseUnit;

    // Alle drei werfen selbst transitiv beim Zugriff – kein Guard in der Entity nötig.
    // Der default(T)-Guard sitzt im jeweiligen Domänentyp, nicht hier (§3).
    public IngredientId Id => _id;
    public IngredientName Name => _name;
    public Unit BaseUnit => _baseUnit;

    // Parameterless ctor must be public (record struct limitation) – fängt new Ingredient() ab:
    public Ingredient() => throw new InvalidOperationException("Uninitialized");
    private Ingredient(IngredientId id, IngredientName name, Unit baseUnit)
    {
        _id = id; _name = name; _baseUnit = baseUnit;
    }

    // Create() akzeptiert nur validierte Domänentypen – kein OneOf nötig wenn keine Cross-Field-Invarianten
    public static Ingredient Create(IngredientId id, IngredientName name, Unit baseUnit) =>
        new Ingredient(id, name, baseUnit);
}

// Server/OneOfExtensions.cs – Applicative-Kombinator neben Map/Bind/MapError (ADR-S119-2).
// Bind kann nicht sammeln: es schließt beim ersten Fehler kurz. Collect wertet seine Eingänge
// unabhängig aus und konkateniert deren Fehler. Nur so bleibt Collect-All auf dem Gleis, statt
// den Fehlerkanal per MapError(_ => …) durch parallel berechneten Zustand zu ersetzen.
// Ein Overload je Arity – Begründung und verworfene Alternativen: ADR-S119-2.
internal static OneOf<TOut, IReadOnlyList<TError>> Collect<T1, T2, TOut, TError>(
    OneOf<T1, TError> first, OneOf<T2, TError> second, Func<T1, T2, TOut> combine);

internal static OneOf<TOut, IReadOnlyList<TError>> Collect<T1, T2, T3, TOut, TError>(
    OneOf<T1, TError> first, OneOf<T2, TError> second, OneOf<T3, TError> third,
    Func<T1, T2, T3, TOut> combine);

// IngredientsEndpoints.cs – file-level mapping
file static class IngredientMappings
{
    // Fehlerfall eines Feldes → Feldname. Reines MapError; hier sitzen die Typargumente,
    // die der Compiler beim Wechsel des Fehlertyps nicht inferieren kann.
    private static OneOf<T, string> OrFieldName<T, TError>(this OneOf<T, TError> field, string fieldName) =>
        field.MapError<T, TError, string>(_ => fieldName);

    // READ-Pfad: collect-all. Der Empfänger ist das Log bzw. der 500-Detailtext (ADR-S039-3:
    // 500 + problem+json bei korrupter DB-Zeile, kein silent null) – wer eine korrupte Zeile
    // repariert, braucht alle kaputten Felder auf einmal, nicht eines pro Durchlauf.
    public static OneOf<Ingredient, Error<string>> ToDomain(this IngredientDbType db) =>
        Collect(
                IngredientId.Create(db.Id).OrFieldName(nameof(db.Id)),
                IngredientName.Create(db.Name).OrFieldName(nameof(db.Name)),
                Unit.Create(db.BaseUnit).OrFieldName(nameof(db.BaseUnit)),
                Ingredient.Create)
            .MapError<Ingredient, IReadOnlyList<string>, Error<string>>(fields =>
                new Error<string>($"DB inconsistency in Ingredient #{db.Id}: invalid {string.Join(", ", fields)}"));

    // WRITE-Pfad: collect-all (ADR-S090-1) – der 422-Body nennt alle Feldfehler gleichzeitig.
    // Gleiche Bauform wie oben; die Pfade unterscheiden sich nur darin, wie die Fehlermenge
    // verbraucht wird.
    //
    // Das Ergebnis trägt KEINE Identität – es ist die validierte Nutzlast, nicht die Entity.
    // Die Id vergibt allein der anlegende Endpoint (ADR-S030-1); ein Pfad, der denselben Body nur
    // validiert (Restore – die Zeile steht über den Routenparameter fest), braucht gar keine.
    // Damit gibt es keinen Ingredient ohne brauchbare Id, und der Compiler verhindert, dass ein
    // solcher an eine Grenze gerät, die eine Identität voraussetzt (Regel 4).
    internal static OneOf<IngredientValues, IReadOnlyList<FieldError>> ToValues(this IngredientValuesDto dto) =>
        Collect(
            IngredientName.Create(dto.Name).MapError(DescribeName),
            Unit.Create(dto.BaseUnit).MapError(DescribeBaseUnit),
            (name, unit) => (Name: name, BaseUnit: unit));

    // Fehlerfall → (Request-Property, fester deutscher Text). Je Verwendungsstelle eine eigene
    // Zuordnung – `Unit` ist geteilt, die Rezept-Einheit bekommt später ihre eigene (ADR-S120-1).
    private static FieldError DescribeName(IngredientNameError e) => e switch
    {
        IngredientNameError.Empty   => new FieldError("name", "Name darf nicht leer sein."),
        IngredientNameError.TooLong => new FieldError("name", "Name darf maximal 30 Zeichen lang sein."),
        _ => SumType.Unreachable<FieldError>(),
    };

    // Zur Grenze hin wieder Primitives – Domänentypen enden hier (Geltungsbereich, §2).
    // Die Zuordnung Fehlerfall → deutscher Text liegt ebenfalls hier, nicht im Typ (Regel 5).
    public static IngredientDto ToDto(this Ingredient domain, bool alwaysInStock) =>
        new(domain.Id.Value, domain.Name.Value, domain.BaseUnit.Value, alwaysInStock);
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
    var ingredient = new IngredientDbType { Id = Guid.NewGuid(), Name = "Tomaten", BaseUnit = "kg" };
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
result.Should().BeEquivalentTo(new { Name = "Tomaten", BaseUnit = "kg" });

// ✓ Erlaubt mit Begründung
result.Should().BeEquivalentTo(expected, options => options
    .Excluding(x => x.Id));
// Id wird in separater Assertion geprüft

// ✗ Ohne Begründung – Gold-Plating-Signal
result.Should().BeEquivalentTo(expected, options => options
    .Excluding(x => x.DeletedAt));
```
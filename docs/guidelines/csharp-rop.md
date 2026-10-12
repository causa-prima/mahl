# Railway-Oriented Programming (ROP) – C# Referenz

<!--
wann-lesen: Beim Schreiben von Endpoints oder Validierungsketten (.Bind()/.Map()/.MatchAsync()).
Voraussetzung: docs/guidelines/coding-guideline-csharp.md (Core-Regeln) bereits gelesen.
-->

<a id="ROP-fehlerbehandlung"></a>
## Railway-Oriented Programming (Fehlerbehandlung ohne Exceptions)

- Verwende das Paket OneOf (`OneOf<T, TError>`), um Erfolgs- und Fehlerfälle explizit im Rückgabetyp zu deklarieren. `TError` ist ein benannter Fehlerfall des Konzepts (z.B. `IngredientNameError`, ADR-S120-1), kein Meldungstext – den erzeugt erst die API-Grenze (ADR-S051-2). `Error<string>` nur für technische Fehler beim Rekonstruieren aus der DB.
- Verwende `.Match(...)`, `.Switch(...)` und `.Bind(...)` für den Kontrollfluss. Vermeide klassische `if/else`-Blöcke, wo Pattern Matching oder Monaden-Verkettung möglich sind.

**`throw` ist eine Ausnahme – keine Regel:**
`throw` darf ausschließlich für nicht-behebbare technische Ausnahmezustände verwendet werden (z.B. uninitialisierter Value-Object-Zustand im Default-Konstruktor, Datenbankverbindung komplett ausgefallen). Domänen- und Validierungsfehler werden **immer** über `OneOf` mit typisiertem Fehlerfall zurückgegeben. Jedes `throw new` im Produktionscode ist ein Review-Pflichtpunkt und muss explizit kommentiert begründet werden. In Tests ist `throw`/`try/catch` erlaubt.

<a id="ROP-allgemein"></a>
### ROP – Allgemein (gilt für den gesamten Produktionscode)

| Kontext | Regel |
|---------|-------|
| Sync-Validierungsketten | MÜSSEN `.Bind()` / `.Map()` / `.MapError()` verwenden |
| Abschluss der Kette | MUSS mit `.Match()` oder `.MatchAsync()` enden |
| Async DB-Operationen | Dürfen *innerhalb* eines `.BindAsync()`-Lambdas early returns (`if/return`) nutzen – das Lambda ist eine abgeschlossene async Funktion, kein Orchestrierungsschritt |

**Im gesamten Produktionscode ausschließlich `.Match(ok => ..., err => ...)` oder `.MatchAsync(...)` verwenden** (Negativ-Beispiele):
```csharp
if (result.IsT1) return ...;  // ❌ imperatives IsT-Check
result.AsT0                   // ❌ ohne .Match()
result.IsT0                   // ❌ imperatives IsT-Check
```

**OneOf-Instanz erzeugen: impliziter Cast statt `FromT0` / `FromT1`**

OneOf definiert `implicit operator`-Überladungen – bevorzuge diese gegenüber den expliziten Factory-Methoden:

```csharp
// ❌ Vermeiden: ausführlich und API-spezifisch
return OneOf<Recipe, RecipeError>.FromT0(recipe);
return OneOf<Recipe, RecipeError>.FromT1(RecipeError.NotFound);

// ✅ Bevorzugen: kürzer, idiomatisch, gleiche Typsicherheit
return recipe;
return RecipeError.NotFound;
// Ist ein Zweig ein Interface (z.B. IResult), greift der implizite Cast nicht – siehe Ausnahmen unten.
```

**Bekannte Ausnahmen – Rangfolge (höchste zuerst):**

| Situation | Lösung |
|-----------|--------|
| Lambda mit mehreren `return`-Statements verschiedener Typen → Compiler kann `TOut` für `BindAsync` nicht inferieren | Explizite Typargumente am Methodenaufruf: `.BindAsync<TIn, TOut, TError>(...)` |
| Ternäre Expression mit heterogenen Branches (`T0` und Fehlertyp) | Expliziter Cast auf einen Branch: `? (OneOf<T, UnitError>) value : UnitError.Empty` |
| Source-Typ ist ein **Interface** (z.B. `IResult`) | `FromT1(...)` — C# wendet user-defined implicit operators für Interface-Typen grundsätzlich nicht an, weder implizit noch per explicit cast |
| Seed-Argument für `Aggregate` o.ä. — kein Zieltyp vorhanden | Expliziter Cast: `(OneOf<T0, T1>) value` |

<a id="ROP-oneof-iresult"></a>
### OneOf→IResult in Endpoints

Endpoints geben immer `IResult` zurück. `OneOf<T, TError>` ist ein internes Muster, dessen Fehlertyp am Endpoint per `MapError` auf `IResult` abgebildet wird – erst dort entsteht der Meldungstext:

```csharp
// ❌ Falsch – err ist der Fehlertyp der Kette, nicht IResult
return values.MatchAsync(ok => Results.Ok(ok), err => err);

// ✅ Richtig – MapError mit expliziten Typparametern bildet den Fehlertyp auf IResult ab
return values
    .MapError<IngredientValues, IReadOnlyList<FieldError>, IResult>(ValidationProblemFor)
    .MatchAsync(ok => Results.Ok(ok), err => err);
```

**Warum explizite Typparameter statt Cast `(IResult)...`?**
In realen Endpoints folgt auf `MapError` meist ein `BindAsync` mit mehreren `return`-Statements, bei dem der Compiler `TError` nicht inferieren kann (→ "Bekannte Ausnahmen"-Tabelle oben). Die expliziten Typparameter lösen das Problem an beiden Stellen konsistent:

```csharp
// Referenz-Pattern (gekürzt aus IngredientsEndpoints.cs, CreateIngredient):
await dto.ToValues()   // Collect über IngredientName.Create / Unit.Create → OneOf<IngredientValues, IReadOnlyList<FieldError>>
    .MapError<IngredientValues, IReadOnlyList<FieldError>, IResult>(ValidationProblemFor)
    .Map(values => Ingredient.Create(IngredientId.New(), values.Name, values.BaseUnit))
    .BindAsync<Ingredient, IngredientDto, IResult>(async ingredient =>
    {
        // DB-Logik – if/return hier erlaubt (abgeschlossenes Lambda)
        try { await db.SaveChangesAsync(); }
        catch (DbUpdateException ex) when (/* Unique-Violation */)
        {
            // liefert OneOf<IngredientDto, IResult>; darin: IResult ist Interface →
            // FromT1 nötig (kein user-defined implicit operator für Interfaces)
            return await SoftDeletedOrDuplicateConflict(dbType, ingredient, db);
        }
        return ingredient.ToDto(xmin); // DTO → impliziter Cast
    })
    .MatchAsync(
        created => Results.Created($"/api/ingredients/{created.Id}", created),
        error   => error);
```

<a id="ROP-value-or-throw"></a>
### Pre-validiertes Unwrap: `ValueOrThrowUnreachable()` (noch nicht implementiert)

> **Status: Muster, noch kein Code.** `Server/OneOfExtensions.cs` enthält aktuell **nur** `Map`/`Bind`/`MapError`/`BindAsync`/`MatchAsync`. `ValueOrThrowUnreachable()` (und das hier ebenfalls erwähnte `ValueOrThrow(string)`) existieren **nicht** – sie sind das vorgesehene Muster für den ersten Fall, der ein pre-validiertes Unwrap in einer LINQ-Pipeline braucht. Wer den Helper zuerst benötigt: in `OneOfExtensions.cs` anlegen und die Designentscheidung (zentralisierte Stryker-Suppression statt throw-Lambda) per ADR festhalten. Bis dahin gibt es keinen Aufrufer.

Wenn eine `OneOf<T, TError>`-Instanz in einer LINQ-Pipeline vorkommt und der Fehlerfall durch eine vorgelagerte Validierung nachweislich ausgeschlossen ist, soll ein gekapseltes `.ValueOrThrowUnreachable()` verwendet werden – **nicht** das rohe `.Match(r => r, _ => throw ...)`.

```csharp
// ❌ Verboten: throw-Lambda direkt im LINQ-Select
.Select(i => RecipeIngredient.Create(...).Match(r => r, _ => throw new InvalidOperationException("Unreachable.")))

// ✅ Ziel-Muster: ValueOrThrowUnreachable() aus OneOfExtensions (erst anzulegen)
.Select(i => RecipeIngredient.Create(...).ValueOrThrowUnreachable())
```

Der Helper soll das Throw-Pattern sowie die Stryker-Suppression an einer einzigen Stelle kapseln. **Warum nicht `.Match(r => r, _ => throw ...)`?** Weil der throw-Pfad unreachable ist und Stryker ihn als Survivor markiert. Ein zentraler `ValueOrThrowUnreachable()` zentralisiert die Suppression – alle Aufrufer profitieren ohne eigene Suppression.

**Voraussetzung:** Die Inputs wurden bereits in einer `.Bind()`-Kette validiert. `ValueOrThrowUnreachable()` ist kein Ersatz für echte Fehlerbehandlung – nur für nachweislich unerreichbare Fehlerpfade.

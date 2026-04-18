# Railway-Oriented Programming (ROP) – C# Referenz

<!--
wann-lesen: Beim Schreiben von Endpoints oder Validierungsketten (.Bind()/.Map()/.MatchAsync()).
Voraussetzung: docs/CODING_GUIDELINE_CSHARP.md (Core-Regeln) bereits gelesen.
-->

## 4. Railway-Oriented Programming (Fehlerbehandlung ohne Exceptions)

- Verwende das Paket OneOf (insbesondere `OneOf<Success, Error<string>>` oder `OneOf<T, Error<string>>`), um Erfolgs- und Fehlerfälle explizit im Rückgabetyp zu deklarieren.
- Verwende `.Match(...)`, `.Switch(...)` und `.Bind(...)` für den Kontrollfluss. Vermeide klassische `if/else`-Blöcke, wo Pattern Matching oder Monaden-Verkettung möglich sind.

**`throw` ist eine Ausnahme – keine Regel:**
`throw` darf ausschließlich für nicht-behebbare technische Ausnahmezustände verwendet werden (z.B. uninitialisierter Value-Object-Zustand im Default-Konstruktor, Datenbankverbindung komplett ausgefallen). Domänen- und Validierungsfehler werden **immer** über `OneOf`/`Error<string>` zurückgegeben. Jedes `throw new` im Produktionscode ist ein Review-Pflichtpunkt und muss explizit kommentiert begründet werden. In Tests ist `throw`/`try/catch` erlaubt.

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
return OneOf<Recipe, IResult>.FromT0(recipe);
return OneOf<Recipe, IResult>.FromT1(Results.NotFound());

// ✅ Bevorzugen: kürzer, idiomatisch, gleiche Typsicherheit
return recipe;
return Results.NotFound();
```

**Bekannte Ausnahmen – Rangfolge (höchste zuerst):**

| Situation | Lösung |
|-----------|--------|
| Lambda mit mehreren `return`-Statements verschiedener Typen → Compiler kann `TOut` für `BindAsync` nicht inferieren | Explizite Typargumente am Methodenaufruf: `.BindAsync<TIn, TOut, TError>(...)` |
| Ternäre Expression mit heterogenen Branches (`T0` und `Error<string>`) | Expliziter Cast auf einen Branch: `? (OneOf<T, Error<string>>) value : new Error<string>(...)` |
| Source-Typ ist ein **Interface** (z.B. `IResult`) | `FromT1(...)` — C# wendet user-defined implicit operators für Interface-Typen grundsätzlich nicht an, weder implizit noch per explicit cast |
| Seed-Argument für `Aggregate` o.ä. — kein Zieltyp vorhanden | Expliziter Cast: `(OneOf<T0, T1>) value` |

### OneOf→IResult in Endpoints

Endpoints geben immer `IResult` zurück. `OneOf<T, Error>` ist ein internes Muster, das am Endpoint-Ende zu `IResult` gecastet wird:

```csharp
// ❌ Falsch – err ist Error<string>, nicht IResult
return value.MatchAsync(ok => Results.Ok(ok), err => err);

// ✅ Richtig – MapError mit expliziten Typparametern konvertiert Error-Typ auf IResult
return value
    .MapError<TDomain, Error<string>, IResult>(e => Results.UnprocessableEntity(e.Value))
    .MatchAsync(ok => Results.Ok(ok), err => err);
```

**Warum explizite Typparameter statt Cast `(IResult)...`?**
In realen Endpoints folgt auf `MapError` meist ein `BindAsync` mit mehreren `return`-Statements, bei dem der Compiler `TError` nicht inferieren kann (→ "Bekannte Ausnahmen"-Tabelle oben). Die expliziten Typparameter lösen das Problem an beiden Stellen konsistent:

```csharp
// Referenz-Pattern (aus IngredientsEndpoints.cs):
return await Ingredient.Create(id, dto.Name, dto.DefaultUnit)
    .MapError<Ingredient, Error<string>, IResult>(e => Results.UnprocessableEntity(e.Value))
    .BindAsync<Ingredient, (IngredientDbType entity, Ingredient domain), IResult>(async ingredient =>
    {
        // DB-Logik – if/return hier erlaubt (abgeschlossenes Lambda)
        // IResult ist Interface → FromT1 nötig (kein user-defined implicit operator für Interfaces)
        if (softDeleted != null)
            return OneOf<(IngredientDbType, Ingredient), IResult>.FromT1(Results.Conflict(...));
        // ...
        return (entity, ingredient); // Tupel → impliziter Cast
    })
    .MatchAsync(
        result => Results.Created(...),
        error  => error);
```

### Pre-validiertes Unwrap: `ValueOrThrowUnreachable()`

Wenn eine `OneOf<T, Error<string>>`-Instanz in einer LINQ-Pipeline vorkommt und der Fehlerfall durch eine vorgelagerte Validierung nachweislich ausgeschlossen ist, darf `.ValueOrThrowUnreachable()` verwendet werden – **nicht** das rohe `.Match(r => r, _ => throw ...)`.

```csharp
// ❌ Verboten: throw-Lambda direkt im LINQ-Select
.Select(i => RecipeIngredient.Create(...).Match(r => r, _ => throw new InvalidOperationException("Unreachable.")))

// ✅ Korrekt: ValueOrThrowUnreachable() aus OneOfExtensions
.Select(i => RecipeIngredient.Create(...).ValueOrThrowUnreachable())
```

`ValueOrThrowUnreachable()` ist in `Server/OneOfExtensions.cs` definiert und kapselt das Throw-Pattern sowie die Stryker-Suppression an einer einzigen Stelle. **Warum nicht `.Match(r => r, _ => throw ...)`?** Weil der throw-Pfad unreachable ist und Stryker ihn als Survivor markiert. `ValueOrThrowUnreachable()` zentralisiert die Suppression – alle Aufrufer profitieren ohne eigene Suppression.

Es gibt außerdem `ValueOrThrow(string message)` für Fälle mit eigener Fehlermeldung.

**Voraussetzung:** Die Inputs wurden bereits in einer `.Bind()`-Kette validiert. `ValueOrThrowUnreachable()` ist kein Ersatz für echte Fehlerbehandlung – nur für nachweislich unerreichbare Fehlerpfade.

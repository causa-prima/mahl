# Stryker-Inline-Suppressions – C# Referenz

<!--
wann-lesen: Beim Behandeln von Stryker-Survivors in [REFACTOR](../process/tdd-process.md#TDD-refactor) (REFACTOR).
Hinweis: Die Pflicht-Suppressionen für Defensive Guards (parameterless ctor, default(T))
stehen bereits in docs/guidelines/coding-guideline-csharp.md [Illegal States Unrepresentable](coding-guideline-csharp.md#CGC-illegal-states) mit Beispielen.
-->

<a id="STK-suppressions"></a>
## Stryker-Inline-Suppressions (für äquivalente Mutanten)

Äquivalente Mutanten (beobachtbar kein Unterschied, z. B. unerreichbarer Code durch private Ctor) werden mit einem Inline-Kommentar auf der Zeile **vor** dem Mutanten unterdrückt:

```csharp
// Stryker disable once <Kategorie> : <Begründung> (<erlaubende ADR> | Einzelfall, vom User freigegeben S<NNN>)
// Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
public Ingredient() => throw new InvalidOperationException("Uninitialized");
```

**Wann ist eine Suppression berechtigt?** Das regelt allein [Welcher Survivor bekommt welche Reaktion?](../process/tdd-process.md#TDD-survivor-entscheidung). Eine Suppression ist **kein Ersatz für einen fehlenden Test**. Der `_`-Arm einer Sum-Type-Fallunterscheidung braucht keine eigene: Er ist `SumType.Unreachable<T>()`, die Suppression sitzt einmal zentral ([csharp-sumtypes](csharp-sumtypes.md)).

**Kategoriename** (Stryker.NET 4.x): ohne Suffix „Mutation" schreiben.

| Kategoriename | Beispiel-Mutant |
|---------------|----------------|
| `String` | `"text"` → `""`, `""` → `"Stryker was here!"` |
| `Equality` | `==` → `!=` |
| `Logical` | `&&` → `\|\|` |
| `Linq` | `OrderBy` → `OrderByDescending` |
| `Statement` | einzelne Anweisung entfernt |
| `Block` | ganzer Block entfernt (z.B. ein `catch`-Rumpf) |
| `NullCoalescing` | `a ?? b` → `a` bzw. `b` |
| `Conditional` | `true`/`false` Ersatz |

Die Tabelle nennt die im Projekt genutzten Kategorien (alle in Suppressionen im Code belegt), nicht alle
von Stryker.NET – weitere stehen in der Stryker.NET-Doku unter „Mutations".

**Syntaxregel:** Beschreibungstext zwingend nach Doppelpunkt – ohne Doppelpunkt wird die Suppression von Stryker ignoriert:
```csharp
// Stryker disable once String : unreachable due to private ctor   ✅
// Stryker disable once String unreachable due to private ctor     ❌ (kein Doppelpunkt → wirkt nicht)
```

**Mehrere Kategorien:** Komma-separiert ohne Leerzeichen zwischen den Kategorien:
```csharp
// Stryker disable once String,Statement : Tag name has no routing or behavioral impact   ✅
// Stryker disable once String Statement : ...                                             ❌ (Leerzeichen → nur erste Kategorie wirkt)
```

**Pflicht:** Die Begründung nennt die ADR, die diese Klasse von Suppression erlaubt – oder, bei einem Einzelfall, die Freigabe des Users. Wann suppressed werden darf und wann der User entscheidet: [Welcher Survivor bekommt welche Reaktion?](../process/tdd-process.md#TDD-survivor-entscheidung).

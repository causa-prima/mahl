# Stryker-Inline-Suppressions – C# Referenz

<!--
wann-lesen: Beim Behandeln von Stryker-Survivors in Phase 3 (REFACTOR).
Hinweis: Die Pflicht-Suppressionen für Defensive Guards (parameterless ctor, default(T))
stehen bereits in docs/CODING_GUIDELINE_CSHARP.md Sektion 3 mit Beispielen.
-->

## 8. Stryker-Inline-Suppressions (für äquivalente Mutanten)

Äquivalente Mutanten (beobachtbar kein Unterschied, z. B. unerreichbarer Code durch private Ctor) werden mit einem Inline-Kommentar auf der Zeile **vor** dem Mutanten unterdrückt:

```csharp
// Stryker disable once <Kategorie> : <Begründung>
_ => throw new InvalidOperationException("Unreachable.")
```

**Wann ist eine Suppression berechtigt?** Ausschließlich bei echten äquivalenten Mutanten – d. h. wenn es beobachtbar keinen Unterschied macht, ob der Mutant überlebt oder nicht (z. B. unerreichbarer Code durch private Ctor). Eine Suppression ist **kein Ersatz für einen fehlenden Test**.

**Kategoriename** (Stryker.NET 4.x): ohne Suffix „Mutation" schreiben.

| Kategoriename | Beispiel-Mutant |
|---------------|----------------|
| `String` | `"text"` → `""` |
| `Equality` | `==` → `!=` |
| `Logical` | `&&` → `\|\|` |
| `Linq` | `OrderBy` → `OrderByDescending` |
| `Statement` | Block-Entfernung |
| `Conditional` | `true`/`false` Ersatz |

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

**Pflicht:** Jede Suppression in `docs/history/decisions.md` begründen.

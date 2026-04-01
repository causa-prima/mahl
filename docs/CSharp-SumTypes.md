# Sum Types / Discriminated Unions – C# Referenz

<!--
wann-lesen: Beim Modellieren neuer Domain-Typen mit Zustandsvarianten (z.B. RecipeSource, Quantity).
Voraussetzung: docs/CODING_GUIDELINE_CSHARP.md (Core-Regeln) bereits gelesen.
-->

## 5. Sum Types / Discriminated Unions

Modelliere verschiedene Zustände immer als distinkte Typen (ADTs), niemals als Flag-Kombinationen. Dies gilt für alle Arten von Zustandsunterscheidungen:

**Verbotene Muster:**
```csharp
bool IsEmpty;              // ❌ Boolean-Flag
string Status;             // ❌ String-basierter Zustand
bool HasError; string? ErrorMessage;  // ❌ inkonsistente Flag+Nullable-Kombination
MyType? Value;             // ❌ null als impliziter Sonderzustand (in Domain-Typen verboten)
decimal? Quantity;         // ❌ null als "nach Geschmack" – stattdessen eigener Summentyp

// ❌ Öffentliche Subtypen – Consumer kann switch ohne Exhaustiveness-Garantie schreiben,
//    externe Subtypen definieren und Subtypen direkt konstruieren
public abstract record RecipeSource;
public sealed record UrlSource(...) : RecipeSource;
public sealed record NoSource : RecipeSource;
```

**Korrekte Modellierung:**

**Variante A – verschachtelte `private` Subtypen (Standard):**

Subtypen sind `private sealed record` innerhalb des Basistyps. Transitionen, die neue Subtypen erzeugen müssen, sind Methoden auf dem Basistyp. Lesende Operationen können als Extension Methods in derselben Datei leben.

```csharp
// Server/Domain/RecipeSource.cs
public abstract record RecipeSource
{
    private RecipeSource() { }  // verhindert externe Subtypen (stärkste Kapselung)

    private sealed record UrlCase(NonEmptyTrimmedString Url) : RecipeSource;
    private sealed record NoSourceCase : RecipeSource;

    public static RecipeSource FromUrl(NonEmptyTrimmedString url) => new UrlCase(url);
    public static RecipeSource None { get; } = new NoSourceCase();

    // Match<T> ist public für Wert-Träger-Sum-Types – der Mapping-Layer benötigt es.
    // Bei operationalen Sum-Types mit reichhaltigen Domänenoperationen: Match internal,
    // Consumer nutzen nur benannte Methoden.
    public T Match<T>(Func<NonEmptyTrimmedString, T> onUrl, Func<T> onNone) => this switch
    {
        UrlCase u    => onUrl(u.Url),
        NoSourceCase => onNone(),
        _ => throw new InvalidOperationException("Unreachable.") // private ctor prevents external subtypes
    };

    // explicit: Konvertierung nach string? verliert die Fallunterscheidung – nicht reversibel.
    // implicit: nur wenn verlustfrei und reversibel (z.B. NonEmptyTrimmedString → string).
    public static explicit operator string?(RecipeSource source) =>
        source.Match(onUrl: url => (string?)url, onNone: () => null);
}
```

**Variante B – `file`-scoped Subtypen + `private protected` Konstruktor:**

Wenn alle Operationen inklusive Transitionen als Extension Methods geführt werden sollen (Guideline 6), können Subtypen als top-level `file`-Records in derselben Datei definiert werden. Der Basiskonstruktor muss dann `private protected` sein – `private` würde den Aufruf durch top-level-Records verhindern.

```csharp
// Server/Domain/ShoppingList.cs
file sealed record EmptyCase : ShoppingList;
file sealed record PopulatedCase(ImmutableList<ShoppingListItem> Items) : ShoppingList;

public abstract record ShoppingList
{
    // private protected: externe Assemblies können nicht subtypen;
    // innerhalb des Assembly gilt Konvention + Code-Review
    private protected ShoppingList() { }

    public static ShoppingList Empty { get; } = new EmptyCase();

    internal T Match<T>(Func<T> onEmpty, Func<ImmutableList<ShoppingListItem>, T> onPopulated) =>
        this switch
        {
            EmptyCase     => onEmpty(),
            PopulatedCase p => onPopulated(p.Items),
            _ => throw new InvalidOperationException("Unreachable.")
        };
}

// Extension Methods in derselben Datei – können file-scoped Subtypen direkt konstruieren
public static class ShoppingListExtensions
{
    public static ShoppingList Add(this ShoppingList list, ShoppingListItem item) =>
        list.Match(
            onEmpty: () => new PopulatedCase([item]),
            onPopulated: items => new PopulatedCase(items.Add(item))
        );
}
```

**Regeln:**
- Subtypen sind immer `private sealed record` (Variante A) oder `file sealed record` (Variante B). Öffentliche Subtypen sind **verboten**.
- Consumer greifen **ausschließlich** über `Match<T>` oder benannte Operationen zu – niemals `is`/`as`/`switch` auf Subtypen.
- Methoden auf dem Basistyp und Extension Methods nutzen **`Match<T>`** intern statt direktem `this switch` – so ist Exhaustiveness an einer Stelle zentriert. Ein neuer Subtyp bricht die `Match`-Signatur → alle Aufrufer bekommen Compile-Fehler.
- `Match<T>` ist **public** für Wert-Träger-Sum-Types (reine Zustands-Container, Mapping-Layer benötigt Zugriff). `Match<T>` ist **internal** für operationale Sum-Types.
- Konvertierungsoperatoren: **`implicit`** wenn verlustfrei und reversibel. **`explicit`** wenn Information verloren geht oder die Konvertierung nicht umkehrbar ist.
- **Ausnahme:** `OneOf<T, Error<string>>` als Rückgabewert für Fehlertypen – ad-hoc Union ohne benannten Basistyp.

Wenn ein Typ mehr als einen konzeptuell unterschiedlichen Zustand repräsentieren kann, ist ein Sum Type die richtige Modellierung.

### Consumer-Pattern: Sum Type im Endpoint

Consumer (Endpoints, Mapping-Layer) greifen ausschließlich über `.Match()` zu – niemals per `is`/`switch` auf private Subtypen:

```csharp
// ✅ Korrekt: Match in Endpoint/Mapping
var sourceString = recipe.Source.Match(
    onUrl: url => (string?)url.Value,
    onNone: () => null);

// ❌ Falsch: direkter Subtyp-Check (private Subtypen nicht sichtbar → Compilefehler)
if (recipe.Source is UrlCase u) ...
```

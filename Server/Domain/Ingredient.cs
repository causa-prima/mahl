namespace mahl.Server.Domain;

// Domain-Entity (coding-guideline-csharp.md §2 Ebene 3): sie nimmt ausschließlich Domänentypen und
// vertraut ihnen – die Feldregeln liegen im jeweiligen Typ, nicht hier und nicht beim Aufrufer.
internal readonly record struct Ingredient
{
    private readonly IngredientId _id;
    private readonly IngredientName _name;
    private readonly Unit _baseUnit;

    // Alle drei werfen transitiv beim Zugriff auf ihren Wert – kein extra Guard nötig:
    public IngredientId Id => _id;
    public IngredientName Name => _name;
    public Unit BaseUnit => _baseUnit;

    // Parameterless ctor must be public (record struct limitation) – catches new Ingredient():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public Ingredient() => throw new InvalidOperationException("Uninitialized");

    private Ingredient(IngredientId id, IngredientName name, Unit baseUnit)
    {
        _id = id;
        _name = name;
        _baseUnit = baseUnit;
    }

    // Kein OneOf: es gibt keine Cross-Field-Invariante, und die Feldregeln haben die Domänentypen
    // bereits durchgesetzt.
    public static Ingredient Create(IngredientId id, IngredientName name, Unit baseUnit) =>
        new(id, name, baseUnit);
}

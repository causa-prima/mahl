namespace mahl.Server.Domain;

using mahl.Server.Types;
using OneOf;
using OneOf.Types;

public readonly record struct Ingredient
{
    private readonly Guid _id;
    private readonly NonEmptyTrimmedString _name;
    private readonly NonEmptyTrimmedString _defaultUnit;

#pragma warning disable S4581 // == default is intentional: checks for default-initialized (unset) Guid value
    public Guid Id => _id == default ? throw new InvalidOperationException("Uninitialized") : _id;
#pragma warning restore S4581
    public NonEmptyTrimmedString Name => _name;
    public NonEmptyTrimmedString DefaultUnit => _defaultUnit;

    // Must be public, as record structs cannot have private parameterless constructors
    public Ingredient()
        => throw new InvalidOperationException($"Valid instances can only be created with {nameof(Create)}.");

    private Ingredient(Guid id, NonEmptyTrimmedString name, NonEmptyTrimmedString defaultUnit)
    {
        _id = id;
        _name = name;
        _defaultUnit = defaultUnit;
    }

    public static OneOf<Ingredient, Error<string>> Create(Guid id, string name, string defaultUnit) =>
        NonEmptyTrimmedString.Create(name)
            .MapError(_ => new Error<string>("Name darf nicht leer sein."))
            .Bind(n => NonEmptyTrimmedString.Create(defaultUnit)
                .MapError(_ => new Error<string>("Einheit darf nicht leer sein."))
                .Map(u => new Ingredient(id, n, u)));
}

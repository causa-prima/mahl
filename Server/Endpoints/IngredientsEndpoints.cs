using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Types;
using Microsoft.EntityFrameworkCore;
using OneOf;
using OneOf.Types;

namespace mahl.Server.Endpoints;

internal static class IngredientsEndpoints
{
    internal static void MapIngredientsEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/ingredients");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact
        group.WithTags("Ingredients");

        group.MapGet(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            // ETag-Determinismus (ADR-S084-1): bewusst noch KEIN OrderBy. Der Collection-
            // Content-Hash-ETag ist erst stabil, wenn die Reihenfolge deterministisch ist.
            // Das alphabetische Sortier-Szenario (@US-904) führt OrderBy(name) Stryker-killbar
            // ein; ein reines OrderBy(id) jetzt wäre mit EF-InMemory nicht killbar (Survivor).
            // Bis dahin ist der ETag in SKELETON folgenlos unwirksam (Tech-Debt in AGENT_MEMORY).
            async (MahlDbContext db) =>
                Results.Ok(await db.Ingredients
                    .Select(i => new IngredientDto(i.Id, i.Name, i.DefaultUnit))
                    .ToListAsync()));

        group.MapPost(
            // Stryker disable once String : Route patterns "/" and "" are treated equivalently by ASP.NET Core routing
            "/",
            async (CreateIngredientDto dto, MahlDbContext db) =>
                await dto.ToDomain()
                    .MapError<Ingredient, IReadOnlyList<IngredientValidationError>, IResult>(IngredientMappings.ValidationProblemFor)
                    .BindAsync<Ingredient, IngredientDto, IResult>(async ingredient =>
                    {
                        db.Ingredients.Add(ingredient.ToDbType());
                        await db.SaveChangesAsync();
                        return ingredient.ToDto();
                    })
                    .MatchAsync(
                        created => Results.Created($"/api/ingredients/{created.Id}", created),
                        error => error));
    }
}

file static class IngredientMappings
{
    // ADR-S051-3: name max. 30 Zeichen, nach Trimming gemessen.
    private const int MaxNameLength = 30;
    // ADR-S051-3: defaultUnit max. 20 Zeichen, nach Trimming gemessen.
    private const int MaxUnitLength = 20;

    // Collect-all validation of the independent required fields (ADR-S000-1, gültig laut ADR-S090-1):
    // name and unit are validated independently and all errors collected, so both-fields-empty reports both
    // field errors at once. The Bind/Map chain carries the validated values on success; MapError replaces the
    // chain's first error with the full collected set.
    internal static OneOf<Ingredient, IReadOnlyList<IngredientValidationError>> ToDomain(this CreateIngredientDto dto)
    {
        var name = ValidateName(dto.Name);
        var unit = ValidateUnit(dto.DefaultUnit);

        // 0-or-1 error per field, concatenated -> the collect-all error set (empty when both fields are valid).
        IReadOnlyList<IngredientValidationError> errors = [.. name.ErrorOrEmpty(), .. unit.ErrorOrEmpty()];

        // ADR-S030-1: server-side UUIDv7 primary key.
        return name
            .Bind(validName => unit.Map(validUnit => Ingredient.Create(Guid.CreateVersion7(), validName, validUnit)))
            .MapError<Ingredient, IngredientValidationError, IReadOnlyList<IngredientValidationError>>(_ => errors);
    }

    // ADR-S051-3: max. Länge je Feld, nach Trimming gemessen -> Länge wird auf dem bereits getrimmten
    // NonEmptyTrimmedString-Wert geprüft. Leer und zu lang schließen sich strukturell aus (Bind stoppt bei Empty).
    // Gemeinsamer Helper für name/unit – identische Struktur, nur Grenzwert und Error-Cases unterscheiden sich.
    private static OneOf<NonEmptyTrimmedString, IngredientValidationError> ValidateField(
        string input, int maxLength, IngredientValidationError emptyError, IngredientValidationError tooLongError) =>
        NonEmptyTrimmedString.Create(input)
            .MapError<NonEmptyTrimmedString, Error, IngredientValidationError>(_ => emptyError)
            .Bind<NonEmptyTrimmedString, NonEmptyTrimmedString, IngredientValidationError>(value =>
                value.Value.Length > maxLength
                    ? (OneOf<NonEmptyTrimmedString, IngredientValidationError>) tooLongError
                    : value);

    private static OneOf<NonEmptyTrimmedString, IngredientValidationError> ValidateName(string input) =>
        ValidateField(input, MaxNameLength, IngredientValidationError.NameEmpty, IngredientValidationError.NameTooLong);

    private static OneOf<NonEmptyTrimmedString, IngredientValidationError> ValidateUnit(string input) =>
        ValidateField(input, MaxUnitLength, IngredientValidationError.UnitEmpty, IngredientValidationError.UnitTooLong);

    // 0-or-1 error for a validated field: empty when valid, the field's error otherwise.
    private static IEnumerable<IngredientValidationError> ErrorOrEmpty(
        this OneOf<NonEmptyTrimmedString, IngredientValidationError> field) =>
        field.Match(_ => Enumerable.Empty<IngredientValidationError>(), e => [e]);

    // ADR-S090-1: field-keyed 422 body { "errors": { "<jsonPropertyName>": ["<msg>"] } } – multiple field
    // errors group into one dictionary so all messages appear simultaneously.
    internal static IResult ValidationProblemFor(IReadOnlyList<IngredientValidationError> errors) =>
        Results.ValidationProblem(
            errors.Select(Describe)
                .GroupBy(d => d.Key, d => d.Message, StringComparer.Ordinal)
                .ToDictionary(g => g.Key, g => g.ToArray(), StringComparer.Ordinal),
            statusCode: StatusCodes.Status422UnprocessableEntity);

    // ADR-S051-2 / ADR-S090-1: one error case maps to one (request-JSON-property key, fixed German message) pair.
    // Mapping lives here at the API boundary that knows the request shape – NonEmptyTrimmedString stays
    // field-agnostic. Exhaustive .Match – a new field variant breaks this signature at compile time.
    private static (string Key, string Message) Describe(IngredientValidationError error) => error.Match(
        onNameEmpty: () => ("name", "Name darf nicht leer sein."),
        onNameTooLong: () => ("name", "Name darf maximal 30 Zeichen lang sein."),
        onUnitEmpty: () => ("defaultUnit", "Einheit darf nicht leer sein."),
        onUnitTooLong: () => ("defaultUnit", "Einheit darf maximal 20 Zeichen lang sein."));

    internal static IngredientDbType ToDbType(this Ingredient domain) =>
        new() { Id = domain.Id, Name = domain.Name.Value, DefaultUnit = domain.DefaultUnit.Value };

    internal static IngredientDto ToDto(this Ingredient domain) =>
        new(domain.Id, domain.Name.Value, domain.DefaultUnit.Value);
}

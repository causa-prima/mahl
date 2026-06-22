using mahl.Infrastructure;
using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Domain;
using mahl.Server.Dtos;
using mahl.Server.Types;
using Microsoft.EntityFrameworkCore;
using OneOf;

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
                    .MapError<Ingredient, IngredientValidationError, IResult>(IngredientMappings.ValidationProblemFor)
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
    // Sequential/short-circuit validation (name first, then unit); each error carries which field failed
    // as a sum-type (IngredientValidationError). No collect-all merge – a single empty field is output-
    // identical to short-circuit, so the merge is deferred to the "beide Pflichtfelder leer"-scenario
    // (TD-S090-1, ADR-S000-1).
    internal static OneOf<Ingredient, IngredientValidationError> ToDomain(this CreateIngredientDto dto) =>
        NonEmptyTrimmedString.Create(dto.Name)
            .MapError(_ => IngredientValidationError.NameEmpty)
            .Bind(name => NonEmptyTrimmedString.Create(dto.DefaultUnit)
                .MapError(_ => IngredientValidationError.UnitEmpty)
                // ADR-S030-1: server-side UUIDv7 primary key.
                .Map(unit => Ingredient.Create(Guid.CreateVersion7(), name, unit)));

    // ADR-S090-1: field-keyed 422 body { "errors": { "<jsonPropertyName>": ["<msg>"] } }.
    // ADR-S051-2: fixed German messages per field. The field-to-(key, text) mapping lives here at the
    // API boundary that knows the request shape – NonEmptyTrimmedString stays field-agnostic (ADR-S051-2).
    // Exhaustive .Match over the sum-type – a new field variant breaks this signature at compile time.
    internal static IResult ValidationProblemFor(IngredientValidationError error) => error.Match(
        onNameEmpty: () => FieldProblem("name", "Name darf nicht leer sein."),
        onUnitEmpty: () => FieldProblem("defaultUnit", "Einheit darf nicht leer sein."));

    private static IResult FieldProblem(string key, string message) => Results.ValidationProblem(
        new Dictionary<string, string[]>(StringComparer.Ordinal) { [key] = [message] },
        statusCode: StatusCodes.Status422UnprocessableEntity);

    internal static IngredientDbType ToDbType(this Ingredient domain) =>
        new() { Id = domain.Id, Name = domain.Name.Value, DefaultUnit = domain.DefaultUnit.Value };

    internal static IngredientDto ToDto(this Ingredient domain) =>
        new(domain.Id, domain.Name.Value, domain.DefaultUnit.Value);
}

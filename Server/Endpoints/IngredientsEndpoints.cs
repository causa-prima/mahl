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
                    .MapError<Ingredient, Error, IResult>(_ => IngredientMappings.NameRequiredProblem())
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
    public static OneOf<Ingredient, Error> ToDomain(this CreateIngredientDto dto) =>
        NonEmptyTrimmedString.Create(dto.Name)
            .Bind(name => NonEmptyTrimmedString.Create(dto.DefaultUnit)
                // ADR-S030-1: server-side UUIDv7 primary key.
                .Map(unit => Ingredient.Create(Guid.CreateVersion7(), name, unit)));

    // ADR-S090-1: field-keyed 422 body { "errors": { "<field>": ["<msg>"] } }; key = request JSON property name.
    // ADR-S051-2: fixed German message for an empty Ingredient name. defaultUnit-keyed messages are
    // deferred to the "leere Einheit"-scenario (unit is valid here), so the only reachable error is name.
    public static IResult NameRequiredProblem() => Results.ValidationProblem(
        new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["name"] = ["Name darf nicht leer sein."],
        },
        statusCode: StatusCodes.Status422UnprocessableEntity);

    public static IngredientDbType ToDbType(this Ingredient domain) =>
        new() { Id = domain.Id, Name = domain.Name.Value, DefaultUnit = domain.DefaultUnit.Value };

    public static IngredientDto ToDto(this Ingredient domain) =>
        new(domain.Id, domain.Name.Value, domain.DefaultUnit.Value);
}

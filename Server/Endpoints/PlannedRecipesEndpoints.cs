namespace mahl.Server.Endpoints;

internal static class PlannedRecipesEndpoints
{
    internal static void MapPlannedRecipesEndpoints(this WebApplication app)
    {
        var group = app.MapGroup($"{ApiRoutes.Prefix}/planned-recipes");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact (ADR-S136-1)
        group.WithTags("PlannedRecipes");

        // ADR-S153-1: GET listet die vorgemerkten Rezepte. Noch schreibt nichts Vormerkungen, die Liste ist
        // daher stets leer.
        group.MapGet("", () => Results.Ok(Array.Empty<object>()));
    }
}

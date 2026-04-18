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
            () => Results.Ok(Array.Empty<object>()));
    }
}

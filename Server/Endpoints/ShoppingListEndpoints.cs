namespace mahl.Server.Endpoints;

internal static class ShoppingListEndpoints
{
    internal static void MapShoppingListEndpoints(this WebApplication app)
    {
        var group = app.MapGroup($"{ApiRoutes.Prefix}/shopping-list");
        // Stryker disable once Statement,String : Tag name has no routing or behavioral impact (ADR-S136-1)
        group.WithTags("ShoppingList");

        // ADR-S154-2: Die Einkaufsliste ist eine Momentaufnahme, die erst das Übernehmen füllt.
        // Solange es das Übernehmen nicht gibt, ist sie immer leer; der Eintragstyp kommt mit ihm.
        group.MapGet("", () => Results.Ok(Array.Empty<object>()));
    }
}

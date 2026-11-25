using mahl.Infrastructure.DatabaseTypes;
using Microsoft.EntityFrameworkCore;

namespace mahl.Server.Endpoints;

internal static class IngredientQueries
{
    // ADR-S142-1: Sortierung der Zutaten nach Name in der DB mit expliziter ICU-Collation – die Default-Collation
    // sortiert auf postgres:18-alpine nach Bytes. Zugleich die deterministische Reihenfolge für den Collection-ETag
    // (ADR-S084-1). Eine Quelle für die Zutaten-Liste und die Einkaufsliste.
    internal static IOrderedQueryable<IngredientDbType> OrderedByName(this IQueryable<IngredientDbType> ingredients) =>
        ingredients.OrderBy(i => EF.Functions.Collate(i.Name, Collations.German));
}

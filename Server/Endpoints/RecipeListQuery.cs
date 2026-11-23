using mahl.Infrastructure.DatabaseTypes;
using mahl.Server.Dtos;
using Microsoft.EntityFrameworkCore;

namespace mahl.Server.Endpoints;

internal static class RecipeListQuery
{
    // Die Listenform aller Rezept-Listen: nach Titel sortiert, als Zusammenfassung projiziert.
    // ADR-S142-1: Sortierung in der DB mit expliziter ICU-Collation – die Default-Collation sortiert auf
    // postgres:18-alpine nach Bytes. Zugleich die deterministische Reihenfolge für den Collection-ETag (ADR-S084-1).
    internal static IQueryable<RecipeSummaryDto> OrderedSummaries(this IQueryable<RecipeDbType> recipes) =>
        recipes
            .OrderBy(r => EF.Functions.Collate(r.Title, Collations.German))
            .Select(r => new RecipeSummaryDto(r.Id, r.Title));
}

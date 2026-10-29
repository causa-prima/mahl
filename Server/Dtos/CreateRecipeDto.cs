using System.Text.Json.Serialization;

namespace mahl.Server.Dtos;

// ADR-S135-2: Ingredients ist der rohe Text des Zutatenfelds (eine Zutat je Zeile), zerlegt wird auf
// dem Server. ADR-S027-1: Steps ohne Nummer – die Listenposition ist die Reihenfolge.
// ADR-S144-2: fehlt ein Property im Body, endet das als 400 (JsonRequired). Ein explizites null kommt
// trotzdem an – System.Text.Json erzwingt die NRT-Annotationen nicht – und zählt wie leer: deshalb
// nullable deklariert.
#pragma warning disable CA1812 // instantiated by ASP.NET Core model binding via reflection
internal sealed record CreateRecipeDto(
    [property: JsonRequired] string? Title,
    [property: JsonRequired] string? Ingredients,
    [property: JsonRequired] IReadOnlyList<StepDto>? Steps);
#pragma warning restore CA1812

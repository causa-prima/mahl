namespace mahl.Server.Dtos;

// ADR-S135-2: Ingredients ist der rohe Text des Zutatenfelds (eine Zutat je Zeile), zerlegt wird auf
// dem Server. ADR-S027-1: Steps ohne Nummer – die Listenposition ist die Reihenfolge.
#pragma warning disable CA1812 // instantiated by ASP.NET Core model binding via reflection
internal sealed record CreateRecipeDto(string Title, string Ingredients, IReadOnlyList<StepDto> Steps);
#pragma warning restore CA1812

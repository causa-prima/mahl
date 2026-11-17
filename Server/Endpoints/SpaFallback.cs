using System.Text.RegularExpressions;

namespace mahl.Server.Endpoints;

internal static class SpaFallback
{
    private const string IndexFile = "index.html";

    // ADR-S150-2: Unbekannte Pfade bekommen index.html (Client-Routing wertet die Adresse aus) – außer unter
    // dem API-Präfix: Der Constraint schließt es aus, dort existiert kein Fallback-Endpoint, und das Routing
    // liefert selbst 404 ohne HTML-Body bzw. 405 bei falscher Methode. "nonfile" gehört bei eigenem Pattern
    // explizit dazu (sonst bekäme /assets/fehlt.js index.html); Regex-Constraints ignorieren die Schreibweise.
    internal static void MapSpaFallback(this WebApplication app)
    {
        var apiSegment = Regex.Escape(ApiRoutes.Prefix.TrimStart('/'));
        app.MapFallbackToFile($"{{*path:nonfile:regex(^(?!{apiSegment}(/|$)))}}", IndexFile);
        // Ein Regex-Constraint trifft nie auf einen fehlenden Catch-all-Wert – das Wurzel-"/" braucht deshalb eine eigene Route.
        // Stryker disable once String : "" and "/" both denote the root route pattern – equivalent mutant (Einzelfall, vom User freigegeben S150)
        app.MapFallbackToFile("/", IndexFile);
    }
}

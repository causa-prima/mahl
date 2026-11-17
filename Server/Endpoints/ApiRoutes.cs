namespace mahl.Server.Endpoints;

// Einzige Quelle des API-Präfixes: Der SPA-Fallback (ADR-S150-2) ist nur korrekt, solange alle
// Endpoints darunter liegen. Annahme der Ableitung im Fallback: Das Präfix beginnt mit "/" und ist genau
// ein Segment (kein weiterer "/").
internal static class ApiRoutes
{
    internal const string Prefix = "/api";
}

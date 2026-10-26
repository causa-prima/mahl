namespace mahl.Server.Endpoints;

internal static class Collations
{
    // ADR-S142-1: ICU-Collation für deutsche Sortierung ohne Rang-Unterschied der Schreibweise.
    // Einzige Quelle für alle Listen-Endpoints.
    internal const string German = "de-x-icu";
}

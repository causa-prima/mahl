namespace mahl.Server.Tests.Helpers;

// Single Source of Truth für die Postgres-Init-Config (CM-S105-1): liest dieselbe committete
// config/postgres.env, die docker-compose.yml via `env_file:` in den Container injiziert. So können
// Testcontainer und Deployment-DB bei der Init-Config (Locale/Encoding) nicht divergieren – die
// Locale-Divergenz aus LL-S105-1 wird by construction verhindert. .env bleibt gitignored für Secrets.
internal static class PostgresTestConfig
{
    private const string SharedEnvRelativePath = "config/postgres.env";

    // Init-Args für den Testcontainer – identisch zu dem, was compose per env_file: injiziert.
    internal static string InitdbArgs => ParseValue(File.ReadAllText(LocateSharedEnv()), "POSTGRES_INITDB_ARGS");

    // Pure: eine key=value-Zeile pro Eintrag, '#' = Kommentar, das ERSTE '=' trennt (der Wert darf '=' enthalten).
    internal static string ParseValue(string envFileContent, string key)
    {
        foreach (var rawLine in envFileContent.Split('\n'))
        {
            var line = rawLine.Trim();
            if (line.Length == 0 || line.StartsWith('#'))
                continue;

            // Split auf das ERSTE '=' (max 2 Teile) -> der Wert darf sein eigenes '=' behalten.
            var parts = line.Split('=', 2);
            if (parts.Length == 2 && string.Equals(parts[0].Trim(), key, StringComparison.Ordinal))
                return parts[1].Trim();
        }

        throw new InvalidOperationException($"Key '{key}' not found in {SharedEnvRelativePath}.");
    }

    // Läuft vom Test-Bin-Verzeichnis nach oben bis zur Repo-Wurzel, die config/postgres.env enthält.
    private static string LocateSharedEnv()
    {
        for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir is not null; dir = dir.Parent)
        {
            var candidate = Path.Combine(dir.FullName, SharedEnvRelativePath);
            if (File.Exists(candidate))
                return candidate;
        }

        throw new InvalidOperationException($"{SharedEnvRelativePath} not found walking up from {AppContext.BaseDirectory}.");
    }
}

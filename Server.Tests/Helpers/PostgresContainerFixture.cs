using System.Data.Common;
using mahl.Infrastructure;
using Microsoft.EntityFrameworkCore;
using Testcontainers.PostgreSql;
using Xunit;

namespace mahl.Server.Tests.Helpers;

// ADR-S137-2: Der Postgres-Container überdauert den Testlauf (Wiederverwendung), jeder Testlauf bekommt
// eine eigene Datenbank als Kopie einer migrierten Vorlage. Ein Testlauf zahlt damit weder Container-Start
// noch Migrationen – unter Stryker ist jeder Mutant ein eigener Testlauf, bis zu zehn davon parallel.
// Innerhalb des Laufs gilt weiter ADR-S105-1: geteiltes Schema, jeder Test setzt seine Daten zurück
// (EndpointsTestsBase.InitializeAsync).
//
// Verwaltet wird über MahlDbContext gegen die Admin-Datenbank `postgres` und über den generischen
// DbConnectionStringBuilder – beides ohne direkte Npgsql-Referenz, die Server.Tests nicht hat (ADR-S137-1).
public sealed class PostgresContainerFixture : IAsyncLifetime
{
    private const string TemplatePrefix = "mahl_tpl_";
    private const string RunPrefix = "mahl_run_";

    // Advisory-Locks gelten je Datenbank – alle Sitzungen nehmen sie deshalb in `postgres`.
    // Fester Schlüssel: serialisiert Anlegen und Aufräumen über parallele Testläufe.
    private const long AdminLockKey = 4_711_137;

    // Image literal (wechselt praktisch nie) – muss mit docker-compose.yml übereinstimmen.
    // Init-Config (Locale/Encoding) dagegen aus der Single Source config/postgres.env (CM-S105-1),
    // damit sie nicht von der Deployment-DB divergieren kann (LL-S105-1).
    // Kein DisposeAsync auf dem Container: Das würde ihn stoppen und die Wiederverwendung zunichtemachen.
#pragma warning disable CA2213 // bewusst nicht freigegeben, siehe Kommentar darüber
    private readonly PostgreSqlContainer _container = new PostgreSqlBuilder("postgres:18-alpine")
        .WithEnvironment("POSTGRES_INITDB_ARGS", PostgresTestConfig.InitdbArgs)
        .WithLabel("reuse-id", "mahl-server-tests")
        // Der Container läuft dauerhaft mit Standard-Zugangsdaten – sein Port gehört nur an localhost, nicht
        // an alle Schnittstellen (Docker-Standard; unter WSL mit mirrored networking sonst im lokalen Netz).
        // Das Label macht die Bindung zum Teil des Wiederverwendungs-Hashes, den der Modifier nicht beeinflusst.
        .WithLabel("bind", "localhost")
        .WithCreateParameterModifier(parameters =>
        {
            foreach (var bindings in parameters.HostConfig?.PortBindings?.Values ?? [])
                foreach (var binding in bindings)
                    binding.HostIP = "127.0.0.1";
        })
        .WithReuse(true)
        .Build();
#pragma warning restore CA2213

    private readonly string _runDatabase = RunPrefix + Guid.NewGuid().ToString("N");

    // Hält für die ganze Laufdauer die Besitz-Sperre der eigenen Datenbank. Stirbt der Prozess, endet die
    // Sitzung und mit ihr die Sperre – daran erkennt der nächste Lauf eine verwaiste Datenbank.
    private MahlDbContext? _ownerSession;

    internal string ConnectionString { get; private set; } = null!;

    public async ValueTask InitializeAsync()
    {
        await _container.StartAsync();

        _ownerSession = await OpenAdminAsync();
        await _ownerSession.Database.ExecuteSqlAsync($"SELECT pg_advisory_lock(hashtextextended({_runDatabase}, 0))");

        await using var admin = await OpenAdminAsync();
        await admin.Database.ExecuteSqlAsync($"SELECT pg_advisory_lock({AdminLockKey})");
        var existing = await admin.Database.SqlQueryRaw<string>("SELECT datname AS \"Value\" FROM pg_database").ToListAsync();

        var template = TemplatePrefix + SchemaIdentity();
        if (!existing.Exists(name => string.Equals(name, template, StringComparison.Ordinal)))
            await CreateTemplateAsync(admin, template);

        foreach (var name in existing.Where(name => IsStaleTemplate(name, template)))
            await ExecuteDdlAsync(admin, $"DROP DATABASE IF EXISTS {Quote(name)} WITH (FORCE)");
        foreach (var name in existing.Where(name => name.StartsWith(RunPrefix, StringComparison.Ordinal)))
            await DropIfOrphanedAsync(admin, name);

        await ExecuteDdlAsync(admin, $"CREATE DATABASE {Quote(_runDatabase)} TEMPLATE {Quote(template)}");
        ConnectionString = WithDatabase(_runDatabase, pooling: true);
    }

    public async ValueTask DisposeAsync()
    {
        if (_ownerSession is null)
            return; // InitializeAsync scheiterte vor dem Anlegen – es gibt nichts abzuräumen.

        await using (var admin = await OpenAdminAsync())
            await ExecuteDdlAsync(admin, $"DROP DATABASE IF EXISTS {Quote(_runDatabase)} WITH (FORCE)");
        await _ownerSession.DisposeAsync();
    }

    // Die Vorlage gilt für genau einen Stand des erzeugten DDL. Das bestimmen die Migrationen
    // (Infrastructure) und die Generatoren, die daraus SQL machen (EF Core Relational, Npgsql-Provider).
    // Ihre MVIDs wechseln mit jedem inhaltlich geänderten Build bzw. Paket-Update (deterministischer Build) –
    // auch wenn eine bestehende Migration nachträglich angepasst wird, was MigrateAsync übersähe.
    private static string SchemaIdentity()
    {
        var mvids = new[]
        {
            typeof(MahlDbContext),
            typeof(RelationalDatabaseFacadeExtensions),
            typeof(NpgsqlDbContextOptionsBuilderExtensions),
        }.Select(type => type.Assembly.ManifestModule.ModuleVersionId.ToString("N"));
        var hash = System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.ASCII.GetBytes(string.Concat(mvids)));
        return Convert.ToHexStringLower(hash)[..16];
    }

    // Unter einem Bau-Namen anlegen und erst nach erfolgreicher Migration umbenennen: Ein Abbruch mittendrin
    // hinterlässt so keine halb migrierte Vorlage unter dem gültigen Namen. Ein liegengebliebener Bau
    // gilt beim nächsten Lauf als veraltete Vorlage (IsStaleTemplate).
    private async Task CreateTemplateAsync(MahlDbContext admin, string template)
    {
        var building = template + "_build";
        await ExecuteDdlAsync(admin, $"DROP DATABASE IF EXISTS {Quote(building)} WITH (FORCE)");
        await ExecuteDdlAsync(admin, $"CREATE DATABASE {Quote(building)}");
        // Ohne Pooling, damit nach dem Migrieren keine Verbindung offen bleibt: RENAME und
        // CREATE DATABASE … TEMPLATE verweigern sich, solange jemand mit der Datenbank verbunden ist.
        await using (var db = NewContext(WithDatabase(building, pooling: false)))
            await db.Database.MigrateAsync();
        await ExecuteDdlAsync(admin, $"ALTER DATABASE {Quote(building)} RENAME TO {Quote(template)}");
    }

    private static bool IsStaleTemplate(string name, string currentTemplate) =>
        name.StartsWith(TemplatePrefix, StringComparison.Ordinal) && !string.Equals(name, currentTemplate, StringComparison.Ordinal);

    // Bekommt die Admin-Sitzung die Besitz-Sperre, lebt der Besitzer nicht mehr. Die Sperre endet mit der
    // Admin-Sitzung. Die eigene Datenbank existiert hier noch nicht, wird also nie erfasst.
    private static async Task DropIfOrphanedAsync(MahlDbContext admin, string name)
    {
        var ownerGone = await admin.Database
            .SqlQuery<bool>($"SELECT pg_try_advisory_lock(hashtextextended({name}, 0)) AS \"Value\"")
            .SingleAsync();
        if (ownerGone)
            await ExecuteDdlAsync(admin, $"DROP DATABASE IF EXISTS {Quote(name)} WITH (FORCE)");
    }

    // Datenbanknamen sind DDL-Bezeichner und lassen sich nicht als Parameter übergeben – deshalb Raw-SQL.
    // Jeder Name läuft durch Quote, das ihn als Bezeichner maskiert; die Namen stammen zudem nur aus dieser
    // Klasse oder aus pg_database.
    private static Task<int> ExecuteDdlAsync(MahlDbContext admin, string sql) => admin.Database.ExecuteSqlRawAsync(sql);

    private static string Quote(string identifier) => "\"" + identifier.Replace("\"", "\"\"", StringComparison.Ordinal) + "\"";

    // Ohne Pooling: Advisory-Locks hängen an der Sitzung und enden erst mit ihr. Eine Verbindung aus dem
    // Pool überlebte das Dispose und hielte die Sperre fest.
    private async Task<MahlDbContext> OpenAdminAsync()
    {
        var admin = NewContext(WithDatabase("postgres", pooling: false));
        await admin.Database.OpenConnectionAsync();
        return admin;
    }

    private string WithDatabase(string database, bool pooling)
    {
        var builder = new DbConnectionStringBuilder { ConnectionString = _container.GetConnectionString() };
        builder["Database"] = database;
        builder["Pooling"] = pooling;
        return builder.ConnectionString;
    }

    private static MahlDbContext NewContext(string connectionString) =>
        new(new DbContextOptionsBuilder<MahlDbContext>().UseNpgsql(connectionString).Options);
}

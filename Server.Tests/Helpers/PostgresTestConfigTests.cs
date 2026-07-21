using AwesomeAssertions;
using mahl.Server.Tests.Helpers;
using Xunit;

namespace mahl.Server.Tests;

// Sichert den .env-Parser von PostgresTestConfig (Single Source der Postgres-Init-Config, CM-S105-1).
// Kein Container nötig (nicht in der Postgres-Collection) -> läuft als schneller Unit-Test.
public class PostgresTestConfigTests
{
    [Fact]
    public void ParseValue_KeepsEmbeddedEquals_SplittingOnlyOnFirstSeparator()
    {
        // Given: eine geteilte env-Datei, deren Wert selbst ein '=' enthält (--encoding=UTF8)
        var content = "# Postgres-Init-Config (CM-S105-1)\n\nPOSTGRES_INITDB_ARGS=--encoding=UTF8\n";

        // When
        var value = PostgresTestConfig.ParseValue(content, "POSTGRES_INITDB_ARGS");

        // Then: nur das ERSTE '=' trennt Key/Value; der Wert behält sein eigenes '='
        value.Should().Be("--encoding=UTF8");
    }

    [Fact]
    public void ParseValue_Throws_WhenKeyMissing()
    {
        // Given: die Datei enthält den gesuchten Key nicht
        var content = "OTHER=x\n";

        // When
        var act = () => PostgresTestConfig.ParseValue(content, "POSTGRES_INITDB_ARGS");

        // Then: Fail-fast statt stillem Leerwert (fehlkonfigurierte Test-Infra ist nicht behebbar)
        act.Should().Throw<InvalidOperationException>();
    }
}

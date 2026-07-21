using Xunit;

namespace mahl.Server.Tests.Helpers;

// xUnit-Collection-Definition: bindet alle [Collection(Name)]-Testklassen an EINE geteilte
// PostgresContainerFixture-Instanz (ADR-S105-1). Muss public sein (xUnit1027) und in eigener
// Datei liegen (MA0048: Dateiname == Typname).
[CollectionDefinition(Name)]
public sealed class PostgresCollectionDefinition : ICollectionFixture<PostgresContainerFixture>
{
    internal const string Name = "Postgres";
}

namespace mahl.Shared.Tests.Types;

using mahl.Shared.Types;
using System.Collections.Generic;

public class SyncItemIdTests
{
    private static IEnumerable<(SyncItemId item, string expected)> Items()
    {
        yield return (SyncItemId.Unknown, "SyncItemId(Unknown)");
        yield return (SyncItemId.Known(24), "SyncItemId(24)");
    }

    [Test, TestCaseSource(nameof(Items))]
    public void ToString_Returns_CorrectstringRepresentation((SyncItemId item, string expected) testdata)
    {
        // Arrange
        var (item, expected) = testdata;

        // Act
        var result = item.ToString();

        // Assert
        result.Should().Be(expected);
    }
}

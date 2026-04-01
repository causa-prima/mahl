namespace mahl.Server.Tests.Types;

using mahl.Server.Types;
using FluentAssertions;
using NUnit.Framework;

[TestFixture]
public class SumTypeTests
{
    [Test]
    public void Unreachable_ThrowsInvalidOperationException()
    {
        var act = () => SumType.Unreachable<int>();

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Unreachable.");
    }
}

namespace mahl.Server.Tests;

using FluentAssertions;
using mahl.Server;
using NUnit.Framework;
using OneOf;
using OneOf.Types;

[TestFixture]
public class OneOfExtensionsTests
{
    [TestCase(0, TestName = "Sequence_FailingItemAtIndex0_ReturnsItsError")]
    [TestCase(1, TestName = "Sequence_FailingItemAtIndex1_ReturnsItsError")]
    [TestCase(2, TestName = "Sequence_FailingItemAtIndex2_ReturnsItsError")]
    public void Sequence_FailingItemAtIndex_ReturnsItsError(int failingIndex)
    {
        var items = new[] { 1, 2, 3 };
        var results = items.Select<int, OneOf<int, Error<string>>>((v, idx) => idx == failingIndex
            ? new Error<string>("fehlgeschlagen")
            : v).ToArray();

        var result = results.Sequence();

        result.Match(_ => (string?)null, e => e.Value).Should().Be("fehlgeschlagen");
    }

    [Test]
    public void Sequence_AllSucceed_ReturnsAllValues()
    {
        OneOf<int, Error<string>>[] results = [1, 2, 3];

        var result = results.Sequence();

        result.Match(v => v, _ => null!)
            .Should().BeEquivalentTo([1, 2, 3], opts => opts.WithStrictOrdering());
    }

    [Test]
    public void ValueOrThrowUnreachable_ErrorCase_ThrowsWithUnreachableMessage()
    {
        OneOf<int, Error<string>> input = new Error<string>("some error");

        var act = () => input.ValueOrThrowUnreachable();

        act.Should().Throw<InvalidOperationException>().WithMessage("Unreachable.");
    }
}

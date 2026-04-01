namespace mahl.Server.Tests.Types;

using mahl.Server.Types;
using FluentAssertions;
using NUnit.Framework;
using OneOf.Types;

[TestFixture]
public class NonEmptyListTests
{
    [Test]
    public void Create_NonEmptyList_ReturnsNonEmptyList()
    {
        var result = NonEmptyList<int>.Create([1, 2, 3]);

        result.Value.Should().BeOfType<NonEmptyList<int>>()
            .Which.Value.Should().Equal(1, 2, 3);
    }

    [Test]
    public void Create_EmptyList_ReturnsError()
    {
        var result = NonEmptyList<int>.Create([]);

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("List must not be empty.");
    }

    [Test]
    public void Value_OnDefaultInstance_ThrowsInvalidOperationException()
    {
        var defaultInstance = default(NonEmptyList<int>);

        var act = () => _ = defaultInstance.Value;

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Cannot access an uninitialized NonEmptyList.");
    }

    [Test]
    public void GetHashCode_DifferentLists_ReturnDifferentHashes()
    {
        var a = NonEmptyList<int>.Create([1, 2, 3]).ValueOrThrowUnreachable();
        var b = NonEmptyList<int>.Create([4, 5, 6]).ValueOrThrowUnreachable();

        a.GetHashCode().Should().NotBe(b.GetHashCode());
    }

    [Test]
    public void EqualityOperator_EqualLists_ReturnsTrue()
    {
        var a = NonEmptyList<int>.Create([1, 2]).ValueOrThrowUnreachable();
        var b = NonEmptyList<int>.Create([1, 2]).ValueOrThrowUnreachable();

        (a == b).Should().BeTrue();
    }

    [Test]
    public void InequalityOperator_DifferentLists_ReturnsTrue()
    {
        var a = NonEmptyList<int>.Create([1, 2]).ValueOrThrowUnreachable();
        var b = NonEmptyList<int>.Create([3, 4]).ValueOrThrowUnreachable();

        (a != b).Should().BeTrue();
    }

    [Test]
    public void Equals_ObjectWithSameContent_ReturnsTrue()
    {
        var a = NonEmptyList<int>.Create([1, 2]).ValueOrThrowUnreachable();
        var b = NonEmptyList<int>.Create([1, 2]).ValueOrThrowUnreachable();

        a.Equals((object)b).Should().BeTrue();
    }

    [Test]
    public void Equals_ObjectOfIncompatibleType_ReturnsFalse()
    {
        var a = NonEmptyList<int>.Create([1, 2]).ValueOrThrowUnreachable();

        a.Equals((object)"not a list").Should().BeFalse();
    }
}

namespace mahl.Server.Tests.Domain;

using FluentAssertions;
using mahl.Server.Domain;
using mahl.Server.Types;
using NUnit.Framework;
using OneOf.Types;

[TestFixture]
public class QuantityTests
{
    [Test]
    public void Unspecified_IsUnspecified()
    {
        var result = Quantity.Unspecified();

        var isUnspecified = result.Match((_, _) => false, () => true);
        isUnspecified.Should().BeTrue();
    }

    private static NonEmptyTrimmedString Unit(string s) =>
        NonEmptyTrimmedString.Create(s).Match(u => u, _ => throw new InvalidOperationException());

    [Test]
    public void Create_WithValidValueAndUnit_IsSpecified()
    {
        var result = Quantity.Create(200m, Unit("g"));

        var qty = result.Value.Should().BeAssignableTo<Quantity>().Subject;
        qty.Match((_, _) => true, () => false).Should().BeTrue();
    }

    [TestCase(0)]
    [TestCase(-1)]
    public void Create_WithNonPositiveValue_ReturnsError(decimal value)
    {
        var result = Quantity.Create(value, Unit("g"));

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Menge muss größer als 0 sein.");
    }

    [TestCase(200, "g")]
    [TestCase(0.5, "kg")]
    public void Create_WithValidValueAndUnit_MatchReturnsValueAndUnit(decimal value, string unit)
    {
        var qty = Quantity.Create(value, Unit(unit)).Value.Should().BeAssignableTo<Quantity>().Subject;

        qty.Match((v, _) => (decimal?)v, () => null).Should().Be(value);
        qty.Match((_, u) => (string?)u, () => null).Should().Be(unit);
    }
}

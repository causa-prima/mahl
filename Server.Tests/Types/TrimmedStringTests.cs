namespace mahl.Server.Tests.Types;

using mahl.Server.Types;

public class TrimmedStringTests
{
    [Test]
    public void ParameterlessConstructor_Intializes_WithAnEmptyString()
    {
        // Arrange

        // Act
        var result = new TrimmedString();

        // Assert
        result.Value.Should().Be(string.Empty);
        ((string)result).Should().Be(string.Empty);
        result.Length.Should().Be(0);
    }

    [Test]
    [TestCase("value")]
    [TestCase("Some test value")]
    [TestCase("Some other test value")]
    public void Constructor_Initializes_WithPassedValue_When_PassedValueHasNoLeadingOrTrailingWhitespace(string testvalue)
    {
        // Arrange

        // Act
        var result = new TrimmedString(testvalue);

        // Assert
        result.Value.Should().Be(testvalue);
        ((string)result).Should().Be(testvalue);
        result.Length.Should().Be(testvalue.Length);
    }

    [Test]
    [TestCase(" ")]
    [TestCase(" \t ")]
    [TestCase(" value")]
    [TestCase("Some test value ")]
    [TestCase("\t\t\tSome test value ")]
    [TestCase(" Some other test value ")]
    public void Constructor_Initializes_WithTrimmedPassedValue_When_PassedValueHasLeadingOrTrailingWhitespace(string testvalue)
    {
        // Arrange

        // Act
        var result = new TrimmedString(testvalue);

        // Assert
        var expected = testvalue.Trim();
        result.Value.Should().Be(expected);
        ((string)result).Should().Be(expected);
        result.Length.Should().Be(expected.Length);
    }

    [Test]
    public void Empty_Returns_EmptyString()
    {
        // Arrange

        // Act
        var result = TrimmedString.Empty;

        // Assert
        result.Value.Should().Be(string.Empty);
        result.Length.Should().Be(0);
    }

    [Test]
    public void ImplicitOperator_Converts_FromTrimmedStringToString()
    {
        // Arrange
        var trimmedString = new TrimmedString(" Test string ");

        // Act
        string result = trimmedString;

        // Assert
        result.Should().Be("Test string");
    }

    [Test]
    public void ToString_ReturnsStringValue()
    {
        var trimmedString = new TrimmedString(" Test string ");

        trimmedString.ToString().Should().Be("Test string");
    }

    [Test]
    public void ExplicitOperator_Converts_FromStringToTrimmedString()
    {
        // Arrange
        var input = " Test string ";

        // Act
        var result = (TrimmedString)input;

        // Assert
        result.Value.Should().Be("Test string");
    }
}

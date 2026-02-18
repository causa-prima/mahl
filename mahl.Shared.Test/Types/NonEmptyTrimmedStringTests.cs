namespace mahl.Shared.Tests.Types;

using mahl.Shared.Types;
using OneOf.Types;

internal class NonEmptyTrimmedStringTests
{
    [Test]
    public void ParameterlessConstructor_Throws()
    {
        // Arrange

        // Act
        Action act = () => new NonEmptyTrimmedString();

        // Assert
        act.Should().Throw<InvalidOperationException>()
                    .WithMessage("Valid instances can only be created with Create.");
    }

    [Test]
    public void Value_WhenInstanceWasCreatedWithDefault_Throws()
    {
        // Arrange
        var nonEmptyTrimmedString = default(NonEmptyTrimmedString);
        TrimmedString? val = null;

        // Act
        Action act = () => val = nonEmptyTrimmedString.Value;

        // Assert
        act.Should().Throw<InvalidOperationException>()
                    .WithMessage("Cannot access an uninitialized NonEmptyTrimmedString.");
    }

    [Test]
    public void ToString_WhenInstanceWasCreatedWithDefault_Throws()
    {
        // Arrange
        var nonEmptyTrimmedString = default(NonEmptyTrimmedString);
        string? val = null;

        // Act
        Action act = () => val = nonEmptyTrimmedString.ToString();

        // Assert
        act.Should().Throw<InvalidOperationException>()
                    .WithMessage("Cannot access an uninitialized NonEmptyTrimmedString.");
    }

    public static IEnumerable<string> ValidCreateInputs
    {
        get
        {
            yield return "value";
            yield return "Some test value";
            yield return "Some other test value";
            yield return " value";
            yield return "Some test value ";
            yield return "\t\t\tSome test value ";
            yield return " Some other test value ";
        }
    }

    [Test, TestCaseSource(nameof(ValidCreateInputs))]
    public void Create_Returns_SuccessWithInstance_WhenGiven_ValidStringInputParameter(string testvalue)
    {
        // Arrange

        // Act
        var result = NonEmptyTrimmedString.Create(testvalue);

        // Assert
        var expected = (TrimmedString)testvalue;
        result.Value.Should().BeOfType<Success<NonEmptyTrimmedString>>()
            .Which.Value.Value.Should().Be(expected);
    }

    public static IEnumerable<string> InvalidCreateInputs
    {
        get
        {
            yield return "";
            yield return " ";
            yield return " \t ";
        }
    }

    [Test, TestCaseSource(nameof(InvalidCreateInputs))]
    public void Create_Returns_ErrorWithMessage_WhenGiven_InvalidStringInputParameter(string testvalue)
    {
        // Arrange

        // Act
        var result = NonEmptyTrimmedString.Create(testvalue);

        // Assert
        result.Value.Should().BeOfType<Error<String>>()
            .Which.Value.Should().Be("Value cannot be null, empty or white space.");
    }

    [Test, TestCaseSource(nameof(ValidCreateInputs))]
    public void ImplicitOperator_Converts_FromNonEmptyTrimmedStringToString(string stringTestValue)
    {
        // Arrange
        var testvalue = NonEmptyTrimmedString.Create(stringTestValue).AsT0.Value;

        // Act
        string result = testvalue;

        // Assert
        result.Should().Be(((TrimmedString)stringTestValue).Value);
    }

    [Test, TestCaseSource(nameof(ValidCreateInputs))]
    public void ImplicitOperator_Converts_FromNonEmptyTrimmedStringToTrimmedString(string stringTestValue)
    {
        // Arrange
        var testvalue = NonEmptyTrimmedString.Create(stringTestValue).AsT0.Value;

        // Act
        TrimmedString result = testvalue;

        // Assert
        result.Value.Should().Be((TrimmedString)stringTestValue);
    }
}

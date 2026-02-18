namespace mahl.Shared.Tests;

using mahl.Shared.Types;
using mahl.Tests.Shared;
using OneOf;
using OneOf.Types;
using Pose;
using System.Collections;

public class ShoppingListItemTests
{
    public static IEnumerable EmptyTitles
    {
        get
        {
            yield return "";
            yield return " ";
            yield return "\n";
            yield return "\t \n";
        }
    }

    [Test, TestCaseSource(nameof(EmptyTitles))]
    public void Constructor_ReturnsError_When_TitleIsEmptyOrWhitespace(string invalidTitle)
    {
        // Arrange

        // Act
        var result = ShoppingListItem.New(invalidTitle, string.Empty);

        // Assert
        result.Switch(
            _ => Helpers.FailWithTypeMismatch($"{nameof(result)}", typeof(Error<string>), _),
            error => error.Value.Should().Be("Value cannot be null, empty or white space.")
            );
    }

    [Test]
    public void Constructor_Returns_Error_When_TitleIsTooLong()
    {
        // Arrange
        const string tooLongTitle = "A very long string that is longer than the character" +
            " limit for a title and thus should throw an exception";

        // Act
        var result = ShoppingListItem.New(tooLongTitle, string.Empty);

        // Assert
        result.Switch(
            _ => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), _),
            error => error.Value.Should().Be("Title must not be longer than 30 characters.")
            );
    }

    [Test]
    public void Constructor_Returns_Error_When_DescriptionIsTooLong()
    {
        // Arrange
        const string tooLongDescription = "A very long string that is longer than the character" +
            " limit for a description and thus should throw an exception";

        // Act
        var result = ShoppingListItem.New("Some title", tooLongDescription);

        // Assert
        result.Switch(
            _ => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), _),
            error => error.Value.Should().Be("Description must not be longer than 100 characters.")
            );
    }

    [Test]
    public void Constructor_Returns_Error_When_BoughtAtDateIsAFutureDate()
    {
        // Arrange
        var futureDate = DateTimeOffset.Now.AddDays(1);

        // Act
        var result = ShoppingListItem.FromPrimitiveTypes((int?)null, "Some title", string.Empty, futureDate);

        // Assert
        result.Switch(
            _ => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), _),
            error => error.Value.Should().Be("BoughtAt must not be a future date.")
            );
    }

    [Test, Ignore("Poser throws an exception: https://github.com/Miista/pose/issues/65")]
    public void Constructor_Returns_Instance_When_BoughtAtDateIsNow()
    {
        // Arrange
        var fakeNow = DateTimeOffset.Now.AddDays(1);
        var pose = Shim.Replace(() => DateTimeOffset.Now).With(() => fakeNow);

        // Act
        PoseContext.Isolate(() =>
        {
            var result = ShoppingListItem.FromPrimitiveTypes((int?)null, "Some title", string.Empty, fakeNow);

            // Assert
            result.Switch(
                item => { },
                _ => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListItem), _)
                );
        }, pose
        );
    }

    [Test]
    public void Constructor_PropertyIdIsUnknown_AndPropertyWasSyncedIsFalse_WhenNotGiven_ConcreteId()
    {
        // Arrange

        // Act
        var result = ShoppingListItem.New("Some title", string.Empty);

        // Assert
        result.Switch(
            item =>
            {
                item.Id.Switch(_ => Helpers.FailWithTypeMismatch($"{nameof(item)}.{nameof(item.Id)}", typeof(Unknown), _), val => { });
                item.WasSynced.Should().BeFalse();
            },
            error => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListItem), error)
            );
    }

    [Test]
    public void Constructor_PropertyIdContainsPassedValue_AndPropertyWasSyncedIsFalse_WhenGiven_ConcreteId()
    {
        // Arrange

        // Act
        var result = ShoppingListItem.Unbought(12, "Some title", string.Empty);

        // Assert
        result.Switch(
            item =>
            {
                item.Id.Switch(v => v.Should().Be(12), _ => Helpers.FailWithTypeMismatch($"{nameof(item)}.{nameof(item.Id)}", typeof(int), _));
                item.WasSynced.Should().BeTrue();
            },
            error => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListItem), error)
            );
    }

    [Test]
    public void Constructor_PropertyWasBoughtIsTrue_WhenGiven_ConcreteDateForBoughtAt()
    {
        // Arrange

        // Act
        var result = ShoppingListItem.FromPrimitiveTypes(SyncItemId.Unknown, "Some title", string.Empty, DateTimeOffset.Now);

        // Assert
        result.Switch(
            item => item.WasBought.Should().BeTrue(),
            error => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListItem), error)
            );
    }

    [Test]
    public void Constructor_PropertyWasBoughtIsFalse_WhenNotGiven_ConcreteDateForBoughtAt()
    {
        // Arrange

        // Act
        var result = ShoppingListItem.Unbought(SyncItemId.Unknown, "Some title", string.Empty);

        // Assert
        result.Switch(
            item => item.WasBought.Should().BeFalse(),
            error => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListItem), error)
            );
    }

    [Test]
    public void Constructor_TrimsWhitespace_WhenGiven_TitleOrDescriptionSourroundedByWhiteSpace()
    {
        // Arrange

        // Act
        var result = ShoppingListItem.New("      Title containing 30 characters\t\n",
                                          "\nA  text that is exactly 100 characters long after trimming the whitespace at the start and end of it  ");
        // Assert
        result.Switch(
            item =>
            {
                ((string)item.Title).Should().Be("Title containing 30 characters");
                ((string)item.Description).Should().Be("A  text that is exactly 100 characters long after trimming the whitespace at the start and end of it");
            },
            error => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListItem), error)
            );
    }

    public static IEnumerable<(ShoppingListItem item1, ShoppingListItem item2)> ItemsRegardedTheSame
    {
        get
        {
            yield return (
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.New("Some title", ""));
            yield return (
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.New("Some title", "Some description"));
            yield return (
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", ""));
            yield return (
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", "Some description"));
            yield return (
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some other title", ""));
            yield return (
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some other title", "Some description"));
        }
    }

    [Test, TestCaseSource(nameof(ItemsRegardedTheSame))]
    public void IsRegardedAsSameAs_ReturnsTrue_ForItemsRegardedTheSame(
        (ShoppingListItem item1, ShoppingListItem item2) testData)
    {
        // Arrange
        (ShoppingListItem item1, ShoppingListItem item2) = testData;

        // Act
        var result1 = item1.IsRegardedAsSameAs(item2);
        var result2 = item2.IsRegardedAsSameAs(item1);

        // Assert
        result1.Should().BeTrue();
        result2.Should().BeTrue();
    }

    public static IEnumerable<(ShoppingListItem item1, ShoppingListItem? item2)> ItemsNotRegardedTheSame
    {
        get
        {
            yield return (
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                null);
            yield return (
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.New("Some other title", ""));
            yield return (
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(13, "Some other title", ""));
            yield return (
                (ShoppingListItem)ShoppingListItem.Unbought(76234, "Some title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(89, "Some other title", ""));
        }
    }

    [Test, TestCaseSource(nameof(ItemsNotRegardedTheSame))]
    public void IsRegardedAsSameAs_ReturnsFalse_ForItemsNotRegardedTheSame(
        (ShoppingListItem item1, ShoppingListItem? item2) testData)
    {
        // Arrange
        (ShoppingListItem item1, ShoppingListItem? item2) = testData;

        // Act
        var result1 = item1.IsRegardedAsSameAs(item2);
        var result2 = item2?.IsRegardedAsSameAs(item1) ?? false;

        // Assert
        result1.Should().BeFalse();
        result2.Should().BeFalse();
    }

    [Test]
    public void Casting_Throws_When_TryingToCastError()
    {
        // Arrange
        OneOf<ShoppingListItem, Error<string>> error = new Error<string>("Some error message");

        // Act
        Action act = () => { var t = (ShoppingListItem)error; };

        // Assert
        act.Should().Throw<InvalidCastException>("an error cannot be cast to an instance")
                    .WithMessage("The underlying value was an instance of Error`1, not an instance of ShoppingListItem");
    }
}
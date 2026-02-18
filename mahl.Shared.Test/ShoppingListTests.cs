namespace mahl.Shared.Tests;

using mahl.Shared.Types;
using mahl.Tests.Shared;
using NUnit.Framework;
using OneOf;
using OneOf.Types;
using System.Collections.Generic;
using System.Collections.Immutable;

public class ShoppingListTests
{
    [Test]
    public void ExplicitCast_OfOneOfShoppingListTypeOrError_Returns_ShoppingList_When_InstanceIsShoppingList()
    {
        // Arrange
        OneOf<ShoppingListType, Error<string>> valueToCast = ShoppingList.Empty;

        ShoppingListType? t = null;
        // Act
        Action act = () => t = (ShoppingListType)valueToCast;

        // Assert
        act.Should().NotThrow();
        t.Should().NotBeNull();
    }

    [Test]
    public void ExplicitCast_OfOneOfShoppingListTypeOrError_Throws_When_InstanceIsError()
    {
        // Arrange
        OneOf<ShoppingListType, Error<string>> valueToCast = new Error<string>("Some error");

        ShoppingListType? t = null;
        // Act
        Action act = () => t = (ShoppingListType)valueToCast;

        // Assert
        act.Should().Throw<InvalidCastException>()
            .WithMessage($"The underlying value was an instance of Error`1, not an instance of ShoppingListType");
    }

    [Test]
    public void Empty_Returns_EmptyShoppingList()
    {
        // Arrange

        // Act
        var list = ShoppingList.Empty;

        // Assert
        list.Any().Should().Be(false);
    }

    public static IReadOnlyList<ShoppingListItem> SimpleList = new List<ShoppingListItem>
            {
                (ShoppingListItem) ShoppingListItem.New("Some title", ""),
                (ShoppingListItem) ShoppingListItem.New("Some different title", "Some description"),
                (ShoppingListItem) ShoppingListItem.New("Some very different title", ""),
                (ShoppingListItem) ShoppingListItem.Unbought(14, "Some unbought item title", ""),
            };

    public static IEnumerable<IReadOnlyList<ShoppingListItem>> ListsWithoutDuplicates
    {
        get
        {
            yield return new List<ShoppingListItem> { (ShoppingListItem)ShoppingListItem.New("Some title", "") };
            yield return new List<ShoppingListItem>
            {
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.New("Some other title", "")
            };
        }
    }

    public static IEnumerable<IReadOnlyList<ShoppingListItem>> ListsWithoutDuplicatesIncludingEmptyList
    {
        get
        {
            yield return new List<ShoppingListItem>();
            foreach (var list in ListsWithoutDuplicates)
                yield return list;
        }
    }

    [Test, TestCaseSource(nameof(ListsWithoutDuplicatesIncludingEmptyList))]
    public void Create_Returns_ShoppingListWitAllItems_When_PassedListIsDuplicateFree(
        IReadOnlyList<ShoppingListItem> items)
    {
        // Arrange

        // Act
        var result = ShoppingList.Create(items);

        // Assert
        result.Switch(
            list => list.Select(i => i).Should().BeEquivalentTo(items),
            e => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListType), e));
    }

    public static IEnumerable<IReadOnlyList<ShoppingListItem>> ListsWithDuplicates
    {
        get
        {
            yield return new List<ShoppingListItem>
            {
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", ""),
            };
            yield return new List<ShoppingListItem>
            {
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.New("Some other title", ""),
                (ShoppingListItem)ShoppingListItem.New("Some title", "Some description"),
            };
        }
    }

    [Test, TestCaseSource(nameof(ListsWithDuplicates))]
    public void Create_Returns_Error_When_PassedListContainsDuplicates(IReadOnlyList<ShoppingListItem> items)
    {
        // Arrange

        // Act
        var result = ShoppingList.Create(items);

        // Assert
        result.Switch(
            list => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), list),
            e => e.Value.Should().Match($"Item with id * already in list."));
    }

    [Test, TestCaseSource(nameof(ListsWithoutDuplicatesIncludingEmptyList))]
    public void Add_Returns_ListWithAddedItem_When_ListWasEmpty(IReadOnlyList<ShoppingListItem> items)
    {
        // Arrange
        var list = ShoppingList.Empty;

        // Act / Assert
        foreach (var item in items)
        {
            list.Add(item).Switch(
                l => list = l,
                e => Helpers.FailWithTypeMismatch(nameof(list), typeof(ShoppingList), e)
                );
        }

        foreach (var item in items)
        {
            list.Contains(item).Should().BeTrue();
        }
    }

    [Test, TestCaseSource(nameof(ListsWithoutDuplicates))]
    public void Add_Returns_Error_When_TryingToAddItemAlreadyInList(IReadOnlyList<ShoppingListItem> items)
    {
        // Arrange
        var list = (ShoppingListType)ShoppingList.Create(items);
        var duplicateItem = items[Random.Shared.Next(items.Count)];

        // Act
        var result = list.Add(duplicateItem);

        // Assert
        result.Switch(
            l => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), l),
            e => e.Value.Should().Be($"Item with id {duplicateItem.Id} already in list.")
            );
    }

    [Test, TestCaseSource(nameof(ListsWithoutDuplicates))]
    public void Add_Returns_Error_When_TryingToAddItemAlreadyInListWithDifferentDescription(
        IReadOnlyList<ShoppingListItem> items)
    {
        // Arrange
        var list = (ShoppingListType)ShoppingList.Create(items);
        var duplicateItem = items[Random.Shared.Next(items.Count)] with
        { Description = (TrimmedString)"Some changed description" };

        // Act
        var result = list.Add(duplicateItem);

        // Assert
        result.Switch(
            l => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), l),
            e => e.Value.Should().Be($"Item with id {duplicateItem.Id} already in list.")
            );
    }

    [Test, TestCaseSource(nameof(ListsWithoutDuplicates))]
    public void Update_Returns_UpdatedList_When_ItemToUpdateWasPresentInShoppingList(
        IReadOnlyList<ShoppingListItem> shoppingListItems)
    {
        // Arrange
        var shoppingList = (ShoppingListType)ShoppingList.Create(shoppingListItems);
        var itemToUpdate = shoppingListItems[Random.Shared.Next(shoppingListItems.Count)] with
        { Description = (TrimmedString)"Some changed description" };

        // Act
        var result = shoppingList.Update(itemToUpdate);

        // Assert
        result.Switch(
            list =>
            {
                var rawList = list.Select(i => i);
                // The item itself was updated
                rawList.Should().ContainSingle(i => i.IsRegardedAsSameAs(itemToUpdate)
                                                    && i.Description == itemToUpdate.Description);

                // all other items are still in the list
                foreach (var item in shoppingListItems.Where(i => !i.IsRegardedAsSameAs(itemToUpdate)))
                    rawList.Should().ContainSingle(i => i == item);
            },
            e => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListType), e));
    }

    [Test, TestCaseSource(nameof(ListsWithoutDuplicatesIncludingEmptyList))]
    public void Update_Returns_Error_When_ItemToUpdateWasNotpresentInShoppingList(
        IReadOnlyList<ShoppingListItem> shoppingListItems)
    {
        // Arrange
        var shoppingList = (ShoppingListType)ShoppingList.Create(shoppingListItems);
        var itemToUpdate = (ShoppingListItem)ShoppingListItem.New("Some item not in the list", "");

        // Act
        var result = shoppingList.Update(itemToUpdate);

        // Assert
        result.Switch(
            list => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), list),
            e => e.Value.Should().Match($"Item with id * not in list."));
    }

    public static IEnumerable<IReadOnlyList<ShoppingListItem>> ListsOfStoredItemsWithoutDuplicates
    {
        get
        {
            foreach (var list in ListsWithoutDuplicates)
            {
                yield return list.Select(i => i with { Id = SyncItemId.Known(Random.Shared.Next()) }).ToImmutableList();
            }
        }
    }

    [Test, TestCaseSource(nameof(ListsOfStoredItemsWithoutDuplicates))]
    public void Update_Returns_Error_When_TryingToUpdateTitleOfAnItem(IReadOnlyList<ShoppingListItem> shoppingListItems)
    {
        // Arrange
        var shoppingList = (ShoppingListType)ShoppingList.Create(shoppingListItems);
        var originalItem = shoppingListItems[Random.Shared.Next(shoppingListItems.Count)];
        var itemToUpdate = originalItem with { Id = Random.Shared.Next() };

        // Act
        var result = shoppingList.Update(itemToUpdate);

        // Assert
        result.Switch(
            list => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), list),
            e => e.Value.Should().Be("The id of an item must not be changed."));
    }

    [Test, TestCaseSource(nameof(ListsOfStoredItemsWithoutDuplicates))]
    public void Update_Returns_Error_When_TryingToUpdateIdOfAnItem(IReadOnlyList<ShoppingListItem> shoppingListItems)
    {
        // Arrange
        var shoppingList = (ShoppingListType)ShoppingList.Create(shoppingListItems);
        var originalItem = shoppingListItems[Random.Shared.Next(shoppingListItems.Count)];
        var newTitle = NonEmptyTrimmedString.Create("Some very random changed title").AsT0.Value;
        var itemToUpdate = originalItem with { Title = newTitle };

        // Act
        var result = shoppingList.Update(itemToUpdate);

        // Assert
        result.Switch(
            list => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), list),
            e => e.Value.Should().Be("The title of an item must not be changed."));
    }

    public static IEnumerable<(IReadOnlyList<ShoppingListItem> list, ShoppingListItem itemRegardedSame)>
        ListsAndItemsRegardedSameAsAnItemFromList
    {
        get
        {
            var list1 = new List<ShoppingListItem>
            {
                (ShoppingListItem)ShoppingListItem.New("Some title", ""),
                (ShoppingListItem)ShoppingListItem.New("Some very different title", ""),
            };
            var list2 = new List<ShoppingListItem>
            {
                (ShoppingListItem)ShoppingListItem.New("Some very different title", ""),
                (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", ""),
            };

            yield return (list1, (ShoppingListItem)ShoppingListItem.New("Some title", ""));
            yield return (list1, (ShoppingListItem)ShoppingListItem.New("Some title", "Some description"));
            yield return (list1, (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", ""));
            yield return (list1, (ShoppingListItem)ShoppingListItem.Unbought(12, "Some title", "Some description"));
            yield return (list2, (ShoppingListItem)ShoppingListItem.Unbought(12, "Some other title", ""));
            yield return (list2, (ShoppingListItem)ShoppingListItem.Unbought(12, "Some other title", "Some description"));
        }
    }

    [Test, TestCaseSource(nameof(ListsAndItemsRegardedSameAsAnItemFromList))]
    public void Contains_Returns_True_When_AnItemRegardedTheSameAsTheSearchedItemIsContained(
        (IReadOnlyList<ShoppingListItem> list, ShoppingListItem itemRegardedSame) testData)
    {
        // Arrange
        (IReadOnlyList<ShoppingListItem> list, ShoppingListItem itemRegardedSame) = testData;
        var shoppingList = (ShoppingListType)ShoppingList.Create(list);

        // Act
        var result = shoppingList.Contains(itemRegardedSame);

        // Assert
        result.Should().BeTrue();
    }

    [Test]
    public void Contains_Returns_False_When_NoItemRegardedTheSameAsTheSearchedItemIsContained()
    {
        // Arrange
        var shoppingList = (ShoppingListType)ShoppingList.Create(SimpleList);
        var uncontainedItem = (ShoppingListItem)ShoppingListItem.New("Uncontained", "");

        // Act
        var result = shoppingList.Contains(uncontainedItem);

        // Assert
        result.Should().BeFalse();
    }

    public static IEnumerable<Func<ShoppingListItem, object>> SelectFunctionsList
    {
        get
        {
            yield return item => item.Title;
            yield return item => item.Title.Length;
            yield return item => ((string)item.Title).Contains("Some");
        }
    }

    [Test, TestCaseSource(nameof(SelectFunctionsList))]
    public void Select_BehavesAsIfFunctionWasCalledOnContainedListOfItems(Func<ShoppingListItem, object> func)
    {
        // Arrange        
        var shoppingList = (ShoppingListType)ShoppingList.Create(SimpleList);

        // Act
        var result = shoppingList.Select(func);

        // Assert
        var expected = SimpleList.Select(func);
        result.Should().BeEquivalentTo(expected);
    }

    [Test]
    public async Task ApplyAsync_AppliesPassedFunctionOnUnwrappedList()
    {
        // Arrange
        var shoppingList = (ShoppingListType)ShoppingList.Create(SimpleList);
        IEnumerable<ShoppingListItem>? callparameter = null;

        Func<IEnumerable<ShoppingListItem>, Task> asyncAction = async items =>
        {
            callparameter = items;
            await Task.CompletedTask;
        };

        // Act
        await shoppingList.ApplyAsync(asyncAction);

        // Assert
        callparameter.Should().BeEquivalentTo(SimpleList);
    }

    public static IEnumerable<(IReadOnlyList<ShoppingListItem> allItems,
        IReadOnlyList<ShoppingListItem> boughtItems,
        IReadOnlyList<ShoppingListItem> unboughtItems)> BoughtAndUnboughtItems
    {
        get
        {
            var unboughtItem1 = (ShoppingListItem)ShoppingListItem.New("Some title", "");
            var unboughtItem2 = (ShoppingListItem)ShoppingListItem.New("Different title", "Some description");
            var unboughtItem3 = (ShoppingListItem)ShoppingListItem.New("Very different title", "");
            var unboughtItem4 = (ShoppingListItem)ShoppingListItem.Unbought(14, "Unbought item title", "");

            var boughtItem1 = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
                SyncItemId.Unknown,
                NonEmptyTrimmedString.Create("Some bought item title").AsT0.Value,
                TrimmedString.Empty,
                new DateTimeOffset(new DateTime(2024, 12, 16)));
            var boughtItem2 = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
                SyncItemId.Known(16),
                NonEmptyTrimmedString.Create("Different bought item title").AsT0.Value,
                TrimmedString.Empty,
                new DateTimeOffset(new DateTime(2024, 12, 16)));
            var boughtItem3 = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
                SyncItemId.Unknown,
                NonEmptyTrimmedString.Create("Very different bought item").AsT0.Value,
                (TrimmedString)"Some bought item description",
                new DateTimeOffset(new DateTime(2024, 12, 16)));
            var boughtItem4 = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
                SyncItemId.Known(468785),
                NonEmptyTrimmedString.Create("Bought item title extended").AsT0.Value,
                TrimmedString.Empty,
                new DateTimeOffset(new DateTime(2024, 12, 16)));

            yield return ([], [], []);
            yield return ([unboughtItem1], [], [unboughtItem1]);
            yield return ([boughtItem1], [boughtItem1], []);
            yield return ([unboughtItem2, boughtItem3, boughtItem1, unboughtItem4],
                          [boughtItem3, boughtItem1],
                          [unboughtItem2, unboughtItem4]);
            yield return (
                [boughtItem3, unboughtItem2, unboughtItem1, unboughtItem4, boughtItem1, boughtItem2, unboughtItem3, boughtItem4],
                [boughtItem3, boughtItem1, boughtItem2, boughtItem4],
                [unboughtItem2, unboughtItem1, unboughtItem4, unboughtItem3]);
        }
    }

    [Test, TestCaseSource(nameof(BoughtAndUnboughtItems))]
    public void GetBoughtItems_Returns_AllAndOnlyBoughtItems((IReadOnlyList<ShoppingListItem> allItems,
        IReadOnlyList<ShoppingListItem> boughtItems,
        IReadOnlyList<ShoppingListItem> unboughtItems) testdata)
    {
        // Arrange
        var (allItems, boughtItems, _) = testdata;
        var shoppingList = (ShoppingListType)ShoppingList.Create(allItems);

        // Act
        var result = shoppingList.GetBoughtItems();

        // Assert
        result.Should().BeEquivalentTo(boughtItems);
    }

    [Test, TestCaseSource(nameof(BoughtAndUnboughtItems))]
    public void GetUnboughtItems_Returns_AllAndOnlyUnboughtItems((IReadOnlyList<ShoppingListItem> allItems,
        IReadOnlyList<ShoppingListItem> boughtItems,
        IReadOnlyList<ShoppingListItem> unboughtItems) testdata)
    {
        // Arrange
        var (allItems, _, unboughtItems) = testdata;
        var shoppingList = (ShoppingListType)ShoppingList.Create(allItems);

        // Act
        var result = shoppingList.GetUnboughtItems();

        // Assert
        result.Should().BeEquivalentTo(unboughtItems);
    }

    [Test]
    public void Any_Returns_False_WhenCalledOn_EmptyShoppingList()
    {
        // Arrange
        var shoppingList = ShoppingList.Empty;

        // Act
        var result = shoppingList.Any();

        // Assert
        result.Should().BeFalse();
    }

    [Test, TestCaseSource(nameof(ListsWithoutDuplicates))]
    public void Any_Returns_True_WhenCallenOn_NonemptyShoppingLists(IReadOnlyList<ShoppingListItem> items)
    {
        // Arrange
        var shoppingList = (ShoppingListType)ShoppingList.Create(items);

        // Act
        var result = shoppingList.Any();

        // Assert
        result.Should().BeTrue();
    }
}
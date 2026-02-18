namespace mahl.Server.Tests;

using FluentAssertions;
using mahl.Server.Data.DatabaseTypes;
using mahl.Shared;
using mahl.Shared.Dtos;
using System.Net;
using System.Net.Http.Json;

[Parallelizable(ParallelScope.All)]
[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[TestFixture]
public class ShoppingListItemEndpointsTest : EndpointsTestsBase
{
    // Tests for POST
    // ------------------

    private static IEnumerable<(IEnumerable<ShoppingListItemDBType> ExistingDbItems,
        ShoppingListItemDto ItemToAdd,
        ShoppingListItemDto ExpectedResponse,
        IEnumerable<ShoppingListItemDBType> ExpectedStoredItems)>
        TestDataForAddingNewItems()
    {
        var newItem1 = new ShoppingListItemDto { Title = "New Item", Description = "New Description" };
        var newItem2 = new ShoppingListItemDto { Title = "Another Item", Description = "" };
        var newItem3 = new ShoppingListItemDto { Title = "Third Item", Description = "With longer description" };

        var existingDbItem = new ShoppingListItemDBType { Id = 100, Title = "Existing Item", Description = "Existing Description" };

        // Expected responses should have IDs assigned (simulating auto-generated IDs)
        var expectedResponse1 = newItem1 with { Id = 1 };
        var expectedResponse2 = newItem2 with { Id = 1 };
        var expectedResponse3 = newItem3 with { Id = 101 }; // Second item when one already exists

        var expectedStoredItem1 = new ShoppingListItemDBType { Id = expectedResponse1.Id.Value, Title = expectedResponse1.Title, Description = expectedResponse1.Description };
        var expectedStoredItem2 = new ShoppingListItemDBType { Id = expectedResponse2.Id.Value, Title = expectedResponse2.Title, Description = expectedResponse2.Description };
        var expectedStoredItem3 = new ShoppingListItemDBType { Id = expectedResponse3.Id.Value, Title = expectedResponse3.Title, Description = expectedResponse3.Description };

        yield return ([], newItem1, expectedResponse1, [expectedStoredItem1]);
        yield return ([], newItem2, expectedResponse2, [expectedStoredItem2]);
        yield return ([existingDbItem], newItem3, expectedResponse3, [existingDbItem, expectedStoredItem3]);
    }

    [Test, TestCaseSource(nameof(TestDataForAddingNewItems))]
    public async Task PostShoppingListItem_Returns_OKAndAddedItem_And_AddsItemToDB_When_ItemIsValid_And_ItemNotInDB(
        (IEnumerable<ShoppingListItemDBType> ExistingDbItems,
         ShoppingListItemDto ItemToAdd,
         ShoppingListItemDto ExpectedResponse,
         IEnumerable<ShoppingListItemDBType> ExpectedStoredItems) testData)
    {
        // Arrange
        SetTestData(testData.ExistingDbItems);

        // Act
        var response = await _client.PostAsJsonAsync(RouteBases.ShoppingListItem, testData.ItemToAdd);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var result = await response.Content.ReadFromJsonAsync<ShoppingListItemDto>();
        result.Should().NotBeNull();
        result.Should().BeEquivalentTo(testData.ExpectedResponse);

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo(testData.ExpectedStoredItems, opts => opts.WithoutStrictOrdering());
    }

    private static IEnumerable<(
        ShoppingListItemDto ItemToAdd,
        string ExpectedErrorMessage)>
        InvalidItems()
    {
        var emptyTitleDto = new ShoppingListItemDto { Title = "", Description = "X" };
        yield return (emptyTitleDto, "Value cannot be null, empty or white space.");

        var tooLongTitle = new string('a', Constants.ShoppingListTitleMaxLength + 1);
        var tooLongTitleDto = new ShoppingListItemDto { Title = tooLongTitle, Description = "" };
        yield return (tooLongTitleDto,
            $"{nameof(ShoppingListItem.Title)} must not be longer than {Constants.ShoppingListTitleMaxLength} characters.");
    }

    [Test, TestCaseSource(nameof(InvalidItems))]
    public async Task PostShoppingListItem_Returns_UnprocessableEntity_And_DoesNotChangeDB_When_ItemIsInvalid(
        (ShoppingListItemDto ItemToAdd,
         string ExpectedErrorMessage) testData)
    {
        // Arrange
        SetTestData([]);

        // Act
        var response = await _client.PostAsJsonAsync(RouteBases.ShoppingListItem, testData.ItemToAdd);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        var content = await response.Content.ReadFromJsonAsync<string>();
        content.Should().Be(testData.ExpectedErrorMessage);

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo(Enumerable.Empty<ShoppingListItemDBType>());
    }

    [Test]
    public async Task PostShoppingListItem_Returns_UnprocessableEntity_And_DoesNotChangeDB_When_ItemHasAnId()
    {
        // Arrange
        SetTestData([]);
        var dtoWithId = new ShoppingListItemDto { Id = 999, Title = "Has Id", Description = "Should fail" };

        // Act
        var response = await _client.PostAsJsonAsync(RouteBases.ShoppingListItem, dtoWithId);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        var content = await response.Content.ReadFromJsonAsync<string>();
        content.Should().Be("The Id of the item is not empty, thus the item must already have been added to the database.");

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo(Enumerable.Empty<ShoppingListItemDBType>());
    }

    [Test]
    public async Task PostShoppingListItem_Returns_UnprocessableEntity_And_DoesNotChangeDB_When_ItemWithSameTitleInDb()
    {
        // Arrange
        var existing = new ShoppingListItemDBType { Id = 500, Title = "Duplicate Title", Description = "Desc" };
        var existing2 = new ShoppingListItemDBType { Id = 501, Title = existing.Title, Description = "Other Desc" };
        SetTestData([existing, existing2]);

        var duplicateTitleDto = new ShoppingListItemDto { Title = existing.Title, Description = "New Desc" };

        // Act
        var response = await _client.PostAsJsonAsync(RouteBases.ShoppingListItem, duplicateTitleDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        var content = await response.Content.ReadFromJsonAsync<string>();
        var expectedMessage = $"Item(s) with same title found when trying to add item, but the tile must be unique. Ids of these Items:\n\t{existing.Id}\n\t{existing2.Id}";
        content.Should().Be(expectedMessage);

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo([existing, existing2], opts => opts.WithoutStrictOrdering());
    }

    // Tests for PUT
    // ------------------

    private static IEnumerable<(IEnumerable<ShoppingListItemDBType> ExistingDbItems,
        ShoppingListItemDto UpdateDto,
        ShoppingListItemDto ExpectedResponse,
        IEnumerable<ShoppingListItemDBType> ExpectedStoredItems)>
        TestDataForUpdatingExistingItems()
    {
        var baseTime1 = new DateTimeOffset(2025, 01, 01, 12, 00, 00, TimeSpan.Zero);
        var baseTime2 = new DateTimeOffset(2025, 02, 02, 08, 30, 00, TimeSpan.Zero);
        var newTime = new DateTimeOffset(2025, 03, 03, 18, 15, 00, TimeSpan.Zero);

        // 1: Update description only (BoughtAt stays null)
        var existing1 = new ShoppingListItemDBType { Id = 10, Title = "Alpha", Description = "Old", BoughtAt = null };
        var update1 = new ShoppingListItemDto { Id = existing1.Id, Title = existing1.Title, Description = "Updated Desc", BoughtAt = null };
        var expectedResp1 = update1;
        var expectedStored1 = new ShoppingListItemDBType
        {
            Id = existing1.Id,
            Title = existing1.Title,
            Description = update1.Description,
            BoughtAt = null
        };
        yield return ([existing1], update1, expectedResp1, [expectedStored1]);

        // 2: Set BoughtAt from null to value
        var existing2 = new ShoppingListItemDBType { Id = 20, Title = "Beta", Description = "Original", BoughtAt = null };
        var update2 = new ShoppingListItemDto { Id = existing2.Id, Title = existing2.Title, Description = "Original", BoughtAt = baseTime1 };
        var expectedResp2 = update2;
        var expectedStored2 = new ShoppingListItemDBType
        {
            Id = existing2.Id,
            Title = existing2.Title,
            Description = update2.Description,
            BoughtAt = baseTime1
        };
        yield return ([existing2], update2, expectedResp2, [expectedStored2]);

        // 3: Remove BoughtAt (value -> null)
        var existing3 = new ShoppingListItemDBType { Id = 30, Title = "Gamma", Description = "Keep", BoughtAt = baseTime2 };
        var update3 = new ShoppingListItemDto { Id = existing3.Id, Title = existing3.Title, Description = "Keep", BoughtAt = null };
        var expectedResp3 = update3;
        var expectedStored3 = new ShoppingListItemDBType
        {
            Id = existing3.Id,
            Title = existing3.Title,
            Description = existing3.Description,
            BoughtAt = null
        };
        yield return ([existing3], update3, expectedResp3, [expectedStored3]);

        // 4: Change description and BoughtAt (value -> different value) with another untouched item present
        var existing4a = new ShoppingListItemDBType { Id = 40, Title = "Delta", Description = "Desc A", BoughtAt = baseTime1 };
        var existing4b = new ShoppingListItemDBType { Id = 41, Title = "Epsilon", Description = "Other item", BoughtAt = null };
        var update4 = new ShoppingListItemDto { Id = existing4a.Id, Title = existing4a.Title, Description = "Desc A Updated", BoughtAt = newTime };
        var expectedResp4 = update4;
        var expectedStored4a = new ShoppingListItemDBType
        {
            Id = existing4a.Id,
            Title = existing4a.Title,
            Description = update4.Description,
            BoughtAt = newTime
        };
        // untouched second item
        var expectedStored4b = existing4b;
        yield return ([existing4a, existing4b], update4, expectedResp4, [expectedStored4a, expectedStored4b]);
    }

    [Test, TestCaseSource(nameof(TestDataForUpdatingExistingItems))]
    public async Task PutShoppingListItem_Returns_OKAndUpdatedItem_And_UpdatesItemInDB_When_ItemIsValid_And_ItemInDB(
        (IEnumerable<ShoppingListItemDBType> ExistingDbItems,
         ShoppingListItemDto UpdateDto,
         ShoppingListItemDto ExpectedResponse,
         IEnumerable<ShoppingListItemDBType> ExpectedStoredItems) testData)
    {
        // Arrange
        SetTestData(testData.ExistingDbItems);

        // Act
        var response = await _client.PutAsJsonAsync(RouteBases.ShoppingListItem, testData.UpdateDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var result = await response.Content.ReadFromJsonAsync<ShoppingListItemDto>();
        result.Should().NotBeNull();
        result.Should().BeEquivalentTo(testData.ExpectedResponse);

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo(testData.ExpectedStoredItems,
            opts => opts.WithoutStrictOrdering(),
            "only the targeted item should change and others remain untouched");
    }

    [Test, TestCaseSource(nameof(InvalidItems))]
    public async Task PutShoppingListItem_Returns_UnprocessableEntity_And_DoesNotChangeDB_When_ItemIsInvalid(
        (ShoppingListItemDto ItemToAdd,
         string ExpectedErrorMessage) testData)
    {
        // Arrange
        SetTestData([]);

        // Act
        var response = await _client.PutAsJsonAsync(RouteBases.ShoppingListItem, testData.ItemToAdd);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        var content = await response.Content.ReadFromJsonAsync<string>();
        content.Should().Be(testData.ExpectedErrorMessage);

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo(Enumerable.Empty<ShoppingListItemDBType>());
    }

    [Test]
    public async Task PutShoppingListItem_Returns_UnprocessableEntity_And_DoesNotChangeDB_When_ItemHasNoId()
    {
        // Arrange
        SetTestData([]);
        var dtoWithId = new ShoppingListItemDto { Id = null, Title = "Has no Id", Description = "Should fail" };

        // Act
        var response = await _client.PutAsJsonAsync(RouteBases.ShoppingListItem, dtoWithId);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        var content = await response.Content.ReadFromJsonAsync<string>();
        content.Should().Be("The Id of the item is empty, thus the item can not have been added to the database yet.");

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo(Enumerable.Empty<ShoppingListItemDBType>());
    }

    [Test]
    public async Task PutShoppingListItem_Returns_UnprocessableEntity_And_DoesNotChangeDB_When_ItemWithSameTitleInDb()
    {
        // Arrange
        var existing = new ShoppingListItemDBType { Id = 700, Title = "Keep", Description = "Orig", BoughtAt = null };
        SetTestData([existing]);

        var mismatchTitleDto = new ShoppingListItemDto { Id = existing.Id, Title = "Changed", Description = existing.Description };

        // Act
        var response = await _client.PutAsJsonAsync(RouteBases.ShoppingListItem, mismatchTitleDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);

        var content = await response.Content.ReadFromJsonAsync<string>();
        var expectedMessage = $"There already was an item with the ID {existing.Id} with a different title,"
                             + " but an items title must not change.\n"
                             + $"\tTitle of item to update: {mismatchTitleDto.Title}\n"
                             + $"\tTitle of item in database: {existing.Title}";
        content.Should().Be(expectedMessage);

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo([existing]);
    }

    private static IEnumerable<(IEnumerable<ShoppingListItemDBType> ExistingDbItems,
        ShoppingListItemDto UpdateDto,
        IEnumerable<ShoppingListItemDBType> ExpectedStoredItems)>
        TestDataForUpdatingItemsWithItemToUpdateMissingInDb()
    {
        // 1: DB is empty
        var updateNotFound = new ShoppingListItemDto { Id = 9999, Title = "Missing", Description = "Desc" };
        yield return ([], updateNotFound, []);

        // 2: DB has other items, but not the one to update
        var existing = new ShoppingListItemDBType { Id = 700, Title = "Keep", Description = "Orig", BoughtAt = null };
        yield return ([existing], updateNotFound, [existing]);
    }

    [Test, TestCaseSource(nameof(TestDataForUpdatingItemsWithItemToUpdateMissingInDb))]
    public async Task PutShoppingListItem_Returns_Error_And_DoesNotChangeDB_When_ItemIsNotInDB(
        (IEnumerable<ShoppingListItemDBType> ExistingDbItems,
         ShoppingListItemDto UpdateDto,
         IEnumerable<ShoppingListItemDBType> ExpectedStoredItems) testData)
    {
        // Arrange
        SetTestData(testData.ExistingDbItems);

        // Act
        var response = await _client.PutAsJsonAsync(RouteBases.ShoppingListItem, testData.UpdateDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        var content = await response.Content.ReadAsStringAsync();
        content.Should().BeEmpty();

        var storedItems = GetAllStoredItems();
        storedItems.Should().BeEquivalentTo(testData.ExpectedStoredItems, opts => opts.WithoutStrictOrdering());
    }
}

namespace mahl.Server.Tests;

using FluentAssertions;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using mahl.Shared;
using mahl.Shared.Dtos;
using Serilog.Events;
using Serilog.Sinks.InMemory.Assertions;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;

[Parallelizable(ParallelScope.All)]
[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[TestFixture]
public class ShoppingListEndpointsTests : EndpointsTestsBase
{
    private static IEnumerable<(IEnumerable<ShoppingListItemDBType> DbItems, IEnumerable<ShoppingListItemDto> Dtos)>
        TestDataContainingUnboughtItems()
    {
        var unboughtDbItem1 = new ShoppingListItemDBType { Id = 4512, Title = "Some title" };
        var unboughtDbItem2 = new ShoppingListItemDBType { Id = 673, Title = "Some other title" };
        var boughtDbItem = new ShoppingListItemDBType { Id = 36, Title = "Bought Item", BoughtAt = DateTimeOffset.Now.AddDays(-2) };

        var unboughtDtoItem1 = unboughtDbItem1.MapToDto();
        var unboughtDtoItem2 = unboughtDbItem2.MapToDto();

        yield return ([unboughtDbItem1], [unboughtDtoItem1]);

        yield return ([unboughtDbItem1, unboughtDbItem2], [unboughtDtoItem1, unboughtDtoItem2]);

        yield return ([unboughtDbItem1, boughtDbItem, unboughtDbItem2], [unboughtDtoItem1, unboughtDtoItem2]);
    }

    [Test, TestCaseSource(nameof(TestDataContainingUnboughtItems))]
    public async Task GetShoppingList_Returns_OkAndPopulatedList_When_UnboughtItemsExist(
        (IEnumerable<ShoppingListItemDBType> DbItems, IEnumerable<ShoppingListItemDto> Dtos) testData)
    {
        // Arrange
        SetTestData(testData.DbItems);

        // Act
        var response = await _client.GetAsync(RouteBases.ShoppingList);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var result = await response.Content.ReadFromJsonAsync<ShoppingListDto>();

        result.Should().NotBeNull();
        result.Items.Should().BeEquivalentTo(testData.Dtos);
    }

    private static IEnumerable<IEnumerable<ShoppingListItemDBType>>
        TestDataNotContainingUnboughtItems()
    {
        var boughtDbItem1 = new ShoppingListItemDBType { Title = "Bought Item", BoughtAt = DateTimeOffset.Now.AddDays(-5) };
        var boughtDbItem2 = new ShoppingListItemDBType { Title = "Other Bought Item", BoughtAt = DateTimeOffset.Now.AddDays(-12) };

        yield return [];

        yield return [boughtDbItem1];

        yield return [boughtDbItem1, boughtDbItem2];
    }

    [Test, TestCaseSource(nameof(TestDataNotContainingUnboughtItems))]
    public async Task GetShoppingList_Returns_OkAndEmptyList_When_NoUnboughtItemExists(
        IEnumerable<ShoppingListItemDBType> testData)
    {
        // Arrange
        SetTestData(testData);

        // Act
        var response = await _client.GetAsync(RouteBases.ShoppingList);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var result = await response.Content.ReadFromJsonAsync<ShoppingListDto>();

        result.Should().NotBeNull();
        result.Items.Should().BeEmpty();
    }

    [Test]
    public async Task GetShoppingList_Returns_Problem_And_LogsError_When_ItemInDbIsInvalid()
    {
        // Arrange
        var invalidItem1 = new ShoppingListItemDBType { Id = 4512, Title = "" };
        var invalidItem2 = new ShoppingListItemDBType { Id = 87, Title = "" };
        ShoppingListItemDBType[] invalidDbItems = [invalidItem1, invalidItem2];
        SetTestData(invalidDbItems);

        // Act
        var response = await _client.GetAsync(RouteBases.ShoppingList);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);

        var content = await response.Content.ReadAsStringAsync();
        var dl = JsonDocument.Parse(content);
        var traceId = dl.RootElement.GetProperty(Shared.Constants.TraceIdString).GetString();
        traceId.Should().NotBeNullOrEmpty();

        const string expectedTemplate = $"Error constructing {nameof(ShoppingList)} with this instance of {nameof(ShoppingListItemDBType)}:"
                                        + " {@itemToMap}, Error: {error}";

        var loggedEvents = ParallelTestLogStore.Logs[_testId];
        var loggedErrors = loggedEvents.Where(e => e.Level == LogEventLevel.Error
                                                   && e.MessageTemplate.Text == expectedTemplate).ToList();

        loggedErrors.Should().HaveCount(1);

        const string expectedErrorMessage = "Value cannot be null, empty or white space.";
        var matchFound = false;
        foreach (var invalidItem in invalidDbItems)
        {
            foreach (var loggedError in loggedErrors)
            {
                loggedError.Properties.TryGetValue("error", out var errorPropertyValue);
                var errorString = (errorPropertyValue as ScalarValue)?.Value as string;
                errorString.Should().Be(expectedErrorMessage);

                loggedError.Properties.TryGetValue("itemToMap", out var dbItemPropertyValue);
                var dbItemStructure = dbItemPropertyValue as StructureValue;
                dbItemStructure.Should().NotBeNull();

                var id = dbItemStructure.ExtractPropertyValue<int>(nameof(ShoppingListItemDBType.Id));
                if (id != invalidItem.Id)
                    continue;
                matchFound = true;

                var title = dbItemStructure.ExtractPropertyValue<string>(nameof(ShoppingListItemDBType.Title));
                title.Should().Be(invalidItem.Title);

                var description = dbItemStructure.ExtractPropertyValue<string>(nameof(ShoppingListItemDBType.Description));
                description.Should().Be(invalidItem.Description);

                var boughtAt = dbItemStructure.ExtractPropertyValue<DateTimeOffset?>(nameof(ShoppingListItemDBType.BoughtAt));
                boughtAt.Should().Be(invalidItem.BoughtAt);

                var tboughtAt = dbItemStructure.ExtractPropertyValue<string?>(nameof(ShoppingListItemDBType.BoughtAt));
                boughtAt.Should().Be(invalidItem.BoughtAt);

                break;
            }
            if (matchFound)
                break;
        }
        matchFound.Should().BeTrue($"the log should contain (at least) one entry for an invalid item");
    }

    [Test]
    public async Task GetShoppingList_Returns_ProblemWithError_When_ListInDbIsInvalid()
    {
        // Arrange
        var validItem = new ShoppingListItemDBType { Id = 4512, Title = "Some title" };
        var validItemDuplicate = new ShoppingListItemDBType { Id = validItem.Id + 1, Title = validItem.Title };
        ShoppingListItemDBType[] invalidDbList = [validItem, validItemDuplicate];
        SetTestData(invalidDbList);

        // Act
        var response = await _client.GetAsync(RouteBases.ShoppingList);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);

        var content = await response.Content.ReadAsStringAsync();
        var dl = JsonDocument.Parse(content);
        var traceId = dl.RootElement.GetProperty(Shared.Constants.TraceIdString).GetString();
        traceId.Should().NotBeNullOrEmpty();

        const string expectedTemplate = $"Error constructing {nameof(ShoppingList)} with this instance of {nameof(ShoppingListItemDBType)}:"
                                        + " {@itemToMap}, Error: {error}";
        var expectedErrorMessage = $"Item with id SyncItemId({validItemDuplicate.Id}) already in list.";

        var loggedEvents = ParallelTestLogStore.Logs[_testId];
        var loggedErrors = loggedEvents.Where(e => e.MessageTemplate.Text == expectedTemplate
                                                   && e.Level == LogEventLevel.Error
                                                   && e.Properties.ContainsKey("error")
                                                   && $"{((ScalarValue)e.Properties["error"]).Value}" == expectedErrorMessage)
                                       .ToArray();
        loggedErrors.Should().HaveCount(1);
        var loggedError = loggedErrors.First();

        loggedError.Properties.TryGetValue("itemToMap", out var dbItemPropertyValue);
        var dbItemStructure = dbItemPropertyValue as StructureValue;
        dbItemStructure.Should().NotBeNull();

        var id = dbItemStructure.ExtractPropertyValue<int>(nameof(ShoppingListItemDBType.Id));
        id.Should().Be(validItemDuplicate.Id);

        var title = dbItemStructure.ExtractPropertyValue<string>(nameof(ShoppingListItemDBType.Title));
        title.Should().Be(validItemDuplicate.Title);

        var description = dbItemStructure.ExtractPropertyValue<string>(nameof(ShoppingListItemDBType.Description));
        description.Should().Be(validItemDuplicate.Description);

        var boughtAt = dbItemStructure.ExtractPropertyValue<DateTimeOffset?>(nameof(ShoppingListItemDBType.BoughtAt));
        boughtAt.Should().Be(validItemDuplicate.BoughtAt);

        var tboughtAt = dbItemStructure.ExtractPropertyValue<string?>(nameof(ShoppingListItemDBType.BoughtAt));
        boughtAt.Should().Be(validItemDuplicate.BoughtAt);
    }
}

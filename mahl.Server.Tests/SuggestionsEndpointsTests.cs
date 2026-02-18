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
public class SuggestionsEndpointsTests : EndpointsTestsBase
{
    private static IEnumerable<(IEnumerable<ShoppingListItemDBType> DbItems, string Query)>
        TestDataWithoutItemsToSuggest()
    {
        var unboughtDbItem1 = new ShoppingListItemDBType { Id = 4512, Title = "Some title" };
        var unboughtDbItem2 = new ShoppingListItemDBType { Id = 673, Title = "Some other title" };
        var boughtDbItem = new ShoppingListItemDBType { Id = 36, Title = "Bought Item", BoughtAt = DateTimeOffset.Now.AddDays(-2) };

        yield return ([unboughtDbItem1], "Test");

        yield return ([unboughtDbItem1, unboughtDbItem2], "A");

        yield return ([unboughtDbItem1, boughtDbItem, unboughtDbItem2], "Cucum");
    }

    [Test, TestCaseSource(nameof(TestDataWithoutItemsToSuggest))]

    public async Task GetSuggestions_Returns_EmptyList_When_NoItemsToSuggestExist(
        (IEnumerable<ShoppingListItemDBType> DbItems, string Query) testData)
    {
        // Arrange
        SetTestData(testData.DbItems);

        // Act
        var response = await _client.GetAsync(RouteBases.Suggestions + $"?query={testData.Query}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var result = await response.Content.ReadFromJsonAsync<IEnumerable<ShoppingListItemDto>>();
        result.Should().NotBeNull();
        result.Should().BeEmpty();
    }

    private static IEnumerable<(IEnumerable<ShoppingListItemDBType> DbItems, string Query, IEnumerable<ShoppingListItemDto> Suggestions)>
        TestDataWithItemsToSuggest()
    {
        var unboughtDbItem1 = new ShoppingListItemDBType { Id = 4512, Title = "Some title" };
        var unboughtDbItem2 = new ShoppingListItemDBType { Id = 673, Title = "Some other title" };
        var boughtDbItem = new ShoppingListItemDBType { Id = 36, Title = "Bought Item", BoughtAt = DateTimeOffset.Now.AddDays(-2) };

        var unboughtDtoItem1 = unboughtDbItem1.MapToDto();
        var unboughtDtoItem2 = unboughtDbItem2.MapToDto();
        var boughtDtoItem = boughtDbItem.MapToDto();

        yield return ([unboughtDbItem1], "Some", [unboughtDtoItem1]);

        yield return ([unboughtDbItem1, unboughtDbItem2], "So", [unboughtDtoItem1, unboughtDtoItem2]);

        yield return ([unboughtDbItem1, boughtDbItem, unboughtDbItem2], "Ite", [boughtDtoItem]);

        yield return ([unboughtDbItem1, boughtDbItem, unboughtDbItem2], "so", [unboughtDtoItem1, unboughtDtoItem2]);

        yield return ([unboughtDbItem1, boughtDbItem, unboughtDbItem2], "o", [unboughtDtoItem1, unboughtDtoItem2, boughtDtoItem]);
    }

    [Test, TestCaseSource(nameof(TestDataWithItemsToSuggest))]

    public async Task GetSuggestions_Returns_FittingSuggestions_When_ItemsToSuggestExist(
        (IEnumerable<ShoppingListItemDBType> DbItems, string Query, IEnumerable<ShoppingListItemDto> Suggestions) testData)
    {
        // Arrange
        SetTestData(testData.DbItems);

        // Act
        var response = await _client.GetAsync(RouteBases.Suggestions + $"?query={testData.Query}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var result = await response.Content.ReadFromJsonAsync<IEnumerable<ShoppingListItemDto>>();
        result.Should().BeEquivalentTo(testData.Suggestions);
    }

    [Test]
    public async Task GetSuggestions_PrioritizesMatchesStartingWithQuery_WhenSufficientMatchesExist()
    {
        // Arrange
        var query = "App";

        // Create enough items that start with "App", i.e. the maximum suggestions count
        var itemsStartingWithQuery = Enumerable.Range(1, Constants.NumberOfSearchSuggestions)
            .Select(i => new ShoppingListItemDBType
            {
                Id = i,
                Title = $"App{i:D3}", // App001, App002, etc.
            });

        // Create items that contain "App" but don't start with it
        var itemsContainingQuery = new List<ShoppingListItemDBType>
    {
        new ShoppingListItemDBType { Id = Constants.NumberOfSearchSuggestions + 1, Title = "Pineapple", },
        new ShoppingListItemDBType { Id = Constants.NumberOfSearchSuggestions + 2, Title = "Snapple Drink", },
        new ShoppingListItemDBType { Id = Constants.NumberOfSearchSuggestions + 3, Title = "Grapes Apple Mix", }
    };

        var allTestData = itemsStartingWithQuery
            .Concat(itemsContainingQuery)
            .OrderBy(_ => Random.Shared.Next());

        SetTestData(allTestData);

        // Act
        var response = await _client.GetAsync(RouteBases.Suggestions + $"?query={query}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var result = await response.Content.ReadFromJsonAsync<IEnumerable<ShoppingListItemDto>>();

        result.Should().NotBeNull();
        result.Should().HaveCount(Constants.NumberOfSearchSuggestions,
            "should return exactly the maximum number of suggestions");

        // All returned items should start with the query (none should be "contains only" items)
        result.Should().OnlyContain(item => item.Title.StartsWith(query, StringComparison.InvariantCultureIgnoreCase),
            "should prioritize items starting with the query over items only containing the query");

        // Verify that items containing but not starting with query are NOT included
        foreach (var item in itemsContainingQuery)
            result.Should().NotContain(i => i.Title == item.Title);
    }

    [Test]
    public async Task GetSuggestions_LogsError_And_Returns_InternalServerError_When_DbItemMappingFails()
    {
        // Arrange
        var invalidItem = new ShoppingListItemDBType
        {
            Id = 1,
            Title = $"Test{new string('a', Constants.ShoppingListTitleMaxLength)}",
        };

        SetTestData([invalidItem]);

        // Act
        var response = await _client.GetAsync(RouteBases.Suggestions + "?query=test");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
        var content = await response.Content.ReadAsStringAsync();
        var dl = JsonDocument.Parse(content);
        var traceId = dl.RootElement.GetProperty(Constants.TraceIdString).GetString();
        traceId.Should().NotBeNullOrEmpty();

        const string expectedTemplate = $"Error constructing {nameof(ShoppingListItem)} with this instance of {nameof(ShoppingListItemDBType)}:"
                                        + " {@itemToMap}, Error: {error}";

        var loggedEvents = ParallelTestLogStore.Logs[_testId];
        var loggedErrors = loggedEvents.Where(e => e.Level == LogEventLevel.Error
                                                   && e.MessageTemplate.Text == expectedTemplate).ToList();

        loggedErrors.Should().HaveCount(1);

        string expectedErrorMessage = $"{nameof(ShoppingListItem.Title)} must not be longer than {Constants.ShoppingListTitleMaxLength} characters.";
        var matchFound = false;

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
        matchFound.Should().BeTrue($"the log should contain (at least) one entry for an invalid item");
    }

    [Test]
    [TestCase("")]
    [TestCase(" ")]
    [TestCase("\t")]
    [TestCase("\n")]
    public async Task GetSuggestions_Returns_Error_WhenQueryParameterIsInvalid(string invalidQuery)
    {
        {
            // Arrange

            // Act
            var response = await _client.GetAsync(RouteBases.Suggestions + $"?query={invalidQuery}");

            // Assert
            response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
            var content = await response.Content.ReadFromJsonAsync<string>();
            content.Should().Be("Parameter query was not valid: Value cannot be null, empty or white space.");
        }

    }
}

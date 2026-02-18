namespace mahl.Server.Tests;
using mahl.Server.Data;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Tests.Helpers;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;
using Serilog.Events;
using System.Collections.Concurrent;

[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[Parallelizable(ParallelScope.All)]
[TestFixture]
public class EndpointsTestsBase : IAsyncDisposable
{
    protected readonly HttpClient _client;
    protected readonly TestWebApplicationFactory _factory;
    protected readonly string _testId;

    public EndpointsTestsBase()
    {
        _testId = Guid.NewGuid().ToString();
        ParallelTestLogStore.Logs[_testId] = new ConcurrentBag<LogEvent>();
        _factory = new TestWebApplicationFactory(_testId);
        _client = _factory.CreateClient();
    }
    public async ValueTask DisposeAsync()
    {
        if (_factory != null)
        {
            using (var scope = _factory.Services.CreateScope())
            {
                var dbContext = scope.ServiceProvider.GetRequiredService<MariaDbContext>();
                await dbContext.Database.EnsureDeletedAsync();
            }
            _factory.Dispose();
        }
        _client?.Dispose();
        ParallelTestLogStore.Logs.TryRemove(_testId, out _);
    }

    protected void SetTestData(IEnumerable<ShoppingListItemDBType> testData)
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MariaDbContext>();
        db.ShoppingListItems.RemoveRange(db.ShoppingListItems);
        if (testData.Any())
        {
            db.ShoppingListItems.AddRange(testData);
        }
        db.SaveChanges();
    }

    protected IEnumerable<ShoppingListItemDBType> GetAllStoredItems()
    {
        using var scope = _factory.Services.CreateScope();
        var dbContext = scope.ServiceProvider.GetRequiredService<MariaDbContext>();
        return dbContext.ShoppingListItems.AsEnumerable().ToList();
    }
}
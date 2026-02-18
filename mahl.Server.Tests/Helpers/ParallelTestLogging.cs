using Serilog.Core;
using Serilog.Events;
using System.Collections.Concurrent;

/// <summary>
/// A global, thread-safe store for logs from all parallel tests.
/// The key is a unique Test ID (GUID).
/// </summary>
public static class ParallelTestLogStore
{
    public static readonly ConcurrentDictionary<string, ConcurrentBag<LogEvent>> Logs = new();
}

/// <summary>
/// A custom Serilog sink that knows which test it belongs to via a unique ID.
/// It writes received logs into the correct "bag" in the ParallelTestLogStore.
/// </summary>
public class TestIdSink : ILogEventSink
{
    private readonly string _testId;

    public TestIdSink(string testId)
    {
        _testId = testId;
    }

    public void Emit(LogEvent logEvent)
    {
        if (ParallelTestLogStore.Logs.TryGetValue(_testId, out var logBag))
        {
            logBag.Add(logEvent);
        }
    }
}
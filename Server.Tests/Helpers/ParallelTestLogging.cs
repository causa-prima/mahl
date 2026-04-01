namespace mahl.Server.Tests.Helpers;

using Serilog.Core;
using Serilog.Events;
using System.Collections.Concurrent;

/// <summary>
/// A global, thread-safe store for logs from all parallel tests.
/// The key is a unique Test ID (GUID).
/// </summary>
#pragma warning disable MA0048 // ParallelTestLogStore and TestIdSink are tightly coupled and belong in one file
public static class ParallelTestLogStore
{
    private static readonly ConcurrentDictionary<string, ConcurrentBag<LogEvent>> _logs =
        new(StringComparer.Ordinal);

    public static ConcurrentDictionary<string, ConcurrentBag<LogEvent>> Logs => _logs;
}

/// <summary>
/// A custom Serilog sink that knows which test it belongs to via a unique ID.
/// It writes received logs into the correct "bag" in the ParallelTestLogStore.
/// </summary>
public sealed class TestIdSink(string testId) : ILogEventSink
{
    public void Emit(LogEvent logEvent)
    {
        if (ParallelTestLogStore.Logs.TryGetValue(testId, out var logBag))
            logBag.Add(logEvent);
    }
}
#pragma warning restore MA0048

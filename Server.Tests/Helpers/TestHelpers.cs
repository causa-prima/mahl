namespace mahl.Server.Tests.Helpers;

using FluentAssertions.Execution;
using System.Diagnostics.CodeAnalysis;

[ExcludeFromCodeCoverage]
public static class TestHelpers
{
    public static Continuation FailWithTypeMismatch(string testSubjectName, Type expectedType, object actualValue) =>
        Execute.Assertion.FailWith($"Expected {testSubjectName} to be of type {expectedType.Name}, but it was of type {actualValue.GetType()}.");

    public static T Satisfy<T>(this T subject, Action<T> assertions)
    {
        assertions(subject);
        return subject;
    }
}

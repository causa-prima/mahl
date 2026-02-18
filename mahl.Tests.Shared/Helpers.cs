namespace mahl.Tests.Shared;

using FluentAssertions.Execution;
using System.Diagnostics.CodeAnalysis;

[ExcludeFromCodeCoverage]
public static class Helpers
{
    public static Continuation FailWithTypeMismatch(string testSubjectName, Type expectedType, object actualValue) =>
        Execute.Assertion.FailWith($"Expected {testSubjectName} to be of type {expectedType.Name}, but it was of type {actualValue.GetType()}.");
}

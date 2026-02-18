namespace mahl.Server.Tests.Helpers;
using FluentAssertions;
using Serilog.Events;
using Serilog.Sinks.InMemory.Assertions;

internal static class SerilogExtensions
{

    internal static T ExtractPropertyValue<T>(this StructureValue item, string propertyName)
    {
        var prop = item.Properties.FirstOrDefault(p => p.Name == propertyName);
        prop.Should().NotBeNull($"the structure should contain a property with name '{propertyName}'");

        switch (prop.Value)
        {
            case ScalarValue { Value: null } s:
                default(T).Should().BeNull($"the property '{propertyName}' was null, which is only valid if a nullable {typeof(T).Name} was expected.");
                return default!;
            case ScalarValue { Value: T tScalar }:
                return tScalar;
            case T tExact:
                return tExact;
            case ScalarValue scalar:
                scalar.Value.Should().BeOfType<T>("the property should have this type");
                // The previous line should make sure we never reach this line.
                throw new NotSupportedException($"Expected type {typeof(T).Name}, but found {scalar.Value.GetType().Name}");
            default:
                prop.Value.Should().BeOfType<T>("the property should have this type");
                // The previous line should make sure we never reach this line.
                throw new NotSupportedException($"Expected type {typeof(T).Name}, but found {prop.Value.GetType().Name}");
        }
    }
}
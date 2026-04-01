namespace mahl.Server;

using OneOf.Types;

public static class Helpers
{
    internal static IResult CreateProblemWithTraceId(HttpContext context) =>
        Results.Problem(
            extensions: new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                [Constants.TraceIdString] = System.Diagnostics.Activity.Current?.TraceId.ToHexString()
                                            ?? context.TraceIdentifier
            });

    internal static void LogMappingError<T>(
        this ILogger logger,
        Type typeToConstruct,
        Error<(T ItemToMap, string ErrorString)> error)
        => logger.LogMappingError(
            typeToConstruct,
            error.Value.ItemToMap,
            error.Value.ErrorString);

    internal static void LogMappingError<T>(
        this ILogger logger,
        Type typeToConstruct,
        T itemToMap,
        Error<string> error)
        => logger.LogMappingError(
            typeToConstruct,
            itemToMap,
            error.Value);

    internal static void LogMappingError<T>(
        this ILogger logger,
        Type typeToConstruct,
        T itemToMap,
        string error)
    {
        // CA1848: LoggerMessage delegates require static partial methods and are incompatible with generic T.
#pragma warning disable CA1848
        logger.LogError(
            "Error constructing {TypeName} with this instance of {ItemTypeName}: {@ItemToMap}, Error: {Error}",
            typeToConstruct.Name, typeof(T).Name, itemToMap, error);
#pragma warning restore CA1848
    }

}

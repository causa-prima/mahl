namespace mahl.Server;

using mahl.Shared;
using OneOf.Types;

public static class Helpers
{
    internal static IResult CreateProblemWithTraceId(HttpContext context) =>
        Results.Problem(
            extensions: new Dictionary<string, object?>()
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
        => logger.LogError(
            $"Error constructing {typeToConstruct.Name} with this instance of {typeof(T).Name}:"
                            + " {@itemToMap}, Error: {error}", itemToMap, error);

}

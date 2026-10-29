namespace mahl.Server.Endpoints;

internal static class ValidationProblems
{
    // ADR-S090-1: field-keyed 422 body { "errors": { "<jsonPropertyName>": ["<msg>"] } } – multiple field
    // errors group into one dictionary so all messages appear simultaneously.
    internal static IResult ValidationProblemFor(IReadOnlyList<FieldError> errors) =>
        Results.ValidationProblem(
            errors.GroupBy(e => e.Key, e => e.Message, StringComparer.Ordinal)
                .ToDictionary(g => g.Key, g => g.ToArray(), StringComparer.Ordinal),
            statusCode: StatusCodes.Status422UnprocessableEntity);
}

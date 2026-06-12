using OneOf;
using OneOf.Types;

namespace mahl.Server;

internal static class OneOfExtensions
{
    public static OneOf<TOut, Error<string>> Map<TIn, TOut>(
        this OneOf<TIn, Error<string>> source, Func<TIn, TOut> map) =>
        source.Match<OneOf<TOut, Error<string>>>(ok => map(ok), err => err);

    public static OneOf<TOut, Error<string>> Bind<TIn, TOut>(
        this OneOf<TIn, Error<string>> source, Func<TIn, OneOf<TOut, Error<string>>> bind) =>
        source.Match(ok => bind(ok), err => err);

    public static OneOf<T, TError> MapError<T, TErrorIn, TError>(
        this OneOf<T, TErrorIn> source, Func<TErrorIn, TError> mapError) =>
        source.Match<OneOf<T, TError>>(ok => ok, err => mapError(err));

    public static async Task<OneOf<TOut, TError>> BindAsync<TIn, TOut, TError>(
        this OneOf<TIn, TError> source, Func<TIn, Task<OneOf<TOut, TError>>> bind) =>
        await source.Match(
            async ok => await bind(ok),
            err => Task.FromResult<OneOf<TOut, TError>>(err));

    public static async Task<TResult> MatchAsync<T, TError, TResult>(
        this Task<OneOf<T, TError>> source, Func<T, TResult> onSuccess, Func<TError, TResult> onError) =>
        (await source).Match(onSuccess, onError);
}

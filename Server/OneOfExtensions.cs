namespace mahl.Server;

using OneOf;
using OneOf.Types;
using System;
using System.Collections.Immutable;

public static class OneOfExtensions
{
    public static OneOf<TOut, TError> Bind<TIn, TOut, TError>
        (this OneOf<TIn, TError> input, Func<TIn, OneOf<TOut, TError>> func) =>
        input.Match(value => func(value), error => error);

    public static OneOf<T, TErrorOut> MapError<T, TErrorIn, TErrorOut>
        (this OneOf<T, TErrorIn> input, Func<TErrorIn, TErrorOut> map) =>
        input.Match<OneOf<T, TErrorOut>>(
            value => value,
            error => map(error)
        );

    public static OneOf<TOut, TError> Map<TIn, TOut, TError>
        (this OneOf<TIn, TError> input, Func<TIn, TOut> mapper) =>
        input.Match<OneOf<TOut, TError>>(
            value => mapper(value),
            error => error);

    public static async Task<OneOf<TOut, TError>> BindAsync<TIn, TOut, TError>
        (this OneOf<TIn, TError> input, Func<TIn, Task<OneOf<TOut, TError>>> func) =>
        await input.Match(
            value => func(value),
            error => Task.FromResult(OneOf<TOut, TError>.FromT1(error)));

    public static async Task<TResult> MatchAsync<T0, T1, TResult>
        (this Task<OneOf<T0, T1>> task, Func<T0, TResult> f0, Func<T1, TResult> f1) =>
        (await task).Match(f0, f1);

    public static T ValueOrThrow<T, TError>(this OneOf<T, TError> input, string message) =>
        input.Match(value => value, _ => throw new InvalidOperationException(message));

    public static T ValueOrThrowUnreachable<T, TError>(this OneOf<T, TError> input) =>
        input.ValueOrThrow("Unreachable.");

    public static OneOf<IReadOnlyList<T>, Error<string>> Sequence<T>(
        this IEnumerable<OneOf<T, Error<string>>> results) =>
        results.Aggregate(
            (OneOf<ImmutableList<T>, Error<string>>) ImmutableList<T>.Empty,
            (acc, item) => acc.Bind(list =>
                item.Match<OneOf<ImmutableList<T>, Error<string>>>(
                    v => list.Add(v),
                    e => e
                ))
        ).Map(list => (IReadOnlyList<T>)list);
}

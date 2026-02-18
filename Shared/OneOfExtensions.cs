namespace mahl.Shared;

using OneOf;
using System;

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
}

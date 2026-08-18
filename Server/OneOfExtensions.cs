using OneOf;

namespace mahl.Server;

internal static class OneOfExtensions
{
    public static OneOf<TOut, TError> Map<TIn, TOut, TError>(
        this OneOf<TIn, TError> source, Func<TIn, TOut> map) =>
        source.Match<OneOf<TOut, TError>>(ok => map(ok), err => err);

    public static OneOf<TOut, TError> Bind<TIn, TOut, TError>(
        this OneOf<TIn, TError> source, Func<TIn, OneOf<TOut, TError>> bind) =>
        source.Match(ok => bind(ok), err => err);

    public static OneOf<T, TError> MapError<T, TErrorIn, TError>(
        this OneOf<T, TErrorIn> source, Func<TErrorIn, TError> mapError) =>
        source.Match<OneOf<T, TError>>(ok => ok, err => mapError(err));

    public static async Task<OneOf<TOut, TError>> BindAsync<TIn, TOut, TError>(
        this OneOf<TIn, TError> source, Func<TIn, Task<OneOf<TOut, TError>>> bind) =>
        await source.Match(
            async ok => await bind(ok),
            err => Task.FromResult<OneOf<TOut, TError>>(err));

    // Applicative-Kombinator für Collect-All (ADR-S119-2). Bind kann strukturell nicht sammeln – es
    // schließt beim ersten Fehler kurz. Collect wertet beide Eingänge unabhängig aus und
    // konkateniert deren Fehler; nur so bleibt die Fehlermenge auf dem Gleis, statt den Fehlerkanal
    // per MapError(_ => …) durch parallel berechneten Zustand zu ersetzen (csharp-rop.md).
    // Ein Overload je Arity; höhere Stelligkeiten erst, wenn ein Aufrufer sie fordert.
    public static OneOf<TOut, IReadOnlyList<TError>> Collect<T1, T2, TOut, TError>(
        OneOf<T1, TError> first, OneOf<T2, TError> second, Func<T1, T2, TOut> combine) =>
        first.Match(
            ok1 => second.Match<OneOf<TOut, IReadOnlyList<TError>>>(
                ok2 => combine(ok1, ok2),
                error2 => new[] { error2 }),
            error1 => second.Match<OneOf<TOut, IReadOnlyList<TError>>>(
                _ => new[] { error1 },
                error2 => new[] { error1, error2 }));

    public static async Task<TResult> MatchAsync<T, TError, TResult>(
        this Task<OneOf<T, TError>> source, Func<T, TResult> onSuccess, Func<TError, TResult> onError) =>
        (await source).Match(onSuccess, onError);
}

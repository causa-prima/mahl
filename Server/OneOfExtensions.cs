using System.Collections.Immutable;
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

    // Collect für Eingänge, die selbst schon mehrere Fehler tragen (z.B. alle fehlerhaften Schritte einer
    // Liste). Eigener Name statt Overload von Collect: mit gleicher Stelligkeit wäre die Auswahl zwischen
    // beiden von der Typinferenz abhängig (TError = IReadOnlyList<…> passte auf beide).
    public static OneOf<TOut, IReadOnlyList<TError>> CollectMany<T1, T2, TOut, TError>(
        OneOf<T1, IReadOnlyList<TError>> first, OneOf<T2, IReadOnlyList<TError>> second, Func<T1, T2, TOut> combine) =>
        first.Match(
            ok1 => second.Match<OneOf<TOut, IReadOnlyList<TError>>>(
                ok2 => combine(ok1, ok2),
                errors2 => OneOf<TOut, IReadOnlyList<TError>>.FromT1(errors2)),
            errors1 => second.Match<OneOf<TOut, IReadOnlyList<TError>>>(
                _ => OneOf<TOut, IReadOnlyList<TError>>.FromT1(errors1),
                errors2 => errors1.Concat(errors2).ToList()));

    // Sammelt die Ergebnisse einer Liste: alle Werte, oder alle Fehler (Reihenfolge der Liste).
    // Ein Durchlauf mit Buildern: die Zahl der Elemente ist nicht begrenzt, ein Falten über CollectMany
    // kopierte je Element Array und Fehlerliste (quadratisch).
    public static OneOf<ImmutableArray<T>, IReadOnlyList<TError>> CollectAll<T, TError>(
        IEnumerable<OneOf<T, TError>> results)
    {
        var values = ImmutableArray.CreateBuilder<T>();
        var errors = new List<TError>();
        foreach (var result in results)
        {
            result.Switch(value => values.Add(value), error => errors.Add(error));
        }

        return errors.Count == 0
            ? values.ToImmutable()
            : errors;
    }

    public static async Task<TResult> MatchAsync<T, TError, TResult>(
        this Task<OneOf<T, TError>> source, Func<T, TResult> onSuccess, Func<TError, TResult> onError) =>
        (await source).Match(onSuccess, onError);
}

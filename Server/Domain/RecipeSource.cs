namespace mahl.Server.Domain;

using mahl.Server.Types;
using System.Diagnostics.CodeAnalysis;

public abstract record RecipeSource
{
    private RecipeSource() { }

    private sealed record UrlCase(Uri Url) : RecipeSource;
    private sealed record NoSourceCase : RecipeSource;

    public static RecipeSource FromUrl(Uri url) => new UrlCase(url);
    public static RecipeSource None { get; } = new NoSourceCase();

    [ExcludeFromCodeCoverage] // _ arm is structurally unreachable; private ctor prevents external subtypes
#pragma warning disable S3060 // Sum-Type dispatch: type test in switch is unavoidable with private-ctor subtypes
    public T Match<T>(Func<Uri, T> onUrl, Func<T> onNone) => this switch
    {
        UrlCase u    => onUrl(u.Url),
        NoSourceCase => onNone(),
        _            => SumType.Unreachable<T>()
    };
#pragma warning restore S3060 // Sum-Type dispatch

    public static explicit operator string?(RecipeSource source) =>
        source.Match(onUrl: url => (string?)url.OriginalString, onNone: () => null);
}

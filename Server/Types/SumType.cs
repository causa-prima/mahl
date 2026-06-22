namespace mahl.Server.Types;

// Shared sum-type infrastructure (ADR-S040-1). Match<T> implementations dispatch via switch with
// `_ => SumType.Unreachable<T>()`; the unreachable `_`-arm is structurally impossible (private/closed
// subtypes), so its single Stryker suppression lives here once instead of in every Match.
internal static class SumType
{
    // Stryker disable once String : "Unreachable." message in the structurally unreachable sum-type Match arm (ADR-S018-2)
    public static T Unreachable<T>() => throw new InvalidOperationException("Unreachable.");
}

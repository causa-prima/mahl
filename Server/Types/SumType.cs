namespace mahl.Server.Types;

public static class SumType
{
    // Stryker disable once String,Statement : unreachable — private ctor prevents external subtypes
    public static T Unreachable<T>() =>
        throw new InvalidOperationException("Unreachable.");
}

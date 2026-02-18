namespace mahl.Server.Types;

public struct NotFound<T>
{
    public NotFound(T value)
    {
        Value = value;
    }

    public T Value { get; }
}

namespace mahl.Server.Types;
public readonly record struct TrimmedString()
{
    public static readonly TrimmedString Empty = new TrimmedString(string.Empty);

    private readonly string? _value;
    public string Value { get => _value ?? string.Empty; init { _value = value.Trim(); } }

    public int Length => Value.Length;

    public TrimmedString(string value) : this() => Value = value;

    public override string ToString() => Value;

    public static implicit operator string(TrimmedString instance) => instance.Value;
    public static explicit operator TrimmedString(string instance) => new TrimmedString(instance);
}

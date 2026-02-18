namespace mahl.Shared.Types;

using OneOf;
using OneOf.Types;

public record struct SyncItemId
{
    private OneOf<int, Unknown> value { get; set; }
    private SyncItemId(OneOf<int, Unknown> value) => this.value = value;

    public TResult Match<TResult>(Func<int, TResult> f0, Func<Unknown, TResult> f1) => value.Match(f0, f1);
    public void Switch(Action<int> f0, Action<Unknown> f1) => value.Switch(f0, f1);

    public static readonly SyncItemId Unknown = new SyncItemId(new Unknown());
    public static SyncItemId Known(int id) => new SyncItemId(id);

    public override string ToString() =>
        value.Match(
            id => $"{nameof(SyncItemId)}({id})",
            _ => $"{nameof(SyncItemId)}(Unknown)"
        );

    public static implicit operator SyncItemId(int _) => new SyncItemId(_);
    public static implicit operator SyncItemId(Unknown _) => new SyncItemId(_);
    public static implicit operator SyncItemId(int? _) => _.HasValue ? new SyncItemId(_.Value) : SyncItemId.Unknown;
    public static implicit operator int?(SyncItemId _) => _.Match(id => id, _ => (int?)null);
}

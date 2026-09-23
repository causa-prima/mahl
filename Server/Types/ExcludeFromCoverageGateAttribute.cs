namespace mahl.Server.Types;

// Nimmt einen Member aus dem 100-%-Coverage-Gate (coverlet.MTP, `--coverlet-exclude-by-attribute`
// in prozesscode/dotnet-test.py) – und NUR daraus. Bewusst nicht [ExcludeFromCodeCoverage]: Stryker.NET
// verwirft Mutanten in so markiertem Code mit (S132 gemessen), womit getestete Logik in derselben
// Methode still aus dem Mutation Testing fiele. Mutations-Ausschlüsse laufen getrennt und zeilengenau
// über `// Stryker disable`. Wann ein Ausschluss zulässig ist: ADR-S041-9 (Addendum S132).
// `class`, nicht `record`: Records dürfen nicht von System.Attribute erben (CS8864).
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Constructor | AttributeTargets.Property, Inherited = false)]
internal sealed class ExcludeFromCoverageGateAttribute(string justification) : Attribute
{
    public string Justification { get; } = justification;
}

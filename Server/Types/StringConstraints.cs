using OneOf;

namespace mahl.Server.Types;

// Constraint-Träger für String-Feldregeln (ADR-S119-1, coding-guideline-csharp.md §2 Ebene 1).
// Feldagnostisch: sie melden einen Verstoß, keinen Meldungstext und keinen Feldnamen – die
// Zuordnung Fehlerfall -> deutscher Text liegt an der API-Grenze (ADR-S051-2, Regel 5).
// Der Ertrag ist, dass die parametrisierte Grenze Teil des Feldtyps wird
// (Bounded<NonEmptyTrimmedString, Max30>) statt ein handgeschriebener Check in Create().
internal enum StringViolation { Empty, TooLong }

// CRTP: TSelf erlaubt es einem Träger, seinen inneren Träger über TInner.Create(...) aufzurufen,
// ohne ihn zu kennen.
// `string?`, nicht `string`: System.Text.Json erzwingt die NRT-Annotationen des DTOs nicht – ein
// fehlendes oder explizit null gesetztes JSON-Property landet als null hier. Der Vertrag muss das
// sagen, sonst schreibt der nächste Implementierer input.Trim() und der Fall wird still zum 500er.
internal interface IStringConstraint<TSelf> where TSelf : IStringConstraint<TSelf>
{
    static abstract OneOf<TSelf, StringViolation> Create(string? input);
    string Value { get; }
}

// C# kennt keine const generics – ein Marker-Typ je Grenzwert trägt den Wert (ADR-S119-1).
internal interface IMaxLength { static abstract int MaxLength { get; } }

internal readonly record struct Bounded<TInner, TMax>
    where TInner : IStringConstraint<TInner> where TMax : IMaxLength
{
    private readonly TInner _inner;
    public string Value => _inner.Value; // wirft transitiv – der Guard sitzt im inneren Träger

    // Parameterless ctor must be public (record struct limitation) – catches new Bounded():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    public Bounded() => throw new InvalidOperationException("Uninitialized");

    private Bounded(TInner inner) => _inner = inner;

    // ADR-S051-3: die Länge wird auf dem bereits getrimmten Wert gemessen – der innere Träger
    // normalisiert, bevor hier gemessen wird.
    public static OneOf<Bounded<TInner, TMax>, StringViolation> Create(string? input) =>
        TInner.Create(input).Bind<TInner, Bounded<TInner, TMax>, StringViolation>(inner =>
            inner.Value.Length > TMax.MaxLength
                ? (OneOf<Bounded<TInner, TMax>, StringViolation>) StringViolation.TooLong
                : new Bounded<TInner, TMax>(inner));
}

// Phantom-Typen: sie tragen ihren Grenzwert ausschließlich statisch, werden nie instanziiert.
// ADR-S051-3: name max. 30, baseUnit max. 20 Zeichen.
internal readonly struct Max30 : IMaxLength { public static int MaxLength => 30; }

internal readonly struct Max20 : IMaxLength { public static int MaxLength => 20; }

using System.Globalization;
using mahl.Server.Types;
using OneOf;

namespace mahl.Server.Domain;

// ADR-S120-1: ein Validierungs-Fehlertyp je Domänentyp, feldagnostisch (Meldungstexte an der API-Grenze, ADR-S051-2).
// MA0048: File name must match type name – der Fehlertyp ist der Fehlerkanal von QuantityAmount.Create,
//         außerhalb dieses Typs bedeutungslos und ändert sich ausschließlich mit ihm.
#pragma warning disable MA0048
internal enum QuantityError { NotANumber, NotPositive, TooManyDecimals, TooLarge }
#pragma warning restore MA0048

// Domänentyp (ADR-S020-1, Addendum S141): der Zahlwert einer angegebenen Menge. Er prüft seine Regeln selbst,
// statt sich aus Constraint-Typen in Server/Types zusammenzusetzen – dort gibt es keinen Baustein für eine
// Dezimalzahl mit Grenzen, und einen auf Vorrat für nur diese eine Verwendung braucht es nicht. Die Regeln entscheiden auf
// der exakten Ziffernfolge, nicht auf einem decimal: System.Decimal rundet jenseits von ~28 Stellen und
// läuft darüber hinaus über (ADR-S135-2: „gerechnet wird exakt dezimal"). Erst ein bestandener Wert wird zum decimal.
internal readonly record struct QuantityAmount
{
    private const char DecimalSeparator = ',';
    private const char Zero = '0';
    private const int MaxDecimals = 3;
    private const int MaxIntegerDigits = 4; // mit höchstens 3 Nachkommastellen gleichbedeutend mit „höchstens 9999,999"
    // 10^MaxDecimals. Bewusst int statt decimal: Als decimal zählte die Line-Coverage diese Zeile nicht (Ursache ungeklärt).
    private const int ThousandthsPerUnit = 1000;

    private readonly decimal _value;

    // 0 ist keine gültige Menge – guard against default(QuantityAmount).Value (ADR-S041-9; ternary adds Conditional mutant).
    // Stryker disable once Equality,String,Conditional : default(T) guard unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("default(T) guard unreachable via normal construction (ADR-S041-9)")]
    public decimal Value => _value == default ? throw new InvalidOperationException("Uninitialized") : _value;

    // Parameterless ctor must be public (record struct limitation) – catches new QuantityAmount():
    // Stryker disable once Statement,String : parameterless ctor unreachable via normal construction (ADR-S041-9)
    [ExcludeFromCoverageGate("parameterless ctor unreachable via normal construction (ADR-S041-9)")]
    public QuantityAmount() => throw new InvalidOperationException("Uninitialized");

    private QuantityAmount(decimal value) => _value = value;

    // ADR-S135-2: Zahlform → größer als 0 → Nachkommastellen → Maximum; die erste verletzte Regel gilt.
    public static OneOf<QuantityAmount, QuantityError> Create(string word)
    {
        var parts = word.Split(DecimalSeparator);
        var integerPart = parts[0];
        var fractionPart = parts.Length == 2 ? parts[1] : string.Empty;
        if (parts.Length > 2 || !IsDigits(integerPart) || (parts.Length == 2 && !IsDigits(fractionPart)))
            return QuantityError.NotANumber;

        // Führende Nullen vorn und Nullen am Ende der Nachkommastellen zählen nicht.
        var integerDigits = integerPart.TrimStart(Zero);
        var fractionDigits = fractionPart.TrimEnd(Zero);
        if (integerDigits.Length == 0 && fractionDigits.Length == 0)
            return QuantityError.NotPositive;
        if (fractionDigits.Length > MaxDecimals)
            return QuantityError.TooManyDecimals;
        if (integerDigits.Length > MaxIntegerDigits)
            return QuantityError.TooLarge;

        // Höchstens 4 + 3 Ziffern: exakt als ganze Tausendstel darstellbar.
        var thousandths = long.Parse(integerDigits + fractionDigits.PadRight(MaxDecimals, Zero), CultureInfo.InvariantCulture);
        return new QuantityAmount((decimal)thousandths / ThousandthsPerUnit);
    }

    private static bool IsDigits(string text) => text.Length > 0 && text.All(char.IsAsciiDigit);
}

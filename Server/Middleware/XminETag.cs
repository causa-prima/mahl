using System.Globalization;

namespace mahl.Server.Middleware;

// ADR-S058-3: Single-Resource-ETag-Format – xmin (Postgres-Zeilenversion) hex-kodiert, quoted.
// Format() erzeugt den ETag (POST-Response), TryParse() liest ihn aus einem If-Match-Header zurück
// in den xmin-Wert (DELETE/PUT/PATCH). Beide Seiten teilen sich das Format – daher hier zentral,
// nicht als Endpoint-Mapping (docs/guidelines/coding-guideline-csharp.md Sektion 5: die
// file-static-Regel gilt für Domain/DbType/DTO-Mapping, nicht für dieses HTTP-Format-Utility, das
// über mehrere Endpoints hinweg gebraucht wird).
internal static class XminETag
{
    public static string Format(uint xmin) => $"\"{xmin:x8}\"";

    // ADR-S106-2: Standard-.NET-TryParse-Idiom statt OneOf/ROP – ein nicht-parsebarer If-Match ist
    // ein technischer Protokoll-Parsing-Fehler (HTTP-Header-Format), kein Domänenfehler
    // (docs/guidelines/csharp-rop.md: ROP gilt für Domänen-/Validierungsfehler). Wirft nie – der
    // Aufrufer entscheidet anhand des bool-Rückgabewerts über 400 vs. Concurrency-Check.
    public static bool TryParse(string etag, out uint value) =>
        uint.TryParse(etag.Trim('"'), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out value);
}

namespace mahl.Server.Endpoints;

// ADR-S120-1: der akkumulierte Fehlertyp IST das Antwortformat (ADR-S090-1: Feld-Key + Meldung),
// keine Zwischenstufe. Reiner Transport-Record an der API-Grenze – kein Domänentyp, deshalb ohne
// Factory und ohne Guards: er hat keine Invariante, die er durchsetzen müsste.
// Geteilt von allen Endpoints mit Feldvalidierung (Zutaten, Rezepte).
internal readonly record struct FieldError(string Key, string Message);

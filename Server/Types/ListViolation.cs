namespace mahl.Server.Types;

// Verstoß einer Listen-Einschränkung: feldagnostisch wie StringViolation – die Zuordnung zum Feld und zum
// deutschen Text liegt an der API-Grenze (ADR-S051-2, ADR-S120-1).
internal enum ListViolation { Empty }

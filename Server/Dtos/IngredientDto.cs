namespace mahl.Server.Dtos;

// ADR-S108-1: Etag = per-Zeile xmin-ETag (XminETag.Format), geteilt zwischen GET (Zeile) und
// POST-201 (neu angelegte Zeile) – If-Match-Quelle für ein nachfolgendes DELETE.
internal sealed record IngredientDto(Guid Id, string Name, string DefaultUnit, string Etag);

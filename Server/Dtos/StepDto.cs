namespace mahl.Server.Dtos;

// ADR-S027-1: nur die Anweisung – die Schrittnummer steht ausschließlich in der DB-Entität.
// Geteilt zwischen Request (CreateRecipeDto) und Response (RecipeDto).
internal sealed record StepDto(string Instruction);

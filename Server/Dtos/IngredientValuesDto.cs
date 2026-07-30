namespace mahl.Server.Dtos;

// ADR-S111-1: Trägt Name + Einheit für einen Ingredient-Schreibzugriff. Wird von ZWEI Endpoints per
// Body gebunden – POST /api/ingredients (Neuanlage) und POST /{id}/restore (Reaktivierung/Undo) –
// beide validieren über denselben ToDomain()-Pfad (ADR-S090-1/S051-2/S051-3). Der Name beschreibt
// den INHALT, nicht eine der beiden Operationen (vormals CreateIngredientDto, umbenannt run-11).
#pragma warning disable CA1812 // instantiated by ASP.NET Core model binding via reflection
internal sealed record IngredientValuesDto(string Name, string DefaultUnit);
#pragma warning restore CA1812

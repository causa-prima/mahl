namespace mahl.Infrastructure;

// Einzige Quelle der Namen der funktionalen Unique-Indizes (ADR-S105-2): Die Migration legt sie an, die
// Endpoints erkennen die Verletzung (Postgres ConstraintName) an genau diesem Namen.
public static class UniqueIndexNames
{
    public const string IngredientName = "IX_Ingredients_Name_Lower";
    public const string RecipeTitle = "IX_Recipes_Title_Lower";
}

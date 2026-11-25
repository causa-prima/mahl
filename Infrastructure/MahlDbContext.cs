using mahl.Infrastructure.DatabaseTypes;
using Microsoft.EntityFrameworkCore;

namespace mahl.Infrastructure;

public class MahlDbContext(DbContextOptions<MahlDbContext> options) : DbContext(options)
{
    public DbSet<IngredientDbType> Ingredients => Set<IngredientDbType>();
    public DbSet<RecipeDbType> Recipes => Set<RecipeDbType>();
    public DbSet<RecipeIngredientDbType> RecipeIngredients => Set<RecipeIngredientDbType>();
    public DbSet<StepDbType> Steps => Set<StepDbType>();
    public DbSet<PlannedRecipeDbType> PlannedRecipes => Set<PlannedRecipeDbType>();
    public DbSet<ShoppingListItemDbType> ShoppingListItems => Set<ShoppingListItemDbType>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        ArgumentNullException.ThrowIfNull(modelBuilder);

        // ADR-S058-3/ADR-S106-1: Single-Resource-ETag-Quelle = xmin (Postgres-Systemspalte, keine
        // eigene Migrations-Spalte nötig) – EF Core wirft DbUpdateConcurrencyException bei stale
        // If-Match automatisch. Kein UseXminAsConcurrencyToken()-Helper in
        // Npgsql.EntityFrameworkCore.PostgreSQL 10.0.1 vorhanden -> Shadow-Property manuell
        // konfiguriert (ADR-S106-1, offizielles Npgsql-Fallback-Muster).
        modelBuilder.Entity<IngredientDbType>().ConfigureXmin();

        ConfigureRecipe(modelBuilder);

        // ADR-S153-1: Rezept-ID als Primär- und Fremdschlüssel – höchstens eine Vormerkung je Rezept.
        var planned = modelBuilder.Entity<PlannedRecipeDbType>();
        planned.HasKey(p => p.RecipeId);
        planned.HasOne<RecipeDbType>().WithMany().HasForeignKey(p => p.RecipeId);

        // ADR-S154-3: Zutat-Id als Primär- und Fremdschlüssel – ein Eintrag je Zutat, auch bei gleichzeitigem Übernehmen.
        // ADR-S154-2: numeric(8,3) setzt die Plausibilitätsgrenze 99999,999 durch.
        var item = modelBuilder.Entity<ShoppingListItemDbType>();
        item.HasKey(i => i.IngredientId);
        item.HasOne<IngredientDbType>().WithMany().HasForeignKey(i => i.IngredientId);
        item.Property(i => i.Quantity).HasPrecision(8, 3);
    }

    // Rezept-Aggregat: Kind-Tabellen ohne Navigation-Properties, nur FK-Skalare – EF sortiert die
    // Inserts trotzdem über die FKs, und Full-State-Vergleiche in Tests bleiben zyklenfrei.
    // Löschverhalten bleibt beim EF-Default (Cascade für Pflicht-FKs): Zutaten werden nur soft-gelöscht
    // (ADR-S000-6), ein Hard-Delete gibt es nicht. DeleteBehavior steht bewusst nicht im eigenen Code – die
    // Reason der IndirectCompileReference in der csproj sagt, dass nur generierter Code das Paket nutzt.
    private static void ConfigureRecipe(ModelBuilder modelBuilder)
    {
        // ADR-S106-1: Muster wie bei IngredientDbType – xmin ist der ETag des Rezepts.
        modelBuilder.Entity<RecipeDbType>().ConfigureXmin();

        var recipeIngredient = modelBuilder.Entity<RecipeIngredientDbType>();
        recipeIngredient.HasKey(ri => new { ri.RecipeId, ri.Position });
        recipeIngredient.HasOne<RecipeDbType>().WithMany().HasForeignKey(ri => ri.RecipeId);
        recipeIngredient.HasOne<IngredientDbType>().WithMany().HasForeignKey(ri => ri.IngredientId);
        // ADR-S020-1: decimal(7,3), NULL = Unspecified.
        recipeIngredient.Property(ri => ri.Quantity).HasPrecision(7, 3);

        var step = modelBuilder.Entity<StepDbType>();
        step.HasKey(s => new { s.RecipeId, s.StepNumber });
        step.HasOne<RecipeDbType>().WithMany().HasForeignKey(s => s.RecipeId);
    }
}

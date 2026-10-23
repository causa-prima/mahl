using mahl.Infrastructure.DatabaseTypes;
using Microsoft.EntityFrameworkCore;

namespace mahl.Infrastructure;

public class MahlDbContext(DbContextOptions<MahlDbContext> options) : DbContext(options)
{
    public DbSet<IngredientDbType> Ingredients => Set<IngredientDbType>();
    public DbSet<RecipeDbType> Recipes => Set<RecipeDbType>();
    public DbSet<RecipeIngredientDbType> RecipeIngredients => Set<RecipeIngredientDbType>();
    public DbSet<StepDbType> Steps => Set<StepDbType>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        ArgumentNullException.ThrowIfNull(modelBuilder);

        // ADR-S058-3/ADR-S106-1: Single-Resource-ETag-Quelle = xmin (Postgres-Systemspalte, keine
        // eigene Migrations-Spalte nötig) – EF Core wirft DbUpdateConcurrencyException bei stale
        // If-Match automatisch. Kein UseXminAsConcurrencyToken()-Helper in
        // Npgsql.EntityFrameworkCore.PostgreSQL 10.0.1 vorhanden -> Shadow-Property manuell
        // konfiguriert (ADR-S106-1, offizielles Npgsql-Fallback-Muster).
        modelBuilder.Entity<IngredientDbType>()
            .Property<uint>("xmin")
            .HasColumnType("xid")
            .ValueGeneratedOnAddOrUpdate()
            .IsConcurrencyToken();

        ConfigureRecipe(modelBuilder);
    }

    // Rezept-Aggregat: Kind-Tabellen ohne Navigation-Properties, nur FK-Skalare – EF sortiert die
    // Inserts trotzdem über die FKs, und Full-State-Vergleiche in Tests bleiben zyklenfrei.
    // Löschverhalten bleibt beim EF-Default (Cascade für Pflicht-FKs): Zutaten werden nur soft-gelöscht
    // (ADR-S000-6), ein Hard-Delete gibt es nicht. DeleteBehavior steht bewusst nicht im eigenen Code – die
    // Reason der IndirectCompileReference in der csproj sagt, dass nur generierter Code das Paket nutzt.
    private static void ConfigureRecipe(ModelBuilder modelBuilder)
    {
        // ADR-S106-1: Muster wie bei IngredientDbType – xmin ist der ETag des Rezepts.
        modelBuilder.Entity<RecipeDbType>()
            .Property<uint>("xmin")
            .HasColumnType("xid")
            .ValueGeneratedOnAddOrUpdate()
            .IsConcurrencyToken();

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

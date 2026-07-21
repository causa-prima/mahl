using mahl.Infrastructure.DatabaseTypes;
using Microsoft.EntityFrameworkCore;

namespace mahl.Infrastructure;

public class MahlDbContext(DbContextOptions<MahlDbContext> options) : DbContext(options)
{
    public DbSet<IngredientDbType> Ingredients => Set<IngredientDbType>();

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
    }
}

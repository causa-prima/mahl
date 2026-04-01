namespace mahl.Server.Data;

using mahl.Server.Data.DatabaseTypes;
using Microsoft.EntityFrameworkCore;

public class MahlDbContext : DbContext
{
    public DbSet<IngredientDbType> Ingredients { get; set; }
    public DbSet<RecipeDbType> Recipes { get; set; }
    public DbSet<RecipeIngredientDbType> RecipeIngredients { get; set; }
    public DbSet<StepDbType> Steps { get; set; }
    public DbSet<WeeklyPoolEntryDbType> WeeklyPoolEntries { get; set; }
    public DbSet<ShoppingListItemDbType> ShoppingListItems { get; set; }

    public MahlDbContext(DbContextOptions<MahlDbContext> options) : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<IngredientDbType>(entity =>
        {
            // Partial unique index: only non-deleted ingredients must have unique names
            entity.HasIndex(e => e.Name).IsUnique().HasFilter("\"DeletedAt\" IS NULL");
        });

        modelBuilder.Entity<RecipeIngredientDbType>(entity =>
        {
            entity.HasIndex(e => new { e.RecipeId, e.IngredientId }).IsUnique();
            entity.HasOne(e => e.Recipe)
                  .WithMany(r => r.Ingredients)
                  .HasForeignKey(e => e.RecipeId)
                  .OnDelete(DeleteBehavior.Cascade);
            entity.HasOne(e => e.Ingredient)
                  .WithMany()
                  .HasForeignKey(e => e.IngredientId)
                  .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<StepDbType>(entity =>
        {
            entity.HasIndex(e => new { e.RecipeId, e.StepNumber }).IsUnique();
            entity.HasOne(e => e.Recipe)
                  .WithMany(r => r.Steps)
                  .HasForeignKey(e => e.RecipeId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<WeeklyPoolEntryDbType>(entity =>
        {
            entity.HasIndex(e => e.RecipeId).IsUnique();
            entity.HasOne(e => e.Recipe)
                  .WithMany()
                  .HasForeignKey(e => e.RecipeId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<ShoppingListItemDbType>(entity =>
        {
            entity.HasOne(e => e.Ingredient)
                  .WithMany()
                  .HasForeignKey(e => e.IngredientId)
                  .OnDelete(DeleteBehavior.Restrict);
        });
    }
}

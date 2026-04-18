using mahl.Infrastructure.DatabaseTypes;
using Microsoft.EntityFrameworkCore;

namespace mahl.Infrastructure;

public class MahlDbContext(DbContextOptions<MahlDbContext> options) : DbContext(options)
{
    public DbSet<IngredientDbType> Ingredients => Set<IngredientDbType>();
}

namespace mahl.Server.Data;

using mahl.Server.Data.DatabaseTypes;
using Microsoft.EntityFrameworkCore;

public class MariaDbContext : DbContext
{
    public DbSet<ShoppingListItemDBType> ShoppingListItems { get; set; }

    public MariaDbContext(DbContextOptions<MariaDbContext> options) : base(options) { }
}

using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace mahl.Infrastructure;

// ADR-S106-1: xmin ist eine Shadow-Property (Postgres-Systemspalte). Name und Cast stehen nur hier, damit
// ein Tippfehler im Literal oder ein falscher Cast nicht an mehreren Stellen verstreut lebt.
// Public in Infrastructure (nicht Server-internal) wie DatabaseResetExtensions; XminETag (HTTP-Format)
// bleibt davon frei.
public static class XminExtensions
{
    // Einzige Quelle für den Spaltennamen: Modellkonfiguration, Lesen in Queries und diese Helfer.
    public const string ColumnName = "xmin";

    // ADR-S106-1: Modellkonfiguration – Shadow-Property auf die Systemspalte, EF prüft sie als Concurrency-Token.
    public static void ConfigureXmin<TEntity>(this EntityTypeBuilder<TEntity> entity)
        where TEntity : class
    {
        ArgumentNullException.ThrowIfNull(entity);
        entity.Property<uint>(ColumnName)
            .HasColumnType("xid")
            .ValueGeneratedOnAddOrUpdate()
            .IsConcurrencyToken();
    }

    // Lesen des aktuellen Werts einer getrackten Zeile (nach SaveChanges oder Load).
    public static uint ReadXmin(this MahlDbContext db, object row)
    {
        ArgumentNullException.ThrowIfNull(db);
        return (uint) db.Entry(row).Property(ColumnName).CurrentValue!;
    }

    // ADR-S058-3: Concurrency-Token setzen – EF Core prüft ihn beim SaveChanges gegen den DB-Wert.
    public static void SetOriginalXmin(this MahlDbContext db, object row, uint xmin)
    {
        ArgumentNullException.ThrowIfNull(db);
        db.Entry(row).Property(ColumnName).OriginalValue = xmin;
    }
}

using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace mahl.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Ingredients",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    BaseUnit = table.Column<string>(type: "text", nullable: false),
                    DeletedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Ingredients", x => x.Id);
                });

            // ADR-S105-2: Eindeutigkeit case-insensitiv (ADR-S051-3) als DB-Constraint statt App-Layer-
            // Check-then-Insert (TOCTOU-Race). Funktionaler Index auf LOWER(name) – nicht per EF-Model-
            // Config ausdrückbar, daher Raw-SQL. Vom Mutation-Testing ausgenommen (generierte Migration).
            migrationBuilder.Sql(
                "CREATE UNIQUE INDEX \"IX_Ingredients_Name_Lower\" ON \"Ingredients\" (LOWER(\"Name\"));");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("DROP INDEX IF EXISTS \"IX_Ingredients_Name_Lower\";");

            migrationBuilder.DropTable(
                name: "Ingredients");
        }
    }
}

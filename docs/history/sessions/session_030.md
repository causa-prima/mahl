# Session 030 – 2026-03-17

## Thema
.NET 10 Upgrade + UUID v7 Migration

## Implementiertes

### .NET 10 Upgrade
- `TargetFramework` in allen 5 `.csproj`-Dateien: `net8.0` → `net10.0`
- Microsoft-Pakete: `10.0.x` (AspNetCore, EF Core, Mvc.Testing, Extensions.Logging.Abstractions)
- Npgsql EF Core: `8.0.4` → `10.0.1`
- Serilog.AspNetCore: `8.0.3` → `9.0.0`
- Swashbuckle entfernt (inkompatibel mit .NET 10) → natives `AddOpenApi()` / `MapOpenApi()`
- EF Core Tools: `8.0.10` → `10.0.5` (`dotnet tool update --global dotnet-ef`)
- `TestWebApplicationFactory` für EF Core 10 gefixt (s.u.)

### UUID v7 Migration
- Alle 6 DbTypes: `int Id { get; set; }` → `Guid Id { get; set; } = Guid.CreateVersion7()`
- Alle FK-Felder: `int XxxId` → `Guid XxxId`
- DTOs: `IngredientDto`, `SoftDeletedConflictDto`, `RecipeIngredientDto`, `StepDto`, `RecipeDto`, `RecipeSummaryDto`, `CreateRecipeIngredientDto`, `WeeklyPoolEntryDto`, `AddToPoolDto`, `ShoppingListItemDto` – alle int-IDs auf Guid
- Domain: `RecipeIngredient._ingredientId: int → Guid`, `Recipe.Create`-Tupel-Parameter `int → Guid`
- Endpoints: `{id:int} → {id:guid}`, `{recipeId:int} → {recipeId:guid}`, Handler-Parameter `int → Guid`
- Tests: hardcodierte int-IDs durch `Guid.NewGuid()` ersetzt; `Delete_NonExistingId_Returns404` Ingredients von 3 TestCases zu 1 Test konsolidiert
- DB-Migration: drop + remove + `InitialCreate` neu erstellt mit `uuid`-Spaltentypen, angewendet

## Ergebnis
- 96 Tests ✅ (98 → 96 durch Konsolidierung der 3 `TestCase`-Parameter)
- Build grün

## Probleme und Lösungen

### Swashbuckle inkompatibel mit .NET 10
`Method 'GetSwagger' does not have an implementation` beim Serverstart. Fix: Swashbuckle entfernt, natives `AddOpenApi()` / `MapOpenApi()` verwendet.

### EF Core 10 TestWebApplicationFactory – mehrere Iterationen
EF Core 10 registriert Datenbankprovider-Konfiguration in **zwei** separaten Descriptors:
1. `DbContextOptions<TContext>` – wie bisher
2. `IDbContextOptionsConfiguration<TContext>` – NEU in EF Core 9/10

Der bisherige Code entfernte nur `DbContextOptions<T>`. Dadurch blieb die Npgsql-Konfiguration erhalten, und EF Core sah beim Initialisieren beide Provider gleichzeitig → `InvalidOperationException: Services for database providers 'Npgsql', 'InMemory' have been registered`.

**Fehlgeschlagene Zwischenlösung:** `EnableServiceProviderCaching(false)` – löst den Konflikt, bricht aber das InMemory-Sharing: jeder `DbContext` erhält eine eigene interne InMemory-Instanz → `SeedRecipes` schreibt in DB A, `GetAllRecipesFromDb` liest aus leerem DB B → `Index was out of range`.

**Richtige Lösung:** Beide Descriptors entfernen + `EnableServiceProviderCaching(false)` NICHT verwenden:
```csharp
var descriptorsToRemove = services
    .Where(d => d.ServiceType == typeof(DbContextOptions<MahlDbContext>)
             || d.ServiceType == typeof(IDbContextOptionsConfiguration<MahlDbContext>))
    .ToList();
foreach (var descriptor in descriptorsToRemove)
    services.Remove(descriptor);
```

## Offene Punkte
- Domain-Typen (`Ingredient`, `Recipe`) tragen noch keine eigene `Guid Id` → `_ingredientId` in `RecipeIngredient` und `ToDto(Recipe, RecipeDbType)` bleiben Workarounds
- Stryker-Gesamtlauf nach Migration noch ausstehend (letzter Stand veraltet)
- WeeklyPoolEndpoints (7 Survivors) + ShoppingListEndpoints L34 – nach Gesamtlauf analysieren
- Kein Commit in dieser Session

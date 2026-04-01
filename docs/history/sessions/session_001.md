# Session 1 – 2026-02-19 (SKELETON komplett)

## Was wurde erledigt

**Infrastruktur:**
- .NET 7 → 8 upgrade
- MariaDB → PostgreSQL (Npgsql EF Core Provider)
- Blazor WebAssembly (`Client/`) komplett gelöscht und durch React/Vite ersetzt

**Backend:**
- 4 Endpoint-Gruppen in `Server/Endpoints/`: IngredientsEndpoints, RecipesEndpoints, WeeklyPoolEndpoints, ShoppingListEndpoints
- EF Core Schema (6 Entities): Ingredient, Recipe, RecipeIngredient, Step, WeeklyPoolEntry, ShoppingListItem
- InitialCreate Migration in `Server/Migrations/`
- Seed-Data: `Server/Data/SeedDataExtensions.cs` – `app.SeedDatabase()` Extension (10 Rezepte + 45 Zutaten)
- 93 Integrationstests in `mahl.Server.Tests/` – alle grün

**Frontend:**
- React 18 + MUI v7 + TypeScript + Vite in `Client/`
- Seiten: Zutaten, Rezepte (inkl. Detail-Expand), Wochen-Pool, Einkaufsliste
- Build-Output → `Server/wwwroot/` (Production)
- Vite-Proxy → `http://localhost:5059` (Development)
- 10 API-Unit-Tests (Vitest + React Testing Library)

**Mutation Testing:**
- Stryker.NET: **91.21%** Endpoint-Coverage (Ziel: 90%+)
- Überlebende Mutanten (äquivalent): Route-Tag-Strings, "/" → "" in MapGet/MapPost, TraceId null-coalescing
- Per-File: Ingredients 88%, Recipes 94.5%, ShoppingList 91.2%, WeeklyPool 88%

## Probleme & Lösungen

- **dotnet in WSL:** `which dotnet` gibt nichts zurück. Lösung: `cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet <command>"`
- **MUI v7 statt v6:** npm installierte neueste Version. Grid-API leicht anders, kein Problem → v7 beibehalten.

## Offene Punkte (übergeben an nächste Session)

- Vite-Proxy-Port in `Client/vite.config.ts` ggf. anpassen (aktuell: 5059)
- Docker Compose für PostgreSQL verifizieren
- PWA-Grundkonfiguration (Workbox) – MVP
- MVP-Phase starten

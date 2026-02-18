# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Complete Project Documentation

**IMPORTANT:** For complete implementation specifications, architecture decisions, and user stories, see:

- **[docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** - Complete technical specification for implementing the full app
  - **READ SECTION 1.1 & 1.2 FIRST:** Projektkontext (Pivot from Blazor/MariaDB) & Decision-Making Guide
- **[docs/USER_STORIES.md](docs/USER_STORIES.md)** - All user stories with priorities (SKELETON → MVP → V1 → V2)
- **[docs/GLOSSARY.md](docs/GLOSSARY.md)** - Ubiquitous language / domain model (binding for all code)
- **[docs/AGENT_MEMORY.md](docs/AGENT_MEMORY.md)** - All technical decisions and implementation status

This CLAUDE.md file contains quick reference information for day-to-day development work.

**Project Context:** This project pivoted from a Blazor/MariaDB playground to a production-ready React/PostgreSQL application. Existing code in `Server/` and `Shared/` serves as reference implementation for patterns, but is not set in stone. See IMPLEMENTATION_GUIDE.md Section 1.1 for details.

---

## Project Overview

"Mahl" is a meal planning and shopping list application. The vision encompasses recipe management, weekly planning with intelligent suggestions, context-aware shopping lists with offline-sync, and a guided cooking mode.

**Current Status:** Early development (SKELETON phase). The project has pivoted from a Blazor/MariaDB "playground" to a production-ready React/PostgreSQL application. Existing shopping list code serves as a reference implementation for patterns.

## Architecture

**Tech Stack:**

**Backend:**
- .NET 8.0
- ASP.NET Core Minimal APIs (endpoint pattern instead of controllers)
- Entity Framework Core 8.0 with Npgsql (PostgreSQL provider)
- Serilog for structured logging
- Swagger/OpenAPI for API documentation

**Frontend:**
- React 18+ with TypeScript
- Material UI v6 (Material Design 3)
- Vite as build tool
- React Router v6 for routing
- Workbox for Service Worker (PWA support)
- React Query for data fetching and caching

**Deployment:**
- Docker & Docker Compose (PostgreSQL 15+)
- Self-hosted

**Project Structure:**
- `Server/` - ASP.NET Core Web API (serves React static files in production)
  - `Endpoints/` - Minimal API endpoints (e.g., ShoppingList, Ingredient, Recipe)
  - `Data/` - EF Core DbContext and database types
  - `Data/Migrations/` - EF Core migrations (PostgreSQL)
  - `Data/SeedData.sql` - Seed data (45 ingredients + 9 recipes)
  - `wwwroot/uploads/` - Uploaded recipe images and files
- `Client/` - React application (TypeScript + Vite)
  - `src/components/` - React components
  - `src/pages/` - Page components (routes)
  - `src/services/` - API client & data fetching
- `Shared/` - Domain models, DTOs, and types (C# - shared between backend and potential C# clients)
  - `Types/` - Custom value types (see Domain Modeling Philosophy below)
  - `Dtos/` - Data transfer objects
- `mahl.Server.Tests/` - Backend integration tests (NUnit)
- `mahl.Shared.Test/` - Shared library unit tests
- `mahl.Tests.Shared/` - Test utilities
- `docker-compose.yml` - PostgreSQL 15+ container setup

## Domain Modeling Philosophy

This codebase follows a **"Make Illegal States Unrepresentable"** approach using strong typing and immutability:

**Custom Value Types:**
- `TrimmedString` - A `readonly record struct` that guarantees strings are trimmed of whitespace
- `NonEmptyTrimmedString` - Like TrimmedString but also guarantees non-empty. Can only be created via `Create()` factory method which returns `OneOf<Success<NonEmptyTrimmedString>, Error<string>>`
- `SyncItemId` - Represents an ID that is either `Unknown` (not persisted) or `Known(int value)` using OneOf. No direct value access - use `Match()` or `Switch()`

**OneOf Library:**
- Used extensively for discriminated unions/sum types
- Example: `OneOf<DateTimeOffset, Unknown>` for BoughtAt - either has a value or is unknown
- Domain models return `OneOf<Success, Error<string>>` from factory methods instead of throwing exceptions

**Validation & Construction:**
- Domain types like `ShoppingListItem` use private constructors
- Creation only via static factory methods that validate first
- All properties use custom value types to guarantee validity
- Once constructed, an instance is guaranteed to be in a valid state

**Immutability:**
- `record` types with `init` setters throughout
- No nullable reference types used where business rules forbid null

See `Vortrag.md` for detailed explanation of this design approach.

## Build, Run & Test Commands

**Start database (Docker):**
```bash
docker-compose up -d
```

**Build backend:**
```bash
dotnet build
```

**Run backend:**
```bash
dotnet run --project Server
# Or from Server directory:
cd Server && dotnet run
```
Backend API runs at https://localhost:7xxx and http://localhost:5xxx (check console output for exact ports).

**Run frontend (development):**
```bash
cd Client
npm install  # First time only
npm run dev
```
Frontend runs at http://localhost:5173 (Vite dev server).

**Run tests:**
```bash
# All tests
dotnet test

# Specific test project
dotnet test mahl.Server.Tests
dotnet test mahl.Shared.Test

# Run single test
dotnet test --filter "FullyQualifiedName~TestMethodName"
```

**Database setup & migrations:**

**IMPORTANT:** During development (before production release), we use a **Database Drop + Recreate** strategy instead of EF Core migrations:

```bash
cd Server

# Drop database and remove old migrations
dotnet ef database drop --force
dotnet ef migrations remove

# Create fresh migration with current schema
dotnet ef migrations add InitialCreate

# Apply migration
dotnet ef database update

# Load seed data (TODO: implement app.SeedDatabase() in Program.cs)
# dotnet run --seed-data
```

**Once in production (V1/V2):** Use normal EF Core migrations workflow:
```bash
# Add new migration
dotnet ef migrations add MigrationName --project Server

# Apply migrations
dotnet ef database update --project Server
```

**Connection string:**
Default connection is in `Server/appsettings.json`:
```
"DefaultConnection": "Host=localhost;Port=5432;Database=mahl;Username=mahl_user;Password=mahl_dev_password"
```
(Matches docker-compose.yml PostgreSQL container)

## Development Guidelines

**Code Style:**
- `Directory.Build.props` enforces:
  - Latest C# language version
  - Nullable reference types enabled globally
  - Nullable warnings treated as errors
- Follow existing patterns with custom value types and OneOf for domain models

**Endpoint Registration:**
- Endpoints are registered in `Server/Program.cs` via extension methods (e.g., `app.MapShoppingListEndpoints()`)
- Add new endpoint groups in `Server/Endpoints/` following existing patterns
- Each endpoint file contains a static class with a `MapXEndpoints(WebApplication app)` extension method

**Testing:**
- Use NUnit for test framework
- Use FluentAssertions for assertions
- Server tests use `Microsoft.AspNetCore.Mvc.Testing` for integration tests
- Use EF Core InMemory provider for database tests (or Testcontainers with PostgreSQL for more realistic tests)
- Test logging with `Serilog.Sinks.InMemory.Assertions`
- Mutation Testing: Stryker.NET for backend, Stryker-JS for frontend (90%+ coverage goal)

**Logging:**
- Server uses Serilog (configured in `Program.cs`)
- Logs to Console and File (daily rolling) in non-development environments
- Format: `[HH:mm:ss LEVEL] [TraceId: {TraceId}] Message`
- Request logging is enabled via `UseSerilogRequestLogging()` in non-development

**API Documentation:**
- Swagger UI available at `/swagger` in development mode
- OpenAPI spec automatically generated

## Important Patterns

**Factory Methods Pattern:**
When creating domain entities, use static factory methods that return `OneOf<Entity, Error<string>>`:
```csharp
var result = ShoppingListItem.New(title, description);
result.Match(
    item => /* handle success */,
    error => /* handle error */
);
```

**SyncItemId Usage:**
When working with IDs that may be unknown (not yet persisted):
```csharp
id.Match(
    known => /* work with int value */,
    unknown => /* handle unknown ID */
);
```

**EF Core Database Types:**
Server-side database entities in `Server/Data/DatabaseTypes/` map to domain models in `Shared/`. Keep these separate - database types are EF-specific (PostgreSQL), domain models are pure business logic.

**Important Notes:**
- Avoid PostgreSQL-specific features (JSONB, Arrays) in V1 to keep database provider flexibility
- All queries should use EF Core LINQ, not raw SQL (unless performance-critical)
- No stored procedures in SKELETON/MVP phases

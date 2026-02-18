# Mahl - Meal Planning & Shopping List App

Intelligente Essensplanung mit automatischen Vorschlägen, kontextbewusster Einkaufsliste und geführtem Kochmodus.

---

## 🚀 Quickstart (Entwicklung)

### Voraussetzungen

- **Docker** & **Docker Compose** (für PostgreSQL)
- **.NET 8 SDK** (für Backend)
- **Node.js 18+** & **npm** (für React Frontend)

### 1. Datenbank starten

```bash
# PostgreSQL Container starten
docker-compose up -d

# Prüfen ob läuft
docker ps
```

### 2. Backend vorbereiten

```bash
cd Server

# Packages installieren
dotnet restore

# Datenbank initialisieren (EF Core)
dotnet ef database update

# Seed-Daten laden (optional)
# TODO: Implementierung in Program.cs via app.SeedDatabase()

# Backend starten
dotnet run
```

Backend läuft unter: **https://localhost:7xxx** (Port siehe Console)

### 3. Frontend vorbereiten

```bash
cd Client  # (React-Projekt, Blazor wurde entfernt)

# Packages installieren
npm install

# Frontend starten
npm run dev
```

Frontend läuft unter: **http://localhost:5173**

---

## 📚 Dokumentation

- **[docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** - Vollständige technische Spezifikation
- **[docs/GLOSSARY.md](docs/GLOSSARY.md)** - Domain-Modell & Fachbegriffe
- **[docs/USER_STORIES.md](docs/USER_STORIES.md)** - Alle Features mit Prioritäten
- **[CLAUDE.md](CLAUDE.md)** - Code-Patterns & Entwicklungsrichtlinien

---

## 🧪 Tests ausführen

```bash
# Alle Tests
dotnet test

# Mutation Testing (nach Feature-Entwicklung)
dotnet stryker --files Server/Services/NeueService.cs

# Mutation Testing (vollständig, am Ende der Phase)
dotnet stryker
```

---

## 🗄️ Datenbank verwalten

### Migration erstellen (ab Production-Release)

```bash
cd Server
dotnet ef migrations add MigrationName
dotnet ef database update
```

### Datenbank zurücksetzen (während Entwicklung)

```bash
cd Server
dotnet ef database drop --force
dotnet ef migrations remove
dotnet ef migrations add InitialCreate
dotnet ef database update
# dotnet run --seed-data  # Seed-Daten laden
```

### Datenbank-Zugriff (pgAdmin oder psql)

```bash
# Via psql
docker exec -it mahl-postgres psql -U mahl_user -d mahl

# Oder pgAdmin (Optional, siehe docker-compose.yml)
# http://localhost:5050
```

---

## 📂 Projekt-Struktur

```
mahl/
├── Server/                 # ASP.NET Core Backend
│   ├── Data/               # EF Core DbContext, Migrations, Seeds
│   ├── Endpoints/          # Minimal API Endpoints
│   └── wwwroot/uploads/    # Rezept-Bilder & Dateien
├── Client/                 # React Frontend (TypeScript + Vite)
│   ├── src/
│   │   ├── components/     # React Components
│   │   ├── pages/          # Seiten (Routes)
│   │   └── services/       # API Client
├── Shared/                 # Domain Models & DTOs (C#)
│   ├── Types/              # Custom Value Types (NonEmptyTrimmedString, etc.)
│   └── Dtos/               # Data Transfer Objects
├── docs/                   # Vollständige Dokumentation
├── docker-compose.yml      # PostgreSQL Container
└── README.md               # Dieser File
```

---

## 🛠️ Tech Stack

**Backend:**
- .NET 8.0 + ASP.NET Core Minimal APIs
- PostgreSQL 15+ (via EF Core + Npgsql)
- Serilog (Logging)
- NUnit + FluentAssertions (Tests)
- Stryker.NET (Mutation Testing)

**Frontend:**
- React 18+ + TypeScript
- Material UI v6 (Material Design 3)
- Vite (Build Tool)
- React Router v6
- Workbox (Service Worker für PWA)

**Deployment:**
- Docker & Docker Compose
- Self-hosted

---

## 📖 Entwicklungs-Workflow

1. **TDD:** Tests ZUERST schreiben (Red-Green-Refactor)
2. **Mutation Testing:** Nach jedem Feature mit `--files`, am Phasenende vollständig
3. **Domain-Patterns:** Custom Value Types, Factory Methods, `OneOf<T, U>` für Discriminated Unions
4. **Commits:** `[US-XXX] Kurzbeschreibung` (z.B. `[US-904] Zutaten CRUD implementiert`)
5. **Keine Migrations:** Bis Production-Release → `dotnet ef database drop --force` + recreate

---

## 🎯 Implementierungs-Phasen

- **[SKELETON]** - Walking Skeleton (aktuell in Arbeit)
  - US-904: Zutaten-Verwaltung
  - US-602: Manuelle Rezepterfassung
  - US-803: Rezept dem Wochen-Pool hinzufügen
  - US-201/303: Einkaufsliste anzeigen & abhaken

- **[MVP]** - Minimum Viable Product (geplant)
- **[V1]** - Version 1.0 (geplant)
- **[V2]** - Version 2.0 (geplant)

Siehe **[docs/USER_STORIES.md](docs/USER_STORIES.md)** für Details.

---

## 🤝 Beitragen

Dieses Projekt wird aktuell von einem LLM implementiert (siehe `docs/AGENT_MEMORY.md` für Status).

Bei Fragen oder Feedback: GitHub Issues erstellen.

---

## 📝 Lizenz

[Lizenz hier einfügen]

---

**Letzte Aktualisierung:** 2026-02-18

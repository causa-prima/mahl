# Technische Entscheidungen – Archiv

> Historisch überholte, redundante oder triviale Einträge aus `decisions.md`.
> Diese Entscheidungen wurden umgesetzt, revidiert oder sind aus dem Code/den Specs ableitbar.
> Nur zum Nachschlagen bei historischen Fragen.

---

## Projektstruktur & Architektur (historisch)

### Backend-Code verwerfen, Neustart mit ATDD (2026-03-26)

**Kontext:** Der Backend-Code wurde im "luftleeren Raum" entwickelt (ohne UI-Consumer, ohne Outside-In-Disziplin). Zu viele zentrale Architekturentscheidungen änderten sich (Hexagonal, Infrastructure Layer, BDD, ATDD).

**Entscheidung:** Backend-Code wurde verworfen. Bewahrt wurden: Specs, `decisions.md`, `lessons_learned.md`, alle Guidelines und Skills. Neustart mit BDD/Gherkin als äußerem Loop.

---

### TDD-Neustart: Alten SKELETON-Code löschen (2026-02-24)

Alle SKELETON-Endpoints und -Tests wurden gelöscht und via striktem TDD neu implementiert. Bestehender Code wurde nicht mit TDD oder aktuellen Guidelines erstellt – keine Garantie auf Korrektheit oder Sauberkeit.

---

### Adopt/Skip/Defer: Best-Practices-Entscheidungen Session 41 (2026-03-26)

| Praxis | Entscheidung | Notizen |
|--------|-------------|---------|
| Health Checks | **Adopt** | Trivial, relevant für Docker-Startsequenz |
| OpenAPI → TS Type Generation | **Adopt** | Statt Pact; single-developer tauglich |
| Metrics/Telemetry | **Adopt** | Vor Produktion; .NET Diagnostics.Metrics |
| Domain Events | **Adopt V1** | Ggf. MVP; Basis für History-Features |
| Aggregate Roots | **Adopt inkrementell** | Wo Invarianten Kinder überspannen (z.B. Recipe) |
| Bounded Contexts | **Adopt V1** | Zusammen mit Domain Events; heute Monolith |
| Property-Based Testing | **Consider nach SKELETON** | Auf Endpoint-Ebene, nicht Value-Object-Ebene |
| Snapshot Testing | **Skip** | BeEquivalentTo + Mutation Testing reichen aus |
| API Versioning | **Skip** | Single-developer, single-client, kein externer Consumer |
| Contract Testing (Pact) | **Skip** | Ersetzt durch OpenAPI → TS Type Generation |
| Specification Pattern | **Review-Hinweis** | Anwenden wo Query-Duplikation es rechtfertigt |

---

### Workflow-Enforcement: Skills + Hooks statt reiner Guidelines (2026-02-26)

Entscheidung TDD-Guidelines durch aktive Mechanismen (Skills, Hooks) zu erzwingen statt nur via passive Dokumentation. Umgesetzt – Details in `.claude/skills/` und `.claude/hooks/`.

### Hook-Implementierung: Python statt Bash+jq (2026-02-26)

`check-one-test.sh` crashte bei fehlendem `jq` ohne exit 1. Auf Python umgestellt (`check-one-test.py`). Umgesetzt – aktueller Stand in `.claude/hooks/`.

---

## SKELETON-Scope (2026-02-17, redundant mit SKELETON_SPEC.md)

### SKELETON-Scope: 4 User Stories
US-904, US-602, US-803, US-201/303. MVP: US-501, US-505, US-506, US-605, US-614, US-801 verschoben.

### Authentifizierung SKELETON: keine Auth
Fokus auf Datenfluss; echtes Auth kommt in MVP.

### Einheiten-Konvertierung SKELETON: keine Umrechnung
US-902 (Einheiten-Management) ist MVP. Duplikate auf Einkaufsliste akzeptiert.

### AlwaysInStock-Flag: Feld angelegt, UI erst MVP
Vorbereitung für US-906, spart Migration-Aufwand.

### Abhaken-Verhalten: BoughtAt-Timestamp, nicht löschen
US-303 spezifiziert "verschieben in 'Zuletzt gekauft'". Ermöglicht Undo (US-401, V1).

### Einkaufslisten-Generierung: Einfache Variante in SKELETON
Löscht alte Items, schreibt alle Pool-Rezepte neu. Kein Tracking welche Zutat aus welchem Rezept. Limitation akzeptiert.

---

## Datenbank (redundant mit SKELETON_SPEC.md / ARCHITECTURE.md)

### Datenbank: PostgreSQL 15+
Bessere JSON-Unterstützung, Npgsql EF Core Provider ausgereift. Keine PostgreSQL-spezifischen Features in V1.

### Bilder-Speicherung: Filesystem statt DB
`Server/wwwroot/uploads/recipe-sources/{recipeId}/original.webp`. DB bleibt klein, einfaches Serving via wwwroot. Revidiert: Format von JPG → WEBP (aktueller Stand in `decisions.md`).

### Soft-Delete: `DeletedAt` statt `IsDeleted` (bool)
Mehr Information (wann gelöscht?), ermöglicht Audit-Queries. In SKELETON_SPEC.md dokumentiert.

### ShoppingListItemSource: Separate Tabelle statt JSON-Feld
Datenintegrität (Foreign Keys, CASCADE), einfachere Queries, DB-agnostisch.

---

## Domain & Datenmodell (veraltet / ersetzt)

### ~~Quantity nullable in RecipeIngredient~~ (revidiert 2026-03-03)
~~`RecipeIngredient.Quantity`: NULL = "nach Geschmack"~~. Revidiert: Eigener `Quantity`-Sum-Type mit `PositiveDecimal | Unspecified`. Aktueller Stand in `decisions.md`.

### `RecipeIngredient.IngredientId` Property entfernt (2026-03-17)
Nach UUID-v7-Migration war `IngredientId` redundant zu `Ingredient.Id`. Entfernt – `recipeIngredient.Ingredient.Id` ist semantisch identisch.

---

## Frontend (redundant / trivial)

### Svelte als React-Alternative evaluiert und abgelehnt (2026-04-01)
Zwei strukturelle Ausschlussgründe: (1) Kein MUI-Äquivalent für MD3. (2) Svelte 5 Runes sind mutationsbasiert – Konflikt mit Immutability-Guideline. Aktueller Stand: React bleibt, in `decisions.md`.

### Frontend Migration: Blazor → React (2026-02-18)
Blazor-Code gelöscht, React-Projekt neu aufgesetzt. Historisch – aktueller Stack in `decisions.md`.

### Material UI v7 statt v6 (2026-02-19)
npm hat neueste Version installiert, v7 statt geplanter v6. Grid-API leicht anders, aber kein Problem. Trivial – aktueller Stand ist v7.

### Einkaufsliste UI: Kachel-Layout (Bring!-Stil) (2026-02-18)
Große Touch-Buttons (min. 80×80px). Offen = volle Farbe, Gekauft = Grau. V1: Icons pro Zutat; V2+: LLM-generierte Icons.

### Frontend-Navigation: Burger (mobil) vs. Tabs (Desktop) (2026-02-18)
Breakpoint: 768px (MUI Standard). Mobile-First Ansatz.

---

## Tooling & Infrastruktur (redundant / trivial)

### dotnet in WSL: Windows-Pfad erforderlich (2026-02-19)
`which dotnet` gibt nichts zurück in WSL. Wrapper: `cmd.exe /c "cd /d C:\...\mahl && dotnet <command>"`. Aktuell dokumentiert in `docs/DEV_WORKFLOW.md`.

### Entwicklungs-Workflow: Drop + Recreate vor Production (2026-02-18)
Schnellere Iteration. Ab Production: Normale Migrations.

### Seed-Data: C# Extension Method (`app.SeedDatabase()`) (2026-02-18)
Type-safe, versioniert mit Code. Aufruf: `dotnet run --project Server -- --seed-data`. In `Server/Data/SeedDataExtensions.cs`.

### DEPENDENCIES.md ohne Versionsnummern (2026-04-01)
Redundant – aktueller Stand und Begründung in `decisions.md`.

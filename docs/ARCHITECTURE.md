# Architektur & Technische Patterns

<!--
wann-lesen: Beim Implementieren von Backend-/Frontend-Code, bei Architektur-Entscheidungen, beim Erstellen neuer Domain-Typen oder Endpoints
kritische-regeln:
  - Jedes Domänen-Konzept bekommt einen eigenen Typ – keine Primitive Obsession (string, int, Guid)
  - Fehler sind Rückgabewerte (OneOf/Result), keine Exceptions – throw nur für technische Ausnahmen
  - Objekte sind nach Konstruktion unveränderlich (init, ImmutableList, readonly)
  - Create() nimmt nur Primitives oder Domain-Typen – niemals DTOs oder DbTypes
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| 0. Design Philosophy | Die 4 Kernprinzipien (Type-Driven Dev, ROP, Layer-Isolation, Immutability) – auch für Test-Code | Immer zuerst beim Einstieg in die Architektur |
| 0b. Wie Regeln lesen | Guidelines ≠ absolute Gesetze; Abweichungen sofort kommunizieren und dokumentieren | Bei Unsicherheit über Regelauslegung |
| 0c. Hexagonal Architecture | Ports & Adapters, Projekt-Visibility (public/internal), kein InternalsVisibleTo | Beim Anlegen neuer Projekte, beim Verstehen der Test-Strategie |
| 1. Tech Stack | Backend (.NET 10, Minimal APIs, EF Core 10), Frontend (React 19, MUI v7, Vite, React Query), DB (PostgreSQL) | Beim Einrichten der Umgebung oder Wahl neuer Abhängigkeiten |
| 2. Domain Modeling | Make Illegal States Unrepresentable, Validation = Konstruktion, Dependency Rule, bestehende Typen (NonEmptyTrimmedString etc.) | Beim Erstellen neuer Domain-Typen oder Validierungslogik |
| 3. Endpoint-Pattern | Dateistruktur für Minimal API Endpoints, EF Core Include-Pflicht | Beim Anlegen neuer Endpoints |
| 4. Projekt-Struktur | Verzeichnis-Layout: mahl.Infrastructure (public) / mahl.Server (internal) – strikt getrennt | Beim Anlegen neuer Dateien oder Projekte |
| 5. TDD-Prozess | Verweis auf `docs/TDD_PROCESS.md` (Red→Green→Refactor, Full State Assertion, Mutation Testing) | Beim Schreiben von Produktionscode oder Tests – TDD gilt für jeden Code-Zyklus |
| 6. Logging | Serilog-Konfiguration, Format, kein Logging sensitiver Daten | Beim Konfigurieren oder Erweitern von Logging |
| 7–10. API Errors / Auth / Git / Bilder | Querschnittsthemen: Problem Details, Auth-Roadmap, Branch-Strategie, Dateispeicherung | Bei spezifischem Bedarf |

> **Wann lesen:** Beim Implementieren von Backend-/Frontend-Code, beim Schreiben von Tests, bei Architektur-Entscheidungen.

---

## 0. Design Philosophy

Dieser Codebase folgt vier übergreifenden Paradigmen, die für **alle** Code-Ebenen (Backend, Frontend, Tests) gelten. Die Details und Code-Beispiele stehen in den sprachspezifischen Richtlinien:

- **C# (Backend, Tests):** `docs/CODING_GUIDELINE_CSHARP.md`
- **TypeScript/React (Frontend):** `docs/CODING_GUIDELINE_TYPESCRIPT.md`

### Die vier Kernprinzipien

**1. Type-Driven Development / "Make Illegal States Unrepresentable"**
Primitive Typen (`string`, `int`, `number`) tragen keine Domänen-Semantik. Jedes Domänen-Konzept bekommt einen eigenen Typ (Value Object / Branded Type), der seine Invarianten selbst durchsetzt. Ein Wert, der diesen Typ hat, ist garantiert gültig – der Compiler erzwingt das.

**2. Railway-Oriented Programming (ROP)**
Fehler sind Rückgabewerte, keine Exceptions. Validierungsfehler und erwartbare Fehlerzustände werden über typisierte Ergebnis-Typen kommuniziert (`OneOf<T, Error<string>>` in C#, `Result<T, E>` via `neverthrow` in TypeScript). `try/catch` ist nur für echte technische Ausnahmezustände (Datenbank nicht erreichbar, Netzwerk-Ausfall) erlaubt.

**3. Layer-Isolation**
Jeder Layer schützt sich aktiv gegen fehlerhafte Daten aus benachbarten Layern. Die Domäne vertraut weder Request-Daten noch DB-Daten – `Create()` ist in beiden Pfaden (Write und Read) die einzige Einstiegsmethode. DB-Inkonsistenzen (z. B. durch manuelle Eingriffe oder Migrations-Fehler) werden im Read-Pfad als `Results.Problem()` (strukturiertes `application/problem+json`) zurückgegeben, nicht als unbehandeltes `throw`.

**4. Immutability**
Objekte und Collections werden nach der Konstruktion nicht verändert. Zustandsänderungen erzeugen neue Objekte. Das gilt für C# (`record`, `init`, `IImmutableList`) wie für TypeScript (`readonly`, `const`, kein direktes Mutieren von Arrays/Objekten).

### Gilt das auch für Test-Code?

Ja, mit pragmatischen Abschwächungen. Tests müssen **lesbar** und **wartbar** sein:
- Branded Types / Value Objects: ✅ auch in Tests verwenden
- ROP-Verkettung: ⚠️ `.unwrap()` / `._unsafeUnwrap()` in Tests erlaubt, wenn der Wert bekannt gültig ist
- `try/catch`: ✅ in Tests erlaubt (Test-Frameworks nutzen Exceptions bewusst)
- Immutability: ✅ Testdaten als `const`/`readonly` definieren

---

## 0b. Wie diese Regeln zu lesen sind

**Regeln sind starke Guidelines, keine absoluten Gesetze.** Wenn es sehr gute Gründe gibt, von einer Regel abzuweichen, ist das in Ordnung – aber:
- Die Entscheidung und Begründung **sofort kommunizieren** (an den Aufrufer: Mensch oder Agent), damit dieser ein Veto einlegen kann
- In `docs/history/decisions.md` dokumentieren

**Hinter jeder Regel steckt ein allgemeines Problem**, nicht nur der beschriebene Spezialfall. Beispiel: "Keine direkten `new`-Konstruktoren" beschreibt das allgemeinere Problem *"Invarianten können nicht durchgesetzt werden, wenn Objekte unkontrolliert erstellt werden"*. Ein Agent soll dieses Problem verstehen und es auch in Fällen erkennen, die nicht explizit in den Beispielen stehen – nicht nur die Buchstaben der Regel befolgen, sondern ihren Geist.

---

## 0c. Hexagonal Architecture (Ports & Adapters)

Dieser Codebase folgt dem **Ports & Adapters**-Prinzip:

- **Eingehende Ports** (Driving Side): HTTP-Endpoints (`mahl.Server/Endpoints/`) – Anfragen von außen gelangen über diese Ports in die Domäne
- **Ausgehende Ports** (Driven Side): `MahlDbContext` (`mahl.Infrastructure`) – die Domäne kommuniziert mit der Infrastruktur über diesen Port

**Tests exercisen ausschließlich über Ports:**
- Kein direkter Zugriff auf Domain-Typen von Testcode (kein `InternalsVisibleTo`)
- Tests senden HTTP-Requests (eingehender Port) und prüfen DB-State via DbContext (ausgehender Port)
- Das ist Black-Box-Testing: Die Implementierung kann vollständig ausgetauscht werden, solange das Port-Verhalten gleich bleibt

### Projekt-Visibility

| Projekt | Sichtbarkeit | Inhalt |
|---------|-------------|--------|
| `mahl.Infrastructure` | `public` | `MahlDbContext`, `*DbType`-Klassen (EF Core Entities) |
| `mahl.Server` | vollständig `internal` | Endpoints, Domain-Typen, DTOs, alles andere |
| `mahl.Server.Tests` | Test-Only | Integration-Tests (via HTTP + DbContext, kein `InternalsVisibleTo`) |

Kein `InternalsVisibleTo` – das erzwingt, dass Tests ausschließlich über die öffentlichen Ports (HTTP + DbContext) zugreifen. Domain-Typen direkt zu instantiieren ist bewusst unmöglich gemacht.

---

## 1. Tech Stack

### Backend
- **.NET 10.0 (LTS)** – ASP.NET Core Web API
- **Minimal APIs** – Endpoint-Pattern statt Controllers (`Server/Endpoints/`)
- **Entity Framework Core 10** mit **Npgsql** (PostgreSQL-Provider)
- **Serilog** – strukturiertes Logging
- **OpenAPI** – API-Dokumentation via `Microsoft.AspNetCore.OpenApi` (built-in seit .NET 9, verfügbar unter `/openapi/v1.json` in Development; kein Swashbuckle erforderlich)

### Frontend
- **React 19** mit TypeScript
- **Material UI v7** (Material Design 3)
- **Vite** als Build-Tool
- **React Router v7** für Routing (Imports aus `react-router`, nicht `react-router-dom`)
- **Workbox** für Service Worker (PWA, offline – ab MVP)
- **React Query** für Daten-Caching

### Datenbank
- **PostgreSQL 15+** via Docker Compose
- **Keine** PostgreSQL-spezifischen Features (JSONB, Arrays) in V1 – DB-Provider soll austauschbar bleiben
- Alle Queries über EF Core LINQ (kein Raw SQL außer Performance-kritisch)

### Deployment
- Docker & Docker Compose (self-hosted)
- Backend liefert React-Build-Output als statische Dateien aus `Server/wwwroot/`

---

## 2. Domain Modeling: "Make Illegal States Unrepresentable"

Gilt für C# und TypeScript gleichermaßen.

Für jedes Domänen-Konzept existiert ein eigener Typ, der seine Invarianten selbst durchsetzt. Ist ein Wert dieses Typs vorhanden, ist er garantiert gültig – der Compiler erzwingt das.

- **Factory Function = Validierung:** Gibt entweder ein gültiges Objekt oder einen Fehler zurück – keine separate Validierungs-Schicht. Fehlerfall im Endpoint/Handler → HTTP 400.
- **Dependency Rule:** Factory Functions nehmen Domain-Typen oder Primitives – niemals DTOs, API-Response-Typen oder DB-Entities. Mapping findet im Endpoint-Layer statt.
- **Cross-Entity-Constraints** (Uniqueness etc.) können nicht im Typ ausgedrückt werden → expliziter Check im Endpoint-Layer.
- **Result-Typen als Bausteine:** `OneOf<A, B>` (C#) / `Result<T, E>` (TypeScript) sind Bausteine, kein Ersatz für eigene Domain-Typen. Je mehr Semantik ein Konzept trägt, desto eher verdient es einen eigenen Typ.
- **Immutability:** Objekte sind nach Konstruktion unveränderlich (C#: `init`-Properties; TypeScript: `readonly`, Spreading statt Mutation).

Implementierungsdetails & Code-Beispiele:
- C#: `docs/CODING_GUIDELINE_CSHARP.md` (Sektion Domain Modeling)
- TypeScript: `docs/CODING_GUIDELINE_TYPESCRIPT.md` (Sektionen 2–4)

---

## 3. Endpoint-Pattern

Jede Endpoint-Gruppe ist eine separate Datei in `Server/Endpoints/`:

```csharp
// Server/Endpoints/IngredientsEndpoints.cs
public static class IngredientsEndpoints
{
    public static void MapIngredientsEndpoints(this WebApplication app)
    {
        app.MapGet("/api/ingredients", async (MahlDbContext db) => { ... })
           .WithTags("Ingredients");

        app.MapPost("/api/ingredients", async (...) => { ... })
           .WithTags("Ingredients");
    }
}

// Server/Program.cs
app.MapIngredientsEndpoints();
app.MapRecipesEndpoints();
// ...
```

**EF Core:** Kein Lazy Loading – immer explizites `Include()` verwenden.

---

## 4. Projekt-Struktur

```
Infrastructure/                   EF Core – public (eigenes Projekt)
  DatabaseTypes/                  *DbType-Klassen (EF Core Entities, public)
  MahlDbContext.cs                DbContext (public)

Server/                           Server-Logik – vollständig internal
  Domain/                         Domain-Typen (internal by default)
  Dtos/                           Request/Response-DTOs (internal)
  Endpoints/                      Minimal API Endpoints + file-level Mappings (internal)

Server.Tests/                     Integration-Tests (kein InternalsVisibleTo)
  Helpers/                        TestWebApplicationFactory, EndpointsTestsBase
```

**Strict separation:**
- `Infrastructure`: Nur EF Core Entities und DbContext – keine Domain-Typen, keine Endpoints
- `Server`: Referenziert `Infrastructure` für DbContext; alle eigenen Typen sind `internal`
- `Server.Tests`: Greift nur auf HTTP-Ports und `MahlDbContext` zu – nie direkt auf `internal`-Typen

Shared-Typen (`NonEmptyTrimmedString`, `NonEmptyList<T>`, etc.) liegen in `Server/Types/` und sind ebenfalls `internal`.

---

## 5. TDD-Prozess (verbindlich)

> Vollständige Beschreibung: **`docs/TDD_PROCESS.md`**

TDD gilt für **jeden Produktionscode** (Features, Bugfixes, Refactorings) – nicht nur für Tests. Jede Änderung durchläuft Red → Green → Refactor. Tests nach der Implementierung schreiben ist **kein TDD**.


## 6. Logging

```csharp
// Serilog – konfiguriert in Program.cs
// Format: [HH:mm:ss LEVEL] [TraceId: {TraceId}] Message
// Development: Console
// Production: Console + File (daily rolling)
// Request-Logging: UseSerilogRequestLogging() (nur non-development)
```

Keine sensitiven Daten loggen (Passwörter, etc.).

---

## 7. API Error Handling

- Backend: **ASP.NET Core Problem Details (RFC 7807)** für alle Fehler
- Frontend: Einheitliche Fehlermeldungen via **MUI Snackbar**

---

## 8. Authentifizierung

- **SKELETON:** Keine Auth (Hardcoded User oder ohne)
- **MVP:** ASP.NET Core Identity + JWT
- **User-Tracking:** `CreatedBy`, `ModifiedBy` auf Entities (ab MVP)
- **Esser-Profile vs. System-User:** System-User = technische Logins; Esser-Profile = fachliche Entität für Bewertungen

---

## 9. Git-Workflow

```
main        Produktionscode
develop     Entwicklungsbranch
feature/us-301-intelligent-article-capture   Feature-Branches
```

**Commit-Format:** `US-301: Implement intelligent article search`

---

## 10. Bilder & Dateispeicherung

- Rezept-Quell-Bilder: `Server/wwwroot/uploads/recipe-sources/{recipeId}/original.jpg`
- **Nicht** in der Datenbank speichern
- Backup: `pg_dump` (DB) + `tar` (Filesystem)

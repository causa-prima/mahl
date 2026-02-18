# Implementation Guide - Mahl App

> **Ziel dieses Dokuments:** Dieses Dokument dient als zentrale Spezifikation für die Implementierung der "Mahl"-App. Es enthält alle notwendigen technischen Entscheidungen, Architekturvorgaben und Implementierungshinweise, sodass ein LLM die Umsetzung vollständig durchführen kann.

---

## 1. Projektübersicht

**Projektname:** Mahl
**Beschreibung:** Eine Meal-Planning und Shopping-List-Applikation, die Familien bei der Essensplanung, dem Einkauf und der Zubereitung unterstützt.

**Vision:**
"Mahl befreit den Familienalltag von der mentalen Last der Essensplanung und macht gesunde, abwechslungsreiche Ernährung zum stressfreien Selbstläufer."

**Mission:**
"Wir entwickeln einen intelligenten Assistenten, der die Lücke zwischen Planung, Einkauf und Kochen schließt. Wir eliminieren Entscheidungsmüdigkeit durch smarte Vorschläge, optimieren den Einkauf durch Kontext-Wissen und führen entspannt durch die Zubereitung - immer mit dem Ziel, Zeit zu sparen und Verschwendung zu vermeiden."

**Kernfunktionen:**
- Intelligente Wochenplanung mit Regel-basiertem Vorschlagssystem
- Kontextbewusste Einkaufsliste mit Offline-Sync
- Geführter Kochmodus mit Schritt-für-Schritt-Anleitung
- Rezeptverwaltung mit Import-Funktion
- Zutaten- und Tag-Verwaltung

### 1.1 Projektkontext & Geschichte

**WICHTIG für implementierende Agenten:**

Dieses Projekt war ursprünglich ein **"Spielprojekt"** zum Ausprobieren verschiedener Technologien (Blazor WebAssembly, MariaDB). Es hat nun einen **"Pivot"** durchlaufen mit neuen technischen Entscheidungen:

**Alt (Spielprojekt):**
- ❌ Blazor WebAssembly Frontend → **wird komplett gelöscht**
- ❌ MariaDB/MySQL Datenbank → **wird durch PostgreSQL ersetzt**
- ❌ Alte Migrations → **werden verworfen**

**Neu (Production-Ready):**
- ✅ React 18+ mit Material UI v6
- ✅ PostgreSQL 15+
- ✅ Neue DB-Schema & Migrations

**Bestehender Code:**
- Der Code in `Server/` und `Shared/` sowie die dazugehörigen Test-Projekte ist **Referenz-Implementierung**
- Dieser Code zeigt die **gewünschten Patterns** (Custom Value Types, Factory Methods, OneOf)
- Er ist **nicht sakrosankt** - wenn du bessere Lösungen siehst, implementiere sie
- Bei Widersprüchen zwischen altem Code und neuer Spec: **Spec gewinnt**

**Deine erste Aufgabe als implementierender Agent:**
1. Bereinige alte Technologie-Referenzen (Blazor, MariaDB)
2. Richte neue Technologien ein (React, PostgreSQL)
3. Erstelle InitialCreate Migration mit vollständigem Schema
4. Nutze bestehenden Shopping-Liste-Code als Vorbild für neue Endpoints

### 1.2 Decision-Making Guide für Agenten

**Du hast Entscheidungsfreiheit!** Diese Spezifikation ist detailliert, aber nicht mikromanagend. Wir möchten, dass du als Agent **eigenständig sinnvolle technische Entscheidungen triffst**.

#### ✅ Was du SELBST entscheiden darfst (ohne nachzufragen):

**Technische Implementierungsdetails:**
- Datenbankschema-Details (z.B. Index-Namen, Foreign Key Constraints, genaue Feldlängen)
- API Response-Formate (solange konsistent mit REST-Konventionen)
- Validierungsregeln für Standard-Fälle (z.B. "Name darf nicht leer sein", "Quantity muss positiv sein")
- Error Codes und Problem Details (RFC 7807)
- Logging-Statements und Log-Levels
- Test-Daten in Unit Tests
- CSS-Klassen und Komponenten-Struktur (solange Material UI verwendet wird)
- Performance-Optimierungen (z.B. Caching, Indexing)
- Code-Organisation (Dateinamen, Namespace-Struktur, solange konsistent)

**Pattern-Anwendung:**
- Wie du Custom Value Types konkret implementierst (solange Patterns eingehalten werden)
- Ob du zusätzliche Helper-Methoden erstellst
- Wie du Dependency Injection nutzt
- Test-Struktur (solange TDD eingehalten wird)

**UI/UX Details:**
- Genaue Button-Positionen (solange Touch-Targets >= 48px)
- Farben (solange Material Design 3 Palette)
- Icons (solange Material UI Icons)
- Animationen und Transitions
- Responsive Breakpoints (zusätzlich zu 768px)

**Beispiele für autonome Entscheidungen:**
```
✅ "Zutat-Name: Maximal 200 Zeichen" → SELBST ENTSCHEIDEN
✅ "Rezept-Schritt: Maximal 2000 Zeichen" → SELBST ENTSCHEIDEN
✅ "DELETE /api/ingredients/{id} gibt 204 No Content zurück" → SELBST ENTSCHEIDEN
✅ "Bei Validation-Fehler: 400 Bad Request mit ProblemDetails" → SELBST ENTSCHEIDEN
✅ "ShoppingListItem.Id als int oder Guid?" → SELBST ENTSCHEIDEN (int bevorzugt, konsistent)
✅ "Einkaufsliste: Icon für 'Milch' = milk icon" → SELBST ENTSCHEIDEN
```

#### ❓ Wann du NACHFRAGEN solltest:

**Business-Logic-Entscheidungen:**
- Verhalten bei mehrdeutigen User Stories (z.B. "Was passiert, wenn Pool leer ist?")
- Priorisierung von Features (z.B. "Soll ich Feature X vor Y implementieren?")
- Änderungen am Domain-Modell (z.B. "Soll ich neues Feld hinzufügen?")
- Abweichungen von Spezifikation (z.B. "Spec sagt X, aber ich denke Y ist besser weil...")

**Architektur-Änderungen:**
- Wechsel zu anderen Technologien (z.B. "Redis statt In-Memory Cache?")
- Neue Dependencies (z.B. "Ich würde gerne Library X nutzen")
- Breaking Changes an API-Contracts
- Änderungen an Datenbank-Schema, die Migration komplizieren

**Unklare Requirements:**
- Widersprüche zwischen Dokumenten (solltest du schon gefunden haben!)
- Fehlende Spezifikationen für kritische Flows
- Edge Cases, die nicht dokumentiert sind UND Business-Impact haben

**Beispiele für Nachfrage-Pflicht:**
```
❓ "Einkaufsliste generieren: Überschreiben oder aggregieren?" → NACHFRAGEN
❓ "Wenn Zutat gelöscht, aber in Rezept verwendet: Fehler oder Warnung?" → NACHFRAGEN
❓ "AlwaysInStock-Zutaten: Niemals auf Liste ODER nur bei explizitem Request?" → NACHFRAGEN
❓ "Sub-Rezepte: Rekursiv auflösen bis max. Tiefe 3 oder unbegrenzt?" → NACHFRAGEN
❓ "Ich würde gerne von PostgreSQL zu SQLite wechseln für einfacheres Deployment" → NACHFRAGEN
```

#### 💡 Best Practice:

**Bei Unsicherheit:**
1. Prüfe GLOSSARY.md (Domain-Begriffe sind bindend)
2. Prüfe bestehenden Code (Shopping-Liste als Referenz)
3. Überlege: Hat meine Entscheidung **Business-Impact** oder nur **technischen Impact**?
   - Technisch → Entscheide selbst
   - Business → Frage nach
4. Dokumentiere deine Entscheidung in AGENT_MEMORY.md (Abschnitt "Technische Entscheidungen")

**Goldene Regel:**
> "Wenn du eine vernünftige Default-Wahl treffen kannst, die mit Standard-Practices übereinstimmt und später leicht änderbar ist → Entscheide selbst und dokumentiere es."

> "Wenn die Entscheidung das Nutzer-Erlebnis, Business-Logic oder Architektur fundamental beeinflusst → Frage nach."

---

## 2. Technische Entscheidungen

### 2.1 Tech Stack

**Backend:**
- .NET 8.0 (oder aktuellste LTS-Version zum Zeitpunkt der Implementierung)
- ASP.NET Core Web API
- Entity Framework Core mit geeignetem Provider
- Minimal APIs (Endpoint-Pattern, keine Controller)
- Serilog für strukturiertes Logging
- Swagger/OpenAPI für API-Dokumentation

**Frontend:**
- Progressive Web App (PWA)

**Entscheidung: React 18+ mit Material UI v6**

**Begründung:**
- Offline-Support (US-306) ist MVP-Anforderung und React hat das beste Ökosystem dafür
- Material UI v6 bietet vollständigen Material Design 3 Support (stabil, kein "experimentell")
- Workbox (Google) für Service Worker ist battle-tested und weit verbreitet
- Mutation Testing mit Stryker-JS ist etabliert und ausgereift
- Bestehender Blazor-Code wird nicht weiterverwendet (rudimentär)
- Exzellente Developer Experience mit modernem Tooling

**Migration:**
- Bestehender `Client/` Ordner (Blazor) wird komplett gelöscht
- Neues React-Projekt wird in `Client/` (oder `client-react/`) aufgesetzt
- Vite-Setup: `npm create vite@latest Client -- --template react-ts`
- Backend bleibt unverändert, liefert nur API

**Tech Stack Frontend:**
- React 18+
- Material UI (MUI) v6
- TypeScript (strikte Typen analog zu C# Custom Value Types)
- Vite als Build-Tool
- React Router v6 für Routing
- Workbox für Service Worker
- React Query + Offline-Plugin für Daten-Caching

**Alternative (falls React abgelehnt wird):**
- Vue 3 + Vuetify 3 (ähnliche Vorteile, etwas kleineres Ökosystem)

**API Error Handling:**
- Backend: ASP.NET Core Problem Details (RFC 7807)
- Frontend: Einheitliche Error-Anzeige via MUI Snackbar

**Datenbank:**

**Entscheidung: PostgreSQL 15+**

**Begründung:**
- Relationale DB ist optimal für stark vernetzte Daten (Rezepte, Zutaten, Tags, Pläne)
- PostgreSQL bietet bessere JSON-Unterstützung für zukünftige Erweiterungen
- Array-Types vereinfachen Tag-Speicherung
- Npgsql EF Core Provider ist ausgereift und performant
- Migration von MariaDB (aktuell im Projekt) ist später möglich (beide SQL-konform)
- Modern, aktive Entwicklung, starke Community

**Flexibilität sicherstellen:**
- Keine PostgreSQL-spezifischen Features verwenden (JSONB, Arrays, etc.) in V1
- Alle Queries über EF Core LINQ (keine Raw SQL außer Performance-kritisch)
- Keine Stored Procedures in V1/MVP
- Datenbank-Provider ist über EF Core austauschbar

**Deployment:**
- Docker & Docker Compose
- Self-hosted auf eigenem Server
- Separate Container für:
  - Backend API
  - Frontend (statische Dateien via nginx oder direkt vom Backend)
  - Datenbank

### 2.2 Architektur-Muster

**Domain-Driven Design:**
- Strikte Trennung zwischen Domain Models (Shared/), Database Types (Server/Data/DatabaseTypes/) und DTOs (Shared/Dtos/)
- Ubiquitäre Sprache aus GLOSSARY.md ist bindend
- Domain Models enthalten Business-Logik

**"Make Illegal States Unrepresentable":**
- Verwendung von Custom Value Types (`TrimmedString`, `NonEmptyTrimmedString`, `SyncItemId`)
- `OneOf<T, U>` für Discriminated Unions (z.B. `SyncItemId` ist entweder `Known(int)` oder `Unknown`)
- Factory Methods statt Public Constructors für Domain Entities
- Rückgabe von `OneOf<Success<T>, Error<string>>` aus Factory Methods
- Immutable Types mit `record` und `init`-only Properties

**Beispiel (bereits im Code vorhanden):**
```csharp
// Custom Value Type
public readonly record struct NonEmptyTrimmedString
{
    private readonly string value;

    private NonEmptyTrimmedString(string value) => this.value = value;

    public static OneOf<Success<NonEmptyTrimmedString>, Error<string>> Create(string input)
    {
        if (string.IsNullOrWhiteSpace(input))
            return new Error<string>("Value cannot be empty");

        return new Success<NonEmptyTrimmedString>(new NonEmptyTrimmedString(input.Trim()));
    }
}

// Domain Entity mit Factory Method
public record ShoppingListItem
{
    public SyncItemId Id { get; init; }
    public NonEmptyTrimmedString Title { get; init; }
    // ... weitere Properties

    private ShoppingListItem() { } // Private Constructor

    public static OneOf<ShoppingListItem, Error<string>> New(
        string title,
        string description)
    {
        var titleResult = NonEmptyTrimmedString.Create(title);
        if (titleResult.IsT1) // Error
            return titleResult.AsT1;

        return new ShoppingListItem
        {
            Id = SyncItemId.Unknown,
            Title = titleResult.AsT0.Value,
            // ...
        };
    }
}
```

**Wichtig:** Diese Patterns sind **NICHT** optional, sondern **bindend** für die Implementierung. Siehe bestehenden Code in `Shared/Types/` und Domain Models.

### 2.3 Authentifizierung & Benutzerverwaltung

**Anforderung:**
- Einfaches Login-System (Username + Passwort)
- Single-Tenant (eine Familie pro Installation)
- Nachvollziehbarkeit: Wer hat welche Änderung vorgenommen?
- **KEINE** komplexe Rechteverwaltung in der ersten Version (für spätere Erweiterung vorbereitet sein)

**Implementierung:**
- ASP.NET Core Identity (vereinfachte Konfiguration) → **Für MVP**
- **SKELETON**: Hardcoded User oder Authentication überspringen (Fokus auf Datenfluss)
- JWT-basierte Authentifizierung für API (bei React-Frontend)
- User-Tracking für Änderungen (CreatedBy, ModifiedBy auf Entities) → **Für MVP**

**Esser-Profile vs. System-User:**
- **System-User:** Technische Benutzer für Login und Änderungsverfolgung
- **Esser-Profile:** Fachliche Entität zur Bewertung von Rezepten (siehe GLOSSARY.md)
- Ein System-User kann mehrere Esser-Profile verwalten

---

## 3. Domain Model & Ubiquitäre Sprache

**WICHTIG:** Die vollständige Definition aller Fachbegriffe und deren Beziehungen ist in `docs/GLOSSARY.md` dokumentiert. Diese Begriffe sind **bindend** für Code, Datenbank-Schema und API.

**Zentrale Konzepte:**
- **Zutat (Ingredient):** Stammdaten eines Lebensmittels
- **Rezept (Recipe):** Anleitung zur Zubereitung
- **Wochen-Pool:** Verbindlich ausgewählte Rezepte für den Planungszeitraum
- **Einkaufsliste (Shopping List):** Aggregierte Liste benötigter Zutaten
- **Kochmodus (Cooking Mode):** Schritt-für-Schritt-Führung

**Siehe:** `docs/GLOSSARY.md` für vollständige Definitionen.

---

## 4. User Stories & Features

Die vollständigen User Stories sind in `docs/USER_STORIES.md` dokumentiert und nach Priorität getaggt:

- **[SKELETON]:** Minimaler technischer Durchstich (End-to-End)
- **[MVP]:** Minimum Viable Product - echter Mehrwert für Nutzer
- **[V1]:** Erste vollständige Version mit Komfortfunktionen
- **[V2]:** Erweiterungen und Optimierungen

**Siehe:** `docs/USER_STORIES.md` für alle Details.

---

## 5. Implementierungsphasen

### Phase 1: SKELETON (Walking Skeleton)

**Ziel:** Ein minimaler, aber vollständiger technischer Durchstich, der alle Schichten der Anwendung verbindet.

**User Stories (reduziert auf echtes Minimum):**
- US-904: Zutaten-Verwaltung (Basisdaten anlegen)
- US-602: Manuelle Rezepterfassung (Titel + mind. 1 Zutat + 1 Schritt)
- US-803: Rezept dem Wochen-Pool hinzufügen (manuell, ohne Wizard)
- US-201 + US-303: Einkaufsliste anzeigen (generiert aus Pool) & Artikel abhaken

**Hinweis:** Die folgenden User Stories wurden zu MVP verschoben:
- US-501 (Pool-Liste), US-505 (Zutaten-Übersicht), US-506 (Koch-Start), US-605 (Schritte anlegen), US-614 (Rezept bearbeiten), US-801 (Rezept-Liste)

**WICHTIG:** Diese 4 Stories reichen, um den kompletten Datenfluss zu demonstrieren:
1. Zutat anlegen → 2. Rezept mit Zutat anlegen → 3. Rezept in Pool → 4. Einkaufsliste generiert & abhakbar

**Technische Infrastruktur:**
- [ ] Projekt-Setup (Backend + Frontend)
- [ ] Docker Compose für PostgreSQL (Pflicht), optional auch Backend-Container für Deployment-Tests
- [ ] Datenbank-Setup (KEINE Migrationen bis Production-Release!)
- [ ] Seed-Data für Entwicklung (5-10 Test-Rezepte aus echten Lieblings-Rezepten)
- [ ] Basis-Authentifizierung → **OPTIONAL für SKELETON, PFLICHT für MVP**
  - Alternativ: Hardcoded User für SKELETON, echtes Auth in MVP
- [ ] PWA-Grundkonfiguration → **Verschoben zu MVP** (US-306 benötigt it)
- [ ] CI/CD-Pipeline → **Verschoben zu Post-MVP**

**Entwicklungs-Workflow (vor Production-Release):**
- **KEINE EF Core Migrations** bis zur ersten Production-Version (V1 oder V2)
- **Bei Schema-Änderungen:** Database Drop + Recreate + Seed
  ```bash
  dotnet ef database drop --force
  dotnet ef migrations remove  # Alte Migration löschen
  dotnet ef migrations add InitialCreate
  dotnet ef database update
  dotnet run --seed-data  # Lädt Test-Daten
  ```
- **Seed-Data Quelle:** `Server/Data/SeedData.sql`
  - **Enthält:** 45 Standard-Zutaten + 9 diverse Rezepte aus echten Familienrezepten
  - **Rezepte:** Chili sin Carne, Lasagne, Käsespätzle, Pilz-Risotto, Gnocchi-Kürbis-Auflauf, Burger, Blätterteigschnecken (2 Varianten), Waffeln, Pizzateig
  - **Ladeoptionen:**
    - **Option A (einfach):** SQL direkt ausführen: `psql -U user -d database -f Server/Data/SeedData.sql`
    - **Option B (eleganter):** C# Extension Method `app.SeedDatabase()` erstellen (siehe unten)
- **Vorteil:** Schnellere Iteration, keine Migrations-Hölle, App ist sofort nutzbar mit echten Daten

**Ab Production-Release:**
- **EF Core Migrations nutzen** (User haben echte Daten!)
- Seed-Data nur für neue Instanzen (nicht bei Updates)

**Datenmodell (Minimum):**
- User → **Optional für SKELETON** (oder Hardcoded)
- Ingredient (Zutat)
- Recipe (Rezept)
- RecipeIngredient (Rezept-Zutat)
- Step (Zubereitungsschritt)
- ShoppingListItem
- WeeklyPoolEntry → **Vereinfacht: Nur Liste von Recipe-IDs, keine Datumslogik**

**Datenbank-Schema (SKELETON - Detailliert):**

**Ingredient:**
- `Id` (int, PK, Auto-Increment)
- `Name` (string, NOT NULL, UNIQUE)
- `DefaultUnit` (string, NOT NULL) // z.B. "g", "ml", "Stück"
- `AlwaysInStock` (bool, NOT NULL, DEFAULT false) // Flag für US-906 (MVP), schon in SKELETON angelegt
- `DeletedAt` (timestamptz?, NULLABLE) // Soft-Delete - NULL = aktiv, NOT NULL = gelöscht

**Recipe:**
- `Id` (int, PK, Auto-Increment)
- `Title` (string, NOT NULL)
- `SourceUrl` (string, NULLABLE) // Für US-601 (MVP: Import)
- `SourceImagePath` (string, NULLABLE) // Für US-602 (SKELETON: Foto aus Kochbuch)
  - Format: `/uploads/recipe-sources/{recipeId}/original.jpg`
  - Bilder werden im Filesystem gespeichert (`Server/wwwroot/uploads/recipe-sources/`)
- `DeletedAt` (timestamptz?, NULLABLE) // Soft-Delete - NULL = aktiv, NOT NULL = gelöscht
- **Constraint:** ENTWEDER SourceUrl ODER SourceImagePath, nie beides

**RecipeIngredient:**
- `Id` (int, PK, Auto-Increment)
- `RecipeId` (int, NOT NULL, FK -> Recipe.Id, ON DELETE CASCADE)
- `IngredientId` (int, NOT NULL, FK -> Ingredient.Id)
- `Quantity` (decimal, NOT NULL)
- `Unit` (string, NOT NULL)
- **Index:** (RecipeId, IngredientId)

**Step:**
- `Id` (int, PK, Auto-Increment)
- `RecipeId` (int, NOT NULL, FK -> Recipe.Id, ON DELETE CASCADE)
- `StepNumber` (int, NOT NULL) // Reihenfolge (1, 2, 3, ...)
- `Instruction` (text, NOT NULL)
- **Index:** (RecipeId, StepNumber)
- **Constraint:** UNIQUE (RecipeId, StepNumber)

**WeeklyPoolEntry:**
- `Id` (int, PK, Auto-Increment)
- `RecipeId` (int, NOT NULL, FK -> Recipe.Id)
- `AddedAt` (timestamptz, NOT NULL, DEFAULT NOW())
- **KEINE Datumslogik in SKELETON** (kein `PlannedDate`-Feld)

**ShoppingListItem:**
- `Id` (int, PK, Auto-Increment)
- `IngredientId` (int, NOT NULL, FK -> Ingredient.Id)
- `Quantity` (decimal, NOT NULL) // Gesamtmenge (in SKELETON einfach, in MVP: berechnet aus Sources + ManualAdjustment)
- `Unit` (string, NOT NULL)
- `BoughtAt` (timestamptz, NULLABLE) // NULL = offen, NOT NULL = gekauft
- `GeneratedAt` (timestamptz, NOT NULL, DEFAULT NOW())
- **Hinweis SKELETON:** Items werden bei "Liste generieren" komplett neu erstellt
  - Alte Items werden gelöscht, neue aus Pool generiert
  - Nur `BoughtAt` bleibt erhalten (wenn Item mit gleicher Ingredient+Unit wieder generiert wird)

**ShoppingListItemSource (nur MVP, nicht SKELETON):**
- `Id` (int, PK, Auto-Increment)
- `ShoppingListItemId` (int, NOT NULL, FK -> ShoppingListItem.Id, ON DELETE CASCADE)
- `RecipeId` (int, NOT NULL, FK -> Recipe.Id, ON DELETE CASCADE)
- `Quantity` (decimal, NOT NULL) // Anteil aus diesem Rezept
- **Index:** (ShoppingListItemId, RecipeId) UNIQUE
- **Hinweis:** Diese Tabelle ermöglicht Tracking "welche Zutat aus welchem Rezept"

**ShoppingListItem erweitert für MVP:**
- `ManualAdjustment` (decimal, NOT NULL, DEFAULT 0) // User-Korrektur zur berechneten Menge
- **Berechnung:** Angezeigte Menge = SUM(Sources.Quantity) + ManualAdjustment

**API-Endpoints (SKELETON - Vollständig):**
```
(Auth-Endpoints optional für SKELETON)

# Zutaten-Verwaltung (US-904)
GET    /api/ingredients               # Liste aller Zutaten (WHERE DeletedAt IS NULL)
POST   /api/ingredients               # Neue Zutat anlegen
GET    /api/ingredients/{id}          # Einzelne Zutat
DELETE /api/ingredients/{id}          # Zutat löschen (Soft-Delete: setzt DeletedAt = NOW())

# Rezept-Verwaltung (US-602)
GET    /api/recipes                   # Liste aller Rezepte (WHERE DeletedAt IS NULL)
POST   /api/recipes                   # Neues Rezept anlegen (inkl. Ingredients + Steps)
  # Body: { title, sourceUrl?, sourceImage?, ingredients: [], steps: [] }
GET    /api/recipes/{id}              # Rezept-Details (inkl. Ingredients + Steps)
DELETE /api/recipes/{id}              # Rezept löschen (Soft-Delete: setzt DeletedAt = NOW())

# Wochen-Pool (US-803)
GET    /api/weekly-pool               # Alle Rezepte im Pool
POST   /api/weekly-pool               # Rezept zum Pool hinzufügen
  # Body: { recipeId: int }
DELETE /api/weekly-pool/recipes/{recipeId}  # Rezept aus Pool entfernen (Hard-Delete aller Entries mit dieser RecipeId)

# Einkaufsliste (US-201, US-303)
POST   /api/shopping-list/generate    # Einkaufsliste aus Pool generieren (löscht alte Items, erstellt neue)
GET    /api/shopping-list             # Aktuelle Einkaufsliste
  # Liefert: { openItems: [], boughtItems: [] }
PUT    /api/shopping-list/items/{id}/check   # Item als gekauft markieren (BoughtAt = NOW())
PUT    /api/shopping-list/items/{id}/uncheck # Item als offen markieren (BoughtAt = NULL)
```

**Frontend-Seiten (SKELETON - Vollständig):**

**1. Navigation (Responsive):**
- **Mobile (< 768px):** Burger-Menü (Material UI Drawer)
- **Desktop (>= 768px):** Horizontale Tabs (Material UI Tabs)
- Menü-Punkte:
  - "Zutaten"
  - "Rezepte"
  - "Wochen-Pool"
  - "Einkaufsliste"

**2. Zutaten-Seite (/ingredients):**
- Liste aller Zutaten (Material UI List oder DataGrid)
  - Zeigt: Name, Einheit
  - Keine Anzeige von AlwaysInStock in SKELETON
- "Neue Zutat"-Button (FAB) → öffnet Dialog
- Zutat-Dialog (Create):
  - Name-Feld (TextField, required)
  - Einheit-Feld (TextField, required, Beispiele: "g", "ml", "Stück")
  - Speichern-Button
- Inline-Löschen-Button pro Zutat (Trash-Icon)
  - Bestätigungsdialog: "Zutat löschen?"

**3. Rezepte-Seite (/recipes):**
- Liste aller Rezepte (Material UI Grid oder List)
  - Zeigt: Nur Titel (SourceImagePath ist Quelle, nicht Rezept-Foto)
- "Neues Rezept"-Button (FAB) → öffnet Rezept-Formular
- Klick auf Rezept → Rezept-Detailansicht

**3.1 Rezept-Detailansicht (/recipes/{id}):**
- Titel
- Quelle (SourceUrl als Link ODER SourceImagePath als Vorschau)
- Zutaten-Liste (Menge + Einheit + Zutat-Name)
- Schritte-Liste (nummeriert)
- Button "Zum Pool hinzufügen" → POST /api/weekly-pool

**3.2 Rezept-Formular (/recipes/new):**
- **Titel-Feld** (TextField, required)
- **Quelle (optional):**
  - Radio-Buttons: "URL" oder "Foto hochladen"
  - Wenn URL: TextField
  - Wenn Foto: File-Upload (accept="image/*") + Kamera-Button (mobile)
- **Zutaten-Sektion:**
  - Liste der hinzugefügten Zutaten (Menge, Einheit, Zutat-Name, Löschen-Button)
  - "Zutat hinzufügen"-Formular:
    - Autocomplete-Dropdown für Zutat (sucht in /api/ingredients)
      - Wenn Zutat nicht existiert: Option "Neue Zutat anlegen" (öffnet Zutat-Dialog)
    - Menge-Feld (NumberInput)
    - Einheit-Feld (TextField)
    - "Hinzufügen"-Button
- **Schritte-Sektion:**
  - Liste der hinzugefügten Schritte (Nummer, Text, Löschen-Button)
  - Textfeld für neuen Schritt (TextField, multiline)
  - "Schritt hinzufügen"-Button
- **Validierung:**
  - Mind. 1 Zutat erforderlich
  - Mind. 1 Schritt erforderlich
- **Speichern-Button** → POST /api/recipes

**4. Wochen-Pool-Seite (/weekly-pool):**
- Liste der Rezepte im Pool (Material UI List)
  - Zeigt: Rezept-Titel
  - "Entfernen"-Button pro Rezept (DELETE /api/weekly-pool/recipes/{recipeId})
- **"Einkaufsliste generieren"-Button** (prominent, z.B. FAB oder großer Button oben)
  - Bei Klick: POST /api/shopping-list/generate
  - Toast-Notification: "Einkaufsliste wurde erstellt"
  - Navigation zur Einkaufsliste (automatisch oder mit "Zur Liste"-Button)

**5. Einkaufsliste-Seite (/shopping-list):**
- **Zwei Bereiche:**
  - "Noch kaufen" (BoughtAt == null)
  - "Zuletzt gekauft" (BoughtAt != null)

- **Item-Darstellung (Große Touch-Buttons, Bring!-Stil):**

  **SKELETON:**
  - Große Button-Kacheln im Grid-Layout (min. 80x80px Touch-Target)
  - Icon: Generic Placeholder (Material UI ShoppingCart Icon)
  - Text: Zutat-Name, Menge + Einheit
  - Bei Klick: Toggle zwischen "offen" ↔ "gekauft"
    - PUT /api/shopping-list/items/{id}/check oder /uncheck
  - **Visueller Zustand:**
    - Offen: Volle Farbe (z.B. Weiß/Blau), normale Schrift
    - Gekauft: Grau-Ton, reduzierte Opacity
  - Optimistic UI: Sofort zwischen Bereichen verschieben

  **V1 - Icons pro Zutat:**
  - `Ingredient`-Tabelle bekommt `IconName`-Feld (string, Material UI Icon-Name)
  - User kann in Zutaten-Verwaltung Icon auswählen (Dropdown mit Vorschau)
  - Einkaufsliste zeigt zugeordnetes Icon statt Generic Placeholder

  **V2+ - Automatisch generierte Icons:**
  - LLM generiert Icon-Vorschläge basierend auf Zutat-Name
  - Oder: Unsplash/Pixabay API für Zutat-Fotos
  - Oder: Simple Strichzeichnungen via DALL-E/Stable Diffusion

- **Leere Liste:** Hinweis "Pool ist leer. Füge Rezepte zum Pool hinzu und generiere die Liste."

**Akzeptanzkriterium:**
Ein Nutzer kann:
1. Eine Zutat anlegen (z.B. "Tomaten, 200g, Stück")
2. Ein Rezept anlegen (Titel + mind. 1 Zutat + 1 Schritt)
3. Das Rezept dem Wochen-Pool hinzufügen (Button)
4. Die Einkaufsliste sehen (zeigt "Tomaten 200g")
5. Den Artikel abhaken (verschiebt in Bereich "Zuletzt gekauft")

**Das reicht als Walking Skeleton!** Alle weiteren Features sind MVP.

**Wichtige Klarstellungen für SKELETON:**

**Einkaufslisten-Generierung (SKELETON - Einfache Variante):**
- Button "Einkaufsliste generieren" am Wochen-Pool
- **Logik:** Löscht alte ShoppingListItems, schreibt ALLE Pool-Rezepte neu
- **Aggregation:** Gleiche Zutat + gleiche Einheit → Mengen summieren
- **KEIN Tracking:** Keine Speicherung, welche Zutat aus welchem Rezept kommt (kommt in MVP)
- **Limitation akzeptiert:** Wenn Rezept aus Pool entfernt wird, bleibt Zutat auf Liste (User muss manuell neu generieren)
- **AlwaysInStock-Filter:** Zutaten mit AlwaysInStock=true werden NICHT auf die Liste geschrieben

**Einkaufslisten-Generierung (MVP - Intelligente Variante):**
- ShoppingListItem wird erweitert mit:
  - `ManualAdjustment` (decimal): Delta zur berechneten Menge
- **Neue Tabelle:** `ShoppingListItemSource` (siehe DB-Schema oben)
  - Speichert: Welche Zutat kommt aus welchem Rezept mit welcher Menge
  - Foreign Keys zu Item + Recipe (referentielle Integrität!)
- **Logik:** Beim Generieren:
  1. Für jedes Pool-Rezept: Berechne benötigte Mengen
  2. Aggregiere nach Zutat (gleiche Ingredient + Unit)
  3. Wenn Item existiert und BoughtAt != null: Ignorieren (schon gekauft)
  4. Wenn Item existiert und BoughtAt == null:
     - Sources aktualisieren (neue Recipes hinzufügen, alte entfernen)
     - Quantity neu berechnen: SUM(Sources.Quantity) + ManualAdjustment
  5. ManualAdjustment bleibt erhalten
- **Beim Pool-Rezept löschen:**
  - DELETE FROM ShoppingListItemSource WHERE RecipeId = X (CASCADE löscht Einträge)
  - Für betroffene Items: Quantity neu berechnen
  - ManualAdjustment bleibt erhalten
  - Wenn SUM(Sources.Quantity) + ManualAdjustment <= 0: Item löschen

**Einkaufslisten-UI-Transparenz (V1):**
- UI zeigt bei jedem Item: "Aus Rezepten: Lasagne (150g), Pizza (50g)"
- ManualAdjustment wird angezeigt: "Angepasst: -50g"

**Weitere Klarstellungen:**
- **Einheiten-Konvertierung:** KEINE Umrechnung zwischen verschiedenen Einheiten (z.B. "200g" + "1 EL" = zwei separate Items). US-902 (Einheiten-Management) ist MVP.
- **AlwaysInStock-Flag:** Wird schon in SKELETON im Datenmodell angelegt, aber KEINE UI-Funktionalität in SKELETON. Filter wird aber schon beim Generieren angewendet (einfach zu implementieren).
- **Abhaken-Verhalten:** Artikel werden als "gekauft" markiert (BoughtAt-Timestamp), nicht gelöscht. Sie verschieben sich in Bereich "Zuletzt gekauft" (US-303).
- **Wochen-Pool:** Nur flache Liste ohne Datumslogik, keine Kalender-Ansicht in SKELETON. MVP bekommt Kalender-Darstellung mit Wochenansicht.
- **Bilder-Speicherung:** Filesystem (`Server/wwwroot/uploads/recipe-sources/{recipeId}/original.jpg`), NICHT in DB. Backup-Strategie: DB (pg_dump) + Filesystem (tar). V2+ bekommt Backup/Restore-Feature im UI.

---

### Phase 2: MVP (Minimum Viable Product)

**Ziel:** Alle Features, die nötig sind, um dem Nutzer echten Mehrwert zu bieten.

**Neue Features:**
- Planungs-Wizard mit automatischen Vorschlägen (US-103, US-105, US-106)
- Intelligente Artikelerfassung (US-301)
- Offline-Verfügbarkeit der Einkaufsliste (US-306)
- Non-Food-Items (US-307)
- Kochmodus mit Schritt-Zutaten (US-508, US-509, US-510)
- Rezept-Import (strukturierte Daten) (US-601 - Basic)
- Zutaten-Zuordnung zu Schritten (US-607)
- Tagging (US-609)
- Zeiterfassung (US-610)
- Rezept-Archivierung (US-616)
- Harte & Sortier-Regeln (US-701, US-702)
- Einheiten-Management (US-902)
- Vorrats-Management (US-906)

**Neue Datenmodell-Entitäten:**
- Tag
- IngredientModifier
- RecipeTag
- Rule (Hard/Soft Constraints)
- Unit & ConversionFactor
- NonFoodItem

**Offline-Sync-Strategie:**
- Service Worker cached alle API-Responses
- IndexedDB für lokale Datenhaltung
- Background-Sync für Uploads bei Reconnect
- **Polling-basierte Aktualisierung:** Einkaufsliste prüft in kurzen Intervallen (z.B. 3-5 Sekunden) auf Server-Updates
  - **Wichtig für paralleles Einkaufen:** Mehrere Nutzer sehen zeitnah Änderungen der anderen
  - Optimierung: Nur wenn App im Vordergrund, bei Offline automatisch pausieren
  - Alternative: Server-Sent Events (SSE) oder WebSockets für Echtzeit-Updates (siehe V2: US-402 Live-Sync)

**Konfliktlösung (Konkret):**

**Strategie für MVP: "Last-Write-Wins mit Nutzer-Transparenz"**

1. **Jede Änderung bekommt einen Timestamp** (client-generiert)
2. **Bei Sync-Konflikt (Server-Version ≠ Client-Version):**
   - Nutze die Änderung mit dem jüngeren Timestamp
   - **Wichtig**: Zeige dem Nutzer eine **Toast-Notification**:
     ```
     "Deine Änderung wurde überschrieben. [Undo]"
     ```
3. **Sonderfall: Abhaken (Check/Uncheck):**
   - Kein Konflikt! Endzustand ist deterministisch (checked oder unchecked)
   - Last-Write-Wins ist hier intuitiv richtig
4. **Konflikt: Gleichzeitiges Bearbeiten (Menge, Beschreibung):**
   - Wähle die Version, die **weniger Probleme** in der realen Welt verursacht:
     - Beispiel: Person A löscht "Milch", Person B ändert zu "Milch 3L"
     - **Lösung**: Änderung von B gewinnt (3L), Löschung von A verliert
     - **Regel**: "Additive Änderungen gewinnen über Delete/Reduce"

**Implementierungs-Hinweis:**
- Verwende **Optimistic Locking** mit Version-Nummern
- Server lehnt Writes mit veralteter Version ab (409 Conflict)
- Client holt neueste Version, merged (nach obigen Regeln), und retried

**Für V2 (US-402 Live-Sync):**
- Wechsel zu **Operational Transformation** oder **CRDTs** evaluieren
- Echtzeitprotokolle (WebSockets) statt Polling

---

### Phase 3: V1 (Version 1.0)

**Ziel:** Vollständige, runde Anwendung mit Komfortfunktionen.

**Neue Features:**
- Geräte-Kontext (US-001)
- Laufweg-Sortierung (US-302)
- Visuelle Darstellung & Varianten (US-304)
- Undo-Funktion (US-401)
- Koch-Start aus Suche (US-507)
- Ad-Hoc Skalierung (US-511)
- Intelligenter Wach-Modus (US-516)
- Rezept-Suche & Filter (US-802)
- Zutaten-Aliase (US-905)
- Tag-Sortierung für Einkaufsliste (US-907)

---

### Phase 4: V2 (Version 2.0)

**Ziel:** Erweiterte Funktionen und KI-Integration.

**Neue Features:**
- Muss-Zutaten (Reste-Verwertung) (US-102)
- Session-Regeln (US-104)
- Tagesregeln (US-107)
- Zeit-Budget (US-108)
- Live-Sync (US-402)
- Sub-Rezepte (US-514, US-603)
- Rezept-Import mit LLM-Fallback (US-601 erweitert)
- Tag-Hierarchie (DAG) (US-901)
- Esser-Profile & Bewertungen (US-903, US-513, US-515)

**LLM-Integration (optional):**
- Provider: Konfigurierbar (OpenAI, Anthropic, lokal)
- Use Cases:
  - Rezept-Extraktion aus unstrukturierten Webseiten
  - (Optional) Unterstützung bei Planungsentscheidungen

---

## 6. Rezept-Import & Schema.org

**Standard:** [Schema.org Recipe](https://schema.org/Recipe)

Viele Rezept-Websites (Chefkoch.de, AllRecipes, etc.) embedden strukturierte Daten im JSON-LD-Format:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Linsen-Dal",
  "image": "https://...",
  "recipeIngredient": [
    "200g rote Linsen",
    "1 Zwiebel",
    "..."
  ],
  "recipeInstructions": [
    {
      "@type": "HowToStep",
      "text": "Zwiebeln schneiden und anbraten"
    }
  ],
  "totalTime": "PT30M",
  "recipeYield": "4 Portionen"
}
</script>
```

**Implementierung:**
1. **Phase MVP:** Parser für Schema.org Recipe (JSON-LD)
   - Extrahiere: name, recipeIngredient, recipeInstructions, totalTime, recipeYield, url
   - **Hinweis:** Bilder werden NICHT importiert oder gespeichert
   - Preprocessing: Zutaten-Parsing (Menge, Einheit, Name)
   - **Wichtig:** Import befüllt nur das Rezept-Formular vor, Nutzer muss speichern

2. **Phase V2:** LLM-Fallback für Websites ohne strukturierte Daten
   - Scrape HTML-Content
   - Sende an LLM mit Prompt: "Extrahiere Rezept aus diesem HTML"
   - Rückgabe im gleichen Format wie Schema.org Parser

**Andere Standards (optional, V2+):**
- Microdata (schema.org als Microdata statt JSON-LD)
- RDFa

**Hinweis:** Ein bestehender Parser wurde in einer anderen Rezeptverwaltung gefunden. Wenn Schema.org nicht zu komplex ist, sollte die Logik selbst implementiert werden, um externe Abhängigkeiten zu reduzieren.

---

## 7. Deployment-Vorbereitung

**Hinweis:** Detailliertes Deployment (Docker-Setup, HTTPS-Konfiguration, Server-Setup) ist NICHT Teil dieser Implementierungs-Specs. Das wird später separat dokumentiert.

### 7.1 Deployment-Anforderungen (für Implementierung relevant)

**Docker-Support:**
- App MUSS via Docker deploybar sein
- `Dockerfile` für Backend (ASP.NET Core)
- `Dockerfile` für Frontend (falls separater Container)
- `docker-compose.yml` für lokales Development & Testing

**Umgebungsvariablen:**
- Konfiguration über Environment Variables (12-Factor-App)
- Secrets NICHT in Code/Config-Files
- `.env`-Template im Repository (ohne Secrets)

**Beispiel `.env.template`:**
```
DB_PASSWORD=<set-this>
JWT_SECRET=<generate-random-string>
ASPNETCORE_ENVIRONMENT=Production
```

**Health-Checks:**
- Backend sollte `/health` Endpoint haben
- Gibt 200 OK zurück wenn App läuft und DB erreichbar

**Logging:**
- Strukturiertes Logging (Serilog) zu stdout
- Für Container-Umgebungen (Docker logs erfassen)

---

## 8. Wichtige Implementierungshinweise

### 8.1 Bestehender Code

**WICHTIG:** Es existiert bereits Code im Repository, der folgende Features implementiert:
- Einkaufsliste (CRUD, Abhaken)
- Grundlegende Domain Models mit Custom Value Types
- Tests mit NUnit + FluentAssertions
- EF Core Setup mit Migrations

**Vorgehen:**
1. **Bestehenden Code analysieren** und als Referenz nutzen
2. **Patterns übernehmen:** Custom Value Types, Factory Methods, OneOf
3. **Nicht neu erfinden:** Wenn ein Feature bereits (teilweise) implementiert ist, darauf aufbauen
4. **Tests erweitern:** Bestehende Test-Patterns fortführen

### 8.2 Code-Qualität & Standards

**Erzwungen via `Directory.Build.props`:**
- Latest C# Language Version
- Nullable Reference Types enabled
- Nullable Warnings as Errors

**Test-Strategie (Test-Driven Development - TDD):**
- **TDD ist PFLICHT:** Tests werden VOR der Implementierung geschrieben (Red-Green-Refactor)
- **Unit Tests:** Für Domain Logic (Shared/)
- **Integration Tests:** Für API-Endpoints (Server.Tests/)
- **E2E-Tests:** Optional mit Playwright/Cypress für kritische User Flows

**Mutation Testing:**
- **Pflicht für ALLE Code-Teile** - Backend und Frontend
- **Tools:**
  - **.NET-Code (Backend):** Stryker.NET
  - **JavaScript/TypeScript (Frontend):** Stryker-JS

**Ziel:** 90%+ Mutation Coverage

**Ausnahmen dokumentieren:**
- Jede Abweichung von 90% MUSS begründet werden (in AGENT_MEMORY.md oder Code-Kommentar)
- Typische legitime Ausnahmen:
  - Generated Code (EF Migrations, Swagger-Config)
  - Triviale Properties/Constructors (bei Records oft automatisch getestet)
  - Logging-Statements (nicht business-kritisch)
  - Framework-Boilerplate (Program.cs Startup-Code)

**Hybrid-Ansatz für Performance:**
- **Periodisch (Ende jeder Phase):** Vollständiger Stryker-Lauf über gesamte Codebase
- **Zwischendurch:** Nach Abschluss von 3-5 User Stories (oder täglich bei schnellem Fortschritt)
- **Schnelle Iteration (während Feature-Entwicklung):** Nur geänderte Klassen/Files
- **Beispiel**:
  ```bash
  # Schnell: Nur ShoppingListService.cs mutieren
  dotnet stryker --files Server/Services/ShoppingListService.cs

  # Periodisch: Alles
  dotnet stryker
  ```
- **Vorsicht**: Coverage für nicht-getestete Bereiche manuell tracken (Spreadsheet oder AGENT_MEMORY.md)

**Integration in Workflow:**
- **Ende jeder Phase:** Vollständiger Stryker-Lauf (SKELETON, MVP, V1, V2) - PFLICHT
- **Während Feature-Entwicklung:** Hybrid-Ansatz nach Bedarf
- **Gate:** Keine Phase gilt als "Done" ohne mindestens 90% Coverage

**Logging:**
- Serilog mit strukturiertem Logging
- Log-Levels: Debug (Development), Information (Production), Warning, Error
- Request-Logging für alle API-Calls
- Sensitive Daten NICHT loggen (Passwörter, etc.)

### 8.3 PWA-Anforderungen

**Mandatory Features:**
- Service Worker für Offline-Caching
- Web App Manifest (manifest.json)
- Installierbar (Add to Homescreen)
- Responsive Design (Mobile-First)
- Touch-optimierte UI

**Offline-Strategie (für Einkaufsliste):**
- **Cache-First:** Daten aus Cache, falls vorhanden
- **Network-First mit Fallback:** Bei Schreiboperationen
- **Background-Sync:** Änderungen bei Reconnect synchronisieren

### 8.4 Performance-Überlegungen

**Backend:**
- EF Core: Lazy Loading vermeiden (Explicit Loading/Include)
- API-Paging für Listen (z.B. Rezepte)
- Caching häufig genutzter Daten (Zutaten, Tags)

**Frontend:**
- Code-Splitting / Lazy Loading von Routes
- Optimierte Bilder (WebP, Lazy Loading) - falls Bilder zukünftig genutzt werden
- **Hinweis:** Virtualisierung für lange Listen ist bei realistischen Einkaufslisten (30-80 Items) nicht notwendig. Moderne Browser rendern auch 200 Items problemlos. Falls in V2+ Performance-Probleme auftreten, kann dies nachträglich optimiert werden.

### 8.5 Datenschutz & Sicherheit

**Datensparsamkeit:**
- Prinzip: Nur Daten erfassen, die tatsächlich benötigt werden
- Keine Erfassung sensibler persönlicher Daten ohne expliziten Bedarf
- Pseudonymisierung über Benutzernamen ausreichend

**DSGVO-Relevanz:**
- **Single-Tenant = Self-Hosted:** Nutzer sind selbst Verantwortliche für ihre Daten
- DSGVO-Pflichten liegen beim Betreiber (= Nutzer), nicht bei der Software
- **Datenexport/Löschung:** Bei Self-Hosting hat der Nutzer direkten DB-Zugriff (pg_dump, mysqldump, DELETE)
  - UI-basierte Export/Löschfunktionen sind Nice-to-Have für V2+, aber nicht essentiell für SKELETON/MVP

**Standard-Sicherheitsmaßnahmen:**
- HTTPS (erzwungen)
- Sichere Passwort-Hashing (ASP.NET Core Identity Default)
- SQL-Injection Prevention (EF Core parametrisiert automatisch)
- XSS-Prevention (Framework-Defaults nutzen)
- CSRF-Protection (ASP.NET Core Anti-Forgery)
- Audit-Log für Änderungsverfolgung (CreatedBy, ModifiedBy)

### 8.6 Entwicklungs-Workflow

**Git-Branching:**
- `main`: Produktionscode
- `develop`: Entwicklungsbranch
- Feature-Branches: `feature/us-301-intelligent-article-capture`

**Commit-Messages:**
- Präfix mit US-Nummer: `US-301: Implement intelligent article search`
- Konvention: `<type>(<scope>): <subject>`

**Code-Reviews:**
- Da dies ein Agentic Engineering Experiment ist: LLM-generierter Code sollte von einem Menschen reviewed werden
- Tests müssen grün sein

---

## 9. Definition of Done

Ein Feature gilt als "Done", wenn:

**Funktional:**
- [ ] **Tests ZUERST geschrieben** (TDD: Red-Green-Refactor)
- [ ] Code implementiert nach Domain-Modell und Patterns
- [ ] Unit Tests grün (100% Coverage angestrebt)
- [ ] Integration Tests (falls relevant) grün
- [ ] **Mutation Testing durchgeführt** (Stryker.NET / Stryker-JS) - falls am Ende einer Phase
- [ ] Refactoring durchgeführt (Code-Qualität)
- [ ] API dokumentiert (Swagger)
- [ ] Frontend-UI implementiert (falls relevant)
- [ ] Manuelle Smoke-Tests durchgeführt

**Non-Functional (NFRs aus Abschnitt 10):**
- [ ] **Performance:** Interaktionen reagieren < 100ms (Optimistic UI)
- [ ] **Accessibility:** Keyboard-navigierbar, ARIA-Labels gesetzt
- [ ] **Responsiveness:** Mobile-optimiert (375px - 428px getestet)
- [ ] **Error Handling:** Nutzerfreundliche Fehlermeldungen
- [ ] **Security:** Input-Validierung, keine XSS/SQL-Injection-Risiken

**Dokumentation & Workflow:**
- [ ] Code committed mit aussagekräftiger Message
- [ ] Migrations erstellt (falls DB-Änderungen)
- [ ] AGENT_MEMORY.md aktualisiert

---

## 10. Non-Functional Requirements (NFRs)

Nicht-funktionale Anforderungen definieren, **WIE** die Software funktionieren soll, nicht **WAS** sie tut.

### 10.1 Performance & Responsiveness ("Snappy")

**Die App MUSS sich schnell und reaktionsfreudig anfühlen.**

**Messbare Metriken:**
- **Perceived Load Time:** < 300ms für Seitenwechsel (Optimistic UI, Skeleton Screens)
- **Interaktions-Feedback:** < 100ms Reaktion auf User-Input (Button-Press, Checkbox-Toggle)
- **API Response Time (Backend):**
  - Einfache Queries (GET /shopping-list): < 200ms (p95)
  - Komplexe Queries (Planungs-Algorithmus): < 2000ms (p95)
- **Offline-First:** Einkaufsliste muss **instant** reagieren (IndexedDB, kein Server-Roundtrip)
- **First Contentful Paint (FCP):** < 1.5s
- **Time to Interactive (TTI):** < 3s
- **Lighthouse Performance Score:** > 90

**Best Practices:**
- Optimistic UI: Sofort UI-Update, Server-Sync im Hintergrund
- Debouncing/Throttling bei Suchen
- Lazy Loading für nicht-kritische Komponenten
- Code-Splitting für Routes
- Caching-Strategien (Service Worker)

### 10.2 Accessibility (a11y)

**Accessibility ist keine Priorität, aber Best Practices sollten als Nebeneffekt guten Designs mitgenommen werden.**

**Best Practices (ohne strikte Tests/Validierung):**
- **Semantisches HTML:** `<button>` statt `<div onclick>`, `<nav>`, `<main>`, `<article>` wo passend
  - **Vorteil für alle:** Bessere Struktur, klarere Code-Lesbarkeit
- **Ausreichende Kontraste:** Text gut lesbar (nicht nur für Sehbehinderte)
  - **Vorteil für alle:** Bessere Lesbarkeit auch bei Sonnenlicht/schlechtem Display
- **Touch-Target-Size:** Mindestens 44x44px für Touch-Elemente
  - **Vorteil für alle:** Auch mit "dicken Fingern" gut bedienbar, weniger Fehlklicks
- **Keyboard-Navigation:** Tabbable Elemente in logischer Reihenfolge
  - **Vorteil für alle:** Schnellere Bedienung für Power-User

**Keine Anforderung:**
- ❌ WCAG-Compliance
- ❌ Screen-Reader-Testing
- ❌ Lighthouse Accessibility Score
- ❌ ARIA-Labels (außer wo Framework sie automatisch setzt)

**Prinzip:** Wenn es keinen zusätzlichen Aufwand bedeutet, accessibility-freundlich sein. Aber keine extra Tests oder Validierungen.

### 10.3 Browser & Device Compatibility

**Unterstützte Browser:**
- Chrome/Edge (Chromium): Letzte 2 Versionen
- Firefox: Letzte 2 Versionen
- Safari (iOS): Letzte 2 Versionen
- **Kein IE11-Support**

**Primäre Zielgeräte (Viewport-Breiten in CSS-Pixeln):**
- **Mobile (Smartphones):** 320px - 767px Viewport
  - Primärer Fokus: Touch-optimierte Bedienung
  - Einkaufsliste und Kochmodus MÜSSEN hier optimal funktionieren
- **Medium (Tablets):** 768px - 1023px Viewport
  - Funktional, Rezeptverwaltung hier komfortabel nutzbar
- **Large (Desktop):** 1024px+ Viewport
  - Funktional, aber nicht primär optimiert

**Hinweis:** Viewport-Breiten = CSS-Pixel (Device-Independent Pixels), nicht physische Display-Auflösung

**Responsive Design:**
- Mobile-First Ansatz
- Breakpoints an obigen Grenzen (320px, 768px, 1024px)

**PWA-Anforderungen:**
- Installierbar auf iOS (Safari) und Android (Chrome)
- Offline-Funktionalität (Service Worker - siehe HTTPS-Anforderung unten)
- Add to Homescreen Prompt

### 10.4 Usability

**Die App MUSS intuitiv und fehlerverzeihend sein.**

**Prinzipien:**
- **Zero-Training:** Nutzer sollen ohne Anleitung starten können
- **Fehlertoleranz:** Undo-Funktionen, Bestätigungsdialoge bei destruktiven Aktionen
- **Klares Feedback:** Jede Aktion hat sichtbares Feedback (Toast, Animation, State-Change)
- **Progressive Disclosure:** Komplexe Features verstecken, einfache im Vordergrund

**Testing:**
- Informelle Usability-Tests mit Nicht-Technikern
- "Five-Second Test" für wichtige Screens (Einkaufsliste, Wochen-Pool)

### 10.5 Reliability & Data Integrity

**Die App MUSS zuverlässig sein und Daten schützen.**

**Anforderungen:**
- **Uptime:** 99%+ (bei Self-Hosting: abhängig vom Nutzer, aber Software darf nicht crashen)
- **Keine Datenverluste:**
  - Bei App-Crash: Letzte Änderungen aus IndexedDB wiederherstellen
  - Bei Server-Crash: Transaktionale DB-Operationen (ACID)
  - Bei Netzwerk-Unterbrechung: Offline-Queue synchronisiert bei Reconnect
- **Graceful Degradation:**
  - Offline: Einkaufsliste voll funktional
  - Offline: Andere Bereiche zeigen "Offline"-Hinweis, crashen aber nicht
- **Error Handling:**
  - Backend-Errors werden geloggt (Serilog)
  - Frontend zeigt nutzerfreundliche Fehlermeldungen
  - Keine technischen Stack-Traces für Endnutzer

### 10.6 Security & HTTPS

**Siehe auch Abschnitt 8.5 (Datenschutz & Sicherheit)**

**HTTPS-Anforderung:**
- **Für MVP erforderlich:** HTTPS ist notwendig für Offline-Funktionalität (US-306)
- **Warum:** Service Worker (= Offline-Caching) funktioniert nur mit HTTPS (oder localhost)
- **Ohne HTTPS:**
  - App funktioniert komplett, aber **nur online**
  - Im Einkaufsladen ohne Internet: App nicht nutzbar
  - Kern-Use-Case ist broken

**Klarstellung für Entwicklung:**
- **Lokale Entwicklung (dev):** Service Worker funktioniert auf `localhost` OHNE HTTPS
  - Chrome/Edge/Firefox erlauben Service Worker auf localhost auch mit HTTP
  - Entwicklung und Tests für US-306 sind also lokal möglich
- **Deployment (Produktion):** HTTPS ist zwingend erforderlich
  - Let's Encrypt Zertifikat via Reverse Proxy (nginx/Caddy)
  - **NICHT Teil der Implementierungs-Specs** - wird separat dokumentiert

**Für den implementierenden Agenten:**
- Du musst KEIN Deployment-Setup implementieren
- Entwickle und teste US-306 (Offline) lokal auf `http://localhost` (oder dein Dev-Port)
- Service Worker wird funktionieren, weil localhost eine Ausnahme ist
- Produktions-Deployment ist eine separate Aufgabe für später

**Standard-Sicherheitsmaßnahmen:**
- Sichere Passwort-Hashing (ASP.NET Core Identity Defaults: PBKDF2)
- SQL-Injection Prevention (EF Core parametrisiert)
- XSS-Prevention (Framework-Defaults + Content Security Policy)
- CSRF-Protection (ASP.NET Core Anti-Forgery Tokens)

### 10.7 Maintainability & Code Quality

**Die Codebase MUSS wartbar und erweiterbar sein.**

**Standards:**
- **Test Coverage:** 100% angestrebt (Mutation Testing validiert)
- **Code-Style:** Erzwungen via `Directory.Build.props` und Linter
- **Domain-Driven Design:** Patterns konsistent umgesetzt
- **Dokumentation:**
  - Inline-Kommentare nur wo notwendig (Code sollte selbsterklärend sein)
  - API-Dokumentation via Swagger
  - Architektur-Entscheidungen in IMPLEMENTATION_GUIDE.md
- **Technische Schuld:** In AGENT_MEMORY.md tracken, regelmäßig abbauen

**Metriken:**
- SonarQube/Code-Analyse-Tool: A-Rating angestrebt
- Cyclomatic Complexity: < 10 pro Methode
- Keine Duplicate Code Blocks > 5 Zeilen

---

## 11. Offene Entscheidungen / Future Work

**Getroffene Entscheidungen (siehe Abschnitt 2.1):**
- ✅ Frontend-Framework: **React 18+ mit Material UI v6**
- ✅ Datenbank: **PostgreSQL 15+**

**Noch offen:**

1. **LLM-Provider (V2):** OpenAI vs. Anthropic vs. Lokal
   - **Empfehlung:** Konfigurierbar über Interface, Provider zur Laufzeit wählbar
   - **Hinweis:** Erst relevant für V2-Phase (Rezept-Import mit LLM-Fallback)

---

## 12. Agentic Workflow & Session-Management

### 12.1 Ziel: One-Shot-Implementierung mit Kontinuität

Dieses Projekt ist ein Experiment in "Agentic Engineering" - die Implementierung wird primär von einem LLM-Agenten durchgeführt. Der Workflow soll session-übergreifend funktionieren.

### 12.2 Feedback & Beratung durch Sub-Agenten

**Der implementierende Agent SOLL und DARF sich beraten lassen:**

**Erlaubte Feedback-Quellen:**
1. **Menschliches Feedback:** Bei Unklarheiten, Entscheidungen, und Code-Reviews
2. **Sub-Agenten für spezialisierte Expertise (als Berater):**
   - **Refactoring-Agent:** Regelmäßig (z.B. nach jedem TDD-Zyklus) nach sinnvollen Refactorings fragen
   - **UI/UX-Experte:** Bei Frontend-Entscheidungen (Layout, User Flows, Accessibility)
   - **Security-Experte:** Bei sicherheitsrelevanten Implementierungen
   - **Performance-Experte:** Bei Performance-kritischen Komponenten (z.B. Offline-Sync)
   - **Test-Experte:** Zur Validierung der Test-Strategie und Mutation Testing Ergebnisse

**Best Practices:**
- Sub-Agenten standardmäßig als "Second Opinion" nutzen, nicht als Implementierer
- Erkenntnisse aus Sub-Agent-Konsultationen dokumentieren
- Refactoring-Vorschläge in technischer Schuld tracken (siehe unten)

### 12.3 Parallelisierung (Advanced, Optional)

**Hinweis:** Parallelisierung über mehrere Agenten ist möglich, aber **nicht empfohlen** für dieses Projekt.

**Warum nicht?**
- Koordinations-Overhead ist hoch (Git-Merges, Schnittstellen-Absprache)
- Sequentielle Entwicklung ist für diese Scope-Größe effizienter
- Nur sinnvoll bei 5+ parallel arbeitenden Teams

**Falls du es trotzdem versuchen willst:**
- Master-Agent koordiniert, definiert klare Schnittstellen (DTOs, API-Kontrakte)
- Sub-Agenten arbeiten auf Feature-Branches (z.B. `feature/backend-us-301`, `feature/frontend-us-301`)
- File-basierte Trennung: Backend-Agent nur `Server/`, Frontend-Agent nur `Client/`
- Regelmäßige Syncs erforderlich

**Empfehlung:** Nutze Sub-Agenten nur als **Berater** (siehe 12.2), nicht als Implementierer.

### 12.4 Session-übergreifendes Gedächtnis

**Der Agent SOLL ein persistentes Gedächtnis führen:**

**Datei: `docs/AGENT_MEMORY.md`**

**Inhalt:**
- **Implementierungsstatus:**
  - Welche User Stories sind komplett implementiert?
  - Welche sind in Arbeit?
  - Was steht noch aus?

- **Technische Entscheidungen:**
  - Getroffene Entscheidungen mit Begründung (z.B. "Frontend: React gewählt wegen XYZ")
  - Verworfene Alternativen

- **Technische Schuld / Refactoring-Kandidaten:**
  - Code-Bereiche, die später verbessert werden sollten
  - Begründung, warum aktuell nicht refactored wurde
  - Priorisierung

- **Lessons Learned:**
  - Was hat gut funktioniert?
  - Was war problematisch?
  - Welche Patterns haben sich bewährt?

- **Offene Fragen / TODOs:**
  - Punkte, die mit Product Owner geklärt werden müssen
  - Recherche-Aufgaben

**Aktualisierung:**
- Am Ende jeder Arbeits-Session
- Bei wichtigen Entscheidungen
- Nach Abschluss einer User Story oder Phase

**Hinweis:** Änderungen an Requirements oder Entscheidungen sollten AUCH in den jeweiligen Dokumenten (IMPLEMENTATION_GUIDE.md, etc.) reflektiert werden, nicht nur im Agent Memory!

### 12.5 Kontinuität zwischen Sessions

**Beim Start einer neuen Session:**
1. `docs/AGENT_MEMORY.md` lesen
2. Letzte Commits im Git-Log prüfen
3. Offene TODOs aus Memory aufgreifen
4. Mit Product Owner abstimmen, was als nächstes priorisiert wird

**Bei Diskrepanzen:**
- Dokumentation (IMPLEMENTATION_GUIDE.md) > Agent Memory
- Bei Widersprüchen: Product Owner fragen

---

## 13. Nächste Schritte für LLM-Implementierung

**Wenn ein LLM mit der Implementierung startet, sollte es:**

1. **Prüfe ob bereits ein Agent Memory existiert** (`docs/AGENT_MEMORY.md`)
   - Falls JA: Lesen und Kontext aufnehmen
   - Falls NEIN: Neues Memory-File anlegen
2. **Dieses Dokument vollständig lesen** und verstehen
3. **GLOSSARY.md** für Domain-Begriffe konsultieren
4. **USER_STORIES.md** für Feature-Details lesen
5. **Bestehenden Code analysieren** (Shared/Types/, Server/Data/, etc.)
6. **Mit SKELETON-Phase beginnen (falls noch nicht geschehen):**
   - Projekt-Setup / Cleanup
   - Datenbank-Auswahl & Setup (mit Begründung dokumentieren)
   - Frontend-Framework-Entscheidung (ggf. Spike durchführen, Entscheidung dokumentieren)
   - Docker-Konfiguration
   - Basis-Authentifizierung
7. **Iterativ vorgehen:** Feature für Feature, mit TDD
8. **Regelmäßig Sub-Agenten konsultieren** (Refactoring, UI/UX, Security)
9. **Bei Unklarheiten nachfragen** (an den Product Owner / Nutzer)
10. **Agent Memory aktualisieren** am Ende jeder Session

---

## 14. Anhang: Referenzen

- **Domain Model:** `docs/GLOSSARY.md`
- **User Stories:** `docs/USER_STORIES.md`
- **Projekt-README:** `CLAUDE.md` (allgemeine Projektinfos)
- **Bestehender Code:** Siehe `Shared/`, `Server/`, `Client/`
- **Schema.org Recipe:** https://schema.org/Recipe
- **Material Design 3:** https://m3.material.io/

---

**Letzte Aktualisierung:** 2026-02-17
**Version:** 1.2
**Status:** Ready for Implementation

**Changelog:**
- v1.2: Accessibility auf Best Practices reduziert, Viewport-Breiten konkretisiert, HTTPS-Anforderung klargestellt, Deployment-Details entfernt
- v1.1: NFRs hinzugefügt, Mutation Testing für alle Code-Teile, Sub-Agenten als optionale Implementierer, Virtuelle Listen entfernt, Datenexport auf V2+ verschoben
- v1.0: Initiale Version

# Agent Memory - Mahl Project

> **Zweck:** Dieses Dokument dient dem implementierenden Agenten als persistentes Gedächtnis zwischen Sessions. Es trackt Fortschritt, Entscheidungen, technische Schuld und offene Fragen.

**Letzte Aktualisierung:** 2026-02-17
**Session:** Spec-Review & Optimierung (Pre-Implementation)

---

## 1. Implementierungsstatus

### Phase: SKELETON
**Status:** Nicht gestartet | In Arbeit | Abgeschlossen

#### Technische Infrastruktur
- [ ] Projekt-Setup (Backend + Frontend)
- [ ] Docker & Docker Compose
- [ ] Datenbank-Setup & Migrations
- [ ] Basis-Authentifizierung
- [ ] PWA-Grundkonfiguration

#### User Stories (SKELETON) - Final Scope
- [ ] US-904: Zutaten-Verwaltung (CRUD)
- [ ] US-602: Manuelle Rezepterfassung (Titel + Zutaten + Schritte + Quelle)
- [ ] US-803: Rezept dem Wochen-Pool hinzufügen
- [ ] US-201: Einkaufsliste anzeigen (generiert aus Pool)
- [ ] US-303: Artikel abhaken (verschiebt in "Zuletzt gekauft")

**Hinweis:** Folgende Stories wurden zu MVP verschoben:
- US-501 (Pool-Liste), US-505 (Zutaten-Übersicht), US-506 (Koch-Start), US-605 (Schritte anlegen), US-614 (Rezept bearbeiten), US-801 (Rezept-Liste)

**Mutation Testing (Stryker.NET):**
- [ ] SKELETON-Phase abgeschlossen: X% Coverage erreicht

---

### Phase: MVP
**Status:** Nicht gestartet | In Arbeit | Abgeschlossen

#### User Stories (MVP)
- [ ] US-103: Muss-Rezepte
- [ ] US-105: Automatische Vorschläge & Regeln
- [ ] US-106: Besuchs-Planung
- [ ] US-202: Mengen-Anpassung
- [ ] US-301: Intelligente Artikelerfassung
- [ ] US-306: Offline-Verfügbarkeit
- [ ] US-307: Non-Food-Items
- [ ] US-508: Kochmodus
- [ ] US-509: Schritt-Zutaten
- [ ] US-510: Quellen-Zugriff
- [ ] US-607: Zutaten-Zuordnung zu Schritten
- [ ] US-609: Manuelles Tagging
- [ ] US-610: Gesamtzeit
- [ ] US-616: Rezept-Archivierung
- [ ] US-701: Harte Regeln
- [ ] US-702: Sortier-Regeln
- [ ] US-902: Einheiten-Management
- [ ] US-906: Vorrats-Management

**Mutation Testing:**
- [ ] MVP-Phase abgeschlossen: X% Coverage erreicht

---

### Phase: V1
**Status:** Nicht gestartet

### Phase: V2
**Status:** Nicht gestartet

---

## 2. Technische Entscheidungen

### Getroffene Entscheidungen

#### 2026-02-17 - Frontend-Framework
- **Entscheidung:** React 18+ mit Material UI v6
- **Begründung:**
  - Offline-Support (US-306) ist MVP-Anforderung, React-Ökosystem ist überlegen (Workbox, React Query)
  - Material UI v6 bietet vollständigen Material Design 3 Support (stabil)
  - Bestehender Blazor-Code wird nicht weiterverwendet (rudimentär)
  - Mutation Testing mit Stryker-JS ist etabliert
- **Verworfene Alternativen:** Blazor WebAssembly, Vue 3 + Vuetify

#### 2026-02-17 - Datenbank
- **Entscheidung:** PostgreSQL 15+
- **Begründung:**
  - Bessere JSON-Unterstützung für zukünftige Erweiterungen
  - Array-Types vereinfachen Tag-Speicherung
  - Npgsql EF Core Provider ist ausgereift
  - Migration von MariaDB später möglich (beide SQL-konform)
- **Flexibilität:** Keine PostgreSQL-spezifischen Features in V1 verwenden (JSONB, Arrays)

#### 2026-02-17 - Material Design Version
- **Entscheidung:** Material Design 3 (via MUI v6)
- **Begründung:** MUI v6 hat vollständigen MD3-Support (stabil, kein "experimentell")

#### 2026-02-17 - Routing (Frontend)
- **Entscheidung:** React Router v6
- **Begründung:** De-facto Standard für React-Apps

#### 2026-02-17 - API Error Handling
- **Entscheidung:** Problem Details (RFC 7807) via ASP.NET Core + MUI Snackbar
- **Begründung:** Standardisiertes Format, einheitliche UX

#### 2026-02-17 - Docker Deployment
- **Entscheidung:** Docker Compose für PostgreSQL (Pflicht), Backend-Container optional
- **Begründung:** Lokale Entwicklung mit dockerized DB, Backend läuft lokal für schnellere Iteration

#### 2026-02-17 - SKELETON-Scope
- **Entscheidung:** Reduzierung von 11 auf 4 User Stories
- **Begründung:** Echter "Walking Skeleton" sollte minimal sein
- **User Stories:** US-904, US-602, US-803, US-201/303
- **Verschoben zu MVP:** US-501, US-505, US-506, US-605, US-614, US-801

#### 2026-02-17 - Mutation Testing Ziel
- **Entscheidung:** 90%+ Coverage (statt 100%)
- **Begründung:** 100% ist unrealistisch, 90%+ mit begründeten Ausnahmen ist machbar
- **Hybrid-Ansatz:** Volltest am Ende jeder Phase, schnelle Iteration mit `--files` während Entwicklung

#### 2026-02-17 - Authentifizierung in SKELETON
- **Entscheidung:** OPTIONAL überspringen
- **Begründung:** Fokus auf Datenfluss, echtes Auth kommt in MVP
- **Alternative:** Hardcoded User oder gar keiner

#### 2026-02-17 - Einheiten-Konvertierung in SKELETON
- **Entscheidung:** KEINE Umrechnung zwischen verschiedenen Einheiten
- **Begründung:** US-902 (Einheiten-Management) ist MVP
- **Konsequenz:** Duplikate auf Einkaufsliste akzeptiert (z.B. "200g Mehl" + "1 EL Mehl")

#### 2026-02-17 - AlwaysInStock-Flag in SKELETON
- **Entscheidung:** Feld wird schon angelegt, aber funktionslos
- **Begründung:** Vorbereitung für US-906 (MVP), spart Migration-Aufwand
- **Konsequenz:** UI-Feature kommt erst in MVP

#### 2026-02-17 - Abhaken-Verhalten (US-201/303)
- **Entscheidung:** Markieren (BoughtAt-Timestamp), nicht löschen
- **Begründung:** US-303 spezifiziert "verschieben in Bereich 'Zuletzt gekauft'"
- **Konsequenz:** Undo-Funktion (US-401, V1) ist dadurch möglich

#### 2026-02-17 - Einkaufslisten-Generierung (SKELETON vs. MVP)
- **SKELETON-Entscheidung:** Einfache Variante mit Button "Liste generieren"
  - Löscht alte Items, schreibt ALLE Pool-Rezepte neu
  - Aggregation: Gleiche Zutat + Einheit = summieren
  - KEIN Tracking welche Zutat aus welchem Rezept
  - Limitation: Bei Pool-Änderung muss User manuell neu generieren
- **MVP-Entscheidung:** Intelligente Variante mit SourceRecipes-Tracking
  - JSON-Feld `SourceRecipes` speichert { recipeId: quantity }
  - `ManualAdjustment`-Feld für User-Korrekturen
  - Automatisches Anpassen bei Pool-Änderungen
- **Begründung:** SKELETON muss minimal sein, MVP ist Kern-Mehrwert

#### 2026-02-17 - Bilder-Speicherung
- **Entscheidung:** Filesystem (`Server/wwwroot/uploads/recipe-sources/`), NICHT DB
- **Begründung:**
  - DB bleibt klein, schnelle Backups
  - Einfaches Serving (wwwroot = static files)
  - Für Self-Hosted optimal
- **Backup-Strategie:** pg_dump (DB) + tar (Filesystem)
- **V2+:** UI-Feature für Backup/Restore

#### 2026-02-17 - Soft-Delete für Ingredients & Recipes
- **Entscheidung:** DELETE-Endpoints setzen nur `IsDeleted=true`
- **Begründung:** Daten können wiederhergestellt werden, Best Practice
- **SKELETON:** Keine Referenz-Checks (Zutat kann gelöscht werden, auch wenn in Rezept verwendet)
- **MVP:** Foreign Key Constraints + Cascading

#### 2026-02-17 - Frontend-Navigation
- **Entscheidung:** Responsive - Burger-Menü (mobil), Tabs (Desktop)
- **Breakpoint:** 768px (Material UI Standard)
- **Begründung:** Mobile-First Ansatz, beste UX für beide Geräteklassen

#### 2026-02-17 - Rezept-Formular Zutat-Auswahl
- **Entscheidung:** Dropdown mit Autocomplete + manuelle Zutat-Erfassung
- **Begründung:** Flexible UX, verhindert Duplikate, erlaubt aber schnelles Hinzufügen neuer Zutaten
- **Implementierung:** Wenn Zutat nicht existiert, Link "Neue Zutat anlegen" (öffnet Zutat-Dialog)

#### 2026-02-18 - Soft-Delete mit DeletedAt statt IsDeleted
- **Entscheidung:** `DeletedAt` (timestamptz?) statt `IsDeleted` (bool)
- **Begründung:**
  - Mehr Information (wann wurde gelöscht?)
  - Ermöglicht Audit-Queries
  - Ermöglicht automatisches Aufräumen (z.B. Hard-Delete nach 30 Tagen)
  - Moderner Standard
- **Queries:** `WHERE DeletedAt IS NULL` (nicht gelöscht)

#### 2026-02-18 - SourceRecipes als Tabelle statt JSON
- **Entscheidung:** Separate Tabelle `ShoppingListItemSource` statt JSON-Feld
- **Begründung:**
  - Datenintegrität über Performance (Foreign Keys, CASCADE)
  - Einfachere Queries ("Welche Items nutzen Rezept X?")
  - DB-agnostisch (funktioniert überall)
  - Performance ist bei ~80 Items kein Problem
- **Verworfene Alternative:** JSON-Feld (keine Foreign Keys, schwierige Queries)

#### 2026-02-18 - Einkaufsliste UI (Bring!-Stil)
- **Entscheidung:** Große Touch-Buttons (min. 80x80px) statt Checkboxen
- **Visueller Zustand:** Offen = volle Farbe, Gekauft = Grau + reduzierte Opacity (KEIN Durchstrich)
- **Begründung:** Bessere Touch-UX, inspiriert von Bring!-App
- **V1:** Icons pro Zutat (Material UI Icons)
- **V2+:** LLM-generierte Icons

#### 2026-02-18 - Entwicklungs-Workflow (keine Migrationen bis Production)
- **Entscheidung:** KEINE EF Core Migrations bis zur ersten Production-Version
- **Stattdessen:** Database Drop + Recreate + Seed bei Schema-Änderungen
- **Seed-Data:** 5-10 echte Lieblings-Rezepte + 20-30 Standard-Zutaten
- **Begründung:**
  - Schnellere Iteration während Entwicklung
  - Keine Migrations-Hölle
  - App ist sofort nutzbar
  - User haben noch keine echten Daten zu verlieren
- **Ab Production:** Normale Migrations nutzen

#### 2026-02-18 - Backup/Restore Persona (US-909/910)
- **Entscheidung:** "Rezepte-Sammler" Persona verwenden (statt "Self-Hoster")
- **Begründung:**
  - In Single-Tenant ist die Person, die Rezepte sammelt, auch die, die Backups macht
  - "Self-Hoster" existiert nicht als definierte Persona
  - Pragmatischer Ansatz, keine neue Persona nötig
- **User Stories:** Abstrakt formuliert (alle Anwendungsdaten), nicht implementierungsspezifisch

#### 2026-02-18 - Frontend Migration (Blazor → React)
- **Entscheidung:** Blazor-Code (`Client/`) wird KOMPLETT entfernt und durch React ersetzt
- **Begründung:**
  - Entscheidung für React 18+ ist bereits getroffen (siehe 2026-02-17)
  - Bestehender Blazor-Code ist rudimentär, keine Weiterverwendung
  - Cleaner Start für React-Projekt
- **Struktur:** Neues Verzeichnis `client-react/` (oder `Client/` nach Blazor-Löschung)

#### 2026-02-18 - PostgreSQL Setup
- **Entscheidung:** Docker Compose für PostgreSQL
- **Begründung:** Konsistente Entwicklungsumgebung, einfach für neue Entwickler
- **ToDo:** `docker-compose.yml` erstellen mit PostgreSQL 15+ Service

#### 2026-02-18 - Authentifizierung in SKELETON
- **Entscheidung:** Hardcoded User (KEIN ASP.NET Identity in SKELETON)
- **Begründung:**
  - SKELETON fokussiert auf Datenfluss, nicht auf Auth
  - Schnellere Iteration, weniger Komplexität
  - Echtes Auth kommt in MVP
- **Implementierung:** Hardcoded User-ID in Startup oder Middleware

#### 2026-02-18 - Seed-Data Implementation
- **Entscheidung:** C# Extension Method statt Raw SQL
- **Begründung:**
  - Type-safe, versioniert mit Code
  - Eleganter, keine manuelle SQL-Ausführung
  - Nutzbar in Tests
- **Implementierung:** `app.SeedDatabase()` Extension in `Program.cs`
- **Quelle:** `Server/Data/SeedData.sql` als Vorlage (migrieren zu C#)

#### 2026-02-18 - Image-Upload Storage
- **Entscheidung:** Echte Dateien in `Server/wwwroot/uploads/recipe-sources/{recipeId}/`
- **Begründung:**
  - Einfach, testbar, Best Practice für Self-Hosted
  - DB bleibt klein, Backups einfach
- **NICHT:** In-Memory oder Azure Blob (erst später bei Multi-Tenant)

#### 2026-02-18 - Mutation Testing Workflow
- **Entscheidung:** Hybrid-Ansatz mit `--files` für schnelles Feedback
- **Workflow:**
  - **Während Feature-Entwicklung:** `dotnet stryker --files <geänderte-Datei>` (schnell)
  - **Nach jedem Feature:** Nur relevante Teile + beeinflusste Bereiche
  - **Am Ende der Phase:** Vollständiger Lauf über gesamte Anwendung
- **Begründung:** Schnelles Feedback-Loop, keine langen Wartezeiten

#### 2026-02-18 - UI/UX Sub-Agent Konsultation
- **Entscheidung:** Nach Bedarf, auch nach einzelnen Features möglich
- **Begründung:** Schnelleres Feedback, iterative Verbesserung
- **Abwägung:** Balance zwischen Feedback-Geschwindigkeit und Overhead

#### 2026-02-18 - Projektkontext & Entscheidungsfreiheit
- **Kontext:** Projekt war ursprünglich "Spielprojekt" (Blazor + MariaDB), nun "Pivot" zu Production-Ready (React + PostgreSQL)
- **Bestehender Code:** Shopping-Liste Code ist **Referenz-Implementierung**, zeigt gewünschte Patterns, aber nicht sakrosankt
- **Agent-Autonomie:** Agent hat **Entscheidungsfreiheit** für technische Details
  - ✅ Selbst entscheiden: Validierung, Error Codes, Schema-Details, UI-Details
  - ❓ Nachfragen: Business-Logic, Architektur-Änderungen, unklare Requirements
- **Dokumentation:** Neue Sektion 1.2 "Decision-Making Guide" in IMPLEMENTATION_GUIDE.md
- **Begründung:** Spec ist detailliert, aber nicht mikromanagend - Agent soll eigenständig arbeiten können

#### 2026-02-18 - Erste Aufgaben für implementierenden Agenten
- **Priority 1:** Bereinigung alter Technologie-Referenzen
  1. Lösche `Client/` (Blazor)
  2. Entferne MariaDB Provider, installiere Npgsql
  3. Fixe Connection String (DefaultConnection)
  4. Erstelle neue InitialCreate Migration für PostgreSQL
  5. Initialisiere React-Projekt (`npm create vite@latest Client -- --template react-ts`)
- **Priority 2:** SKELETON User Stories implementieren (TDD)
- **Referenz:** Bestehender Shopping-Liste Code als Vorbild für Patterns

---

## 3. Technische Schuld / Refactoring-Kandidaten

### Hohe Priorität
- **[Bereich/File]:** [Beschreibung des Problems]
  - **Grund:** Warum wurde es nicht sofort behoben?
  - **Vorgeschlagene Lösung:** [...]
  - **Geschätzte Dauer:** [...]

### Mittlere Priorität
- [...]

### Niedrige Priorität / Nice-to-Have
- [...]

---

## 4. Lessons Learned

### Was hat gut funktioniert?
- TDD-Zyklus mit [Framework/Tool]
- [...]

### Was war problematisch?
- [Problem-Beschreibung]
  - **Lösung:** [...]

### Bewährte Patterns
- Custom Value Types für Domain Validation
- [...]

---

## 5. Sub-Agent Konsultationen

### [Datum] - Refactoring-Agent
- **Kontext:** Nach Implementierung von US-XXX
- **Feedback:** [Zusammenfassung]
- **Umgesetzt:** Ja | Nein | Teilweise
- **Begründung:** [...]

### [Datum] - UI/UX-Experte
- **Kontext:** Einkaufsliste Layout
- **Feedback:** [...]
- **Umgesetzt:** [...]

---

## 6. Offene Fragen / TODOs

### Klärung mit Product Owner benötigt
- [ ] [Frage 1]
- [ ] [Frage 2]

### Recherche-Aufgaben
- [ ] [Aufgabe 1]

### Nächste Session
- [ ] [Was sollte als nächstes gemacht werden?]

---

## 7. Mutation Testing Ergebnisse

### SKELETON-Phase
- **Datum:** [...]
- **Coverage:** X%
- **Survived Mutants:** X
- **Probleme:** [...]
- **Maßnahmen:** [...]

### MVP-Phase
- **Datum:** [...]
- **Coverage:** X%
- [...]

---

## 8. Git-Historie (Wichtige Commits)

- `[Commit-Hash]`: [US-XXX] [Kurzbeschreibung]
- `[Commit-Hash]`: [US-YYY] [Kurzbeschreibung]

---

## 9. Session-Log

### Session 1 - [Datum]
- **Dauer:** X Stunden
- **Erledigt:** US-201, US-303
- **Probleme:** [...]
- **Nächste Session:** US-501 fortsetzen

### Session 2 - [Datum]
- [...]

---

**Hinweise:**
- Dieses Dokument ist für den Agenten, nicht für Menschen optimiert
- Bei Widersprüchen zu IMPLEMENTATION_GUIDE.md: Specs in IMPLEMENTATION_GUIDE.md sind führend
- Änderungen an Requirements sollten AUCH in IMPLEMENTATION_GUIDE.md reflektiert werden

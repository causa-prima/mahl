# Session 044 – 2026-04-01

**Phase:** SKELETON (Neustart – Projekt-Setup)
**Dauer:** ~1 Session (kein Code implementiert)

---

## Was wurde gemacht

### Architektur-Check US-904 (Schritt 0 von implementing-feature)
- Gherkin-Feature-Datei `features/ingredients.feature` geschrieben (6 Szenarien: 2 happy-path, 2 error, 1 edge-case)
- Outside-In ATDD Reihenfolge geklärt: Gherkin → Playwright E2E (rot) → Frontend → Backend-Test (rot) → Code (grün)
- PUT-Endpoint für Zutaten nach MVP verschoben (kein Edit-UI im SKELETON-Frontend)
- Architektur-Entscheidungen für US-904 dokumentiert (CA1062, AlwaysInStock-Platzierung)

### Dependency-Freigabe
- Vollständige 5-Punkte-Begründung für alle Pakete (NuGet + npm) erstellt
- Svelte als React-Alternative evaluiert und abgelehnt (MUI-v7-Inkompatibilität, Immutability-Konflikt)
- AwesomeAssertions statt FluentAssertions gewählt (Apache 2.0 Fork, identisches API)
- xUnit v3 (`xunit.v3`) statt v2 gewählt (v2 nur noch Security-Updates)
- DEPENDENCIES.md ohne Versionsnummern beschlossen

### Projekt-Setup
- `Infrastructure/mahl.Infrastructure.csproj`, `Server/mahl.Server.csproj`, `Server.Tests/mahl.Server.Tests.csproj` angelegt (durch User manuell)
- `Client/package.json` angelegt (durch User manuell)
- `mahl.sln` erstellt, alle drei C#-Projekte hinzugefügt
- `dotnet restore` erfolgreich
- `npm install` + `npm update` + `npm audit fix` via cmd.exe (WSL-npm-Problem entdeckt und behoben)
- Playwright Chromium-Browser installiert
- Alle Pakete auf aktuelle Versionen gebracht

### Dokumentations-Updates
- `docs/SKELETON_SPEC.md`: PUT-Endpoint nach MVP verschoben
- `docs/history/decisions.md`: 4 neue Einträge (AwesomeAssertions, xUnit v3, Svelte, DEPENDENCIES-Versionspolicy)
- `docs/DEV_WORKFLOW.md`: npm via cmd.exe dokumentiert, Playwright-Setup, E2E-Test-Befehl, OpenAPI-URL korrigiert
- `Directory.Build.props`: Meziantou 3.0.43, SonarAnalyzer 10.22.0 aktualisiert

---

## Probleme / Reibungspunkte

- **Infrastructure-Pfad falsch:** User legte `.claude/Infrastructure/mahl.Infrastructure.csproj` an statt `Infrastructure/mahl.Infrastructure.csproj` – manuell korrigiert.
- **npm in WSL defekt:** WSL-npm zeigt auf Windows-nvm-Pfade die im WSL-Kontext nicht auflösen. Workaround: `cmd.exe /c` wie bei dotnet. In DEV_WORKFLOW.md dokumentiert.
- **Paket-Begründungen im ersten Anlauf unvollständig:** Punkt 4 (warum Alternativen ausscheiden) fehlte bei einigen Paketen – musste nachgebessert werden.

---

## Offene Punkte (nächste Session)

- implementing-feature Schritt 1 (TDD-Zyklus) für US-904 noch nicht gestartet:
  - Playwright-Konfiguration (`playwright.config.ts`) noch nicht geschrieben
  - Vite-Konfiguration (`vite.config.ts`) noch nicht geschrieben
  - Playwright E2E-Test für `@US-904-happy-path` (rot) noch nicht geschrieben
  - Backend-Code + Tests: nicht begonnen
- `npx playwright install chromium` via cmd.exe muss der User noch manuell ausführen (wurde erklärt, aber nicht verifiziert)
